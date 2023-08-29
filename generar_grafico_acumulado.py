import pandas as pd
import matplotlib.pyplot as plt

archivos = [['Caso_Base_Juntado.xlsx','acum_caso_base.png', 'caso base'],
            ['tiempos_p_3_v_45_Juntado.xlsx', 'acum_p3.png', 'p = 3'],
            [ 'tiempos_p_5_v_45_Juntado.xlsx','acum_p5.png', 'p = 5'],
            [ 'tiempos_p_10_v_45_Juntado.xlsx', 'acum_p10.png', 'p = 10']]

for archivo in archivos:
    bdd = pd.read_excel(archivo[0])
    dict_caso = bdd.set_index('ID Cliente')[['Tiempo', 'Categoria']].to_dict(orient='index')

    horas = range(25)
    categorias = ['Premium', 'Silver', 'Gold']

    plt.figure(figsize=(10, 6))

    for categoria in categorias:
        porcentajes = [
            (sum(1 for cliente in dict_caso.values() if cliente['Tiempo'] <= hora and cliente['Categoria'] == categoria) /
            sum(1 for cliente in dict_caso.values() if cliente['Categoria'] == categoria) * 100)
            for hora in horas
        ]
        plt.plot(horas, porcentajes, label=categoria)

    plt.axvline(x=12, color='gray', linestyle='--', linewidth=1.5)  # Línea vertical en la hora 12
    plt.axvline(x=24, color='gray', linestyle='--', linewidth=1.5)  # Línea vertical en la hora 24

    plt.xlabel('Horas', fontsize=16)
    plt.ylabel('Despachos acumulados', fontsize=16)
    plt.title(f'Despachos acumulados por hora {archivo[2]}', fontsize=16)
    plt.legend(fontsize=16) 
    plt.grid(True)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    plt.savefig(archivo[1], dpi=300, bbox_inches='tight')

    plt.show()

    
