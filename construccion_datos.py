import pandas as pd
from gurobipy import Model, GRB, quicksum
import numpy as np

# Importación base de datos
bdd_ventas = pd.read_excel("BDD_Bodegas.xlsx")
bdd_proyeccion = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=1)
bdd_bodegas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=2)
bdd_comunas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=3)

# Pasamos la columna de fechas a formato de fechas
bdd_ventas['Fecha'] = pd.to_datetime(bdd_ventas['Fecha'])
bdd_proyeccion['Fecha'] =pd.to_datetime(bdd_proyeccion['Fecha'])

# Agrupación de ventas por cliente y completar comuna
bdd_ventas_agrupadas = bdd_ventas.groupby("ID Cliente").agg({"Cantidad": "sum", "Comuna Despacho": "first"}).reset_index()
bdd_ventas_agrupadas = bdd_ventas_agrupadas.merge(bdd_comunas, left_on='Comuna Despacho', right_on='Comuna')
bdd_ventas_agrupadas = bdd_ventas_agrupadas[bdd_ventas_agrupadas["Cantidad"] >= 0]

# Armamos los diccionarios
dict_bodegas = bdd_bodegas.set_index('ID Bodega')[['LAT', 'LONG']].to_dict(orient='index') 
dict_comunas = bdd_comunas.set_index('Comuna')[['Region', 'LAT', 'LON']].to_dict(orient='index') 
dict_ventas = bdd_ventas_agrupadas.set_index('ID Cliente')[['Cantidad', 'Comuna Despacho', 'LAT', 'LON']].to_dict(orient='index') 

# Radio aproximado de la Tierra en metros
radio_tierra = 6371000  # metros

# Cantidad de bodegas y ventas
num_bodegas = len(dict_bodegas)
num_ventas = len(dict_ventas)

# Crear diccionario que contiene las distancias Manhattan
d = dict() # Distancias Manhattan

# creamos una iteración sobre los id de ventas
for i in dict_ventas.keys():
    d[i] = dict()
    # creamos una iteración sobre los id de bodegas
    for j in dict_bodegas.keys():
        # Sacamos la diferencia y hacemos la conversión a metros
        lat_diff = abs(dict_bodegas[j]['LAT'] - dict_ventas[i]['LAT']) * (np.pi / 180) * radio_tierra
        lon_diff = abs(dict_bodegas[j]['LONG'] - dict_ventas[i]['LON']) * (np.pi / 180) * radio_tierra * np.cos((dict_bodegas[j]['LAT'] + dict_ventas[i]['LAT']) * 0.5 * (np.pi / 180)) 
        
        d[i][j] = round((lat_diff + lon_diff)/1000, 2)  # Distancia Manhattan en kilometros, redondeado al segundo decimal

######## definición de h

h = bdd_ventas_agrupadas.set_index('ID Cliente')['Cantidad'].to_dict()

######## definición de t´s

def generar_t(bdd, inferior, superior):
    bdd_copy = bdd.copy()
    bdd_copy = bdd_copy.sort_values(by=['Cantidad'], ascending=True)
    bdd_copy['Horas'] = 48
    clientes_inferior = bdd['Cantidad'][bdd['Cantidad'] <= inferior]
    clientes_medio =  bdd['Cantidad'][( bdd['Cantidad'] >  inferior ) & ( bdd['Cantidad'] <=  superior)]
    clientes_sobre =  bdd['Cantidad'][superior < bdd['Cantidad']]
    bdd_copy.loc[bdd_copy['ID Cliente'].isin(clientes_medio.index), 'Horas'] = 24
    bdd_copy.loc[bdd_copy['ID Cliente'].isin(clientes_sobre.index), 'Horas'] = 12 
    cantidad_por_categoria = bdd_copy['Horas'].value_counts()
    t = bdd_copy.set_index('ID Cliente')['Horas'].to_dict()
    return t

t1 = generar_t(bdd_ventas_agrupadas, 906, 11033)

######## definición de I
I = list(dict_ventas.keys())

######## definición de J
J = list(dict_bodegas.keys())
