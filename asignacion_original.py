# Importación base de datos
import pandas as pd
import numpy as np
import construccion_datos
import folium

def generar_data_frame(dict, filename):
    df = pd.DataFrame(dict)
    df = df.T
    df.to_excel(filename, index=True)

def generar_mapa(dict_clientes, v):
    dict_bodegas = construccion_datos.dict_bodegas
    colores_bodega = {1: "blue", 2: "red", 3: "green", 4: "darkgreen", 5: "orange", 
                        6: "purple", 7: "gray", 8: "cadetblue", 9: "black", 
                        10: "darkblue"}

    # Crear un mapa centrado en una ubicación inicial
    m = folium.Map(location=[-33.45, -70.65], zoom_start=7)

    # Agregar marcadores para las bodegas que tienen al menos un cliente asignado
    for bodega_id, coordenadas in dict_bodegas.items():
        num = bodega_id
        if num == 10:
            num = 'warehouse'
        lat = coordenadas['LAT']
        long = coordenadas['LONG']
        folium.Marker(
            location=[lat, long],
            popup=f'Bodega {bodega_id}',
            icon=folium.Icon(icon=str(num), prefix='fa', 
                                color=colores_bodega[bodega_id])
        ).add_to(m)

    # Agregar círculos para los clientes en el mapa con colores de bodega
    for cliente_id, datos_cliente in dict_clientes.items():
        lat = datos_cliente['LAT']
        long = datos_cliente['LON']
        color = colores_bodega[datos_cliente['ID Bodega Despacho']]
        folium.Circle(
            location=[lat, long],
            radius=1000,  # Radio del círculo en metros
            popup=f'Cliente {cliente_id}',
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)
        # Conectar el cliente con su bodega asignada con una línea coloreada
        bodega_coords = dict_bodegas[datos_cliente['ID Bodega Despacho']]
        folium.PolyLine(
            locations=[[lat, long], [bodega_coords['LAT'], bodega_coords['LONG']]],
            color=color,
            weight=2.5,
            opacity=1
        ).add_to(m)

    # Guardar el mapa en un archivo HTML
    m.save(f'resultados/mapa_p_{10}_v_{v}_original.html')

v1 = 30 
v2 = 45
I = construccion_datos.I
J = construccion_datos.J
h = construccion_datos.h
d = construccion_datos.d_Manhattan
dict_ventas = construccion_datos.dict_ventas
dict_bodegas = construccion_datos.dict_bodegas


# Caso base con v = 30 km/hr y distancia Manhattan

suma = 0
tiempos = dict()
for i in I:
    tiempos[i] = dict()
    for j in J:
        if dict_ventas[i]['ID Bodega Despacho'] == j:
            suma += h[i] * d[i][j]
            tiempos[i]['Tiempo'] = d[i][j] / v1

generar_data_frame(tiempos, f'resultados/tiempos_p_{10}_v_{30}_Manhattan_original.xlsx')
generar_mapa(dict_ventas, v1)

print(dict_ventas)

# Caso base con v = 45 km/hr y distancia Manhattan
suma = 0
tiempos = dict()
for i in I:
    tiempos[i] = dict()
    for j in J:
        if dict_ventas[i]['ID Bodega Despacho'] == j:
            suma += h[i] * d[i][j]
            tiempos[i]['Tiempo'] = d[i][j] / v2

generar_data_frame(tiempos, f'resultados/tiempos_p_{10}_v_{45}_Manhattan_original.xlsx')
generar_mapa(dict_ventas, v2)

#TODO calcular valores FO para estos casos