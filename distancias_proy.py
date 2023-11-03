
import pandas as pd
import numpy as np
import math
import json
import pyproj
# Importación base de datos
bdd_categoria = "BDD_Bodegas_Categorizada.xlsx"
bdd_ventas = pd.read_excel(bdd_categoria)
bdd_bodegas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=2)
bdd_comunas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=3)

# Pasamos la columna de fechas a formato de fechas
bdd_ventas['Fecha'] = pd.to_datetime(bdd_ventas['Fecha'])

# Agrupación de ventas por cliente y completar comuna
bdd_ventas_agrupadas = bdd_ventas.groupby("ID Cliente").agg({"Cantidad": "sum", "Comuna Despacho": "first", 'ID Bodega Despacho': 'first', 'Categoria': 'first'}).reset_index()
bdd_ventas_agrupadas = bdd_ventas_agrupadas.merge(bdd_comunas, left_on='Comuna Despacho', right_on='Comuna')
bdd_ventas_agrupadas = bdd_ventas_agrupadas[bdd_ventas_agrupadas["Cantidad"] != 0] #TODO revisar

# Armamos los diccionarios
dict_bodegas = bdd_bodegas.set_index('ID Bodega')[['LAT', 'LONG']].to_dict(orient='index') 
dict_ventas = bdd_ventas_agrupadas.set_index('ID Cliente')[['Cantidad', 'Comuna Despacho', 'LAT', 'LON', 'ID Bodega Despacho', 'Categoria']].to_dict(orient='index') 


def calcular_coordenadas_xy_2(lat, lon):
    transformer =  pyproj.Transformer.from_crs("epsg:20040", "epsg:20049", always_xy=True)
    x, y = transformer.transform(lon, lat)
    return [x/1000, y/1000]

def calcular_xy_coordenadas_2(x, y):
    x = x * 1000
    y = y * 1000
    transformer =  pyproj.Transformer.from_crs("epsg:20049", "epsg:20040", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return [lon, lat]

d_Manhattan_2 = dict()
for i in dict_ventas.keys():
    d_Manhattan_2[i] = dict()
    # creamos una iteración sobre los id de bodegas
    for j in dict_bodegas.keys():
        # Sacamos la diferencia y hacemos la conversión a metros
        print('transformando', i, j)
        coordenadas1 = calcular_coordenadas_xy_2(dict_bodegas[j]['LAT'], dict_bodegas[j]['LONG'])
        coordenadas2 = calcular_coordenadas_xy_2(dict_ventas[i]['LAT'], dict_ventas[i]['LON'])

        lat_diff = abs(coordenadas1[0] - coordenadas2[0])
        lon_diff = abs(coordenadas1[1] - coordenadas2[1])

        if round((lat_diff + lon_diff), 2) > 0:
            d_Manhattan_2[i][j] = round((lat_diff + lon_diff), 2)  # Distancia Manhattan en kilometros, redondeado al segundo decimal
        elif round((lat_diff + lon_diff), 2) == 0:
            d_Manhattan_2[i][j] = 0.01
# Nombre del archivo donde se guardará el diccionario
nombre_archivo = "d_manhattan_2.json"

# Guardar el diccionario en un archivo JSON
with open(nombre_archivo, "w") as archivo:
    json.dump(d_Manhattan_2, archivo)

print(f"El diccionario ha sido guardado en '{nombre_archivo}'.")