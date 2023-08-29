import pandas as pd
import os

def asignar_tiempo_maximo(categoria):
    if categoria == 'Silver':
        return 48
    elif categoria == 'Gold':
        return 24
    elif categoria == 'Premium':
        return 12
    else:
        return None

def cumple_condicion(row):
    if row['Tiempo'] <= row['Tiempo maximo']:
        return 1
    else:
        return 0

def convertir_a_excel(archivo_resultados):
    ## Leer BDD Categorizada
    bdd_categorizada_df = pd.read_excel('BDD_Bodegas_Categorizada.xlsx')

    ## Leer otro archivo
    caso_resultados_df = pd.read_excel(archivo_resultados)


    # Iterar a través de los IDs de cliente en caso_base_df
    for id_cliente in caso_resultados_df['ID Cliente']:
        # Buscar el valor de la columna 'Categoria' en bdd_categorizada
        categoria = bdd_categorizada_df[bdd_categorizada_df['ID Cliente'] == id_cliente]['Categoria'].values
        
        # Verificar si se encontró una categoría para el ID de cliente
        if len(categoria) > 0:
            # Asignar la categoría encontrada a la columna 'Tiempo maximo' en caso_base_df
            caso_resultados_df.loc[caso_resultados_df['ID Cliente'] == id_cliente, 'Categoria'] = categoria[0]

    # Aplica la función a la columna 'Categoria' para crear la columna 'Tiempo maximo'
    caso_resultados_df['Tiempo maximo'] = caso_resultados_df['Categoria'].apply(asignar_tiempo_maximo)

    # Aplica la función a lo largo de las filas del DataFrame
    caso_resultados_df['Cumple'] = caso_resultados_df.apply(cumple_condicion, axis=1)

    # Especifica el nombre del archivo Excel en el que deseas guardar el DataFrame
    nombre_archivo = archivo_resultados.split('.')[0] + "_Juntado.xlsx"

    # Guarda el DataFrame en un archivo Excel
    caso_resultados_df.to_excel(nombre_archivo, index=False)  # El argumento index=False evita que se incluya el índice en el archivo

    print(f"DataFrame guardado en {nombre_archivo}")

    return nombre_archivo
    
convertir_a_excel(os.path.join("Tiempos p-median con v45", "tiempos_p_3_v_45.xlsx"))

