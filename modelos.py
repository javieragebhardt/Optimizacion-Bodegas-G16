import pandas as pd
from gurobipy import Model, GRB, quicksum
import construccion_datos
import folium

class Modelos:

    def __init__(self, modelo, tipo_d, proy):
        datos = construccion_datos.ConstruccionDatos(modelo, tipo_d, proy)
        self.h = datos.h
        self.d = datos.d
        self.tipo_distancia = datos.tipo_d
        self.I = datos.I
        self.J = datos.J
        self.a = datos.a
        self.N = datos.N
        self.M = datos.M
        self.ns = datos.ns
        self.IP = datos.ip
        self.IPP = datos.ipp
        self.c = datos.c
        self.p = 3
        self.datos = datos
        self.resultados = dict()
        self.modelo = modelo
        if self.modelo == 'pmedian':
            self.pmedian()
        elif self.modelo == 'aloc':
            self.aloc()

    def pmedian(self):
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
        self.m.addConstr(self.x.sum() == self.p, name = "número_bodegas")
        self.m.optimize()
        self.resultados_pmedian()
    
    def resultados_pmedian(self):
        ventas = self.datos.dict_ventas
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
                if self.y[i, j].x > 0 and self.x[j].x > 0:
                    self.resultados[i]['Bodega Asignada'] = j
                    self.resultados[i]['Tiempo'] = self.d[i][j] / 45
                    self.resultados[i]['Cantidad'] = ventas[i]['Cantidad']
                    self.resultados[i]['Comuna Despacho'] = ventas[i]['Comuna Despacho']
                    self.resultados[i]['Tiempo Categoría'] = tiempo_max
                    self.resultados[i][f'Cumple Mínimo v={45}'] = 0
                    if self.d[i][j] / 45 <= tiempo_max:
                        self.resultados[i][f'Cumple Mínimo v={45}'] = 1
        if self.datos.proy:
            nombre_archivo = f'resultados/datos_{self.modelo}_p_{self.p}_{self.tipo_distancia}_proy.xlsx'
        else:
            nombre_archivo = f'resultados/datos_{self.modelo}_p_{self.p}_{self.tipo_distancia}.xlsx'
        df = pd.DataFrame.from_dict(self.resultados, orient='index')
        df.to_excel(nombre_archivo, index=True)
        self.generar_mapa() 

    def aloc(self):
        self.m = Model()
        self.m.setParam('StartNodeLimit', 100000)
        # Variables
        self.x = self.m.addVars(self.J, vtype=GRB.CONTINUOUS, name="x") 
        self.y = self.m.addVars(self.J, vtype=GRB.CONTINUOUS, name="y")
        self.z = self.m.addVars(self.IPP, self.J, vtype=GRB.BINARY, name="z")
        self.D = self.m.addVars(self.I, self.J, vtype=GRB.CONTINUOUS, name="D")
        self.delta_x_pos = self.m.addVars(self.I, self.J, name="delta_x_pos")
        self.delta_x_neg = self.m.addVars(self.I, self.J, name="delta_x_neg")
        self.delta_y_pos = self.m.addVars(self.I, self.J, name="delta_y_pos")
        self.delta_y_neg = self.m.addVars(self.I, self.J, name="delta_y_neg")
        self.m.update()
        # Función Objetivo
        self.m.setObjective(quicksum(self.D[i, j] for i in self.I for j in self.J), GRB.MINIMIZE)
        # Restricciones
        self.m.addConstrs((quicksum(self.z[i, j] for j in self.J) == 1 for i in self.IPP), name="asignación clientes-bodega")
        # Modificar esta restricción para cada M
        self.m.addConstrs((self.M[i]* self.z[i, j] >= self.D[i, j] for i in self.IPP for j in self.J), name='relacion z-D IPP')
        self.m.addConstrs((self.a[i][0] - self.x[j] == self.delta_x_pos[i, j] - self.delta_x_neg[i, j] for i in self.I for j in self.J), name='deltas 1')
        self.m.addConstrs((self.a[i][1] - self.y[j] == self.delta_y_pos[i, j] - self.delta_y_neg[i, j] for i in self.I for j in self.J), name='deltas 2')
        self.m.addConstrs((self.D[i, j] >= self.delta_x_pos[i, j] + self.delta_x_neg[i, j] + self.delta_y_pos[i, j] + self.delta_y_neg[i, j] - self.N[i] * (1 - self.z[i, j]) for i in self.IPP for j in self.J), name='definición de D')
        self.m.addConstrs((self.delta_x_pos[i, j] >= 0 for i in self.I for j in self.J), name='delta x positivo')
        self.m.addConstrs((self.delta_x_neg[i, j] >= 0 for i in self.I for j in self.J), name='delta x negativo')
        self.m.addConstrs((self.delta_y_pos[i, j] >= 0 for i in self.I for j in self.J), name='delta y positivo')
        self.m.addConstrs((self.delta_y_neg[i, j] >= 0 for i in self.I for j in self.J), name='delta y negativo')
        self.m.addConstrs((self.D[i, j] <= self.ns[i] for i in self.I for j in self.J), name='nivel servicio')
        self.m.addConstrs(self.y[j] <= self.y[j+1] for j in self.J[:-1])
        self.m.addConstrs((self.M[i] * self.c[i][j] >= self.D[i, j] for i in self.IP for j in self.J), name='relacion z-D IP')
        self.m.addConstrs((self.D[i, j] >= self.delta_x_pos[i, j] + self.delta_x_neg[i, j] + self.delta_y_pos[i, j] + self.delta_y_neg[i, j] - self.N[i] * (1 - self.c[i][j]) for i in self.IP for j in self.J), name='definición de D IP')
        self.m.optimize()
        self.resultados_aloc()

    def resultados_aloc(self):
        self.localizacion_bodegas = dict()
        for j in self.J:
            self.localizacion_bodegas[j] = dict()
            xy = self.datos.calcular_xy_coordenadas_2(self.x[j].x, self.y[j].x)
            print(f'Bodega {j}:  LON: {xy[0]}, LAT: {xy[1]}')
            self.localizacion_bodegas[j]['LONG'] = xy[0]
            self.localizacion_bodegas[j]['LAT'] = xy[1]
        ventas = self.datos.dict_ventas
        for i in self.I:
            self.resultados[i] = dict()
            for j in self.J:           
                if self.D[i, j].x > 0:
                    self.resultados[i]['Bodega Asignada'] = j
                    self.resultados[i]['Tiempo'] = self.D[i, j].x / 45
                    self.resultados[i]['Cantidad'] = ventas[i]['Cantidad']
                    self.resultados[i]['Comuna Despacho'] = ventas[i]['Comuna Despacho']
                    self.resultados[i]['Categoria'] = ventas[i]['Categoria']
                    self.resultados[i]['LAT'] = ventas[i]['LAT']
                    self.resultados[i]['LON'] = ventas[i]['LON'] 
                    self.resultados[i]['X'] = self.a[i][0]
                    self.resultados[i]['Y'] = self.a[i][1]
        if self.datos.proy:
            nombre_archivo = f'resultados/datos_{self.modelo}_p_{self.p}_{self.tipo_distancia}_proy.xlsx'
        else:
            nombre_archivo = f'resultados/datos_{self.modelo}_p_{self.p}_{self.tipo_distancia}.xlsx'
        df = pd.DataFrame.from_dict(self.resultados, orient='index')
        df.to_excel(nombre_archivo, index=True)
        self.generar_mapa() 

    def generar_mapa(self):
        
        colores_bodega = {1: "blue", 2: "red", 3: "green", 4: "darkblue", 5: "orange", 
                          6: "purple", 7: "gray", 8: "cadetblue", 9: "black", 
                          10: "darkgreen"}

        # Crear un mapa centrado en una ubicación inicial
        m = folium.Map(location=[-33.45, -70.65], zoom_start=7)

        # Agregar marcadores para las bodegas que tienen al menos un cliente asignado
        if self.modelo == 'pmedian':
            dict_bodegas = self.datos.dict_bodegas
        elif self.modelo == 'aloc':
            dict_bodegas = self.localizacion_bodegas
        for bodega_id, coordenadas in dict_bodegas.items():
            if bodega_id in (cliente['Bodega Asignada'] for cliente in self.resultados.values()):
                num = bodega_id
                if num == 10:
                    num = 'warehouse'
                lat = coordenadas['LAT']
                long = coordenadas['LONG']
                folium.Marker(location=[lat, long], popup=f'Bodega {bodega_id}', icon=folium.Icon(icon=str(num), prefix='fa', color=colores_bodega[bodega_id])).add_to(m)

        # Agregar círculos para los clientes en el mapa con colores de bodega
        dict_clientes = self.datos.dict_ventas
        for cliente_id, datos_cliente in self.resultados.items():
            if len(datos_cliente) != 0:
                # print(cliente_id, datos_cliente)
                lat = dict_clientes[cliente_id]['LAT']
                long = dict_clientes[cliente_id]['LON']
                destino = [lat, long]
                comuna = dict_clientes[cliente_id]['Comuna Despacho']
                color = colores_bodega[datos_cliente['Bodega Asignada']]
                folium.Circle( location=[lat, long], radius=1000, popup=f'Cliente {cliente_id}', color=color, fill=True, fill_color=color).add_to(m) 
                # Conectar el cliente con su bodega asignada con una línea coloreada
                bodega_coords = dict_bodegas[datos_cliente['Bodega Asignada']]
                origen = [bodega_coords['LAT'], bodega_coords['LONG']]
                if self.tipo_distancia == 'manhattan':
                    folium.PolyLine(locations=[[(destino[0], origen[1]), (origen[0], origen[1])]], color=color, weight=2.5, opacity=1, popup=f'Cliente {cliente_id}').add_to(m)
                    folium.PolyLine(locations=[[(destino[0], destino[1]), (destino[0], origen[1])]], color=color, weight=2.5, opacity=1, popup=f'Cliente {cliente_id}').add_to(m)
                elif self.tipo_distancia == 'mapbox':
                    route_coords = self.rutas[comuna][datos_cliente['Bodega Asignada']]
                    formatted_coords = [(coord[1], coord[0]) for coord in route_coords] 
                    folium.PolyLine(locations=formatted_coords, color=color, popup=f'Cliente {cliente_id}', weight = 2.5, opacity = 1).add_to(m)

        # Guardar el mapa en un archivo HTML
        if self.datos.proy:
            nombre_archivo = f'resultados/mapa_{self.modelo}_p_{self.p}_{self.tipo_distancia}_proy.html'
        else:
            nombre_archivo = f'resultados/mapa_{self.modelo}_p_{self.p}_{self.tipo_distancia}.html'
        m.save(nombre_archivo) 

# Modelos('pmedian', 'manhattan', proy=True)
Modelos('aloc', 'manhattan', proy=True)      