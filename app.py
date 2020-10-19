##################################### IMPORTING ################################
# -*- coding: utf-8 -*-
# importamos las librerias que implementaremos
import pandas as pd;
import base64;
import io
import plotly.graph_objs as go
import dash;
import dash_table;
from dash.dependencies import Output, Input
import dash_core_components as dcc;
import dash_html_components as html
# ademas importamos la funcion de consulta.py que ejecuta las querys SQL
import assets.consulta as consulta;
from collections import defaultdict

##################################### IMPORTING ################################
#################################### CONSULTA DB ###############################

# instanciamos en totales todos los datos de preinscriptos y tambien guardamos un diccionario con nombres y siglas de propuestas
estados = consulta.consulta_estados()
datos = consulta.datos_uni()

nacion = pd.read_csv('assets/nacionalidades.csv',encoding='latin',sep='|')
nacion_dic = {nacion.cod_nacionalidad.iloc[i]:nacion.nacionalidad.iloc[i] for i in range(len(nacion))}

#################################### CONSULTA DB ###############################
#################################### RAW PYTHON  ###############################
# genero un diccionario por default para guardar un mapeo de nro_solicitud vs. nro_documento
avaiable_dic = defaultdict(lambda: '',
                           {str(datos.nro_documento.iloc[i]): datos.nro_solicitud.iloc[i] for i in range(len(datos))})
# genero una lista de nros de documentos disponibles para buscar
avaiable = list(datos.nro_documento.unique())
avaiable = [str(i) for i in avaiable]

propuestas_lst = list(datos.certificado.unique())

# genero una tabla con la documentación presentada
documentacion = ['solicitud_alumno', 'libre_deuda', 'tesis_tfi_cd', 'titulo_grado',
                 'documento_identidad', 'constancia_actividades_aprobadas',
                 'nota_director', 'acta_final', 'totalidad_actas']

docu_dic = {'solicitud_alumno': 'Solicitud del Alumno', 'libre_deuda': 'Libre Deuda',
            'tesis_tfi_cd': 'Tesis/TFI en CD', 'titulo_grado': 'Copia de Título de Grado',
            'documento_identidad': 'Copia de Documento de Identidad',
            'constancia_actividades_aprobadas': 'Constancia de Actividades Aprobadas',
            'nota_director': 'Nota del Director', 'acta_final': 'Copia de Acta Final',
            'totalidad_actas': 'Totalidad de Actas en Original'}

try:
    estados.fecha_cambio_estado = pd.DatetimeIndex(estados.fecha_cambio_estado).strftime("%d/%m")  # /%Y
except:
    pass

try:
    datos.fecha_nacimiento = pd.DatetimeIndex(datos.fecha_nacimiento).strftime("%d/%m/%Y")  #
except:
    pass


# quito la numeración de estado nuevo
estados['estado_nuevo'] = [' '.join(estados.estado_nuevo.iloc[i].split('. ')[1:]) for i in range(len(estados))]

# agrego saltos de linea
estados['estado_nuevo'] = [estados.estado_nuevo.iloc[i].replace(' - ', '\n') for i in range(len(estados))]

dic_acciones = {'Iniciar Solicitud': 'Iniciar Solicitud',
                'Presenta Solicitud': 'Presenta Solicitud',
                'Observar Solicitud': 'Observar Solicitud',
                'Solicitar Expte.': 'Solicitar Expediente',
                'Expte. Recibido': 'Expediente Recibido',
                'Normativa Correcta / Emitir Analítico': 'Emitir Analítico',
                'Recibir Diploma': 'Recibir Diploma',
                'b. Cargar en SIDCER': 'Cargar en SIDCER',
                'c. Observar SIDCER': 'Observar SIDCER',
                'Corregir SIDCER': 'Corregir SIDCER',
                'Sacar Foto / Subir Imagen': 'Subir Imagen',
                'Aprobar Imagen': 'Aprobar Imagen',
                'Pase a Colación / Entrega': 'Pase a Colación',
                'Pase a Archivo Definitivo': 'Pase a Archivo Definitivo'}

estados['accion'] = estados.accion.map(dic_acciones)

# reordeno las columnas
estados = estados[
    ['nro_solicitud', 'fecha_cambio_estado', 'estado_anterior', 'accion', 'estado_nuevo', 'observaciones']]
# defino un dic para renombrar las columnas al mostrarlas

dic_estados_columns = {'fecha_cambio_estado': 'Fecha',
                       'estado_anterior': 'Estado Anterior',
                       'accion': 'Acción',
                       'estado_nuevo': 'Estado Actual',
                       'observaciones': 'Observaciones',
                       'nro_solicitud': 'Nro Solicitud',
                       'presento' : 'Presentó',
                       '':'',
                       }

