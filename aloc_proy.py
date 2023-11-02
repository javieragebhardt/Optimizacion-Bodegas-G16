import folium
import pandas as pd
from gurobipy import Model, GRB, quicksum
import construccion_datos_aloc_proy

# CONSTRUCCIÓN DE DATOS:

I = construccion_datos_aloc_proy.I
J = construccion_datos_aloc_proy.J
a = construccion_datos_aloc_proy.a
N = construccion_datos_aloc_proy.N
localizaciones_iniciales = construccion_datos_aloc_proy.localizaciones_iniciales
M = construccion_datos_aloc_proy.M
ns = construccion_datos_aloc_proy.ns
IP = construccion_datos_aloc_proy.ip
IPP = construccion_datos_aloc_proy.ipp
c = construccion_datos_aloc_proy.c

print(f"Largos: {len(I)}, {len(J)}")


# MODELO:

m = Model()

m.setParam('StartNodeLimit', 100000)
# m.Params.TimeLimit = 20


# Variables
x = m.addVars(J, vtype=GRB.CONTINUOUS, name="x") 
y = m.addVars(J, vtype=GRB.CONTINUOUS, name="y")
z = m.addVars(IPP, J, vtype=GRB.BINARY, name="z")
D = m.addVars(I, J, vtype=GRB.CONTINUOUS, name="D")
delta_x_pos = m.addVars(I, J, name="delta_x_pos")
delta_x_neg = m.addVars(I, J, name="delta_x_neg")
delta_y_pos = m.addVars(I, J, name="delta_y_pos")
delta_y_neg = m.addVars(I, J, name="delta_y_neg")

m.update()

# Función Objetivo
m.setObjective(quicksum(D[i, j] for i in I for j in J), GRB.MINIMIZE)

# Restricciones
m.addConstrs((quicksum(z[i, j] for j in J) == 1 for i in IPP), name="asignación clientes-bodega")

# Modificar esta restricción para cada M
m.addConstrs((M[i]* z[i, j] >= D[i, j] for i in IPP for j in J), name='relacion z-D IPP')

m.addConstrs((a[i][0] - x[j] == delta_x_pos[i, j] - delta_x_neg[i, j] for i in I for j in J), name='deltas 1')

m.addConstrs((a[i][1] - y[j] == delta_y_pos[i, j] - delta_y_neg[i, j] for i in I for j in J), name='deltas 2')

m.addConstrs((D[i, j] >= delta_x_pos[i, j] + delta_x_neg[i, j] + delta_y_pos[i, j] + delta_y_neg[i, j] - N[i] * (1 - z[i, j]) for i in IPP for j in J), name='definición de D')

m.addConstrs((delta_x_pos[i, j] >= 0 for i in I for j in J), name='delta x positivo')
m.addConstrs((delta_x_neg[i, j] >= 0 for i in I for j in J), name='delta x negativo')
m.addConstrs((delta_y_pos[i, j] >= 0 for i in I for j in J), name='delta y positivo')
m.addConstrs((delta_y_neg[i, j] >= 0 for i in I for j in J), name='delta y negativo')
m.addConstrs((D[i, j] <= ns[i] for i in I for j in J), name='nivel servicio')
m.addConstrs(y[j] <= y[j+1] for j in J[:-1])
m.addConstrs((M[i] * c[i][j] >= D[i, j] for i in IP for j in J), name='relacion z-D IP')
m.addConstrs((D[i, j] >= delta_x_pos[i, j] + delta_x_neg[i, j] + delta_y_pos[i, j] + delta_y_neg[i, j] - N[i] * (1 - c[i][j]) for i in IP for j in J), name='definición de D IP')

#Solucion inicial entregada
for j, [x_val, y_val] in localizaciones_iniciales.items():
    # if j <= construccion_datos_aloc.p:
    if j == 9:
        val = 1
    elif j == 4:
        val = 2
    elif j == 1:
        val = 3
    x[val].start = x_val
    y[val].start = y_val


#Calculamos el valor objetivo de esta solución inicial:
objective_value = 0
for i in I:
    for j in J:
        objective_value += abs(a[i][0]-x[j].start) + abs(a[i][1]-y[j].start)

print(f"Objetivo: {objective_value}")


# Optimiza el modelo
m.optimize()


# # Para ver cuales son las restricciones infactibles
# m.computeIIS()

