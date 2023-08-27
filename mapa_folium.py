import pandas as pd

# Cargar la hoja de Excel en un DataFrame de pandas
df_bodegas = pd.read_excel('Base de Datos Bodega.xlsx', sheet_name='BODEGAS')
bodega_data = list(zip(df_bodegas['LAT'], df_bodegas['LONG'], df_bodegas['ID Bodega'])) #tengo ese data frame, cómo puedo pasar a una lista de tuplas del estilo [(lat, lon), (lat, lon), ...]

df_ventas = pd.read_excel('Base de Datos Bodega.xlsx', sheet_name='VENTAS')

df_comunas = pd.read_excel('Base de Datos Bodega.xlsx', sheet_name='COMUNAS')

df_combined = df_ventas.merge(df_comunas, left_on='Comuna Despacho', right_on='Comuna')

clientes_data = list(zip(df_combined['LAT'], df_combined['LON'], df_combined['Cantidad'],df_combined['ID Cliente']))

print(clientes_data[4])