import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def crear_excel(archivo_ventas, porcentaje_1, porcentaje_2):
    ventas_df = pd.read_excel('BDD_Bodegas.xlsx', sheet_name='VENTAS')
    # Eliminar filas con valores faltantes
    ventas_df.dropna(inplace=True)
    ventas_df = ventas_df.drop_duplicates()

    # Calcular las cantidades totales por cliente
    cantidades_totales = ventas_df.groupby('ID Cliente')['Cantidad'].sum()
    cantidades_totales = cantidades_totales.sort_values()

    # Crear la columna 'Suma Acumulada' que contendrá la suma acumulada de 'Cantidad' por cliente
    cantidades_acumuladas = cantidades_totales.cumsum()

    # Calcular los cuartiles
    umbral_silver = cantidades_totales.sum()*porcentaje_1
    umbral_premium = cantidades_totales.sum()*porcentaje_2

    ventas_df['Categoria'] = 'Silver'  # Inicialmente, establecer a 'Silver' para todos
    clientes_con_menos_umbral_silver = cantidades_acumuladas[cantidades_acumuladas <= umbral_silver]
    clientes_con_entre_medio = cantidades_acumuladas[(cantidades_acumuladas > umbral_silver) & (cantidades_acumuladas <= umbral_premium)]
    clientes_con_sobre_umbral_premium = cantidades_acumuladas[umbral_premium < cantidades_acumuladas]

    # # Actualizar la columna 'Categoria' según las condiciones
    ventas_df.loc[ventas_df['ID Cliente'].isin(clientes_con_entre_medio.index), 'Categoria'] = 'Gold'
    ventas_df.loc[ventas_df['ID Cliente'].isin(clientes_con_sobre_umbral_premium.index), 'Categoria'] = 'Premium'

    # # Contar la cantidad de cada categoría en la columna 'Categoria'
    cantidad_por_categoria = ventas_df['Categoria'].value_counts()

    print(cantidad_por_categoria)
    print("-"*100)
    print(f"Clientes bajo el {porcentaje_1} del total: ",clientes_con_menos_umbral_silver.count())
    print("Clientes entre medio: ",clientes_con_entre_medio.count())
    print(f"Clientes sobre el {porcentaje_2} del total: ",clientes_con_sobre_umbral_premium.count())
    print("Suma de clientes: ",clientes_con_menos_umbral_silver.count()+clientes_con_entre_medio.count()+
        clientes_con_sobre_umbral_premium.count())
    print('-'*100)
    print("Clientes sgn df: ", ventas_df['ID Cliente'].nunique())

    # Especifica el nombre del archivo Excel en el que deseas guardar el DataFrame
    nombre_archivo = "BDD_Categorizacion_"+str(porcentaje_1)+"_"+str(porcentaje_2)+".xlsx"

    # Guarda el DataFrame en un archivo Excel
    ventas_df.to_excel(nombre_archivo, index=False)  # El argumento index=False evita que se incluya el índice en el archivo

    print(f"DataFrame guardado en {nombre_archivo}")

#crear_excel("BDD_Bodegas.xlsx", porcentaje_1=0.15, porcentaje_2=0.7)

def crear_excel_2(porcentaje_1, porcentaje_2):
    ventas_df = pd.read_excel('BDD_Bodegas.xlsx', sheet_name=1)
    # Eliminar filas con valores faltantes
    ventas_df.dropna(inplace=True)
    ventas_df = ventas_df.drop_duplicates()

    # Calcular las cantidades totales por cliente
    cantidades_totales = ventas_df.groupby('ID Cliente')['Cantidad'].sum()
    cantidades_totales = cantidades_totales.sort_values()

    # Crear la columna 'Suma Acumulada' que contendrá la suma acumulada de 'Cantidad' por cliente
    cantidades_acumuladas = cantidades_totales.cumsum()

    # Calcular los cuartiles
    umbral_silver = cantidades_totales.sum()*porcentaje_1
    umbral_premium = cantidades_totales.sum()*porcentaje_2

    ventas_df['Categoria'] = 'Silver'  # Inicialmente, establecer a 'Silver' para todos
    clientes_con_menos_umbral_silver = cantidades_acumuladas[cantidades_acumuladas <= umbral_silver]
    clientes_con_entre_medio = cantidades_acumuladas[(cantidades_acumuladas > umbral_silver) & (cantidades_acumuladas <= umbral_premium)]
    clientes_con_sobre_umbral_premium = cantidades_acumuladas[umbral_premium < cantidades_acumuladas]

    # # Actualizar la columna 'Categoria' según las condiciones
    ventas_df.loc[ventas_df['ID Cliente'].isin(clientes_con_entre_medio.index), 'Categoria'] = 'Gold'
    ventas_df.loc[ventas_df['ID Cliente'].isin(clientes_con_sobre_umbral_premium.index), 'Categoria'] = 'Premium'

    # # Contar la cantidad de cada categoría en la columna 'Categoria'
    cantidad_por_categoria = ventas_df['Categoria'].value_counts()

    print(cantidad_por_categoria)
    print("-"*100)
    print(f"Clientes bajo el {porcentaje_1} del total: ",clientes_con_menos_umbral_silver.count())
    print("Clientes entre medio: ",clientes_con_entre_medio.count())
    print(f"Clientes sobre el {porcentaje_2} del total: ",clientes_con_sobre_umbral_premium.count())
    print("Suma de clientes: ",clientes_con_menos_umbral_silver.count()+clientes_con_entre_medio.count()+
        clientes_con_sobre_umbral_premium.count())
    print('-'*100)
    print("Clientes sgn df: ", ventas_df['ID Cliente'].nunique())

    # Especifica el nombre del archivo Excel en el que deseas guardar el DataFrame
    nombre_archivo = "BDD_Proyeccion_Categorizacion_"+str(porcentaje_1)+"_"+str(porcentaje_2)+".xlsx"

    # Guarda el DataFrame en un archivo Excel
    ventas_df.to_excel(nombre_archivo, index=False)  # El argumento index=False evita que se incluya el índice en el archivo

    print(f"DataFrame guardado en {nombre_archivo}")

crear_excel_2(porcentaje_1=0.25, porcentaje_2=0.75)