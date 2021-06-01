import psycopg2, psycopg2.extras
import pandas as pd

def get_columns(desc):
    cols = []
    for i in desc:
        cols.append(i[0])
    return cols

class Persona():
    data_db = 'guarani3162posgrado'
    data_db = 'guarani3162posgradoprueba'

    def __init__(self, persona):
        self.persona = persona
        self.legajo = ''

        if persona == None:
            self.persona = 0

        if persona != 0:
            conn = psycopg2.connect(database=self.data_db, user='postgres', password='uNTreF2019!!',
                                    host='170.210.45.210')
            cur = conn.cursor()
            cur.execute(f'''SELECT TDOC.desc_abreviada as tipo_doc, DOC.nro_documento, PER.apellido, PER.nombres,
                                   SEX.descripcion as sexo, PER.fecha_nacimiento, NAC.descripcion as nacionalidad,
                                   PAIS.nombre as pais_origen
                            FROM negocio.mdp_personas PER
                                     LEFT JOIN negocio.mdp_personas_documentos DOC ON PER.persona = DOC.persona
                                     LEFT JOIN negocio.mdp_tipo_documento TDOC ON DOC.tipo_documento = TDOC.tipo_documento
                                     LEFT JOIN negocio.mdp_nacionalidades NAC ON PER.nacionalidad = NAC.nacionalidad
                                     LEFT JOIN negocio.mug_paises PAIS ON PER.pais_origen = PAIS.pais
                                     LEFT JOIN negocio.mdp_personas_sexo SEX ON PER.sexo = SEX.sexo
                                 WHERE PER.persona = '{self.persona}'; ''')
            cols = get_columns(cur.description)
            self.db_personal = pd.DataFrame(cur.fetchall(), columns=cols)
            conn.close()

    def isPersona(self):
        conn = psycopg2.connect(database=self.data_db, user='postgres', password='uNTreF2019!!', host='170.210.45.210')
        cur = conn.cursor()
        cur.execute(f'''SELECT persona
                        FROM negocio.mdp_personas
                        WHERE persona = '{self.persona}'; ''')

        cols = get_columns(cur.description)
        self.hay_persona = pd.DataFrame(cur.fetchall(), columns=cols)

        if len(self.hay_persona) > 0:
            return True
        else:
            return False

    def isAlumno(self):
        conn = psycopg2.connect(database=self.data_db, user='postgres', password='uNTreF2019!!', host='170.210.45.210')
        cur = conn.cursor()
        cur.execute(f'''SELECT legajo FROM negocio.sga_alumnos WHERE persona = '{self.persona}'; ''')
        try:
            self.legajo = int(cur.fetchone()[0])
            return True
        except:
            self.legajo = 0
            return False

    def getLegajo(self):
        self.isAlumno()
        return self.legajo

    def getPersonalData(self):
        if self.isPersona():
            return self.db_personal


class Alumno(Persona):

    def getEstudiosGrado(self):
        if self.isPersona():
            conn = psycopg2.connect(database=self.data_db, user='postgres', password='uNTreF2019!!',
                                    host='170.210.45.210')
            cur = conn.cursor()
            cur.execute(f'''SELECT E.persona, N.descripcion as nivel_estudios, E.institucion_otra as institucion_grado,
                                   E.titulo_otro as titulo_grado, E.fecha_egreso as egreso_grado
                            FROM negocio.mdp_datos_estudios E
                                LEFT JOIN negocio.mdp_nivel_estudio N ON E.nivel_estudio = N.nivel_estudio
                            WHERE persona = '{self.persona}'
                            AND E.nivel_estudio = 5
                            ; ''')
            cols = get_columns(cur.description)
            self.db_datos_grado = pd.DataFrame(cur.fetchall(), columns=cols)
            conn.close()
            return self.db_datos_grado

    def hasCertificado(self):
        conn = psycopg2.connect(database=self.data_db, user='postgres', password='uNTreF2019!!', host='170.210.45.210')
        cur = conn.cursor()
        cur.execute(f'''SELECT nro_solicitud FROM negocio.sga_certificados_otorg  WHERE persona = {self.persona}; ''')
        certificado_db = pd.DataFrame(cur.fetchall())

        if len(certificado_db) > 0:
            return True
        else:
            return False

    def getCertificado(self):
        if self.isPersona():
            if self.hasCertificado():
                conn = psycopg2.connect(database=self.data_db, user='postgres', password='uNTreF2019!!',
                                        host='170.210.45.210')
                cur = conn.cursor()
                cur.execute(
                    f'''SELECT CERTO.nro_solicitud, CERTO.fecha_inicio_tramite, CERTO.persona, CERTO.alumno, CERT.nombre as certificado, 
                                       PLAN.nombre as plan, PLAN.codigo, CERTO.plan_version, 
                                       CERTO.nro_expediente as expte_tramite, CERTO.fecha_egreso as fecha_egreso_posgrado, CERTO.promedio, 
                                       E.descripcion as estado, D.documento_numero as UNTREF, D.fecha as UNTREF_fecha
                                FROM negocio.sga_certificados_otorg CERTO
                                    INNER JOIN negocio.sga_certificados CERT ON CERTO.certificado = CERT.certificado
                                    INNER JOIN negocio.sga_planes_versiones PV ON CERTO.plan_version = PV.plan_version
                                    INNER JOIN negocio.sga_planes PLAN ON PV.plan = PLAN.plan
                                    INNER JOIN negocio.mce_estados E ON CERTO.estado = E.estado
                                    INNER JOIN negocio.sga_documentos D ON PV.documento_alta = D.documento
                                WHERE CERTO.persona = {self.persona}
                                ; ''')
                cols = get_columns(cur.description)
                certificado_db = pd.DataFrame(cur.fetchall(), columns=cols)
                certificado_db = certificado_db.rename(columns={'untref': 'UNTREF', 'untref_fecha': 'UNTREF_fecha'})
                plan_version = certificado_db.plan_version.iloc[0]

                conn = psycopg2.connect(database=self.data_db, user='postgres', password='uNTreF2019!!',
                                        host='170.210.45.210')
                cur = conn.cursor()
                cur.execute(f'''SELECT plan_version, tipo, nro_resolucion, fecha_desde
                                FROM negocio.sga_certificados_resoluciones
                                WHERE tipo IN ('CONEAU','MINISTERIAL') AND plan_version = {plan_version}
                                ; ''')
                cols = get_columns(cur.description)
                norma = pd.DataFrame(cur.fetchall(), columns=cols)
                norma = norma.sort_values(['plan_version', 'tipo', 'fecha_desde'])
                norma = norma.drop_duplicates(['plan_version', 'tipo'], keep='last')
                traspuesto = norma.groupby('plan_version')['tipo', 'nro_resolucion', 'fecha_desde'].apply(
                    lambda norma: norma.reset_index(drop=True)).unstack()
                traspuesto.reset_index(inplace=True, drop=False)
                normaOK = pd.concat([traspuesto.plan_version,
                                     traspuesto['nro_resolucion'][0], traspuesto['fecha_desde'][0], \
                                     traspuesto['nro_resolucion'][1], traspuesto['fecha_desde'][1]], axis=1)
                normaOK.columns = ['plan_version', 'CONEAU', 'CONEAU_fecha', 'MINISTERIAL', 'MINISTERIAL_fecha']
                certificado_db = certificado_db.merge(normaOK)

                return certificado_db
#    def __str__(self):
#        return 'Persona: '+str(self.persona)+' | Apellido: '+self.apellido+', '+self.nombre.capitalize() + ' | DNI: '+self.nro_documento

#    __repr__ = __str__