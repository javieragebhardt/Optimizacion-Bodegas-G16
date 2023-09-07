import pandas as pd
import numpy as np

# Importación base de datos
bdd_categoria = "BDD_Bodegas_Categorizada.xlsx"
bdd_ventas = pd.read_excel(bdd_categoria)
bdd_proyeccion = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=1)
bdd_bodegas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=2)
bdd_comunas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=3)
bdd_comuna_bodega = pd.read_excel("distancias_comunas_bodegas.xlsx")

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

# Transpone el DataFrame para tener las columnas como índices
df = bdd_comuna_bodega.T

# Crea un diccionario para almacenar los datos
dict_comunas_bodegas = {}

# Itera a través de las columnas del DataFrame
for columna in df.columns:
    # Obtiene los valores de la columna como una lista
    valores = df[columna].tolist()    
    # Agrega el diccionario de la columna al diccionario principal
    dict_comunas_bodegas[valores[0]] = {i: valores[i] for i in range(1,11)}

# Ahora, data_dict contiene el diccionario que deseas

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

# Descargamos matriz de distancias en red
distancias_en_red = pd.read_excel("distancias_comunas_bodegas.xlsx")
distancias_en_red = distancias_en_red.replace(0, 0.0001)

#### Creamos otro diccionario
d_mapbox = dict()

for i in dict_ventas.keys():
    data_dict = dict()
    comuna = dict_ventas[i]['Comuna Despacho']
    bodegas_comuna = distancias_en_red[distancias_en_red['Unnamed: 0']== comuna]
    data_dict = bodegas_comuna.set_index('Unnamed: 0').squeeze().to_dict()
    d_mapbox[i] = data_dict


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


######## definición de I
I = list(dict_ventas.keys())

######## definición de J
J = list(dict_bodegas.keys())
