# Importación base de datos
import pandas as pd
import numpy as np
import construccion_datos

#self.m.setObjective(quicksum(self.h[i] * self.d[i][j] * self.y[i, j] for i in self.I for j in self.J)) 

I = construccion_datos.I
J = construccion_datos.J
h = construccion_datos.h
d = construccion_datos.d
dict_ventas = construccion_datos.dict_ventas
dict_bodegas = construccion_datos.dict_bodegas

suma = 0
for i in I:
    for j in J:
        if dict_ventas[i]['ID Bodega Despacho'] == j:
            suma += h[i] * d[i][j]

print(suma)
