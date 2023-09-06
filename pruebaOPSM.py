import mapbox
import pandas as pd
from mapbox import Directions

# Configura el cliente con tu token de acceso
service = Directions(access_token="pk.eyJ1IjoiamF2aWVyYWdlYmIiLCJhIjoiY2xtN3Y4ZmR5MDNtcDNkbW4zd2Y4M2t1OSJ9.Nvg5ie5hjdGn7Knj6PpcaQ")

# Importación base de datos
bdd_ventas = pd.read_excel("BDD_Bodegas.xlsx")
bdd_proyeccion = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=1)
bdd_bodegas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=2)
bdd_comunas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=3)

# Pasamos la columna de fechas a formato de fechas
bdd_ventas['Fecha'] = pd.to_datetime(bdd_ventas['Fecha'])
bdd_proyeccion['Fecha'] =pd.to_datetime(bdd_proyeccion['Fecha'])

# Agrupación de ventas por cliente y completar comuna
bdd_ventas_agrupadas = bdd_ventas.groupby("ID Cliente").agg({"Cantidad": "sum", "Comuna Despacho": "first", 'ID Bodega Despacho': 'first'}).reset_index()
bdd_ventas_agrupadas = bdd_ventas_agrupadas.merge(bdd_comunas, left_on='Comuna Despacho', right_on='Comuna')
bdd_ventas_agrupadas = bdd_ventas_agrupadas[bdd_ventas_agrupadas["Cantidad"] != 0] #TODO revisar

# Armamos los diccionarios
dict_bodegas = bdd_bodegas.set_index('ID Bodega')[['LAT', 'LONG']].to_dict(orient='index') 
dict_ventas = bdd_ventas_agrupadas.set_index('ID Cliente')[['Cantidad', 'Comuna Despacho', 'LAT', 'LON', 'ID Bodega Despacho']].to_dict(orient='index') 
dict_comunas = bdd_comunas.to_dict(orient='records')

# Crear diccionario 
distances = {}


for comuna in dict_comunas:
    for j in dict_bodegas.keys():
        start_coords = (comuna['LON'], comuna['LAT'])
        end_coords = (dict_bodegas[j]['LONG'], dict_bodegas[j]['LAT'])
        
        # Configura tu feature de GeoJSON
        feature = {
            'type': 'Feature',
            'properties': {'name': 'route'},
            'geometry': {
                'type': 'LineString',
                'coordinates': [start_coords, end_coords]
            }
        }
        # Calcula la ruta
        response = service.directions([feature], profile='mapbox/driving', geometries='geojson')
        # Verificar si la respuesta es válida
        if response.status_code == 200:
            data = response.geojson()
            if data['features']:
                route_data = data['features'][0]
                distance = route_data['properties']['distance'] / 1000  # Convertir a kilómetros
                distances[(comuna['Comuna'], j)] = distance
                with open('distancias.txt', 'a') as file:
                    file.write(f"{comuna['Comuna'], j, distance}\n")
            else:
                with open('distancias.txt', 'a') as file:
                    file.write(f"No se encontró ruta entre {comuna['Comuna']} y bodega {j}\n")
        else:
            with open('distancias.txt', 'a') as file:
                file.write(f"Error en la solicitud para {comuna['Comuna']} y bodega {j}. Código de estado: {response.status_code}\n")
                                                                                    
df = pd.DataFrame()

for (comuna, bodega), distance in distances.items():
    if bodega not in df.columns:
        df[bodega] = None
    df.at[comuna, bodega] = distance

df.to_excel("distancias_comunas_bodegas.xlsx")



