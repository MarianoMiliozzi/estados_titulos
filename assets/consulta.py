import psycopg2
import pandas as pd
import assets.data_db as data

def get_columns(desc):
    cols = []
    for i in desc:
        cols.append(i[0])
    return cols

def parse_date(date):
    try:
        return date.strftime('%d/%m/%Y')
    except:
        return date

def get_solicitudes_activas():
    # obtenemos un listado de certificados únicos que no estén en el último estado
    conn = psycopg2.connect(database=data.data_db, user=data.user, password=data.password, host=data.host)
    cur = conn.cursor()
    cur.execute(f'''SELECT * from (
                        SELECT CERT_O.certificado as id_, CERT.nombre as certificado, CERT_O.nro_solicitud as sol_id,
                               CERT_O.persona, ESTA.nombre as estado, PERS.grupo,
                               CASE CERT_O.estado WHEN 1013 THEN 'Final' ELSE 'Activo' END as con_estado

                        FROM negocio.sga_certificados_otorg CERT_O
                            LEFT JOIN negocio.sga_certificados CERT
                                ON CERT_O.certificado = CERT.certificado
                            LEFT JOIN negocio.mce_estados ESTA 
                                ON CERT_O.estado = ESTA.estado
                            LEFT JOIN negocio_pers.sga_certificados_otorg_pers PERS 
                                ON CERT_O.nro_solicitud = PERS.id_solicitud) as "my_table"
                    WHERE con_estado = 'Activo' ''')
    cols = get_columns(cur.description)
    certif = pd.DataFrame(cur.fetchall(), columns=cols)
    certif = certif.drop('con_estado',axis=1)

    certif.estado.fillna('00. Coordinación - Armado de Solicitud',inplace=True)

    certif.grupo.fillna('Indeterminado',inplace=True)


    conn.close()
    return certif



def get_solicitudes_filtradas(nros_solicitud=[]):
    conn = psycopg2.connect(database=data.data_db, user=data.user, password=data.password, host=data.host)
    cur = conn.cursor()
    cur.execute(f'''SELECT CERT_O.nro_solicitud, PERS.grupo, PER.apellido, DOC.nro_documento, CERT_O.fecha_inicio_tramite,
                           CERT.nombre as certificado, 
                           CONCAT(PLAN.nombre,' • ',PLAN.version) as nombre_plan,
                           REPLACE(CIR.nombre,'Solicitud de Título de Posgrado','Titulación') as circuito,
                           CERT_O.nro_expediente,
                           CERT_O.fecha_egreso, EST.nombre as estado_actual,
                           CERT_O.fecha_cambio_estado, PER.persona

                    FROM negocio.sga_certificados_otorg CERT_O
                        LEFT JOIN negocio.sga_certificados CERT ON CERT_O.certificado = CERT.certificado
                        LEFT JOIN negocio.mdp_personas PER ON CERT_O.persona = PER.persona
                        LEFT JOIN negocio.sga_planes_versiones PLAN ON CERT_O.plan_version = PLAN.plan_version
                        LEFT JOIN negocio.mce_circuitos CIR ON CERT_O.circuito = CIR.circuito
                        LEFT JOIN negocio.mce_estados EST ON CERT_O.estado = EST.estado
                        LEFT JOIN negocio.mdp_personas_documentos DOC ON PER.documento_principal = DOC.documento
                        LEFT JOIN negocio_pers.sga_certificados_otorg_pers PERS ON CERT_O.nro_solicitud = PERS.id_solicitud

                    WHERE CERT_O.nro_solicitud IN ({str(nros_solicitud)[1:-1]})
                    ''')
    cols = get_columns(cur.description)
    filtro_certificado = pd.DataFrame(cur.fetchall(), columns=cols)
    conn.close()

    filtro_certificado['fecha_inicio_tramite'] = filtro_certificado.fecha_inicio_tramite.map(parse_date)
    filtro_certificado['fecha_cambio_estado'] = filtro_certificado.fecha_cambio_estado.map(parse_date)


    return filtro_certificado

def get_datos_persona(persona=int):
    conn = psycopg2.connect(database=data.data_db, user=data.user, password=data.password, host=data.host)
    cur = conn.cursor()
    cur.execute(f'''SELECT PER.apellido, PER.nombres, PER.sexo, PER.fecha_nacimiento, NAC.descripcion as nacionalidad,
                           PAIS1.nombre as pais_origen,
                           TIPODOC.desc_abreviada as tipo_doc, DOC.nro_documento, PAIS2.nombre as pais_emisor,
                           EST.institucion_otra as institucion_ant, EST.titulo_otro as titulo_ant, EST.fecha_egreso as f_egreso_ant
                    FROM negocio.mdp_personas PER
                        LEFT JOIN negocio.mdp_nacionalidades NAC ON PER.nacionalidad = NAC.nacionalidad
                        LEFT JOIN negocio.mug_paises PAIS1 ON PER.pais_origen = PAIS1.pais
                        LEFT JOIN negocio.mdp_personas_documentos DOC ON PER.documento_principal = DOC.documento
                        LEFT JOIN negocio.mdp_tipo_documento TIPODOC ON DOC.tipo_documento = TIPODOC.tipo_documento
                        LEFT JOIN negocio.mug_paises PAIS2 ON DOC.pais_documento = PAIS2.pais
                        LEFT JOIN negocio.mdp_datos_estudios EST ON PER.persona = EST.persona AND EST.nivel_estudio = 5
                    WHERE PER.persona = {persona} ''')
    cols = get_columns(cur.description)
    datos_persona = pd.DataFrame(cur.fetchall(), columns=cols)
    datos_persona['fecha_nacimiento'] = datos_persona.fecha_nacimiento.map(parse_date)
    datos_persona['f_egreso_ant'] = datos_persona.f_egreso_ant.map(parse_date)
    conn.close()
    return datos_persona

