# Importación base de datos
import json
import pandas as pd
import folium

class CasoBase:

    def __init__(self, proy, tipo_distancia):
        self.proy = proy
        self.vo = 0
        self.resultados = dict()
        self.tipo_distancia = tipo_distancia
        self.cargar_datos()

    def cargar_datos(self):
        if not self.proy:
            nombre_bdd = "BDD_Bodegas_Categorizada.xlsx"
        else:
            nombre_bdd = "BDD_Bodegas_Categorizada_proy.xlsx"

        # Importación base de datos
        self.bdd_ventas = pd.read_excel(nombre_bdd)
        self.bdd_bodegas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=2)
        self.bdd_comunas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=3)

        # Pasamos la columna de fechas a formato de fechas
        self.bdd_ventas['Fecha'] = pd.to_datetime(self.bdd_ventas['Fecha'])

        # Agrupación de ventas por cliente y completar comuna
        self.bdd_ventas_agrupadas = self.bdd_ventas.groupby("ID Cliente").agg({"Cantidad": "sum", "Comuna Despacho": "first", 'ID Bodega Despacho': 'first', 'Categoria': 'first'}).reset_index()
        self.bdd_ventas_agrupadas = self.bdd_ventas_agrupadas.merge(self.bdd_comunas, left_on='Comuna Despacho', right_on='Comuna')
        self.bdd_ventas_agrupadas = self.bdd_ventas_agrupadas[self.bdd_ventas_agrupadas["Cantidad"] != 0] #TODO revisar

        # Armamos los diccionarios
        self.dict_bodegas = self.bdd_bodegas.set_index('ID Bodega')[['LAT', 'LONG']].to_dict(orient='index') 
        self.dict_ventas = self.bdd_ventas_agrupadas.set_index('ID Cliente')[['Cantidad', 'Comuna Despacho', 'LAT', 'LON', 'ID Bodega Despacho', 'Categoria']].to_dict(orient='index') 

        # Parametros
        self.I = list(self.dict_ventas.keys())
        self.J = list(self.dict_bodegas.keys())

        if self.tipo_distancia == 'manhattan':

            nombre_archivo = 'd_manhattan.json'
            if self.proy:
                nombre_archivo = 'd_manhattan_proy.json'
            with open(nombre_archivo, 'r') as archivo_json:
                d_Manhattan = json.load(archivo_json)
            self.d = {int(k1): {int(k2): v2 for k2, v2 in v1.items()} for k1, v1 in d_Manhattan.items()}    


        elif self.tipo_distancia == 'mapbox':
            distancias_en_red = pd.read_excel("distancias_comunas_bodegas_mapbox.xlsx")
            distancias_en_red = distancias_en_red.replace(0, 0.0001)
            self.d = {}
            for i in self.dict_ventas.keys():
                data_dict = dict()
                comuna = self.dict_ventas[i]['Comuna Despacho']
                bodegas_comuna = distancias_en_red[distancias_en_red['Unnamed: 0']== comuna]
                data_dict = bodegas_comuna.set_index('Unnamed: 0').squeeze().to_dict()
                self.d[i] = data_dict

            with open('rutas.json', 'r') as archivo_json:
                data = json.load(archivo_json)

            # Convierte los índices de bodegas a enteros
            self.rutas = {
                comuna: {int(id_bodega): coordenadas for id_bodega, coordenadas in bodegas.items()}
                for comuna, bodegas in data.items()
            }



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
                for v in [15, 30, 45]:
                    if self.dict_ventas[i]['ID Bodega Despacho'] == j:
                        self.vo += self.d[i][j]
                        self.resultados[i]['Tiempo'] = self.d[i][j] / v
                        self.resultados[i]['Bodega Asignada'] = j
                        self.resultados[i]['Tiempo Categoría'] = tiempo_max
                        self.resultados[i][f'Cumple Mínimo v={v}'] = 0
                        if self.d[i][j] / v <= tiempo_max:
                            self.resultados[i][f'Cumple Mínimo v={v}'] = 1

    def generar_data_frame(self, dict, filename):
        df = pd.DataFrame(dict)
        df = df.T
        df.to_excel(filename, index=True)

    def generar_mapa(self):
        dict_clientes = self.dict_ventas
        dict_bodegas = self.dict_bodegas
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

            if self.tipo_distancia == 'manhattan':
                folium.PolyLine(
                    locations=[[lat, long], [bodega_coords['LAT'], bodega_coords['LONG']]],
                    color=color,
                    weight=2.5,
                    opacity=1
                ).add_to(m)
            else:

                route_coords = self.rutas[comuna][datos_cliente['ID Bodega Despacho']]

                formatted_coords = [(coord[1], coord[0]) for coord in route_coords] 

                folium.PolyLine(locations=formatted_coords, color=color, popup=f'Cliente {cliente_id}', weight = 2.5, opacity = 1).add_to(m)
       


        # Guardar el mapa en un archivo HTML
        m.save(f'resultados/mapa_{self.tipo_distancia}_caso_base.html')

    def guardar_vo(self):
        with open('resultados/valoresFO.txt', 'a') as file:
            file.write(f"{self.tipo_distancia}_caso_base = {self.vo}\n")

    def resolver(self):
        self.calculos()
        self.generar_data_frame(self.resultados, f'resultados/tiempos_{self.tipo_distancia}_caso_base.xlsx')
        self.generar_mapa()
        self.guardar_vo()


CasoBase(False, 'mapbox').resolver()

#TODO calcular valores FO para estos casos