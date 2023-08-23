import pandas as pd
from gurobipy import Model, GRB, quicksum
import numpy as np
import construccion_datos

#######################
#### MODELO GUROBI ####
#######################

m = Model()


#Conjuntos



#Parámetros

h =
p = 10 # Número de bodegas a ubicar
v = 60 # Velocidad promedio del vehículo de desoacho TODO cambiar
d = construccion_datos.d

#Variables

x = m.addVars()
y = m.addVars()

m.update()

#Función Objetivo

#Restricciones
