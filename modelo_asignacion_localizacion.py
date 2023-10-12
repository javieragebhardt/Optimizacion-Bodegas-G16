import folium
import pandas as pd
import numpy as np
from gurobipy import Model, GRB, quicksum
import construccion_datos
import matplotlib.pyplot as plt
import json
import csv



# Guardar log

filename = 'modelo_localizacion.log'

# Función de callback
obj_vals = []
runtimes = []
gaps = []

def mycallback(model, where):
    if where == GRB.Callback.MIP:
        objbnd = model.cbGet(GRB.Callback.MIP_OBJBND)
        objbst = model.cbGet(GRB.Callback.MIP_OBJBST)
        runtime = model.cbGet(GRB.Callback.RUNTIME)
        gap = abs(objbst - objbnd) / abs(objbst)
        obj_vals.append(objbnd)
        runtimes.append(runtime)
        gaps.append(gap)

# Ubicación inicial de bodegas en coordenadas cartesianas:

localizaciones_iniciales = dict()
for i in range(1, 3):
    localizaciones_iniciales[i] = construccion_datos.calcular_coordenadas_xy_2(construccion_datos.dict_bodegas[i]['LAT'], construccion_datos.dict_bodegas[i]['LONG'])

# Importación de datos
# I = construccion_datos.I

p = 3

J = range(1, p + 1)
M = 1400 #TODO VER
N = M
a = construccion_datos.a


with open('valores_y.json', 'r') as archivo:
    valores_y = json.load(archivo)

valores_y = {int(k): {int(k2): v2 for k2, v2 in v.items()} for k, v in valores_y.items()}

I = []

for cliente, asignaciones in valores_y.items():
    for bodega in range(1, p + 1):
        if asignaciones.get(bodega, 0) == 1:  # Verificar si está asignado a la bodega 1
            I.append(cliente)


nuevos_valores_y = {}

for cliente, asignaciones in valores_y.items():
    asignaciones_filtradas = {bodega: valor for bodega, valor in asignaciones.items() if bodega in (1, 2)}
    if asignaciones_filtradas:
        for bodega in range(1, p + 1):
            if asignaciones_filtradas.get(bodega, 0) == 1:
                nuevos_valores_y[cliente] = asignaciones_filtradas


# Modelo
m = Model()

# m.setParam('TimeLimit', 3600)
# m.setParam('LogFile', filename)
m.setParam('StartNodeLimit', 100000)
# m.setParam('Method', 2)
# m.setParam('Heuristics', 0)
# m.setParam('MipFocus', 3)
# m.Params.MIPGap = 0.80  # 50%
m.Params.TimeLimit = 300

# Configurar la tolerancia de factibilidad para limitar a dos decimales
# m.Params.FeasibilityTol = 0.01  # Esto limitará a dos decimales (0.01) en los cálculos


# Variables
x = m.addVars(J, vtype=GRB.CONTINUOUS, name="x") 
y = m.addVars(J, vtype=GRB.CONTINUOUS, name="y")
z = m.addVars(I, J, vtype=GRB.BINARY, name="z")
D = m.addVars(I, J, vtype=GRB.CONTINUOUS, name="D")
delta_x_pos = m.addVars(I, J, name="delta_x_pos")
delta_x_neg = m.addVars(I, J, name="delta_x_neg")
delta_y_pos = m.addVars(I, J, name="delta_y_pos")
delta_y_neg = m.addVars(I, J, name="delta_y_neg")

m.update()

# Función Objetivo
m.setObjective(quicksum(D[i, j] for i in I for j in J), GRB.MINIMIZE)

# Restricciones
m.addConstrs((quicksum(z[i, j] for j in J) == 1 for i in I), name="asignación clientes-bodega")

m.addConstrs((M * z[i, j] >= D[i, j] for i in I for j in J), name='relacion z-D')

m.addConstrs((a[i][0] - x[j] == delta_x_pos[i, j] - delta_x_neg[i, j] for i in I for j in J), name='deltas 1')

m.addConstrs((a[i][1] - y[j] == delta_y_pos[i, j] - delta_y_neg[i, j] for i in I for j in J), name='deltas 2')

m.addConstrs((D[i, j] >= delta_x_pos[i, j] + delta_x_neg[i, j] + delta_y_pos[i, j] + delta_y_neg[i, j] - N * (1 - z[i, j]) for i in I for j in J), name='definición de D')

