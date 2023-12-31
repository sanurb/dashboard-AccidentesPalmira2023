import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from datetime import datetime
import dash_bootstrap_components as dbc
from mappings import barrio_comuna_mapping, month_mapping

color_scale = px.colors.sequential.Plasma
month_colors = px.colors.qualitative.Plotly
day_colors = px.colors.qualitative.Pastel

# Leer el CSV y parsear la fecha
df_accidentes = pd.read_csv(
    "../accidentes_palmira.csv",
    parse_dates=["FECHA"],
    date_format='%d/%m/%Y %I:%M:%S %p'  # Usamos date_format en lugar de date_parser
)

# Convertimos la columna "FECHA" a datetime utilizando el formato adecuado
df_accidentes['FECHA'] = df_accidentes['FECHA'].apply(
    lambda x: datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p'))

# Crear columna 'MES' basada en la columna 'FECHA'
df_accidentes['MES'] = df_accidentes['FECHA'].dt.month

# Convertimos la columna "AÑO" solo si es de tipo string
if df_accidentes['AÑO'].dtype == 'object':
    df_accidentes['AÑO'] = df_accidentes['AÑO'].str.replace(
        ',', '').astype(int)

# Crear rangos de edad
bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
labels = [
    '0-10',
    '11-20',
    '21-30',
    '31-40',
    '41-50',
    '51-60',
    '61-70',
    '71-80',
    '81-90',
    '91-100']
df_accidentes['RANGO_EDAD'] = pd.cut(
    df_accidentes['EDAD'],
    bins=bins,
    labels=labels,
    right=False)

# Columna para las comunas
df_accidentes['COMUNA'] = df_accidentes['BARRIOS-CORREGIMIENTO- VIA'].map(
    barrio_comuna_mapping)
total_accidentes = len(df_accidentes)
comunas_count = df_accidentes['COMUNA'].value_counts().reset_index()
comunas_count.columns = ['COMUNA', 'CUENTA']
comunas_percent = (
    df_accidentes['COMUNA'].value_counts() /
    total_accidentes *
    100).reset_index()
comunas_percent.columns = ['COMUNA', 'PORCENTAJE']
comunas_percent = comunas_percent.merge(comunas_count, on="COMUNA")

# Gráfico de barras para hipótesis de accidentes
NmaxHipotesis = 15  # Número de hipótesis más frecuentes a mostrar
top_hipotesis = df_accidentes['HIPOTESIS'].value_counts().nlargest(
    NmaxHipotesis).index.tolist()
df_accidentes['HIPOTESIS_AJUSTADA'] = df_accidentes['HIPOTESIS'].where(
    df_accidentes['HIPOTESIS'].isin(top_hipotesis), 'Otras')
df_hipotesis_ajustada = df_accidentes['HIPOTESIS_AJUSTADA'].value_counts(
).reset_index()
df_hipotesis_ajustada.columns = ['HIPOTESIS_AJUSTADA', 'CUENTA']

MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZHNhbnR1cmJhbiIsImEiOiJjbGwxaWhpNGQwMGxkM3BtaWlidDlpOTdqIn0.Q2nMClAqoAHrwIktR-kcKA"
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)
df_accidentes['MES_NOMBRE'] = df_accidentes['MES'].map(month_mapping)

# Crear visualizaciones
fig_mes = px.histogram(
    df_accidentes,
    y="MES_NOMBRE",
    title="Accidentes por Mes (2022-2023)",
    color="MES_NOMBRE",
    color_discrete_map={month: color for month, color in zip(df_accidentes['MES_NOMBRE'].unique(), month_colors)},
    labels={'MES_NOMBRE': 'Mes', 'count': 'Número de Accidentes'})
fig_dia_semana = px.histogram(
    df_accidentes,
    y="DIA_SEMANA",
    color="DIA_SEMANA",
    color_discrete_sequence=day_colors,
    title="Accidentes por Día de la Semana (2022-2023)",
    labels={'DIA_SEMANA': 'Día de la Semana', 'count': 'Número de Accidentes'})
fig_barrio = px.histogram(
    df_accidentes,
    x="BARRIOS-CORREGIMIENTO- VIA",
    title="Accidentes por Barrio (2022-2023)")