dic_datos_columns = {'grupo':'Grupo',
                     'nro_solicitud':'Nro Solicitud',
                     'fecha_alta':'Fecha Alta',
                     'apellido':'Apellido',
                     'nombres':'Nombres',
                     'desc_tipo_documento':'Tipo Doc',
                     'nro_documento':'Documento',
                     'estado_actual':'Estado Actual'
                     }

################################### RAW PYTHON ###############################
################################## APP SETTING ###############################
# seteamos la url del ccs
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# instanciamos la app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# le definimos un título
app.title = 'Estado de Titulaciones de POSGRADOS'
# instanciamos el servidor
server = app.server  # the Flask app

freedb = pd.DataFrame()
################################## APP SETTING ###############################
################################## APP LAYOUT ################################
app.layout = html.Div([
    # genero la misma cabecera que las otras apps
    html.Div(className='row',
             children=[
                 html.H4('Estado de Titulaciones de POSGRADOS', className='eight columns'),
                 html.Img(src='/assets/untref_logo.jpg',
                          className='four columns',
                          style={'margin-top': '13px'}),
             ]
             ),

    # SELECCION DE CERTIFICADO
    html.Div(children=[
        dcc.Dropdown(id='carrera-elegida',
                     options=[dict({'label': propuestas_lst[i], 'value': propuestas_lst[i]}) for i in
                              range(len(propuestas_lst))],
                     value='',
                     clearable=True,
                     placeholder='Seleccione un Certificado',
#                    persistence=True,  # !!! INVESTIGAR SI SE GUARDA LOCAL ESTÁ BUENO
                     ),
        ]
    ),

    # TABLA DE TOTAL POR CERTIFICADO
    html.Div(id='div-tabla-estados-totales',
             className='row',
             style={'text-align':'center',
                    'align-content':'center'},
             hidden=False,
             children=[
                 html.Hr(),
                 html.H5(id='titulo-carrera-elegida'),
                 html.Div(style={#'width':'70%',
                                 'padding-left':'10%',
                                 'padding-right':'10%',},
                          children=[
                              dash_table.DataTable(
                                 id='tabla-estados-totales',
                                 row_selectable="single",
                                 include_headers_on_copy_paste=True,
                                 # GENERL STYLE
                                 style_cell={
                                     'textAlign': 'left',
                                 },
                                 style_data={'whiteSpace': 'pre-line'},
                                 # ancho columnas
                                 style_cell_conditional=[
                                     {
                                         'if': {'column_id': 'estado_actual'},
                                         'textAlign': 'center',
                                         'fontWeight': 'bold',
                                         'width':'300px',
                                     },
                                     {
                                         'if': {'column_id': ['nro_solicitud','grupo','fecha_alta']},
                                         'textAlign': 'center',
                                         'width':'120px',
                                     },
                                     {
                                         'if': {'column_id': ['apellido','nombres']},
                                         'textAlign': 'center',
                                         'width': '200px',
                                     }],
                                 ## STRIPED ROWS
                                 style_data_conditional=[
                                     {
                                         'if': {'row_index': 'odd'},
                                         'backgroundColor': 'rgb(248, 248, 248)',
                                     }
                                 ],
                                 ## HEADER
                                 style_header={
                                     'backgroundColor': 'rgb(230, 230, 230)',
                                     'fontWeight': 'bold'
                                 },
                            ),]
                 ),
             ]
             ),

    html.Div(id='datos-alumno-individual',
             style={'background-color':'#EEEEEE',
                    'margin-left':'5%',
                    'margin-right':'5%',
                    'margin-top':'10px',
                    'border-radius':'20px',
                    },
             hidden=True,
             children=[
                 # HIDDEN para alojar el ID de trámite
                 html.Div(html.H3(id='tramite-seleccionado', hidden=True, children='', )),

                 # CABEZERA ALUMNO
                 html.Div(id='heather-alumno',
                          style={'text-align': 'center',
                                 'padding': '2%',
                                 },
                          children=[
                              html.H3(id='apellido',
                                      style={'fontWeight': 'bold'})
                          ]
                          ),

                 # TABLA DE DOCUMENTACION PRESENTADA
                 html.Div(id='div-datos-documentacion',
                          className='row',
                          hidden=True,
                          children=[
                              # DATOS PRINCIPALES
                              html.Hr(style={'margin':'0px'}),
                              html.Div(className='six columns',
                                       children=[
                                           html.H5(children='Datos Principales'),

                                           html.Div(className='span-mio',
                                                    children=[
                                                        html.Span('Documento Tipo: ', style={'fontWeight': 'bold'}),
                                                        html.Span(id='docu-tipo'),
                                                        html.Br(),
                                                        html.Span('Documento Número: ', style={'fontWeight': 'bold'}),
                                                        html.Span(id='docu-numero'),
                                                        html.Br(),
                                                        html.Span('Nacionalidad: ', style={'fontWeight': 'bold'}),
                                                        html.Span(id='nacionalidad'),
                                                        html.Br(),
                                                        html.Span('Fecha de Nacimiento: ', style={'fontWeight': 'bold'}),
                                                        html.Span(id='fecha-nacimiento'),])
                                       ]),

                              html.Div(className='five columns',

                                       children=[
                                           html.H5(children='Documentación Presentada',
                                                   style={'text-align':'right'}),
                                           html.Div(
                                               dash_table.DataTable(
                                                   id='tabla-doc-presentada',
                                                   style_as_list_view=True,
                                                   # FECHA ACCION BOLD
                                                   style_cell_conditional=[
                                                       {
                                                           'if': {'column_id': 'presento'},
                                                           'textAlign': 'center',
                                                           'fontWeight': 'bold',
                                                           'padding-left': '10px',
                                                           'padding-right': '10px',
                                                       }
                                                   ],
                                               ),
                                           ),
                                       ]),
                          ]
                          ),

                 # TABLA DE CAMBIOS DE ESTADOS
                 html.Div(id='div-tabla-cambios-estados',
                          className='row',
                          hidden=True,
                          style={'padding':'4%',
                                 'padding-top':'0%'},
                          children=[
                              html.Hr(style={'padding':'0',}),
                              html.H5(children='Cambios de Estados',),
                              dash_table.DataTable(

                                  id='tabla-estados-cambios',
                                  style_as_list_view=True,

                                  # GENERL STYLE
                                  style_cell={
                                      'whiteSpace': 'normal',
                                      'height': 'auto',
                                      'textAlign': 'left',
                                  },
                                  # LINE BREAKS
                                  style_data={'whiteSpace': 'pre-line'},
                                  # FECHA ACCION BOLD
                                  style_cell_conditional=[
                                      {
                                          'if': {'column_id': c},
                                          'textAlign': 'center',
                                          'fontWeight': 'bold',
                                          'padding-left': '10px',
                                          'padding-right': '10px',
                                          # 'width':'100px',
                                      } for c in ['fecha_cambio_estado', 'accion']
                                  ],
                                  ## STRIPED ROWS
                                  style_data_conditional=[
                                      {
                                          'if': {'row_index': 'odd'},
                                          'backgroundColor': 'rgb(248, 248, 248)',
                                      }
                                  ],
                                  ## HEADER
                                  style_header={
                                      'backgroundColor': 'rgb(230, 230, 230)',
                                      'fontWeight': 'bold'
                                  },
                                    )
                              ]
                              ),
                 ]
             )

], className='cuerpo',
)