def get_estados_solicitud(solicitud =int):
    conn = psycopg2.connect(database=data.data_db, user=data.user, password=data.password, host=data.host)
    cur = conn.cursor()
    cur.execute(f'''
                    SELECT CAMBIO.fecha as fecha_cambio, 
                           ESTA.nombre as estado_anterior, ACCION.nombre as accion ,ESTN.nombre as estado_nuevo,
                           CAMBIO.observaciones, PER.apellido as auditoria_usuario
                    FROM   negocio.sga_certificados_otorg_cmb CAMBIO
                        LEFT JOIN negocio.mce_estados ESTA ON CAMBIO.estado_anterior = ESTA.estado
                        LEFT JOIN negocio.mce_acciones ACCION ON CAMBIO.accion = ACCION.accion
                        LEFT JOIN negocio.mce_estados ESTN ON CAMBIO.estado_nuevo = ESTN.estado
                        LEFT JOIN negocio_auditoria.logs_sga_certificados_otorg_cmb AUDIT ON CAMBIO.cambio_estado = AUDIT.cambio_estado
                        LEFT JOIN negocio.mdp_personas PER ON AUDIT.auditoria_usuario = PER.usuario
                    WHERE CAMBIO.nro_solicitud = {solicitud}
                    ''')
    cols = get_columns(cur.description)
    detalle_solicitud = pd.DataFrame(cur.fetchall(), columns=cols)
    detalle_solicitud = detalle_solicitud.sort_values(by='fecha_cambio')
    detalle_solicitud['hora'] = [str(detalle_solicitud.fecha_cambio.iloc[i].hour)+':'+ str(detalle_solicitud.fecha_cambio.iloc[i].minute)
                                 if len(str(detalle_solicitud.fecha_cambio.iloc[i].minute)) == 2
                                 else str(detalle_solicitud.fecha_cambio.iloc[i].hour)+':'+'0'+str(detalle_solicitud.fecha_cambio.iloc[i].minute)
                                 for i in range(len(detalle_solicitud))]
    detalle_solicitud['fecha_cambio'] = detalle_solicitud.fecha_cambio.map(parse_date)
    conn.close()
    return detalle_solicitud

def get_datos_solicitud(solicitud=int):
    conn = psycopg2.connect(database=data.data_db, user=data.user, password=data.password, host=data.host)
    cur = conn.cursor()
    cur.execute(f'''
                    SELECT id_solicitud, fecha_inicio, resolucion_nro, resolucion_fecha, resolucion_untref,
                           resolucion_rme, coneau, registro_libro, registro_folio, registro_orden,
                           fecha_egreso_personalizado as fecha_egreso, fecha_emision, nro_solicitud_sidcer,
                            nro_diploma, fecha_finalizacion_sidcer, fecha_colacion
                    FROM   negocio_pers.sga_certificados_otorg_pers
                    WHERE id_solicitud = {solicitud}
                    ''')
    cols = get_columns(cur.description)
    datos_sol = pd.DataFrame(cur.fetchall(),columns=cols)
    conn.close()

    return datos_sol


def get_datos_documentacion(solicitud=int):
    conn = psycopg2.connect(database=data.data_db, user=data.user, password=data.password, host=data.host)
    cur = conn.cursor()
    cur.execute(f'''
                    SELECT grupo,
                           CASE solicitud_alumno WHEN True THEN 'SI' ELSE 'NO' END as solicitud_alumno,
                           CASE libre_deuda WHEN True THEN 'SI' ELSE 'NO' END as libre_deuda,
                           CASE tesis_tfi_cd WHEN True THEN 'SI' ELSE 'NO' END as tesis_cd,
                           CASE titulo_grado WHEN True THEN 'SI' ELSE 'NO' END as titulo_previo,
                           CASE documento_identidad WHEN True THEN 'SI' ELSE 'NO' END as documento,
                           CASE constancia_actividades_aprobadas WHEN True THEN 'SI' ELSE 'NO' END as car,
                           CASE nota_director WHEN True THEN 'SI' ELSE 'NO' END as nota_dir,
                           CASE acta_final WHEN True THEN 'SI' ELSE 'NO' END as acta_final,
                           CASE totalidad_actas WHEN True THEN 'SI' ELSE 'NO' END as actas_totales
                    FROM   negocio_pers.sga_certificados_otorg_pers
                    WHERE id_solicitud = {solicitud}
                    ''')
    cols = get_columns(cur.description)
    documentacion = pd.DataFrame(cur.fetchall(),columns=cols)
    conn.close()

    return documentacion