fig_zona = px.histogram(
    df_accidentes,
    x="ZONA",
    title="Accidentes por Zona (2022-2023)")
fig_gravedad = px.pie(
    df_accidentes,
    names="GRAVEDAD",
    title="Gravedad de las lesiones")
fig_rango_edad = px.histogram(
    df_accidentes,
    x="RANGO_EDAD",
    color="GENERO",
    title="Distribución de Accidentes por Rango de Edad y Género")
fig_condicion_victima = px.histogram(
    df_accidentes,
    x="CONDICION DE LA VICTIMA",
    title="Condición de la Víctima")
fig_mapa = px.scatter_mapbox(df_accidentes,
                             lat="LAT",
                             lon="LONG",
                             hover_data=["BARRIOS-CORREGIMIENTO- VIA", "ZONA"],
                             zoom=12,
                             center={"lat": 3.5391, "lon": -76.3035},
                             mapbox_style="mapbox://styles/mapbox/streets-v11")

fig_hipotesis_ajustada = px.bar(
    df_hipotesis_ajustada,
    x='HIPOTESIS_AJUSTADA',
    y='CUENTA',
    title='Top {} Accidentes por Hipótesis'.format(NmaxHipotesis),
    labels={
        'HIPOTESIS_AJUSTADA': 'Hipótesis',
        'CUENTA': 'Cantidad de Accidentes'},
    color='CUENTA',
    color_continuous_scale=px.colors.sequential.Blues)
fig_comuna = px.pie(
    comunas_percent,
    names="COMUNA",
    values="PORCENTAJE",
    title="Porcentaje de Accidentes por Comuna (2022-2023)",
    labels={
        'COMUNA': 'Comuna',
        'PORCENTAJE': '% de Accidentes'},
    hole=0.3)

# Crear la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Dropdown para Seleccionar el Año
year_dropdown = dbc.Row(
    dbc.Col(
        dcc.Dropdown(
            id='year-dropdown',
            options=[
                {'label': '2022', 'value': 2022},
                {'label': '2023', 'value': 2023}
            ],
            value=2022,
            multi=False
        ),
        md=6, xs=12, className="mb-3"
    ),
    justify="center",
)

# Callback para actualizar gráficos


@app.callback(
    [Output('dia-plot', 'figure'),
     Output('mes-plot', 'figure'),
     Output('barrio-plot', 'figure'),
     Output('zona-plot', 'figure'),
     Output('gravedad-plot', 'figure'),
     Output('rango-edad-plot', 'figure'),
     Output('condicion-victima-plot', 'figure'),
     Output('comuna-plot', 'figure')],
    [Input('year-dropdown', 'value')]
)
def update_graphs(selected_year):
    filtered_df = df_accidentes[df_accidentes['AÑO'] == selected_year]

    fig_dia_updated = px.histogram(
        filtered_df,
        y="DIA_SEMANA",
        title=f"Accidentes por Día de la Semana ({selected_year})",
        color="DIA_SEMANA",
        color_discrete_sequence=day_colors,
        labels={'DIA_SEMANA': 'Día de la Semana', 'count': 'Número de Accidentes'}
    )
    grouped_by_month = filtered_df.groupby(filtered_df['FECHA'].dt.to_period("M")).size().reset_index(name='Count')
    grouped_by_month['FECHA'] = grouped_by_month['FECHA'].dt.to_timestamp()

    fig_mes_updated = px.line(
        grouped_by_month,
        x="FECHA",
        y="Count",
        title=f"Accidentes por Mes ({selected_year})",
        labels={'FECHA': 'Fecha'},
    )
    fig_barrio_updated = px.histogram(
        filtered_df,
        x="BARRIOS-CORREGIMIENTO- VIA",
        title=f"Accidentes por Barrio ({selected_year})")
    fig_zona_updated = px.histogram(
        filtered_df,
        x="ZONA",
        title=f"Accidentes por Zona ({selected_year})")
    fig_gravedad_updated = px.pie(
        filtered_df,
        names="GRAVEDAD",
        title=f"Gravedad de las lesiones ({selected_year})")
    fig_rango_edad_updated = px.histogram(
        filtered_df,
        x="RANGO_EDAD",
        color="GENERO",
        title=f"Distribución de Accidentes por Rango de Edad y Género ({selected_year})")
    fig_condicion_victima_updated = px.histogram(
        filtered_df,
        x="CONDICION DE LA VICTIMA",
        title=f"Condición de la Víctima ({selected_year})")
    comunas_percent_updated = (
        filtered_df['COMUNA'].value_counts() /
        len(filtered_df) *
        100).reset_index()
    comunas_percent_updated.columns = ['COMUNA', 'PORCENTAJE']
    fig_comuna_updated = px.pie(
        comunas_percent_updated,
        names="COMUNA",
        values="PORCENTAJE",
        title=f"Porcentaje de Accidentes por Comuna ({selected_year})",
        labels={
            'COMUNA': 'Comuna',
            'PORCENTAJE': '% de Accidentes'},
        hole=0.3)

    return fig_dia_updated, fig_mes_updated, fig_barrio_updated, fig_zona_updated, fig_gravedad_updated, fig_rango_edad_updated, fig_condicion_victima_updated, fig_comuna_updated