################################ APP LAYOUT ##################################
################################ CALL BACKS ##################################
@app.callback(
    [
        dash.dependencies.Output('div-tabla-estados-totales', 'hidden'),
        dash.dependencies.Output('tabla-estados-totales', 'data'),
        dash.dependencies.Output('tabla-estados-totales', 'columns'),

        dash.dependencies.Output('titulo-carrera-elegida', 'children'),

        dash.dependencies.Output('tabla-estados-totales', 'derived_virtual_selected_rows'),
        dash.dependencies.Output('tabla-estados-totales', 'selected_rows'),
    ],
    [
        dash.dependencies.Input('carrera-elegida', 'value')
    ]
)
def carrera_totales(carrera):

    if carrera == None:
        carrera = ''

    if carrera != '':
        tabla_totales = datos.copy()

        tabla_totales = tabla_totales.loc[tabla_totales.certificado == carrera]

        tabla_totales = tabla_totales[['grupo', 'nro_solicitud', 'fecha_alta', 'apellido', 'nombres']]



        estados_detalle = estados.loc[estados.nro_solicitud.isin(tabla_totales.nro_solicitud.unique())]
        estados_detalle = estados_detalle.drop_duplicates(subset='nro_solicitud',keep='last')

        tabla_totales['estado_actual'] = tabla_totales.nro_solicitud.map(lambda x : estados_detalle.loc[estados_detalle.nro_solicitud == x].estado_nuevo.iloc[0])

        return [False,  # visibilidad del div de la tabla
                tabla_totales.to_dict('records'),
                [{"name": dic_datos_columns[i], "id": i} for i in tabla_totales.columns],
                carrera,
                [],
                [],
                ]

    else:
        tabla_totales = freedb
        carrera = ''
        return [True,  # visibilidad del div de la tabla
                tabla_totales.to_dict('records'),
                [{"name": i, "id": i} for i in tabla_totales.columns],
                carrera,
                [],
                [],
                ]


