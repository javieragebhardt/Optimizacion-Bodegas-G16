import pandas as pd
import numpy as np
from gurobipy import Model, GRB, quicksum
import construccion_datos
import matplotlib.pyplot as plt

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
for i in range(1, 11):
    localizaciones_iniciales[i] = construccion_datos.calcular_coordenadas_xy(construccion_datos.dict_bodegas[i]['LAT'], construccion_datos.dict_bodegas[i]['LONG'])

# Importación de datos
I = construccion_datos.I
J = range(1, 11)
M = 1800 #TODO VER
N = M
a = construccion_datos.a

# Modelo
m = Model()

# m.setParam('TimeLimit', 3600)
m.setParam('LogFile', filename)

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

for j, [x_val, y_val] in localizaciones_iniciales.items():
    x[j].start = x_val
    y[j].start = y_val

# Optimiza el modelo
m.optimize(mycallback)

# Solución:
for j in J:
    print(j, x[j].x, y[j].x)

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