# Nuevo archivo limpiador para archivos de base SIES
import numpy as np
import pandas as pd
import time
# import logging
# import sys
# import os


def Main(foldername, oferta_path, mat_path, titulados_path):
    """Ejecuta programa para ordenar bases de datos
    y guardarlas en archivo xlsx en el directorio foldername.

    Keyword arguments:
    foldername -- Nombre del directorio donde guardar archivos
    """
    # main_log.info('Se inicia Main')

    # Nuevo archivo limpiador para archivos de base SIES
    def lecto_limpiador(archivo):
        # main_log.info(f'Función para depurar archivo {archivo}')
        x = pd.read_csv(archivo,
                        encoding='Windows 1252',
                        sep=";",
                        encoding_errors='ignore',
                        low_memory=False)
        x.columns = x.columns.str.strip()
        return x

    oferta = lecto_limpiador(oferta_path)
    matricula = lecto_limpiador(mat_path)
    titulados = lecto_limpiador(titulados_path)

    # Cambiar columna Código Único por
    # columna de código corto con sede en bases
    # de Matrícula y Titulados.
    # Para base de Oferta, crear columna calculada
    # como concatenación de Código IES y Código carrera

    def codigo_corto(df):
        """Cambiar código de la carrera por el código único reducido."""
        x = df
        regex_codigo = r"[SJV]\d*"
        x = x.str.replace(pat=regex_codigo, repl='', regex=True)
        return x

    matricula['CÓDIGO CARRERA'] = codigo_corto(matricula['CÓDIGO CARRERA'])
    titulados['CÓDIGO CARRERA'] = codigo_corto(titulados['CÓDIGO CARRERA'])

    codigo_oferta = (
                     'I'
                     + oferta['Código IES'].astype(str)
                     + 'C'
                     + oferta['Código Carrera'].astype(str)
                     )

    oferta.insert(0, 'Código Corto', codigo_oferta)

    # Exportar base de Sedes

    Sedes = matricula[[
                       'CÓDIGO CARRERA',
                       'NOMBRE INSTITUCIÓN',
                       'NOMBRE CARRERA',
                       'NOMBRE SEDE',
                       'TOTAL MATRICULADOS'
                       ]]

    Sedes = Sedes.groupby(by=[
                            'CÓDIGO CARRERA',
                            'NOMBRE INSTITUCIÓN',
                            'NOMBRE CARRERA',
                            'NOMBRE SEDE'],
                          as_index=False).sum()

    Sedes = Sedes.rename(columns={
                        'CÓDIGO CARRERA': 'Código Corto',
                        'NOMBRE INSTITUCIÓN': 'Nombre IES',
                        'NOMBRE CARRERA': 'Nombre carrera o programa',
                        'NOMBRE SEDE': 'Nombre Sede',
                        'TOTAL MATRICULADOS': 'Matrícula Total'}
                        )

    PATH_sedes = foldername + '/sedes.xlsx'

    Sedes.to_excel(PATH_sedes, index=False)

    Base_oferta = oferta[[
        'Código Corto',
        'Tipo Institución 1',
        'Nombre IES',
        'Nombre Carrera',
        'Nivel Global',
        'Nivel Carrera',
        'Área del conocimiento'
    ]]

    Base_matricula = matricula[[
        'CÓDIGO CARRERA',
        'TOTAL MATRICULADOS',
        'TOTAL MATRICULADOS PRIMER AÑO'
    ]]
    Base_matricula = Base_matricula.rename(columns={
        'CÓDIGO CARRERA': 'Código Corto',
        'TOTAL MATRICULADOS': 'Matrícula Total',
        'TOTAL MATRICULADOS PRIMER AÑO':
            'Matrícula Primer Año'}
    )

    Base_titulados = titulados[[
        'CÓDIGO CARRERA',
        'TOTAL TITULADOS'
    ]]
    Base_titulados = Base_titulados.rename(columns={
        'CÓDIGO CARRERA': 'Código Corto',
        'TOTAL TITULADOS': 'Titulados'}
    )

    # Quedarse con una base de casos únicos
    Base_oferta = Base_oferta.drop_duplicates()

    Base_matricula = Base_matricula.groupby(by=['Código Corto'],
                                            as_index=False).sum()

    Base_titulados = Base_titulados.groupby(by=['Código Corto'],
                                            as_index=False).sum()

    # Generar base con cruce

    base_general = pd.merge(Base_oferta,
                            Base_matricula,
                            on='Código Corto',
                            how='left')

    base_general = pd.merge(base_general,
                            Base_titulados,
                            on='Código Corto',
                            how='left')

    # Condiciones escritas para filtrar.
    eemmoo_str = "Especialidad Médica U Odontológica"
    bachi_pc_ci_str = "Bachillerato, Ciclo Inicial o Plan Común"
    TNS_str = 'Técnico de Nivel Superior'
    Postitulo_str = 'Postítulo'

    def Filtro_codigos(df, condition_mask):
        """Retorna Data Frame df filtrado según condition_mask"""
        return df['Código Corto'].copy().loc[condition_mask].unique()

    set_matr_vigente = Filtro_codigos(
        base_general,
        base_general['Matrícula Primer Año'] > 0)

    set_titulados = Filtro_codigos(
        base_general,
        base_general['Titulados'] > 0)

    eemmoo = Filtro_codigos(
        base_general,
        base_general['Nivel Carrera'] == eemmoo_str)

    pre_post = Filtro_codigos(
        base_general,
        base_general['Nivel Global'] != Postitulo_str)

    bachi_pc_ci = Filtro_codigos(
        base_general,
        base_general['Nivel Carrera'] == bachi_pc_ci_str)

    programas = np.setdiff1d(np.union1d(eemmoo, pre_post), bachi_pc_ci)
    elegibles = np.intersect1d(np.intersect1d(programas,
                                              set_matr_vigente), set_titulados)

    # Agregar columna caso TNS

    base_general.insert(base_general.shape[1], 'TNS', '')

    base_general.loc[base_general['Nivel Carrera'] == TNS_str, 'TNS'] = 'Sí'

    # Agregar columna con elegibilidad

    base_general.insert(base_general.shape[1], 'Elegibles', '')

    base_general.loc[np.isin(base_general['Código Corto'], elegibles),
    'Elegibles'] = 'Sí'

    base_general.loc[np.isin(
        base_general['Código Corto'],
        elegibles,
        invert=True),
    'Elegibles'] = 'No'

    base_general.loc[base_general['Nivel Carrera'] == eemmoo_str,
    'Nivel Global'] = 'Postgrado'

    # Renombrar columnas a nomenclatura CNA

    base_general = base_general.rename(columns={
        'Tipo Institución 1':
            'Tipo Institución',
        'Nombre Carrera':
            'Nombre  Carrera o Programa',
        'Nombre IES': 'IES',
        'Nivel Global': 'Nivel CNA',
        'Nivel Carrera': 'Nivel Carrera SIES'}
    )

    # Quitar las IES en convenio

    bool_convenio = base_general['IES'].str.contains('convenio',
                                                     case=False)
    base_general = base_general.loc[~bool_convenio]

    # Quitar los postítulos

    bool_postitulo = base_general['Nivel CNA'].str.contains('Postítulo',
                                                            case=False)
    base_general = base_general.loc[~bool_postitulo]

    base_general.to_excel(foldername + '/elegibles consolidado.xlsx', index=False)

    # Guardar tabla de datos  y elegibles en formato .xlsx.
    for i in base_general['IES'].unique():
        # self.update_bar()
        directorio = foldername + '/Elegibles/{fies}.xlsx'.format(fies=i)
        base_general[base_general['IES'] == i].to_excel(directorio,
                                                        index=False)