# m.write("model.ilp")

# Solución:
for j in J:
    print(j, x[j].x, y[j].x)

# Pasar a latitud y longitud:

localizacion_bodegas = dict()
for j in J:
    localizacion_bodegas[j] = dict()
    xy = construccion_datos_aloc_proy.calcular_xy_coordenadas_2(x[j].x, y[j].x)
    print(f'Bodega {j}:  LON: {xy[0]}, LAT: {xy[1]}')
    localizacion_bodegas[j]['LON'] = xy[0]
    localizacion_bodegas[j]['LAT'] = xy[1]

dict_resultados = dict()

ventas = construccion_datos_aloc_proy.dict_ventas
for i in I:
    dict_resultados[i] = dict()
    for j in J:           
        if D[i, j].x > 0:
            dict_resultados[i]['Bodega Asignada'] = j
            dict_resultados[i]['Tiempo'] = D[i, j].x / 45
            dict_resultados[i]['Cantidad'] = ventas[i]['Cantidad']
            dict_resultados[i]['Comuna Despacho'] = ventas[i]['Comuna Despacho']
            dict_resultados[i]['Categoria'] = ventas[i]['Categoria']
            dict_resultados[i]['LAT'] = ventas[i]['LAT']
            dict_resultados[i]['LON'] = ventas[i]['LON'] 
            dict_resultados[i]['X'] = a[i][0]
            dict_resultados[i]['Y'] = a[i][1] 
    
dict_bodegas = construccion_datos_aloc_proy.dict_bodegas
colores_bodega = {1: "blue", 2: "red", 3: "green", 4: "darkblue", 5: "orange", 
                    6: "purple", 7: "gray", 8: "cadetblue", 9: "black", 
                    10: "darkgreen"}

# Crear un mapa centrado en una ubicación inicial
m = folium.Map(location=[-33.45, -70.65], zoom_start=7)

# Agregar marcadores para las bodegas que tienen al menos un cliente asignado
for bodega_id, coordenadas in localizacion_bodegas.items():
    if bodega_id in (cliente['Bodega Asignada'] for cliente in dict_resultados.values()):
        num = bodega_id
        if num == 10:
            num = 'warehouse'
        lat = coordenadas['LAT']
        lon = coordenadas['LON']
        folium.Marker(
            location=[lat, lon],
            popup=f'Bodega {bodega_id}',
            icon=folium.Icon(icon=str(num), prefix='fa', 
                            color=colores_bodega[bodega_id])
        ).add_to(m)

# Agregar círculos para los clientes en el mapa con colores de bodega
dict_clientes = construccion_datos_aloc_proy.dict_ventas
for cliente_id, datos_cliente in dict_resultados.items():
    if datos_cliente:
        if datos_cliente['Bodega Asignada'] == 0:
            print(f'cliente {cliente_id} no asignado')
        elif len(datos_cliente) != 0:
            lat = dict_clientes[cliente_id]['LAT']
            lon = dict_clientes[cliente_id]['LON']
            destino = [lat, lon]
            comuna = dict_clientes[cliente_id]['Comuna Despacho']
            color = colores_bodega[datos_cliente['Bodega Asignada']]
            folium.Circle(
                location=[lat, lon],
                radius=1000,  # Radio del círculo en metros
                popup=f'Cliente {cliente_id}',
                color=color,
                fill=True,
                fill_color=color
            ).add_to(m)
            # Conectar el cliente con su bodega asignada con una línea coloreada
            bodega_coords = localizacion_bodegas[datos_cliente['Bodega Asignada']]
            origen = [bodega_coords['LAT'], bodega_coords['LON']]
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

            # elif self.d == construccion_datos.d_mapbox:
            #     route_coords = self.rutas[comuna][datos_cliente['Bodega Asignada']]
            #     formatted_coords = [(coord[1], coord[0]) for coord in route_coords] 
            #     folium.PolyLine(locations=formatted_coords, color=color, popup=f'Cliente {cliente_id}', weight = 2.5, opacity = 1).add_to(m)
        else:
            print(f'cliente {cliente_id} no asignado')

df = pd.DataFrame.from_dict(dict_resultados, orient='index')
df.to_excel('Datos_Aloc_proy_3_bodegas.xlsx', index=True)



m.save(f'resultados/mapa_p_3_localizacion_asignacion_proy.html')
