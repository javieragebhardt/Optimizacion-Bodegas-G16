# [ICS2122] Localización Óptima de Bodegas Grupo 16

Repositorio correspondiente a los archivos de programación y datos utilizados por el grupo 16 en el Taller de Investigación Operativa 2023-2. A continuación, se explican los distintos archivos:

**Datos**:
- `BDD_Bodegas.xlsx`: Base de datos inicial entregada con modificaciones menores de limpieza de datos.
- `Analisis_Datos_Bodegas.ipynb`: Archivo de análisis de situación inicial que permitió analizar y realizar una categorización mediante el Prinicipo de Paretto.
- `BDD_Bodegas_Categorizada.xlsx` o `BDD_Categorizacion_0.25_0.75.xlsx` : Base de datos que contiene la caracterización inicial de clientes (25 % Silver, 50 % Gold y 25 % Premium)
- `contruccion_categorizacion.py`: crea un excel con la categorización establecida como parámentros.
- `BDD_Categorizacion_0.2_0.7.xlsx`: Base de datos segunda carecterización (20 % Silver, 50% Gold y 30% Premium).
- `BDD_Categorizacion_0.15_0.7.xlsx`: Base de datos tercera categorización (15% Silver, 55 % Gold y 30 % Premium).
- `construccion_datos.py`:  archivo que importa y ordena datos entregados del problema.

**Levantamiento de resultados, gráficos y mapas**

- ``caso_base.py``: contiene la clase CasoBase que genera mapa y un dataframe con la asignacion inicial sin cambios.
- ``distancias_mapbox.py``: trabajo de distancias reales comuna-bodega (con mapbox). Crea el archivo ``rutas.json`` (contiene las rutas arrojadas).
- `distancias_comunas_bodegas.xlsx`: Distancias reales entre las distintas comunas y bodegas. 
- ``modelo.py``: contiene la clase LocalizacionOptima que mediante Gurobi optimiza la asignación cliente-bodega (p-median), además de generar datframes con resultados y mapas visuales de la asignación.

**Manejo de Resultados**

- ``generar_grafico_acumulado.py``: genera gráficos de despachos acumulados según las horas de despacho. Los resultados para los casos analizados se encuentran en la carpeta *graficos* con el nombre "acum_{característica}.png", siendo característica: caso base o el valor de p.
  
**Carpeta Resultados**

Carpeta que contiene los resultados dependiendo de los parámetros (inputs) entregados. Hay 5 carpetas: una para la primera categorización (carpeta "Primera categorización"), otras para el resto de las categorizaciones (con nombre "Categorizacion_{porcentaje hasta silver}_{porcentaje hasta gold}"). Cada carpeta contiene y la última que corresponde a los resultados si es que se asigna la segunda bodega (no la más cercana). Cada carpeta contiene:
- ``bodegas_abiertas_p_{valor p}_{distancia utilizada}.xlsx``: base de datos que contiene el detalle de las bodegas abiertas al resolver el p-median con esos parámetros y distancias.
- ``mapa_p_{valor p}_{distancia utilizada}.html``: muestra la asignación de clientes a bodegas en un mapa al resolver el p-median con esos parámetros y distancias.
- ``tiempos_p_{valor p}_{distancia}.xlsx``: base de datos que contiene los resultados arrojados al resolver el problema mediante p-median. Las filas representan a cada cliente y las columnas: id, tiempo de entrega, bodega asignada, categoría perteneciente (en horas) y si cumple o no el nivel de servicio (si cumple toma el valor de 1, de contrario valor 0).
- ``valoresFO.txt``: valores que toma la función objetivo establecida para los distintos parámetros y datos.
- (para la primera categorización solamente): los mismos archivos anteriores pero para el caso base.


**Integrantes**

- Alvaro Cruz Errázuriz
- Dante Comparini Jiménez
- Javiera Gebhardt Rishmague
- Martín González Sepúlveda
- José Ignacio Fernández Rodríguez
- Diego Nahum Viada
- Diego San Martín González

