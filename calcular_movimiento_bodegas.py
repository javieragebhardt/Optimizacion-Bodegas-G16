import pyproj

bodegas_acutales = {8: { 'LON': -72.349, 'LAT': -36.9226666666667}, 
 4:  {'LON': -70.9796666666667, 'LAT': -34.5826666666667}, 
 1:  {'LON': -71.293, 'LAT': -29.9623333333333}}

bodegas_historico = {8: { 'LON': -72.28493666107894, 'LAT': -36.94972320272767}, 
 4:  {'LON': -71.19979328980153, 'LAT': -34.59885659314397}, 
 1:  {'LON': -71.17766666666667, 'LAT': -30.56766666666668}}

bodegas_proyeccion = {8: { 'LON': -72.28415863186918, 'LAT': -36.94974474475612}, 
 4:  {'LON': -71.19995428777983, 'LAT': -34.60495926990576}, 
 1:  {'LON': -71.17766666666667, 'LAT': -30.56766666666668}}


transformer =  pyproj.Transformer.from_crs("epsg:20040", "epsg:20049", always_xy=True)


for i in [1, 4, 8]:
    x_h, y_h = transformer.transform(bodegas_historico[i]['LON'], bodegas_historico[i]['LAT'])
    x_p, y_p = transformer.transform(bodegas_proyeccion[i]['LON'], bodegas_proyeccion[i]['LAT'])
    dif = round(abs(x_h - x_p) + abs(y_h - y_p), 2)

    print(f'La bodega {i} se desplazó {round(dif/1000, 2)} kms')