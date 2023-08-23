import pandas as pd
from gurobipy import Model, GRB, quicksum
import numpy as np
import construccion_datos

#######################
#### MODELO GUROBI ####
#######################

m = Model()

# Conjuntos

I = construccion_datos.I
J = construccion_datos.J

# Parámetros

h = construccion_datos.h  # Demanda clientes -> diccionario h[id_cliente]
d = construccion_datos.d
p = 10 # Número de bodegas a ubicar
t = 48 # Tiempo máximo de despacho a clientes TODO nos lo tienen que dar
v = 60 # Velocidad promedio del vehículo de despacho TODO cambiar

# Variables

x = m.addVars(J, vtype = GRB.BINARY, name = "x")
y = m.addVars(I, J, vtype = GRB.CONTINUOUS, name = "y")

m.update()

# Función Objetivo

m.setObjective(quicksum(h[i] * d[i, j - 1] * y[i, j] for i in I for j in J)) 

# Restricciones

m.addConstrs((y.sum(i, '*') == 1 for i in I), name = "asignación_demanda")
m.addConstrs((y[i, j] <= x[j] for i in I for j in J), name = "límite_asignación")
m.addConstr(x.sum() == p, name = "número_bodegas")
m.addConstrs((quicksum(y[i, j] * (d[i, j - 1] / v) for j in J) <= t for i in I), name = "tiempo_máximo")

m.optimize()

for j in J:
    if x[j].x > 0:
        print(f"La bodega {j} es abierta")
    else:
        print(f"La bodega {j} NO es abierta")

for i in I:
    for j in J:
        if y[i, j].x > 0:
            print(f"Fracción de la demanda del cliente {i} que es asignada a la bodega {j} = {y[i, j].x}")


def obtener_resultados(modelo, x, y, I, J):
    resultados = {}
    asignaciones = {}

    for j in J:
        if x[j].x > 0.5:
            resultados[j] = []

    for i in I:
        for j in J:
            if y[i, j].x > 0:
                if j in resultados:
                    resultados[j].append(i)
                asignaciones[(i, j)] = y[i, j].x

    return resultados, asignaciones

resultados, asignaciones = obtener_resultados(m, x, y, I, J)