# Constantes globables


AC = 'Área del conocimiento'
NIVEL = 'Nivel CNA'

art_8 = 'Resultados de la fórmula (RE DJ N°346-45 de 2023, artículo 8)'
art_10 = ('Reemplazo de carreras o programas ' +
          '(RE DJ N°346-45 de 2023, artículo 10)')
art_11 = ('Ordenación y selección de sedes' +
          '(RE DJ N°346-45 de 2023, artículo 11)')


def seleccionar_N_programas(base: pd.DataFrame, N):
    """
    Dados un DataFrame y un N, selecciona N filas de este DF
    según reglamento y devuelve un DF con sólo estas columnas
    """
    base = base.sort_values(by='Matrícula Total', ascending=False)
    indices = np.arange(len(base))+1
    base.insert(0, column='Índices', value=indices)
    indices_elegidos = np.random.choice(indices, size=N)
    # seleccion_log.info('Se seleccionaron las carreras o programas N°: ' +
    #                  f'{np.array2string(indices_elegidos)}')
    programas_elegidos = np.isin(base['Índices'], indices_elegidos)
    eleccion = base.loc[programas_elegidos]
    eleccion = eleccion.drop(columns='Índices')
    return eleccion

def Seleccionar_prog(base: pd.DataFrame):
    """
    Función que escoge un programa aleatorio según reglamento,
    recibe una base ya filtrada según AC y escoge de ella una
    carrera o programa
    """
    base = base.sort_values(by='Matrícula Total', ascending=False)
    indices = np.arange(len(base))+1
    base.insert(0, column='Índices', value=indices)
    indice_elegido = np.random.choice(indices, size=1)
    indice_elegido = int(indice_elegido[0])
    # seleccion_log.info('Se selecciona carrera o programa N°: ' +
    #                   f'{indice_elegido} en el área ' +
    #                   f'{np.array2string(base[AC].unique())}')
    prog_elegido = base['Índices'] == indice_elegido
    eleccion = base.loc[prog_elegido]
    eleccion = eleccion.drop(columns='Índices')
    eleccion_np = eleccion.to_numpy(copy=True)
    return eleccion_np

