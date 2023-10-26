import folium
import pandas as pd
import numpy as np
from gurobipy import Model, GRB, quicksum
import construccion_datos_aloc
import construccion_datos
import matplotlib.pyplot as plt
import json
import csv

# CONSTRUCCIÓN DE DATOS:

I = construccion_datos_aloc.I
J = construccion_datos_aloc.J
a = construccion_datos_aloc.a
M = construccion_datos_aloc.M
localizaciones_iniciales = construccion_datos_aloc.localizaciones_iniciales

# MODELO:

m = Model()

m.setParam('StartNodeLimit', 100000)
m.Params.TimeLimit = 300


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

# Modificar esta restricción para cada M
m.addConstrs((M[i] * z[i, j] >= D[i, j] for i in I for j in J), name='relacion z-D')

m.addConstrs((a[i][0] - x[j] == delta_x_pos[i, j] - delta_x_neg[i, j] for i in I for j in J), name='deltas 1')

m.addConstrs((a[i][1] - y[j] == delta_y_pos[i, j] - delta_y_neg[i, j] for i in I for j in J), name='deltas 2')

m.addConstrs((D[i, j] >= delta_x_pos[i, j] + delta_x_neg[i, j] + delta_y_pos[i, j] + delta_y_neg[i, j] - M[i] * (1 - z[i, j]) for i in I for j in J), name='definición de D')

m.addConstrs((delta_x_pos[i, j] >= 0 for i in I for j in J), name='delta x positivo')
m.addConstrs((delta_x_neg[i, j] >= 0 for i in I for j in J), name='delta x negativo')
m.addConstrs((delta_y_pos[i, j] >= 0 for i in I for j in J), name='delta y positivo')
m.addConstrs((delta_y_neg[i, j] >= 0 for i in I for j in J), name='delta y negativo')
m.addConstrs(y[j] <= y[j+1] for j in J[:-1])

for j, [x_val, y_val] in localizaciones_iniciales.items():
    if j <= construccion_datos_aloc.p:
        x[j].start = x_val
        y[j].start = y_val

# Optimiza el modelo
m.optimize()


# Solución:
for j in J:
    print(j, x[j].x, y[j].x)

# Pasar a latitud y longitud:

localizacion_bodegas = dict()
for j in J:
    localizacion_bodegas[j] = dict()
    xy = construccion_datos_aloc.calcular_xy_coordenadas_2(x[j].x, y[j].x)
    print(f'Bodega {j}:  LON: {xy[0]}, LAT: {xy[1]}')
    localizacion_bodegas[j]['LON'] = xy[0]
    localizacion_bodegas[j]['LAT'] = xy[1]

print(f'Valor objetivo: {m.objVal}')





