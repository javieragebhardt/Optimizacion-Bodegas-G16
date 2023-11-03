import pandas as pd
import json
import pyproj
import copy

class ConstruccionDatos:

    def __init__(self, modelo, tipo_d, proy):

        self.d = dict()
        self.modelo = modelo
        self.tipo_d = tipo_d
        self.proy = proy

        if not self.proy:
            nombre_bdd = "BDD_Bodegas_Categorizada.xlsx"
        else:
            nombre_bdd = "BDD_Bodegas_Categorizada_proy.xlsx"

        # Importación base de datos
        self.bdd_ventas = pd.read_excel(nombre_bdd)
        self.bdd_bodegas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=2)
        self.bdd_comunas = pd.read_excel("BDD_Bodegas.xlsx", sheet_name=3)

        # Pasamos la columna de fechas a formato de fechas
        self.bdd_ventas['Fecha'] = pd.to_datetime(self.bdd_ventas['Fecha'])

        # Agrupación de ventas por cliente y completar comuna
        self.bdd_ventas_agrupadas = self.bdd_ventas.groupby("ID Cliente").agg({"Cantidad": "sum", "Comuna Despacho": "first", 'ID Bodega Despacho': 'first', 'Categoria': 'first'}).reset_index()
        self.bdd_ventas_agrupadas = self.bdd_ventas_agrupadas.merge(self.bdd_comunas, left_on='Comuna Despacho', right_on='Comuna')
        self.bdd_ventas_agrupadas = self.bdd_ventas_agrupadas[self.bdd_ventas_agrupadas["Cantidad"] != 0] #TODO revisar

        # Armamos los diccionarios
        self.dict_bodegas = self.bdd_bodegas.set_index('ID Bodega')[['LAT', 'LONG']].to_dict(orient='index') 
        self.dict_ventas = self.bdd_ventas_agrupadas.set_index('ID Cliente')[['Cantidad', 'Comuna Despacho', 'LAT', 'LON', 'ID Bodega Despacho', 'Categoria']].to_dict(orient='index') 

        # Parametros
        self.I = list(self.dict_ventas.keys())
        if modelo == 'aloc':
            self.J = range(1, 4)
        else:
            self.J = list(self.dict_bodegas.keys())
        self.h = self.bdd_ventas_agrupadas.set_index('ID Cliente')['Cantidad'].to_dict()

        if self.tipo_d == 'manhattan':
            self.manhattan()
        elif self.tipo_d == 'mapbox':
            self.mapbox()
        
        self.generar_a()
        self.generar_m()
        self.generar_n()
        self.generar_ns_c_ipp_ip()

    def calcular_coordenadas_xy_2(self, lat, lon):
        transformer =  pyproj.Transformer.from_crs("epsg:20040", "epsg:20049", always_xy=True)
        x, y = transformer.transform(lon, lat)
        return [x/1000, y/1000]

    def calcular_xy_coordenadas_2(self, x, y):
        transformer =  pyproj.Transformer.from_crs("epsg:20049", "epsg:20040", always_xy=True)
        lon, lat = transformer.transform(x * 1000, y * 1000)
        return [lon, lat]

    def generar_a(self):
        self.a = dict()
        for cliente in self.dict_ventas.keys():
            self.a[cliente] = self.calcular_coordenadas_xy_2(self.dict_ventas[cliente]['LAT'], self.dict_ventas[cliente]['LON'])

    def manhattan(self):
        nombre_archivo = 'd_manhattan.json'
        if self.proy:
            nombre_archivo = 'd_manhattan_proy.json'
        with open(nombre_archivo, 'r') as archivo_json:
            d_Manhattan = json.load(archivo_json)
        self.d = {int(k1): {int(k2): v2 for k2, v2 in v1.items()} for k1, v1 in d_Manhattan.items()}

    def mapbox(self):
        distancias_en_red = pd.read_excel("distancias_comunas_bodegas_mapbox.xlsx")
        distancias_en_red = distancias_en_red.replace(0, 0.0001)

        for i in self.dict_ventas.keys():
            data_dict = dict()
            comuna = self.dict_ventas[i]['Comuna Despacho']
            bodegas_comuna = distancias_en_red[distancias_en_red['Unnamed: 0']== comuna]
            data_dict = bodegas_comuna.set_index('Unnamed: 0').squeeze().to_dict()
            self.d[i] = data_dict

        with open('rutas.json', 'r') as archivo_json:
            data = json.load(archivo_json)

        # Convierte los índices de bodegas a enteros
        self.rutas = {
            comuna: {int(id_bodega): coordenadas for id_bodega, coordenadas in bodegas.items()}
            for comuna, bodegas in data.items()
        }

    def generar_m(self):
        # Diccionario M para almacenar las distancias máximas
        error_2 = 16
        self.M = {}

        # Bucle para cada cliente
        for i in self.dict_ventas.keys():
            max_distance = 0  # Inicializa la distancia máxima para el cliente i

            # Bucle para todas las bodegas
            for j in self.dict_bodegas.keys():
                # Calcula la distancia entre el cliente i y la bodega j 
                distance = self.d[i][j]

                # Actualiza la distancia máxima si es mayor
                if distance > max_distance:
                    max_distance = distance

            # Almacena la distancia máxima para el cliente i en el diccionario M
            self.M[i] = max_distance + (max_distance*error_2) #Acá podríamos darle un margen 1% del maximo este caso
            # No se si quieren redondear tmb round(max_distance + max_distance*0.01, 2)

    def generar_n(self):
        # Diccionario N para almacenar las distancias máximas

        error = 0
        self.N = {}

        # Bucle para cada cliente
        for i in self.dict_ventas.keys():
            max_distance = 0  # Inicializa la distancia máxima para el cliente i

            # Bucle para todas las bodegas
            for j in self.dict_bodegas.keys():
                # Calcula la distancia entre el cliente i y la bodega j 
                distance = self.d[i][j]

                # Actualiza la distancia máxima si es mayor
                if distance > max_distance:
                    max_distance = distance

            # Almacena la distancia máxima para el cliente i en el diccionario M
            self.N[i] = max_distance + (max_distance*error) #Acá podríamos darle un margen 1% del maximo este caso
            # No se si quieren redondear tmb round(max_distance + max_distance*0.01, 2)

    def generar_ns_c_ipp_ip(self):
        self.ns = dict()
        for cliente in self.dict_ventas.keys():
            if self.dict_ventas[cliente]['Categoria'] == 'Premium':
                self.ns[cliente] = 12 * 45
            elif self.dict_ventas[cliente]['Categoria'] == 'Gold':
                self.ns[cliente] = 24 * 45
            else:
                self.ns[cliente] = 48 * 45

        ## Diccionario pre-asignaciones 
        self.ipp = list()
        self.ip = list()
        self.c = dict()

        # Latitudes bodegas LAP 20% GAP
        if self.proy:
            n1 = 27.034
            n2 = 31.62
            c1 = 35.316
            c2 = 32.885
            s1 = 36.411
            s2 = 42.607
        else:
            n1 = 27.034
            n2 = 32.52
            c1 = 35.635
            c2 = 32.718
            s1 = 36.11
            s2 = 42.607            

        prom_lat_norte = (-n1 -n2)/2 
        prom_lat_centro = (-c1 - c2)/2 
        prom_lat_sur = (-s1 - s2)/2 

        for cliente in self.dict_ventas.keys():
            lat = self.dict_ventas[cliente]['LAT']
            if lat > prom_lat_norte - 1: 
                self.ip.append(cliente)
                self.c[cliente] = {1:0 , 2:0, 3:1}
            elif lat < prom_lat_sur + 1:
                self.ip.append(cliente)
                self.c[cliente] = {1:1 , 2:0, 3:0}
            elif lat < (prom_lat_centro + 0.25*(c1 - c2)) and lat > (prom_lat_centro - 0.25*(c1 - c2)):
                self.ip.append(cliente)
                self.c[cliente] = {1:0 , 2:1, 3:0}
            else:
                self.ipp.append(cliente)