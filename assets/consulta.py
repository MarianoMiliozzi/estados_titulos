import numpy as np; import pandas as pd; import time; import datetime
import psycopg2, psycopg2.extras; import os; from collections import defaultdict

dic_operaciones = {'I': 'Insert', 'U': 'Update', 'D': 'Delete'}

#
#
# # Esta celda permite obtener toda la tabla que sea seleccionada (el orden de las columnas varía desde la db hacia aqui)
# # elegimos el origen
# data_db = 'guarani3162posgrado'
# data_db = 'guarani3162posgradoprueba'
#
# # nos conectamos a la base seleccionada en data
# conn = psycopg2.connect(database=data_db, user='postgres', password='uNTreF2019!!', host='170.210.45.210')
# cur = conn.cursor()
#
# cur.execute(
#     '''SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA in ('negocio','negocio_pers') ''')
# tablas = pd.DataFrame(cur.fetchall())
# conn.close()
#
#
# def get_table(esquema, tabla_objetivo, columns, where):
#     ''' toma como parametros: esquema, tabla_objetivo, columns, where
#     esquema y tabla_objetivo son variables definidas, y columns es una lista de columnas filtrada de tablas[0]
#     siempre se trabajará con la base de datos declarada en data_db al inicio de esta notebook.
#     '''
#     global output_df
#     conn = psycopg2.connect(database=data_db, user='postgres', password='uNTreF2019!!', host='170.210.45.210')
#     cur = conn.cursor()
#
#     if where == '':
#         if columns == '*':
#             cur.execute('SELECT {} FROM {}.{}'.format(columns, esquema, tabla_objetivo))
#             output_df = pd.DataFrame(cur.fetchall(), columns=list(
#                 tablas.loc[(tablas[0] == esquema) & (tablas[1] == tabla_objetivo)][2]))
#         else:
#             cur.execute('SELECT {} FROM {}.{}'.format(', '.join(columns), esquema, tabla_objetivo))
#             output_df = pd.DataFrame(cur.fetchall(), columns=columns)
#
#     else:
#         if columns == '*':
#             cur.execute('SELECT {} FROM {}.{} WHERE {}'.format(columns, esquema, tabla_objetivo, where))
#             output_df = pd.DataFrame(cur.fetchall(), columns=list(
#                 tablas.loc[(tablas[0] == esquema) & (tablas[1] == tabla_objetivo)][2]))
#
#         else:
#             cur.execute('SELECT {} FROM {}.{} WHERE {}'.format(', '.join(columns), esquema, tabla_objetivo, where))
#             output_df = pd.DataFrame(cur.fetchall(), columns=columns)
#
#     # cerrar siempre la conexion por las dudas...
#     conn.close()
#     return output_df.tail(3)
#
#
# # primero vemos los certificados del circuito de egreso nuevo
#
# extraemos = ['nro_solicitud', 'certificado', 'alumno', 'plan_version', 'fecha_alta',
#              'fecha_inicio_tramite', 'nro_expediente', 'fecha_egreso',
#              'fecha_cambio_estado', 'estado', 'resolucion_rectorado', 'interfaz']
#
# get_table('negocio', 'sga_certificados_otorg', extraemos, 'circuito = 1003')
# tramites = output_df.copy()
#
# tramites.head(3)
#
# # obtengo las solicitudes que corren con el circuito de egreso nuestro
# nro_tramites = list(tramites.nro_solicitud)
# # convierto todo a string para poder joinear
# nro_tramites = [str(i) for i in nro_tramites]
# # genero una cadena de texto apta para el SQL
# nro_tramites = '(' + ','.join(nro_tramites) + ')'
#
# # extraigo los cambios de estados de los nros de solicitud brindados
# get_table('negocio', 'sga_certificados_otorg_cmb',
#           ['nro_solicitud', 'fecha', 'estado_anterior', 'accion', 'estado_nuevo', 'observaciones'],
#           "nro_solicitud in {}".format(nro_tramites))
# cambios = output_df.copy()
#
# # corrijo el formato de fecha
# cambios.fecha = [cambios.fecha.iloc[i].date() for i in range(len(cambios))]
#
# # necesitamos traducir las acciones y estados en palabras
# get_table('negocio', 'mce_acciones', ['accion', 'nombre'], "activo = 'S'")
# dic_acciones = {output_df.accion.iloc[i]: output_df.nombre.iloc[i] for i in range(len(output_df))}
# cambios.accion = cambios.accion.map(dic_acciones)
#
# # para los estados
# get_table('negocio', 'mce_estados', ['estado', 'nombre'], "activo = 'S'")
#
# dic_estados = {output_df.estado.iloc[i]: output_df.nombre.iloc[i] for i in range(len(output_df))}
#
# dic_estados.update({0: "00. Inicio del Trámite - Inicio"})
#
# cambios.estado_anterior.fillna(0, inplace=True)
# cambios.estado_nuevo.fillna(0, inplace=True)
#
# cambios.estado_anterior = cambios.estado_anterior.map(dic_estados)
# cambios.estado_nuevo = cambios.estado_nuevo.map(dic_estados)
#
# # temporalmente lockeamos en mi trámite modelo
# # cambios = cambios.loc[cambios.nro_solicitud == 1647]
#
# cambios.reset_index(inplace=True, drop=True)
#
# cambios
#
# # mergeamos tramites y estados
#
# tramites = tramites.merge(cambios)
#
# # obtenemos mas datos para mapear
#
# # obtengo las solicitudes que corren con el circuito de egreso nuestro
# cert_a_buscar = list(tramites.certificado.unique())
# # convierto todo a string para poder joinear
# cert_a_buscar = [str(i) for i in cert_a_buscar]
# # genero una cadena de texto apta para el SQL
# cert_a_buscar = '(' + ','.join(cert_a_buscar) + ')'
#
# get_table('negocio', 'sga_certificados', ['certificado', 'nombre', 'certificado_tipo'],
#           'certificado in {}'.format(cert_a_buscar))
# cert_ext = output_df.copy()
#
# cert_ext
#
# # mapeamos el db de certificados para obtener los nombres
# tramites.certificado = tramites.certificado.map(lambda x: cert_ext.loc[cert_ext.certificado == x].nombre.iloc[0])
#
# ### traemos la persona con el dato de alumno
#
# tramites.head(1)
#
# # obtengo las solicitudes que corren con el circuito de egreso nuestro
# alum_a_buscar = list(tramites.alumno.unique())
# # convierto todo a string para poder joinear
# alum_a_buscar = [str(i) for i in alum_a_buscar]
# # genero una cadena de texto apta para el SQL
# alum_a_buscar = '(' + ','.join(alum_a_buscar) + ')'
#
# get_table('negocio', 'sga_alumnos', ['alumno', 'persona'], 'alumno in {}'.format(alum_a_buscar))
# alumnos = output_df.copy()
#
# # mapeamos del dato alumno al dato persona
# tramites.alumno = tramites.alumno.map(lambda x: alumnos.loc[alumnos.alumno == x].persona.iloc[0])
#
# ### traemos los datos de la persona
#
# # obtengo las solicitudes que corren con el circuito de egreso nuestro
# alum_a_buscar = list(tramites.alumno.unique())
# # convierto todo a string para poder joinear
# alum_a_buscar = [str(i) for i in alum_a_buscar]
# # genero una cadena de texto apta para el SQL
# alum_a_buscar = '(' + ','.join(alum_a_buscar) + ')'
#
# get_table('negocio', 'vw_personas',
#           ['persona', 'apellido', 'nombres', 'sexo',
#            'desc_tipo_documento', 'nro_documento'],
#           'persona in {}'.format(alum_a_buscar))
# personas = output_df.copy()
#
#
# get_table('negocio', 'mdp_personas',
#           ['persona', 'fecha_nacimiento', 'pais_origen'],
#           'persona in {}'.format(alum_a_buscar))
# personas = personas.merge(output_df)
#
#
#
#
# # mergeamos los tramites con los datos del alumno
# tramites = tramites.merge(personas, left_on='alumno', right_on='persona')
#
# # de aca obtenemos los campos nuevos
# get_table('negocio_pers', 'sga_certificados_otorg_pers', '*', '')
#
# pers_cols = ['id_solicitud', 'fecha_inicio', 'solicitud_alumno', 'libre_deuda', 'tesis_tfi_cd', 'titulo_grado',
#              'documento_identidad', 'constancia_actividades_aprobadas', 'nota_director', 'acta_final',
#              'totalidad_actas',
#              'expte_nro', 'resolucion_nro', 'resolucion_fecha', 'resolucion_untref', 'resolucion_rme', 'coneau',
#              'registro_libro', 'registro_folio', 'registro_orden', 'fecha_egreso_personalizado', 'fecha_emision',
#              'nro_solicitud_sidcer', 'nro_diploma', 'fecha_finalizacion_sidcer', 'fecha_colacion', 'grupo']
#
# output_df.columns = pers_cols
# campos_pers = output_df.copy()
#
# campos_pers
#
# tramites = tramites.merge(campos_pers, left_on='nro_solicitud', right_on='id_solicitud')
#
# estados_detalle = tramites[
#     ['nro_solicitud', 'fecha_cambio_estado', 'estado_anterior', 'accion', 'estado_nuevo', 'observaciones']]
# estados_detalle
#
# datos_unicos = tramites[[
#
#     # datos de la solicitud de certificado
#     'grupo', 'nro_solicitud', 'certificado', 'plan_version', 'fecha_alta', 'fecha_inicio_tramite', 'estado', 'interfaz',
#
#     # HISTORIA ACADEMICA
#     'fecha_egreso',
#     'fecha_egreso_personalizado','certificado',
#
#     # DATOS DE LA PERSONA
#     'apellido', 'nombres', 'sexo', 'desc_tipo_documento', 'nro_documento','fecha_nacimiento', 'pais_origen',
#
#     # DOCUMENTACION PRESENTADA
#     'solicitud_alumno', 'libre_deuda', 'tesis_tfi_cd', 'titulo_grado', 'documento_identidad',
#     'constancia_actividades_aprobadas', 'nota_director', 'acta_final', 'totalidad_actas',
#
#     # DATOS ADMINISTRATIVOS
#     'expte_nro', 'resolucion_nro', 'resolucion_fecha', 'resolucion_untref', 'resolucion_rme', 'coneau',
#     'registro_libro', 'registro_folio', 'registro_orden',
#
#     # DATOS DE LOS DOCUMENTOS
#     # 'fecha_emision','nro_solicitud_sidcer', 'nro_diploma',
#
#     # DATOS DE FINALIZACION
#     # 'fecha_finalizacion_sidcer','fecha_colacion'
#
# ]].drop_duplicates()
#
#
# estados_detalle.to_csv('estados_detalle.csv', sep='|')
# datos_unicos.to_csv('datos_unicos.csv', sep='|')


estados_detalle = pd.read_csv('estados_detalle.csv',sep='|',index_col=[0])
datos_unicos = pd.read_csv('datos_unicos.csv',sep='|',index_col=[0])

def consulta_estados():
    return estados_detalle

def datos_uni():
    return datos_unicos