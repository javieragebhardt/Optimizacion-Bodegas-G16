# Importación base de datos
import pandas as pd
import numpy as np
import construccion_datos
import folium

class CasoBase:

    def __init__(self, v, d):
        self.v = v
        self.d = d
        self.I = construccion_datos.I
        self.J = construccion_datos.J
        self.h = construccion_datos.h
        self.dict_ventas = construccion_datos.dict_ventas
        self.dict_bodegas = construccion_datos.dict_bodegas 
        if self.d == construccion_datos.d_Manhattan:
            self.tipo_distancia = 'Manhattan'
        elif self.d == construccion_datos.d_mapbox:
            self.tipo_distancia = 'Mapbox'
        self.vo = 0
        self.resultados = dict()
        self.rutas = construccion_datos.rutas

    def calculos(self):
        for i in self.I:
            self.resultados[i] = dict()
            categoria = self.dict_ventas[i]['Categoria'] 
            if categoria == 'Premium':
                tiempo_max = 12
            elif categoria == 'Gold':
                tiempo_max = 24
            elif categoria == 'Silver':
                tiempo_max = 48

            for j in self.J:
                if self.dict_ventas[i]['ID Bodega Despacho'] == j:
                    self.vo += self.d[i][j]
                    self.resultados[i]['Tiempo'] = self.d[i][j] / self.v
                    self.resultados[i]['Bodega Asignada'] = j
                    self.resultados[i]['Tiempo Categoría'] = tiempo_max
                    self.resultados[i]['Cumple Mínimo'] = 0
                    if self.d[i][j] / self.v <= tiempo_max:
                        self.resultados[i]['Cumple Mínimo'] = 1

    def generar_data_frame(self, dict, filename):
        df = pd.DataFrame(dict)
        df = df.T
        df.to_excel(filename, index=True)

    def generar_mapa(self):
        dict_clientes = self.dict_ventas
        dict_bodegas = construccion_datos.dict_bodegas
        colores_bodega = {1: "blue", 2: "red", 3: "green", 4: "darkblue", 5: "orange", 
                          6: "purple", 7: "gray", 8: "cadetblue", 9: "black", 
                          10: "darkgreen"}
        # Crear un mapa centrado en una ubicación inicial
        m = folium.Map(location=[-33.45, -70.65], zoom_start=7)

        # Agregar marcadores para las bodegas que tienen al menos un cliente asignado
        for bodega_id, coordenadas in dict_bodegas.items():
            num = bodega_id
            if num == 10:
                num = 'warehouse'
            lat = coordenadas['LAT']
            long = coordenadas['LONG']
            folium.Marker(
                location=[lat, long],
                popup=f'Bodega {bodega_id}',
                icon=folium.Icon(icon=str(num), prefix='fa', 
                                    color=colores_bodega[bodega_id])
            ).add_to(m)


        # Agregar círculos para los clientes en el mapa con colores de bodega
        for cliente_id, datos_cliente in dict_clientes.items():
            # print(datos_cliente)
            lat = datos_cliente['LAT']
            long = datos_cliente['LON']
            comuna = datos_cliente['Comuna Despacho']
            color = colores_bodega[datos_cliente['ID Bodega Despacho']]
            folium.Circle(
                location=[lat, long],
                radius=1000,  # Radio del círculo en metros
                popup=f'Cliente {cliente_id}',
                color=color,
                fill=True,
                fill_color=color
            ).add_to(m)
            # Conectar el cliente con su bodega asignada con una línea coloreada
            bodega_coords = dict_bodegas[datos_cliente['ID Bodega Despacho']]

            if self.d == construccion_datos.d_Manhattan:
                folium.PolyLine(
                    locations=[[lat, long], [bodega_coords['LAT'], bodega_coords['LONG']]],
                    color=color,
                    weight=2.5,
                    opacity=1
                ).add_to(m)
            elif self.d == construccion_datos.d_mapbox:

                route_coords = self.rutas[comuna][datos_cliente['ID Bodega Despacho']]

                formatted_coords = [(coord[1], coord[0]) for coord in route_coords] 

                folium.PolyLine(locations=formatted_coords, color=color, weight = 2.5, opacity = 1).add_to(m)
       


        # Guardar el mapa en un archivo HTML
        m.save(f'resultados/mapa_v_{self.v}_{self.tipo_distancia}_caso_base.html')

    def guardar_vo(self):
        with open('resultados/valoresFO.txt', 'a') as file:
            file.write(f"v_{self.v}_{self.tipo_distancia}_caso_base = {self.vo}\n")

    def resolver(self):
        self.calculos()
        self.generar_data_frame(self.resultados, f'resultados/tiempos_v_{self.v}_{self.tipo_distancia}_caso_base.xlsx')
        self.generar_mapa()
        # self.guardar_vo()
        
# CasoBase(15, construccion_datos.d_Manhattan).resolver()
CasoBase(15, construccion_datos.d_mapbox).resolver()
# CasoBase(30, construccion_datos.d_Manhattan).resolver()
# CasoBase(30, construccion_datos.d_mapbox).resolver()
# CasoBase(45, construccion_datos.d_Manhattan).resolver()
# CasoBase(45, construccion_datos.d_mapbox).resolver()


#TODO calcular valores FO para estos casos