def Seleccionar_sede(sedes_funcion: pd.DataFrame):
    """
    Función que escoge sedes aleatorias según reglamento,
    recibe una base ya filtrada para un código corto específico
    (en otras palabras, una carrera/programa) y determina tanto
    número de sedes a agregar como las sedes escogidas
    El output siempre será un array de 3 elementos
    """
    programa = sedes_funcion['Código Corto'].unique()
    sedes_funcion = sedes_funcion.sort_values(by='Matrícula Total',
                                              ascending=False)
    indices = np.arange(len(sedes_funcion))+1
    sedes_funcion.insert(0, column='Índices', value=indices)
    if len(indices) in np.arange(1, 3 + 1):
        indices_elegidos = np.random.choice(indices, size=1)
    elif len(indices) in np.arange(4, 9 + 1):
        indices_elegidos = np.random.choice(indices, size=2)
    elif len(indices) >= 10:
        indices_elegidos = np.random.choice(indices, size=3)
    sedes_elegidas = np.isin(sedes_funcion['Índices'], indices_elegidos)
    eleccion = sedes_funcion.loc[sedes_elegidas]
    eleccion_sedes = eleccion['Nombre Sede']
    eleccion_np = eleccion_sedes.to_numpy(copy=True)
    # seleccion_log.debug('Se seleccionaron las sedes: ' +
    #                    f'{np.array2string(eleccion_np)} ' +
    #                    f'para el programa {programa}')
    while len(eleccion_np) < 3:
        eleccion_np = np.append(eleccion_np, [''])
    return eleccion_np


def agregar_sedes(base, base_sedes):
    """
    Agrega las sedes a la base, iterando sobre cada programa
    que contenga la selección. Esta función se usa en el caso de
    la selección final (con o sin reemplazo)
    """
    for codigo in base['Código Corto']:
        sedes_codigo = base_sedes.loc[base_sedes['Código Corto'] == codigo]
        sedes_seleccionadas = Seleccionar_sede(sedes_codigo)
        base.loc[base['Código Corto'] == codigo,
                 ['Sede 1', 'Sede 2', 'Sede 3']] = sedes_seleccionadas