# Callback para el heatmap
@app.callback(
    Output('heatmap', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_heatmap(start_date, end_date):
    # Filtrar el dataframe según las fechas seleccionadas
    df_filtered = df_accidentes[(df_accidentes['FECHA'] >= start_date) & (
        df_accidentes['FECHA'] <= end_date)]

    # Agrupa por barrio y calcula la latitud y longitud promedio y cuenta los
    # accidentes
    df_grouped = df_filtered.groupby('BARRIOS-CORREGIMIENTO- VIA').agg(
        LAT=pd.NamedAgg(column='LAT', aggfunc='mean'),
        LONG=pd.NamedAgg(column='LONG', aggfunc='mean'),
        COUNT=pd.NamedAgg(column='BARRIOS-CORREGIMIENTO- VIA', aggfunc='count')
    ).reset_index()

    # Crear mapa de calor basado en la densidad por barrio
    fig = px.density_mapbox(df_grouped, lat='LAT', lon='LONG',
                            z='COUNT', radius=10,
                            center=dict(lat=3.53, lon=-76.3), zoom=12,
                            mapbox_style="outdoors",
                            title="Mapa de Calor de Accidentes por Barrio")

    fig.update_layout(mapbox_style="outdoors")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig


# Componente de selección de fecha para el heatmap
date_picker = dbc.Row(
    dbc.Col(
        [
            html.Label("Seleccione rango de fechas:"),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=df_accidentes['FECHA'].min(),
                end_date=df_accidentes['FECHA'].max(),
                display_format='DD/MM/YYYY'
            )
        ],
        md=6, xs=12, className="mb-3"
    ),
    justify="center",
)

# Definir el layout de la aplicación
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Accidentes de Tránsito en Palmira"), width=12, className="text-center mb-4")
    ]),
    dbc.Row(
        [
            dbc.Col(
                year_dropdown,
                md=6, xs=12, className="mb-3"
            ),
        ],
        justify="center",
    ),
    dbc.Row([
        dbc.Col(dcc.Graph(id='mes-plot', figure=fig_mes), md=6, xs=12),
        dbc.Col(dcc.Graph(id='dia-plot', figure=fig_dia_semana), md=6, xs=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='barrio-plot', figure=fig_barrio), md=12),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='zona-plot', figure=fig_zona), md=6, xs=12, className="mb-3"),
        dbc.Col(dcc.Graph(id='gravedad-plot', figure=fig_gravedad), md=6, xs=12, className="mb-3")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='rango-edad-plot', figure=fig_rango_edad), md=6, xs=12, className="mb-3"),
        dbc.Col(dcc.Graph(id='condicion-victima-plot', figure=fig_condicion_victima), md=6, xs=12, className="mb-3")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafica-hipotesis', figure=fig_hipotesis_ajustada), width=12, className="mb-3")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='comuna-plot', figure=fig_comuna), width=12, className="mb-3")
    ]),
    dbc.Row([
        dbc.Col(date_picker, md=6, xs=12, className="mb-3")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='heatmap'), width=12, className="mb-3")
    ]),
], fluid=True, className="p-4")

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
