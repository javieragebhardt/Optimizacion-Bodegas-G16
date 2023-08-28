import pandas as pd
from gurobipy import Model, GRB, quicksum
import numpy as np
import construccion_datos
import folium


#######################
#### MODELO GUROBI ####
#######################

class LocalizacionOptima:

    contador = 0

    def __init__(self, p, v, t, filename):
        # Parámetros
        self.p = p
        self.v = v
        self.t = t
        self.filename = filename
        self.h = construccion_datos.h
        self.d = construccion_datos.d
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
        self.m.setObjective(quicksum(self.h[i] * self.d[i][j] * self.y[i, j] for i in self.I for j in self.J)) 
        # Restricciones
        self.m.addConstrs((self.y.sum(i, '*') == 1 for i in self.I), name = "asignación_demanda")
        self.m.addConstrs((self.y[i, j] <= self.x[j] for i in self.I for j in self.J), name = "límite_asignación")
        self.m.addConstr(self.x.sum() == p, name = "número_bodegas")
        self.m.addConstrs((quicksum(self.y[i, j] * (self.d[i][j] / v) for j in self.J) <= self.t[i] for i in self.I), name = "tiempo_máximo")

    def optimizar(self):
        self.m.optimize()

    def generar_diccionario_resultados(self):
        resultados = dict()
        dict_ventas = construccion_datos.dict_ventas
        for i in self.I:
            for j in self.J:
                if self.y[i, j].x > 0 and self.x[j].x > 0:
                    dict_ventas[i]['Bodega Asignada'] = j
                    resultados[i] = j    
        return dict_ventas

    def generar_mapa(self):
        dict_bodegas = construccion_datos.dict_bodegas
        dict_clientes = self.generar_diccionario_resultados()
        colores_bodega = {1: "blue", 2: "red", 3: "green", 4: "darkgreen", 5: "orange", 6: "purple", 7: "gray", 8: "cadetblue", 9: "black", 10: "darkblue"}

        # Crear un mapa centrado en una ubicación inicial
        m = folium.Map(location=[-33.45, -70.65], zoom_start=7)

        # Agregar marcadores para las bodegas que tienen al menos un cliente asignado
        for bodega_id, coordenadas in dict_bodegas.items():
            if any(cliente['Bodega Asignada'] == bodega_id for cliente in dict_clientes.values()):
                lat = coordenadas['LAT']
                long = coordenadas['LONG']
                folium.Marker(
                    location=[lat, long],
                    popup=f'Bodega {bodega_id}',
                    icon=folium.Icon(icon='warehouse', prefix='fa', color=colores_bodega[bodega_id])
                ).add_to(m)

        # Agregar círculos para los clientes en el mapa con colores de bodega
        for cliente_id, datos_cliente in dict_clientes.items():
            lat = datos_cliente['LAT']
            long = datos_cliente['LON']
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
            folium.PolyLine(
                locations=[[lat, long], [bodega_coords['LAT'], bodega_coords['LONG']]],
                color=color,
                weight=2.5,
                opacity=1
            ).add_to(m)

        # Guardar el mapa en un archivo HTML
        m.save(f'mapa_p_{self.p}_v_{self.v}_{self.filename[11:13]}.html')

    def generar_data_frame(self, dict, filename):
        df = pd.DataFrame(dict)
        df = df.T
        df.to_excel(filename, index=False)

    def resolver(self):
        self.optimizar()
        self.generar_data_frame(self.generar_diccionario_resultados(), self.filename)
        self.generar_mapa()
        return self.generar_diccionario_resultados(), self.m.objVal
    


prueba1 = LocalizacionOptima(10, 60, construccion_datos.t1, 'resultados_t1.xlsx').resolver()
prueba2 = LocalizacionOptima(10, 116, construccion_datos.t2, 'resultados_t2.xlsx').resolver()

print(prueba1[1])
print(prueba2[1])