def caso_1_AC(df):
    """
    Recibe un DataFrame con la base de carreras y retorna DF
    con sólo elegibles según reglas en caso con 1 AC.
    Agrega TNS al inicio de ser necesario.
    """
    N_prog = df.shape[0]

    caso_TNS = 'Sí' in df['TNS'].unique()

    if caso_TNS:
        #seleccion_log.info(
        #    'Caso IES con 1 AC con TNS. ' +
        #    'Se procede a realizar selección de  TNS')

        base_TNS = df[df['TNS'] == 'Sí']
        print(base_TNS)
        TNS_elegida = seleccionar_N_programas(base_TNS, 1)
        base_sin_TNS_elegida = df.loc[
                    df['Código Corto'] !=
                    TNS_elegida['Código Corto'].unique()[0]
                    ]
        print(base_sin_TNS_elegida)
        if N_prog == 1:
            programas = TNS_elegida
        elif N_prog >= 2 and N_prog <= 9:
            prog_no_TNS = seleccionar_N_programas(base_sin_TNS_elegida, 1)
            programas = pd.concat([TNS_elegida, prog_no_TNS])
        elif N_prog >= 10:
            prog_no_TNS = seleccionar_N_programas(base_sin_TNS_elegida, 2)
            programas = pd.concat([TNS_elegida, prog_no_TNS])
        return programas

    elif not caso_TNS:
        if N_prog == 1:
            programas = seleccionar_N_programas(df, 1)
        elif N_prog >= 2 and N_prog <= 9:
            programas = seleccionar_N_programas(df, 2)
        elif N_prog >= 10:
            programas = seleccionar_N_programas(df, 3)
        return programas

def caso_FFAA(df):
    """
    Recibe un DataFrame con la base de carreras y retorna DF
    con sólo elegibles según reglas de FFAA
    """
    N_prog = df.shape[0]
    if N_prog == 1:
        programas = seleccionar_N_programas(df, 1)
    if N_prog == 2:
        programas = seleccionar_N_programas(df, 2)
    elif N_prog > 2 and N_prog <= 15:
        programas = seleccionar_N_programas(df, 2)
    elif N_prog > 15 and N_prog <= 30:
        programas = seleccionar_N_programas(df, 3)
    elif N_prog > 30:
        programas = seleccionar_N_programas(df, 4)
    return programas