@app.callback(
    [
        dash.dependencies.Output('datos-alumno-individual', 'hidden'),
        dash.dependencies.Output('apellido', 'children'),
    ],
    [
        dash.dependencies.Input('tabla-estados-totales', 'derived_virtual_selected_rows'),
        dash.dependencies.Input('carrera-elegida', 'value')
    ]
)
def datos_personales(row_selected, carrera):
    if type(row_selected) == list:
        pass
    else:
        row_selected = []

    if carrera==None:
        carrera = ''

    if carrera != '':
        tabla = datos.loc[datos.certificado == carrera]
    else:
        tabla = datos.copy()

    if len(row_selected) > 0:

        tabla.reset_index(inplace=True, drop=True)
        tram = tabla.loc[row_selected].nro_solicitud.iloc[0]

        tabla = tabla.loc[tabla.nro_solicitud == tram]
        apellido = tabla.apellido.iloc[0]
        nombres = tabla.nombres.iloc[0]

        apellido += ' '+nombres

        return [False,
                apellido
                ]

    else:
        tabla = freedb
        apellido = 'Sarasa'
        return [True,
                apellido
                ]


dash.dependencies.Output('docu-tipo', 'children'),
dash.dependencies.Output('docu-numero', 'children'),
dash.dependencies.Output('nacionalidad', 'children'),
dash.dependencies.Output('fecha-nacimiento', 'children'),



@app.callback([
        dash.dependencies.Output('tramite-seleccionado', 'children'),

        dash.dependencies.Output('docu-tipo', 'children'),
        dash.dependencies.Output('docu-numero', 'children'),
        dash.dependencies.Output('nacionalidad', 'children'),
        dash.dependencies.Output('fecha-nacimiento', 'children'),

        dash.dependencies.Output('div-datos-documentacion', 'hidden'),
        dash.dependencies.Output('tabla-doc-presentada', 'data'),
        dash.dependencies.Output('tabla-doc-presentada', 'columns'),

        dash.dependencies.Output('div-tabla-cambios-estados', 'hidden'),
        dash.dependencies.Output('tabla-estados-cambios', 'data'),
        dash.dependencies.Output('tabla-estados-cambios', 'columns'),
    ],
    [
        dash.dependencies.Input('tabla-estados-totales', 'derived_virtual_selected_rows'),
        dash.dependencies.Input('carrera-elegida', 'value')
    ]
)
def select_target(row_selected,carrera):
    if type(row_selected) == list:
        pass
    else:
        row_selected = []

    if carrera==None:
        carrera = ''

    if carrera != '':
        tabla = datos.loc[datos.certificado == carrera]
    else:
        tabla = datos.copy()



    if len(row_selected) > 0:
        tabla.reset_index(inplace=True, drop=True)
        tram = tabla.loc[row_selected].nro_solicitud.iloc[0]

        # para la tabla de documentación
        docu = tabla.loc[tabla.nro_solicitud == tram][documentacion].T
        docu.columns = ['presento']
        docu.loc[docu.presento == True, 'presento'] = 'Si'
        docu.loc[docu.presento == False, 'presento'] = 'No'
        docu.reset_index(inplace=True)
        docu.columns = ['', 'presento']
        docu[''] = docu[''].map(docu_dic)
        tabla_docu = docu.copy()

        # Datos sueltos
        docu_tipo = tabla.desc_tipo_documento.iloc[0]
        docu_numero = tabla.nro_documento.iloc[0]
        nacionalidad = nacion_dic[tabla.pais_origen.iloc[0]]
        fecha_nacimiento = tabla.fecha_nacimiento.iloc[0]

        # para la tabla de estados
        tabla = estados.copy()
        tabla = tabla.loc[tabla.nro_solicitud == tram]

        tabla_estados = tabla.drop(['nro_solicitud','estado_anterior'], axis=1)  #



        return [tram,
                docu_tipo,
                docu_numero,
                nacionalidad,
                fecha_nacimiento,
                False,  # visibilidad del div de la tabla
                tabla_docu.to_dict('records'),
                [{"name": dic_estados_columns[i], "id": i} for i in tabla_docu.columns],
                False,  # visibilidad del div de la tabla
                tabla_estados.to_dict('records'),
                [{"name": dic_estados_columns[i], "id": i} for i in tabla_estados.columns],
                ]

    else:
        tabla = freedb
        tram = ''
        docu_tipo = ''
        docu_numero = ''
        nacionalidad = ''
        fecha_nacimiento = ''
        return [tram,
                docu_tipo,
                docu_numero,
                nacionalidad,
                fecha_nacimiento,
                True,  # visibilidad del div de la tabla
                tabla.to_dict('records'),
                [{"name": i, "id": i} for i in tabla.columns],
                True,  # visibilidad del div de la tabla
                tabla.to_dict('records'),
                [{"name": dic_estados_columns[i], "id": i} for i in tabla.columns],
                ]


################################ CALL BACKS ##################################
################################# APP LOOP ###################################
if __name__ == '__main__':
    app.run_server(debug=True)