m.addConstrs((delta_x_pos[i, j] >= 0 for i in I for j in J), name='delta x positivo')
m.addConstrs((delta_x_neg[i, j] >= 0 for i in I for j in J), name='delta x negativo')
m.addConstrs((delta_y_pos[i, j] >= 0 for i in I for j in J), name='delta y positivo')
m.addConstrs((delta_y_neg[i, j] >= 0 for i in I for j in J), name='delta y negativo')
m.addConstrs(y[j] <= y[j+1] for j in {1,2})

for j, [x_val, y_val] in localizaciones_iniciales.items():
    x[j].start = x_val
    y[j].start = y_val

for i in I:
    for j in J:
        z[i, j].start = valores_y[i][j]


# Optimiza el modelo
m.optimize(mycallback)

# Verificar si se detuvo debido a la brecha de optimización
if m.status == GRB.OPTIMAL:
    print("Optimización exitosa.")
elif m.status == GRB.TIME_LIMIT:
    print("Se detuvo debido al límite de tiempo.")
elif m.status == GRB.OBJ_LIMIT:
    print("Se detuvo debido al límite de brecha de optimización.")
else:
    print("Optimización finalizada con estado:", m.status)


# Solución:
for j in J:
    print(j, x[j].x, y[j].x)

resultados_Z = []
for i in I:
    asignado = False
    for j in J:
        if z[i, j].X > 0:
            resultados_Z.append([f'z[{i},{j}]', z[i, j].X])
            asignado = True
    if not asignado:
        resultados_Z.append([f'z[{i},{j}]', 0])

# Guardar los resultados en el archivo CSV
with open('resultados_Z.csv', 'w', newline='') as archivo:
    writer = csv.writer(archivo)
    writer.writerows(resultados_Z)

resultados_D = []

# Guardar los resultados en el archivo CSV
with open('resultados_D.csv', 'w', newline='') as archivo:
    writer = csv.writer(archivo)
    writer.writerows(resultados_D)


for j in J:
    for i in I:
        if D[i, j].X > 0:
            resultados_D.append([f'D[{i},{j}]', D[i, j].X])

# Guardar los resultados en el archivo CSV
with open('resultados_D.csv', 'w', newline='') as archivo:
    writer = csv.writer(archivo)
    writer.writerows(resultados_D)


#guardar bodegas
localizacion_bodegas = dict()
for j in J:
    localizacion_bodegas[j] = dict()
    xy = construccion_datos.calcular_xy_coordenadas_2(x[j].x, y[j].x)
    print(f'Bodega {j}:  LON: {xy[0]}, LAT: {xy[1]}')
    localizacion_bodegas[j]['LON'] = xy[0]
    localizacion_bodegas[j]['LAT'] = xy[1]


dict_resultados = dict()

ventas = construccion_datos.dict_ventas
for i in I:
    dict_resultados[i] = dict()
    categoria = ventas[i]['Categoria'] 
    if categoria == 'Premium':
        tiempo_max = 12
    elif categoria == 'Gold':
        tiempo_max = 24
    elif categoria == 'Silver':
        tiempo_max = 48
    for j in J:
        for v in [15, 30, 45]:
            # dict_resultados[i]['Tiempo'] = 0
            # dict_resultados[i]['Bodega Asignada'] = 0
            # dict_resultados[i]['Tiempo Categoría'] = tiempo_max
            # dict_resultados[i][f'Cumple Mínimo v={v}'] = 0            
            if D[i, j].x > 0:
                dict_resultados[i]['Tiempo'] = D[i, j].x / v
                dict_resultados[i]['Bodega Asignada'] = j
                dict_resultados[i]['Tiempo Categoría'] = tiempo_max
                dict_resultados[i][f'Cumple Mínimo v={v}'] = 0
                if D[i, j].x / v <= tiempo_max:
                    dict_resultados[i][f'Cumple Mínimo v={v}'] = 1


    
dict_bodegas = construccion_datos.dict_bodegas
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
dict_clientes = construccion_datos.dict_ventas
for cliente_id, datos_cliente in dict_resultados.items():
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

m.save(f'resultados/mapa_p_3_localizacion_asignacion.html')


# Graficar
plt.figure(figsize=(15, 5))

# Gráfico de Valores Objetivos
plt.subplot(1, 3, 1)
plt.plot(runtimes, obj_vals, '-o')
plt.title('Valor Objetivo vs. Tiempo')
plt.xlabel('Tiempo (s)')
plt.ylabel('Valor Objetivo')

# Gráfico de Gaps
plt.subplot(1, 3, 3)
plt.plot(runtimes, gaps, '-o', color='red')
plt.title('Gap vs. Tiempo')
plt.xlabel('Tiempo (s)')
plt.ylabel('Gap (%)')

plt.tight_layout()
plt.show()