def funcion_seleccion(IES: str):

    # seleccion_log.info(f'Se inicia selección para la Institución: {IES}')

    PATH_base = f'../Bases Depuradas/Elegibles/{IES}.xlsx'
    PATH_sedes = 'C:/Users/19990772/Desktop/Bases Depuradas/Sedes.xlsx'

    base = pd.read_excel(PATH_base)
    Sedes = pd.read_excel(PATH_sedes)

    # Agregar nuevas columnas donde irán las sedes

    N_columnas = base.shape[1]

    base.insert(N_columnas, 'Sede 1', '')
    base.insert(N_columnas + 1, 'Sede 2', '')
    base.insert(N_columnas + 2, 'Sede 3', '')

    # Sólo trabajar con la base de elegibles

    bool_elegibles = base['Elegibles'] == 'Sí'

    base = base.loc[bool_elegibles]
    # seleccion_log.debug('Se filtra base para trabajar con elegibles')

    # Revisar número AC institución

    AREAS = base[AC].unique()
    N_AC = len(AREAS)

    AC_pre = base[base[NIVEL] == 'Pregrado'][AC].unique()
    N_AC_pre = len(AC_pre)

    AC_post = base[base[NIVEL] == 'Postgrado'][AC].unique()
    N_AC_post = len(AC_post)

    Resumen_AC = 'Resumen de Areas del Conocimiento (AC):'

    # seleccion_log.info(f'{Resumen_AC}')
    # seleccion_log.info(f'Número AC total = {N_AC}')
    # seleccion_log.info(f'Número AC pregrado = {N_AC_pre}')
    # seleccion_log.info(f'Número AC postgrado = {N_AC_post}')

    # Revisar número AC institución, si hay postgrado entonces
    # calculamos el índice de AC a escoger

    def formula_post(ac, ac_pre, ac_post):
        # Fórmula usada en el cálculo de índices
        frac = ac/(1 + ac_pre/ac_post)
        # if frac - np.floor(frac) <= 0.4:
        #     valor = np.floor(frac)
        # elif frac - np.floor(frac) >= 0.5:
        #     valor = np.floor(frac) + 1
        valor = np.ceil(frac)  # Caso actual
        return int(valor)

    if N_AC_post > 0:
        indice_post = formula_post(N_AC, N_AC_pre, N_AC_post)
        indice_pre = N_AC - indice_post

        # seleccion_log.info(f'{art_8}')
        # seleccion_log.info(
        #     'N° de programas de postgrado a seleccionar ' +
        #     f'= {indice_post}')
        # seleccion_log.info(
        #    'N° de carreras de pregrado a seleccionar ' +
        #    f'= {indice_pre}')

    else:
        indice_pre = N_AC
        indice_post = 0

        # seleccion_log.info(f'{art_8}')
        # seleccion_log.info(
        #    'N° de carreras de postgrado a seleccionar ' +
        #    f'= {indice_post}')
        # seleccion_log.info(
        #    'N° de carreras de pregrado a seleccionar ' +
        #    f'= {indice_pre}')

    # Revisar el caso N_AC = 1

    if N_AC == 0:
        msg_N_AC_0 = (
            'La institución no tiene carreras o programas ' +
            'elegibles, por lo tanto, no hay resultado en la ' +
            'selección de muestra intencionada.')
        # seleccion_log.info(
        #    'Terminado con excepción: ' + msg_N_AC_0)
        raise Exception('Terminado con errores')
        return False

    elif 'FFAA' in IES.split(' '):
        # seleccion_log.info('Se ejecuta Seleccion caso FFAA')

        seleccion_final = caso_FFAA(base)

    elif N_AC == 1:
        # seleccion_log.info('Se ejecuta Selección caso 1 AC')

        seleccion_final = caso_1_AC(base)

    elif N_AC > 1:
        # seleccion_log.info('Se ejecuta Selección caso General')

        data_seleccion_0 = np.empty((N_AC, len(base.columns)), dtype=object)

        # Hacer excepción para el caso Universidad con TNS
        # (implementación alternativa 1)

        caso_universidad = 'UNIVERSIDAD' in IES.split(' ')
        caso_TNS = 'Sí' in base['TNS'].unique()

        AC_bloqueada_TNS = np.array([])
        if caso_TNS and caso_universidad:
            # seleccion_log.info(
            #    'Caso Universidad con TNS. ' +
            #    'Se procede a realizar bloqueo de AC con TNS')
            #display_log.info(
            #    'Caso Universidad con TNS.' +
            #    'Se procede a realizar bloqueo de AC con TNS')

            base_TNS = base[base['TNS'] == 'Sí']
            AC_TNS = base_TNS[AC].unique()
            AC_bloqueada_TNS = np.random.choice(AC_TNS, size=1)
            print(f'AC_bloqueada_TNS es tipo {type(AC_bloqueada_TNS)}')
            print(AC_bloqueada_TNS)
            print(str(AC_bloqueada_TNS))
            # seleccion_log.info('Se bloquea AC: ' +
            #                   f'{str(AC_bloqueada_TNS)}')

        for n, area in enumerate(AREAS):
            base_AC = base[base[AC] == area]
            if len(AC_bloqueada_TNS) > 0 and area == AC_bloqueada_TNS:
                base_AC = base_AC[base_AC['TNS'] == 'Sí']
            data_seleccion_0[n] = Seleccionar_prog(base_AC)

        seleccion_0 = pd.DataFrame(data=data_seleccion_0, columns=base.columns)

        # Exportar tabla de selección antes de reemplazo

        #PATH_seleccion_inicial = ('../Bases Depuradas/'
        #                          + 'selección/'
        #                          + f'{IES}_selección_inicial.xlsx')

        #seleccion_0.to_excel(PATH_seleccion_inicial,
        #                     index=False)
        #seleccion_log.info('Se guarda selección en archivo ' +
        #                   f'{PATH_seleccion_inicial}')

        # -------------------------------------------------------------
        # Algoritmo de reemplazo

        # Cantidad de postgrados de la MI

        # seleccion_log.info(f'{art_10}')

        hist_nivel_seleccion = seleccion_0[NIVEL].value_counts()
        if 'Postgrado' in hist_nivel_seleccion:
            post_en_MI = hist_nivel_seleccion['Postgrado']
        else:
            post_en_MI = 0

        # Verificar grupo en exceso
        if post_en_MI == indice_post:
            # seleccion_log.info('No se realizó reemplazo')
            seleccion_final = seleccion_0
            agregar_sedes(seleccion_final, Sedes)

            # Guardar en excel
            PATH_seleccion_final = (
                f'../Bases Depuradas/selección/{IES}_selección.xlsx')
            seleccion_final.to_excel(PATH_seleccion_final,
                                     index=False)
            # seleccion_log.info('Se guarda seleccion en archivo' +
            #                   f'{PATH_seleccion_final}')

            return True
        elif post_en_MI > indice_post:
            # seleccion_log.info('Nivel en exceso: Postgrado')
            N_reemplazo = post_en_MI - indice_post
            nivel_en_exceso = 'Postgrado'
            nivel_escasez = 'Pregrado'
        else:
            # seleccion_log.info('Nivel de exceso: Pregrado')
            N_reemplazo = - (post_en_MI - indice_post)
            nivel_en_exceso = 'Pregrado'
            nivel_escasez = 'Postgrado'

        # Identificar áreas seleccionadas en exceso que también
        # estén en grupo en escasez
        areas_en_exceso = seleccion_0[seleccion_0[NIVEL] ==
                                      nivel_en_exceso][AC].unique()

        if nivel_escasez == 'Pregrado':
            areas_base_escasez = AC_pre
        else:
            areas_base_escasez = AC_post

        conjunto_reemplazo = np.intersect1d(areas_en_exceso,
                                            areas_base_escasez)

        # Quitar la AC bloqueada, en caso que exista

        conjunto_reemplazo = np.setdiff1d(conjunto_reemplazo, AC_bloqueada_TNS)
        conjunto_reemplazo_str = np.array2string(conjunto_reemplazo,
                                                 separator=', ')
        # seleccion_log.info('Conjunto disponible para reemplazo ' +
        #                   f'{conjunto_reemplazo_str}')
        # seleccion_log.info('Se procede a usar base sólo con programas' +
        #                   ' o carreras en el nivel en escasez')

        # Determinar las áreas a reemplazar

        if len(conjunto_reemplazo) == N_reemplazo:
            AC_reemplazo = conjunto_reemplazo
        elif len(conjunto_reemplazo) > N_reemplazo:
            AC_reemplazo = np.random.choice(conjunto_reemplazo,
                                            size=N_reemplazo,
                                            replace=False)
        else:
            # seleccion_log.info(
            #    'Terminado con excepción: ' +
            #    'Sin áreas disponibles para reemplazo')
            raise Exception('Terminado con errores')
            return False

        # Hacer el reemplazo en esta área, sólo tomando programas
        # del área en escasez

        seleccion_final = seleccion_0.copy()

        for area in AC_reemplazo:
            base_AC = base[base[AC] == area]
            base_AC = base_AC[base_AC[NIVEL] == nivel_escasez]
            prog_elegido = Seleccionar_prog(base_AC)
            bool_AC = seleccion_final[AC] == area
            seleccion_final[bool_AC] = prog_elegido

    # Agregar sedes en el caso con reemplazo

    agregar_sedes(seleccion_final, Sedes)
    # seleccion_log.info(f'{art_11}')

    # Guardar en excel
    PATH_seleccion_final = f'../Bases Depuradas/Selección/{IES}_selección final y sedes.xlsx'
    seleccion_final.to_excel(PATH_seleccion_final,
                             index=False)
    # seleccion_log.info('Se guarda seleccion en archivo' +
    #                    f'{PATH_seleccion_final}')

    return True


