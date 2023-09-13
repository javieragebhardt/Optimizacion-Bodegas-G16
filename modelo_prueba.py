import pandas as pd
import numpy as np
from gurobipy import Model, GRB, quicksum
import construccion_datos

# Importación de datos
I = construccion_datos.I
J = range(1, 11)
M = 1800
N = M
a = construccion_datos.a

# Modelo
m = Model()
#Variables
x = m.addVars(J, vtype = GRB.CONTINUOUS, name = "x") 
y = m.addVars(J, vtype = GRB.CONTINUOUS, name = "y")
z = m.addVars(I, J, vtype = GRB.BINARY, name = "z")
D = m.addVars(I, J, vtype = GRB.CONTINUOUS, name = "D")
M1 = m.addVars(I, J, name="M1")
M2 = m.addVars(I, J, name="M2")
m.update()

# Función Objetivo
m.setObjective(quicksum(D[i, j] for i in I for j in J))

m.update()
# Restricciones
m.addConstrs((quicksum(z[i, j] for j in J) == 1 for i in I), name = 'asignación clientes-bodega')
m.addConstrs((M * z[i, j] >= D[i, j] for i in I for j in J), name = 'relación D-z')
# valor absoluto de la definición de D1

# m.addConstrs(((a[i][0] - x[j]) + (a[i][1] - y[j]) >= D[i, j] + N * (1 - z[i, j]) for i in I for j in J), name = 'definición D 1')
# m.addConstrs((- (a[i][0] - x[j]) + (a[i][1] - y[j]) >= D[i, j] + N * (1 - z[i, j]) for i in I for j in J), name = 'definición D 2')
# m.addConstrs(((a[i][0] - x[j]) - (a[i][1] - y[j]) >= D[i, j] + N * (1 - z[i, j]) for i in I for j in J), name = 'definición D 3')
# m.addConstrs((- (a[i][0] - x[j]) - (a[i][1] - y[j]) >= D[i, j] + N * (1 - z[i, j]) for i in I for j in J), name = 'definición D 4')

# Restricciones para el primer valor absoluto
m.addConstrs((a[i][0] - x[j] <= M1[i, j] for i in I for j in J), name='Abs1a')
m.addConstrs((-a[i][0] + x[j] <= M1[i, j] for i in I for j in J), name='Abs1b')

# Restricciones para el segundo valor absoluto
m.addConstrs((a[i][1] - y[j] <= M2[i, j] for i in I for j in J), name='Abs2a')
m.addConstrs((-a[i][1] + y[j] <= M2[i, j] for i in I for j in J), name='Abs2b')

# Añadir la restricción que une todo
m.addConstrs((M1[i, j] + M2[i, j] >= D[i, j] + N * (1 - z[i, j]) for i in I for j in J), name='definición D total')


# # Añadir restricciones para el primer valor absoluto
# m.addConstrs((a[i][0] - x[j] >= M1[i, j] for i in I for j in J), name='Abs1a')
# m.addConstrs((-a[i][0] + x[j] >= M1[i, j] for i in I for j in J), name='Abs1b')

# # Añadir restricciones para el segundo valor absoluto
# m.addConstrs((a[i][1] - y[j] >= M2[i, j] for i in I for j in J), name='Abs2a')
# m.addConstrs((-a[i][1] + y[j] >= M2[i, j] for i in I for j in J), name='Abs2b')

# # Añadir la restricción que une todo
# m.addConstrs((M1[i, j] + M2[i, j] >= D[i, j] + N * (1 - z[i, j]) for i in I for j in J), name='definición D 1')

m.optimize()

# m.computeIIS()
# archivo = 'encontrar infactibilidad.lp'
# m.write(archivo)

# Resultados:

# print(f'Valor objetivo: {m.objVal}')
# for j in J:
#     print(f'La bodega {j} tiene coordenadas ({x[j].x}, {y[j].x})')

for i in I:
    for j in J:
        if z[i,j].x > 0:
            print(M1[i,j].x)
            print(f'{j}: {i}')