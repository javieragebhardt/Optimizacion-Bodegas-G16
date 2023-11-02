import pandas as pd
import numpy as np
import math
import json
import pyproj

# Importación base de datos
bdd_categoria = "BDD_Bodegas_Categorizada.xlsx"
bdd_ventas = pd.read_excel(bdd_categoria)
bdd_proyeccion = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=1)
bdd_bodegas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=2)
bdd_comunas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=3)

# Pasamos la columna de fechas a formato de fechas
bdd_ventas['Fecha'] = pd.to_datetime(bdd_ventas['Fecha'])
bdd_proyeccion['Fecha'] =pd.to_datetime(bdd_proyeccion['Fecha'])

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


# Definir coordenadas en x e y de clientes
def calcular_coordenadas_xy(lat, lon):
    x = - radio_tierra * math.radians(lon)/1000
    y = - radio_tierra * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))/1000
    return [x, y]


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

def calcular_coordenadas_LL(x, y): 
    longitud = math.degrees(- x / radio_tierra)
    latitud = math.degrees(2 * math.atan(math.exp(math.radians(- y / radio_tierra))) - math.pi / 2) 
    return latitud, longitud

print('hola1')


# Cargar el archivo JSON como un diccionario
with open('d_manhattan_2.json', 'r') as archivo_json:
    d_Manhattan_2 = json.load(archivo_json)

d_Manhattan_2 = {int(k1): {int(k2): v2 for k2, v2 in v1.items()} for k1, v1 in d_Manhattan_2.items()}

# # Crear diccionario que contiene las distancias Manhattan
# d_Manhattan_2 = dict() # Distancias Manhattan

# proj = pyproj.Transformer.from_crs(4326, 3857, always_xy=True)

# #####
# for cliente in dict_ventas.keys():
#     x, y = proj.transform(dict_ventas[cliente]['LON'], dict_ventas[cliente]['LAT'])
#     dict_ventas[cliente]["x"] = -x/1000
#     dict_ventas[cliente]["y"] = -y/1000

# for bodega in dict_bodegas.keys():
#     x, y = proj.transform(dict_bodegas[bodega]['LONG'], dict_bodegas[bodega]['LAT'])
#     dict_bodegas[bodega]["x"] = -x/1000
#     dict_bodegas[bodega]["y"] = -y/1000

# d_Manhattan_2 = dict()

# for i in dict_ventas.keys():
#     d_Manhattan_2[i] = dict()
#     for j in dict_bodegas.keys():
#         dif_x = abs(dict_bodegas[j]['x'] - dict_ventas[i]['x'])
#         dif_y = abs(dict_bodegas[j]['y'] - dict_ventas[i]['y'])
#         if round((dif_x + dif_y), 2) > 0 :
#             d_Manhattan_2[i][j] = round((dif_x + dif_y), 2)
#         else:
#             d_Manhattan_2[i][j] = 0.01


a = dict()
for cliente in dict_ventas.keys():
    a[cliente] = calcular_coordenadas_xy_2(dict_ventas[cliente]['LAT'], dict_ventas[cliente]['LON'])

    
# Descargamos matriz de distancias en red
distancias_en_red = pd.read_excel("distancias_comunas_bodegas_mapbox.xlsx")
distancias_en_red = distancias_en_red.replace(0, 0.0001)

#### Creamos otro diccionario
d_mapbox = dict()

for i in dict_ventas.keys():
    data_dict = dict()
    comuna = dict_ventas[i]['Comuna Despacho']
    bodegas_comuna = distancias_en_red[distancias_en_red['Unnamed: 0']== comuna]
    data_dict = bodegas_comuna.set_index('Unnamed: 0').squeeze().to_dict()
    d_mapbox[i] = data_dict

#### Creamos el diccionario rutas de mapbox
# Lee el archivo JSON
with open('rutas.json', 'r') as archivo_json:
    data = json.load(archivo_json)

# Convierte los índices de bodegas a enteros
rutas = {
    comuna: {int(id_bodega): coordenadas for id_bodega, coordenadas in bodegas.items()}
    for comuna, bodegas in data.items()
}

##### diccionario
import copy

def bodegas(diccionario, b1, b2, b3, b4, b5, b6, b7):
    diccionario_copia = copy.deepcopy(diccionario)  
    for key in diccionario_copia:
        """diccionario_copia[key][b1] = 99999
        diccionario_copia[key][b3] = 99999
        diccionario_copia[key][b2] = 99999
        diccionario_copia[key][b4] = 99999
        diccionario_copia[key][b5] = 99999
        diccionario_copia[key][b6] = 99999
        diccionario_copia[key][b7] = 99999"""
        min_valor = min(diccionario_copia[key].values())
        for sub_key in diccionario_copia[key]:
            if diccionario_copia[key][sub_key] == min_valor:
                diccionario_copia[key][sub_key] = 99999
    return diccionario_copia

"""dic_segunda_bodega = bodegas(d_mapbox, 2, 3, 5, 6, 7, 9, 10)""" #para p = 3
"""dic_segunda_bodega = bodegas(d_mapbox, 2, 4, 6, 8, 10, 0, 0)""" # para p = 5
dic_segunda_bodega = bodegas(d_mapbox, 0, 0, 0, 0, 0, 0, 0) # para p = 10

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
    # Actualizamos las horas para los diferentes grupos de clientes
    bdd_copy.loc[clientes_medio.index, 'Horas'] = 24
    bdd_copy.loc[clientes_sobre.index, 'Horas'] = 12 
    # Contamos la cantidad de horas por categoría
    cantidad_por_categoria = bdd_copy['Horas'].value_counts()
    # Creamos un diccionario con ID Cliente como clave y Horas como valor
    t = bdd_copy.set_index('ID Cliente')['Horas'].to_dict()

    return t

# Diccionario M para almacenar las distancias máximas
M = {}

# Bucle para cada cliente
for i in dict_ventas.keys():
    max_distance = 0  # Inicializa la distancia máxima para el cliente i

    # Bucle para todas las bodegas
    for j in dict_bodegas.keys():
        # Calcula la distancia entre el cliente i y la bodega j 
        distance = d_Manhattan[i][j]

        # Actualiza la distancia máxima si es mayor
        if distance > max_distance:
            max_distance = distance

    # Almacena la distancia máxima para el cliente i en el diccionario M
    M[i] = max_distance + (max_distance*0.01) #Acá podríamos darle un margen 1% del maximo este caso
    # No se si quieren redondear tmb round(max_distance + max_distance*0.01, 2)

######## definición de I
I = list(dict_ventas.keys())

######## definición de J
J = list(dict_bodegas.keys())