def funcion_seleccion_por_partes(IES: str):
    try:
        PATH_base = f'../Bases Depuradas/Elegibles/{IES}.xlsx'
        PATH_sedes = '../Bases Depuradas/Sedes.xlsx'

        base = pd.read_excel(PATH_base)
        Sedes = pd.read_excel(PATH_sedes)

        # Agregar nuevas columnas para sedes
        N_columnas = base.shape[1]
        base.insert(N_columnas, 'Sede 1', '')
        base.insert(N_columnas + 1, 'Sede 2', '')
        base.insert(N_columnas + 2, 'Sede 3', '')

        # Filtrar base de elegibles
        bool_elegibles = base['Elegibles'] == 'Sí'
        base = base.loc[bool_elegibles]

        # Revisar número AC institución
        AREAS = base[AC].unique()
        N_AC = len(AREAS)

        AC_pre = base[base[NIVEL] == 'Pregrado'][AC].unique()
        N_AC_pre = len(AC_pre)

        AC_post = base[base[NIVEL] == 'Postgrado'][AC].unique()
        N_AC_post = len(AC_post)

        # Fórmula usada en el cálculo de índices
        def formula_post(ac, ac_pre, ac_post):
            frac = ac / (1 + ac_pre / ac_post)
            valor = np.ceil(frac)
            return int(valor)

        # Calcular índices
        if N_AC_post > 0:
            indice_post = formula_post(N_AC, N_AC_pre, N_AC_post)
            indice_pre = N_AC - indice_post
        else:
            indice_pre = N_AC
            indice_post = 0

        if N_AC == 0:
            raise Exception('La institución no tiene carreras o programas elegibles.')

        data_seleccion_0 = np.empty((N_AC, len(base.columns)), dtype=object)

        # Hacer excepción para el caso Universidad con TNS
        caso_universidad = 'UNIVERSIDAD' in IES.split(' ')
        caso_TNS = 'Sí' in base['TNS'].unique()

        AC_bloqueada_TNS = np.array([])
        if caso_TNS and caso_universidad:
            base_TNS = base[base['TNS'] == 'Sí']
            AC_TNS = base_TNS[AC].unique()
            AC_bloqueada_TNS = np.random.choice(AC_TNS, size=1)

        for n, area in enumerate(AREAS):
            base_AC = base[base[AC] == area]
            if len(AC_bloqueada_TNS) > 0 and area == AC_bloqueada_TNS:
                base_AC = base_AC[base_AC['TNS'] == 'Sí']
            data_seleccion_0[n] = Seleccionar_prog(base_AC)

        seleccion_0 = pd.DataFrame(data=data_seleccion_0, columns=base.columns)

        PATH_seleccion_inicial = ('C:/Users/19990772/Desktop/Bases Depuradas/'
                                  + 'selección/'
                                  + f'{IES}_selección_inicial.xlsx')
        seleccion_0.to_excel(PATH_seleccion_inicial, index=False)

        hist_nivel_seleccion = seleccion_0[NIVEL].value_counts()

        if 'Postgrado' in hist_nivel_seleccion:
            post_en_MI = hist_nivel_seleccion['Postgrado']
        else:
            post_en_MI = 0

        if post_en_MI == indice_post:
            seleccion_final = seleccion_0
            agregar_sedes(seleccion_final, Sedes)

            PATH_seleccion_final = (
                f'../Bases Depuradas/selección/{IES}_selección.xlsx')
            seleccion_final.to_excel(PATH_seleccion_final, index=False)
            return seleccion_final
        elif post_en_MI > indice_post:
            N_reemplazo = post_en_MI - indice_post
            nivel_en_exceso = 'Postgrado'
            nivel_escasez = 'Pregrado'
        else:
            N_reemplazo = - (post_en_MI - indice_post)
            nivel_en_exceso = 'Pregrado'
            nivel_escasez = 'Postgrado'

        areas_en_exceso = seleccion_0[seleccion_0[NIVEL] == nivel_en_exceso][AC].unique()

        if nivel_escasez == 'Pregrado':
            areas_base_escasez = AC_pre
        else:
            areas_base_escasez = AC_post

        conjunto_reemplazo = np.intersect1d(areas_en_exceso, areas_base_escasez)
        conjunto_reemplazo = np.setdiff1d(conjunto_reemplazo, AC_bloqueada_TNS)
        conjunto_reemplazo_str = np.array2string(conjunto_reemplazo, separator=', ')

        if len(conjunto_reemplazo) == N_reemplazo:
            AC_reemplazo = conjunto_reemplazo
        elif len(conjunto_reemplazo) > N_reemplazo:
            AC_reemplazo = np.random.choice(conjunto_reemplazo, size=N_reemplazo, replace=False)
        else:
            raise Exception('No hay suficientes áreas de reemplazo.')

        seleccion_final = seleccion_0.copy()

        for area in AC_reemplazo:
            base_AC = base[base[AC] == area]
            base_AC = base_AC[base_AC[NIVEL] == nivel_escasez]
            prog_elegido = Seleccionar_prog(base_AC)
            bool_AC = seleccion_final[AC] == area
            seleccion_final[bool_AC] = prog_elegido

        agregar_sedes(seleccion_final, Sedes)
        return seleccion_0
    except Exception as e:
        print(f'Error: {e}')
        return pd.DataFrame()  # Retornar un DataFrame vacío en caso de error


