import pandas as pd
from gurobipy import Model, GRB, quicksum
import construccion_datos
import folium
import json


#######################
#### MODELO GUROBI ####
#######################

class LocalizacionOptima:

    contador = 0

    def __init__(self, p, d):
        # Parámetros
        self.valores_y = {}
        self.p = p
        self.h = construccion_datos.h
        self.d = d
        if self.d == construccion_datos.d_Manhattan:
            self.tipo_distancia = 'Manhattan'
        # elif self.d == construccion_datos.d_Manhattan_2:
        #     self.tipo_distancia = 'Manhattan_2'
        elif self.d == construccion_datos.d_mapbox:
            self.tipo_distancia = 'Mapbox'
        else:
            self.tipo_distancia = 'Segunda Bodega'
        self.rutas = construccion_datos.rutas
        self.resultados = dict()
        # Conjuntos
        self.I = construccion_datos.I
        self.J = construccion_datos.J
        # Modelo
        self.m = Model()
        # Variables
        self.x = self.m.addVars(self.J, vtype = GRB.BINARY, name = "x")
        self.y = self.m.addVars(self.I, self.J, vtype = GRB.CONTINUOUS, name = "y")
        self.m.update()
        # Función Objetivo
        self.m.setObjective(quicksum(self.d[i][j] * self.y[i, j] for i in self.I for j in self.J)) 
        # Restricciones
        self.m.addConstrs((self.y.sum(i, '*') == 1 for i in self.I), name = "asignación_demanda")
        self.m.addConstrs((self.y[i, j] <= self.x[j] for i in self.I for j in self.J), name = "límite_asignación")
        self.m.addConstr(self.x.sum() == p, name = "número_bodegas")
        # self.m.addConstrs((quicksum(self.y[i, j] * (self.d[i][j] / v) for j in self.J) <= self.t[i] for i in self.I), name = "tiempo_máximo")

    def optimizar(self):
        self.m.optimize()

    def generar_mapa(self):
        dict_bodegas = construccion_datos.dict_bodegas
        colores_bodega = {1: "blue", 2: "red", 3: "green", 4: "darkblue", 5: "orange", 
                          6: "purple", 7: "gray", 8: "cadetblue", 9: "black", 
                          10: "darkgreen"}

        # Crear un mapa centrado en una ubicación inicial
        m = folium.Map(location=[-33.45, -70.65], zoom_start=7)

        # Agregar marcadores para las bodegas que tienen al menos un cliente asignado
        for bodega_id, coordenadas in dict_bodegas.items():
            if bodega_id in (cliente['Bodega Asignada'] for cliente in self.resultados.values()) and bodega_id in [1, 2, 3] or True:
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
        dict_clientes = construccion_datos.dict_ventas
        for cliente_id, datos_cliente in self.resultados.items():
            # print(cliente_id, datos_cliente)
            if datos_cliente['Bodega Asignada'] in [1, 2, 3] or True:
                lat = dict_clientes[cliente_id]['LAT']
                long = dict_clientes[cliente_id]['LON']
                destino = [lat, long]
                comuna = dict_clientes[cliente_id]['Comuna Despacho']
                color = colores_bodega[datos_cliente['Bodega Asignada']]
                folium.Circle(
                    location=[lat, long],
                    radius=1000,  # Radio del círculo en metros
                    popup=f'Cliente {cliente_id}',
                    color=color,
                    fill=True,
                    fill_color=color
                ).add_to(m)
                # Conectar el cliente con su bodega asignada con una línea coloreada
                bodega_coords = dict_bodegas[datos_cliente['Bodega Asignada']]
                origen = [bodega_coords['LAT'], bodega_coords['LONG']]
                if self.d == construccion_datos.d_Manhattan:
                    folium.PolyLine(    
                        locations=[[(destino[0], origen[1]), (origen[0], origen[1])]],
                        color=color,
                        weight=2.5,
                        opacity=1,
                        popup=f'Cliente {cliente_id}'
                    ).add_to(m)

                    folium.PolyLine(
                        locations=[[(destino[0], destino[1]), (destino[0], origen[1])]],
                        color=color,
                        weight=2.5,
                        opacity=1,
                        popup=f'Cliente {cliente_id}'
                    ).add_to(m)
        
                elif self.d == construccion_datos.d_mapbox:
                    route_coords = self.rutas[comuna][datos_cliente['Bodega Asignada']]
                    formatted_coords = [(coord[1], coord[0]) for coord in route_coords] 
                    folium.PolyLine(locations=formatted_coords, color=color, popup=f'Cliente {cliente_id}', weight = 2.5, opacity = 1).add_to(m)

        # Guardar el mapa en un archivo HTML
        m.save(f'resultados/mapa_p_{self.p}_{self.tipo_distancia}.html')

    def generar_data_frame(self, dict, filename):
        df = pd.DataFrame(dict)
        df = df.T
        df.to_excel(filename, index=True)

    def resolver(self):
        self.optimizar()
        # self.generar_data_frame(self.generar_diccionario_resultados(), self.filename)
        self.calcular_tiempos()
        self.generar_mapa()
        self.guardar_vo()
        self.guardar_x()

    def guardar_valores_y_json(self, nombre_archivo):
        with open(nombre_archivo, 'w') as archivo:
            json.dump(self.valores_y, archivo)

    def resolver_2(self):
        self.optimizar()
        # Guarda los valores de y en el diccionario
        for i in self.I:
            self.valores_y[i] = dict()
            for j in self.J:
                self.valores_y[i][j] = round(self.y[i, j].x)
        # Llama al método para guardar los valores en un archivo JSON
        self.guardar_valores_y_json('valores_y.json')

    
    def guardar_vo(self):
        with open('resultados/valoresFO.txt', 'a') as file:
            file.write(f"p_{self.p}_{self.tipo_distancia} = {self.m.ObjVal}\n")
    
    def guardar_x(self):
        estado =  dict()
        for j in self.J:
            if self.x[j].x != 0:
                estado[j] = 1
            else:
                estado[j] = 0
        df = pd.DataFrame(estado, index=[0])
        df = df.T
        df.to_excel(f'resultados/bodegas_abiertas_p_{self.p}_{self.tipo_distancia}.xlsx', index=True)
    
    def calcular_tiempos(self):
        ventas = construccion_datos.dict_ventas
        for i in self.I:
            self.resultados[i] = dict()
            categoria = ventas[i]['Categoria'] 
            if categoria == 'Premium':
                tiempo_max = 12
            elif categoria == 'Gold':
                tiempo_max = 24
            elif categoria == 'Silver':
                tiempo_max = 48
            for j in self.J:
                for v in [15, 30, 45]:
                    if self.y[i, j].x > 0 and self.x[j].x > 0:
                        self.resultados[i]['Tiempo'] = self.d[i][j] / v
                        self.resultados[i]['Bodega Asignada'] = j
                        self.resultados[i]['Tiempo Categoría'] = tiempo_max
                        self.resultados[i][f'Cumple Mínimo v={v}'] = 0
                        if self.d[i][j] / v <= tiempo_max:
                            self.resultados[i][f'Cumple Mínimo v={v}'] = 1

        self.generar_data_frame(self.resultados, f'resultados/tiempos_p_{self.p}_{self.tipo_distancia}.xlsx')  
        return self.resultados


#### Distintos casos #####

# for p in [3, 5, 10]:
#     # LocalizacionOptima(p, construccion_datos.d_Manhattan).resolver()
#     LocalizacionOptima(p, construccion_datos.d_mapbox).resolver()
LocalizacionOptima(10, construccion_datos.d_Manhattan).resolver()

#TODO FALTA CORRER CASOS PARA DISTINTA CATEGORICACIÓN mapbox y v = 30 km/hr p=10, p= 5 y p= 3

#LocalizacionOptima(10, construccion_datos.dic_segunda_bodega).resolver()   # para segunda bodega mas cercana con p = 10
