import pandas as pd
from gurobipy import Model, GRB, quicksum
import numpy as np

bdd_ventas = pd.read_excel("Base de Datos Bodega.xlsx")
bdd_proyeccion = pd.read_excel("Base de Datos Bodega.xlsx", sheet_name=1)
bdd_bodegas = pd.read_excel("Base de Datos Bodega.xlsx", sheet_name=2)
bdd_comunas = pd.read_excel("Base de Datos Bodega.xlsx", sheet_name=3)

# Pasamos la columna de fechas a formato de fechas
bdd_ventas['Fecha'] = pd.to_datetime(bdd_ventas['Fecha'])
bdd_proyeccion['Fecha'] =pd.to_datetime(bdd_proyeccion['Fecha'])

bdd_ventas_agrupadas = bdd_ventas.groupby("ID Cliente").agg({"Cantidad": "sum", "Comuna Despacho": "first"}).reset_index()

bdd_ventas_agrupadas = bdd_ventas_agrupadas.merge(bdd_comunas, left_on='Comuna Despacho', right_on='Comuna')

# Armamos los diccionarios
dict_bodegas = bdd_bodegas.to_dict(orient='index') #Keys del 0 al 9
dict_comunas = bdd_comunas.to_dict(orient='index') #keys del 0 al 342
dict_ventas = bdd_ventas_agrupadas.to_dict(orient='index') 

# Supongamos que tienes los diccionarios 'dict_bodegas' y 'dict_ventas'
# Radio aproximado de la Tierra en metros
radio_tierra = 6371000  # metros

# Crear una matriz de distancias con ceros
num_bodegas = len(dict_bodegas)
num_ventas = len(dict_ventas)
d = np.zeros((num_bodegas, num_ventas)) # Matriz Manhattan

# Llenar la matriz de distancias
for i, (bodega, bodega_coords) in enumerate(dict_bodegas.items()): #Revisamos todas las tuplas (key, valores) del diccionario de bodegas
    for j, (venta, venta_coords) in enumerate(dict_ventas.items()): #Revisamos todas las tuplas (key, valores) del diccionario de comunas
        # Sacamos la diferencia y hacemos la conversión a metros
        lat_diff = abs(bodega_coords['LAT'] - venta_coords['LAT']) * (np.pi / 180) * radio_tierra
        lon_diff = abs(bodega_coords['LONG'] - venta_coords['LON']) * (np.pi / 180) * radio_tierra * np.cos((bodega_coords['LAT'] + venta_coords['LAT']) * 0.5 * (np.pi / 180)) 
        
        d[i, j] = round((lat_diff + lon_diff)/1000, 2)  # Distancia Manhattan en kilometros, redondeado al segundo decimal

