import pandas as pd
from gurobipy import Model, GRB, quicksum
import numpy as np
import construccion_datos

#######################
#### MODELO GUROBI ####
#######################

class LocalizacionOptima:

    def __init__(self, p, v, t):
        # Parámetros
        self.p = p
        self.v = v
        self.t = t
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
        self.m.addConstrs((quicksum(self.y[i, j] * (self.d[i][j] / v) for j in self.J) <= t for i in self.I), name = "tiempo_máximo")

    def optimizar(self):
        self.m.optimize()
    
    def generar_diccionario_resultados(self):
        resultados = dict()
        for j in self.J:
            if self.x[j].x > 0:
                resultados[j] = list()
                for i in self.I:
                    if self.y[i, j].x > 0:
                        resultados[j].append(i)
        return resultados
    
    def resolver(self):
        self.optimizar()
        return self.generar_diccionario_resultados(), self.m.objVal

prueba = LocalizacionOptima(10, 60, 48).resolver()[0]
print(prueba)