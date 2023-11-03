import pandas as pd
import numpy as np
import math
import json
import pyproj

# Importación base de datos
bdd_categoria = "BDD_Bodegas_Categorizada_proy.xlsx"
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


# Radio aproximado de la Tierra en metros
radio_tierra = 6371000  # metros

# Cantidad de bodegas y ventas
num_bodegas = len(dict_bodegas)
num_ventas = len(dict_ventas)

# Crear diccionario que contiene las distancias Manhattan
d_Manhattan = dict() # Distancias Manhattan

# creamos una iteración sobre los id de ventas
for i in dict_ventas.keys():
    d_Manhattan[i] = dict()
    # creamos una iteración sobre los id de bodegas
    for j in dict_bodegas.keys():
        # Sacamos la diferencia y hacemos la conversión a metros
        lat_diff = abs(dict_bodegas[j]['LAT'] - dict_ventas[i]['LAT']) * (np.pi / 180) * radio_tierra
        lon_diff = abs(dict_bodegas[j]['LONG'] - dict_ventas[i]['LON']) * (np.pi / 180) * radio_tierra * np.cos((dict_bodegas[j]['LAT'] + dict_ventas[i]['LAT']) * 0.5 * (np.pi / 180)) 
        if round((lat_diff + lon_diff)/1000, 2) > 0:
            d_Manhattan[i][j] = round((lat_diff + lon_diff)/1000, 2)  # Distancia Manhattan en kilometros, redondeado al segundo decimal
        elif round((lat_diff + lon_diff)/1000, 2) == 0:
            d_Manhattan[i][j] = 0.01

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

# Cargar el archivo JSON como un diccionario
with open('d_manhattan_2_proy.json', 'r') as archivo_json:
    d_Manhattan_2 = json.load(archivo_json)

d_Manhattan_2 = {int(k1): {int(k2): v2 for k2, v2 in v1.items()} for k1, v1 in d_Manhattan_2.items()}

a = dict()
for cliente in dict_ventas.keys():
    a[cliente] = calcular_coordenadas_xy_2(dict_ventas[cliente]['LAT'], dict_ventas[cliente]['LON'])

    
# Descargamos matriz de distancias en red
distancias_en_red = pd.read_excel("distancias_comunas_bodegas_mapbox.xlsx")
distancias_en_red = distancias_en_red.replace(0, 0.0001)

######## definición de h

h = bdd_ventas_agrupadas.set_index('ID Cliente')['Cantidad'].to_dict()

# Diccionario N para almacenar las distancias máximas

error = 0
N = {}

# Bucle para cada cliente
for i in dict_ventas.keys():
    max_distance = 0  # Inicializa la distancia máxima para el cliente i

    # Bucle para todas las bodegas
    for j in dict_bodegas.keys():
        # Calcula la distancia entre el cliente i y la bodega j 
        distance = d_Manhattan_2[i][j]

        # Actualiza la distancia máxima si es mayor
        if distance > max_distance:
            max_distance = distance

    # Almacena la distancia máxima para el cliente i en el diccionario M
    N[i] = max_distance + (max_distance*error) #Acá podríamos darle un margen 1% del maximo este caso
    # No se si quieren redondear tmb round(max_distance + max_distance*0.01, 2)

# Diccionario M para almacenar las distancias mínimas
error_2 = 10
M = {}

# Bucle para cada cliente
for i in dict_ventas.keys():
    min_distance = 10000  # Inicializa la distancia máxima para el cliente i

    # Bucle para todas las bodegas
    for j in dict_bodegas.keys():
        # Calcula la distancia entre el cliente i y la bodega j 
        distance = d_Manhattan_2[i][j]

        # Actualiza la distancia máxima si es mayor
        if distance < min_distance and distance >= 30:
            min_distance = distance

    # Almacena la distancia máxima para el cliente i en el diccionario M
    M[i] = min_distance + (min_distance*error_2) #Acá podríamos darle un margen 1% del maximo este caso
    # No se si quieren redondear tmb round(max_distance + max_distance*0.01, 2)

######## definición de I
I = list(dict_ventas.keys())

######## definición de J

p = 3
J = range(1, p + 1)

######## Localizaciones iniciales

localizaciones_iniciales = dict()
for i in [8, 4, 1]:
    localizaciones_iniciales[i] = calcular_coordenadas_xy_2(dict_bodegas[i]['LAT'], dict_bodegas[i]['LONG'])
    print(localizaciones_iniciales[i])


ns = dict()
for cliente in dict_ventas.keys():
    if dict_ventas[cliente]['Categoria'] == 'Premium':
        ns[cliente] = 12 * 45
    elif dict_ventas[cliente]['Categoria'] == 'Gold':
        ns[cliente] = 24 * 45
    else:
        ns[cliente] = 48 * 45

## Diccionario pre-asignaciones 
ipp = list()
ip = list()
c = dict()

# Latitudes bodegas LAP 20% GAP
n1 = 27.034
n2 = 31.62
c1 = 35.316
c2 = 32.885
s1 = 36.411
s2 = 42.607

prom_lat_norte = (-n1 -n2)/2 
prom_lat_centro = (-c1 - c2)/2 
prom_lat_sur = (-s1 - s2)/2 

for cliente in dict_ventas.keys():
    lat = dict_ventas[cliente]['LAT']
    if lat > prom_lat_norte - 1: 
        ip.append(cliente)
        c[cliente] = {1:0 , 2:0, 3:1}
    elif lat < prom_lat_sur + 1:
        ip.append(cliente)
        c[cliente] = {1:1 , 2:0, 3:0}
    elif lat < (prom_lat_centro + 0.25*(c1 - c2)) and lat > (prom_lat_centro - 0.25*(c1 - c2)):
        ip.append(cliente)
        c[cliente] = {1:0 , 2:1, 3:0}
    else:
        ipp.append(cliente)