if __name__ == "__main__":

    tiempo_inicio = time.time()

    IES = "UNIVERSIDAD CATOLICA DEL MAULE"

    lista_df = []

    for i in range(1, 1000):
        df = funcion_seleccion_por_partes(IES)
        if not df.empty:
            lista_df.append(df)
        else:
            print(f"No se generó el archivo para la iteración {i} debido a un error en la selección.")

    if lista_df:
        df_concatenado = pd.concat(lista_df, ignore_index=True)
        PATH_seleccion_inicial = ('C:/Users/19990772/Desktop/Bases Depuradas/Seleccion final test'
                                  + f'{IES}_selección_inicial_0.xlsx')
        df_concatenado.to_excel(PATH_seleccion_inicial,
                    index=False)
    else:
        print("Vali kk ql malo")

    tiempo_final = time.time()

    tiempo_minutos = (tiempo_final-tiempo_inicio)/60

    print("El tiempo de compilación del codigo fue de:", tiempo_minutos, "minutos")

    """
    carpeta = "C:/Users/19990772/Desktop/Bases Depuradas/Seleccion final test"
    dfs = []

    for archivo in os.listdir(carpeta):
        if archivo.endswith('.xlsx'):  # Asegúrate de que el archivo sea un Excel
            ruta_archivo = os.path.join(carpeta, archivo)
            # Lee el archivo Excel
            df = pd.read_excel(ruta_archivo)
            # Añade el DataFrame a la lista
            dfs.append(df)

    # Combina todos los DataFrames en uno solo
    df_combined = pd.concat(dfs, ignore_index=True)

    # Opcional: Guarda el DataFrame combinado en un nuevo archivo Excel
    df_combined.to_excel("C:/Users/19990772/Desktop/Bases Depuradas/Seleccion final test/combined_file.xlsx", index=False)
    """


    # PATH_seleccion_inicial = ('../Bases Depuradas/'
    #                          + 'selección/'
    #                          + f'{IES}_selección_inicial.xlsx')

    # seleccion_0.to_excel(PATH_seleccion_inicial,
    #                     index=False)


    """
    df = funcion_seleccion_por_partes(IES)
    carreras = df.iloc[:, 3]
    carreras = carreras.tolist()
    print(carreras)
    """


    # Python parte del 0, mucho tiempo en R

