import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from datetime import datetime
import dash_bootstrap_components as dbc


# Leer el CSV y parsear la fecha
df_accidentes = pd.read_csv(
    "../accidentes_palmira.csv",
    parse_dates=["FECHA"],
    date_format='%d/%m/%Y %I:%M:%S %p'  # Usamos date_format en lugar de date_parser
)

# Convertimos la columna "FECHA" a datetime utilizando el formato adecuado
df_accidentes['FECHA'] = df_accidentes['FECHA'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p'))

# Crear columna 'MES' basada en la columna 'FECHA'
df_accidentes['MES'] = df_accidentes['FECHA'].dt.month

# Convertimos la columna "AÑO" solo si es de tipo string
if df_accidentes['AÑO'].dtype == 'object':
    df_accidentes['AÑO'] = df_accidentes['AÑO'].str.replace(',', '').astype(int)

# Crear rangos de edad
bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']
df_accidentes['RANGO_EDAD'] = pd.cut(df_accidentes['EDAD'], bins=bins, labels=labels, right=False)

MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZHNhbnR1cmJhbiIsImEiOiJjbGwxaWhpNGQwMGxkM3BtaWlidDlpOTdqIn0.Q2nMClAqoAHrwIktR-kcKA"
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

# Crear visualizaciones
fig_mes = px.histogram(df_accidentes, x="MES", title="Accidentes por Mes (2022-2023)")
fig_dia_semana = px.histogram(df_accidentes, x="DIA_SEMANA", title="Accidentes por Día de la Semana (2022-2023)")
fig_barrio = px.histogram(df_accidentes, x="BARRIOS-CORREGIMIENTO- VIA", title="Accidentes por Barrio (2022-2023)")
fig_zona = px.histogram(df_accidentes, x="ZONA", title="Accidentes por Zona (2022-2023)")
fig_gravedad = px.pie(df_accidentes, names="GRAVEDAD", title="Gravedad de las lesiones")
fig_rango_edad = px.histogram(df_accidentes, x="RANGO_EDAD", color="GENERO", title="Distribución de Accidentes por Rango de Edad y Género")
fig_condicion_victima = px.histogram(df_accidentes, x="CONDICION DE LA VICTIMA", title="Condición de la Víctima")
fig_mapa = px.scatter_mapbox(df_accidentes,
                             lat="LAT",
                             lon="LONG",
                             hover_data=["BARRIOS-CORREGIMIENTO- VIA", "ZONA"],
                             zoom=12,
                             center={"lat": 3.5391, "lon": -76.3035},
                             mapbox_style="mapbox://styles/mapbox/streets-v11")


# Crear la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Dropdown para Seleccionar el Año
year_dropdown = dcc.Dropdown(
    id='year-dropdown',
    options=[
        {'label': '2022', 'value': 2022},
        {'label': '2023', 'value': 2023}
    ],
    value=2022,
    multi=False
)

# Callback para actualizar gráficos
@app.callback(
    [Output('dia-plot', 'figure'),
     Output('mes-plot', 'figure'),
     Output('barrio-plot', 'figure'),
     Output('zona-plot', 'figure'),
     Output('gravedad-plot', 'figure'),
     Output('rango-edad-plot', 'figure'),
     Output('condicion-victima-plot', 'figure')],
    [Input('year-dropdown', 'value')]
)
def update_graphs(selected_year):
    filtered_df = df_accidentes[df_accidentes['AÑO'] == selected_year]

    fig_dia_updated = px.histogram(filtered_df, x="DIA_SEMANA", title=f"Accidentes por Día de la Semana ({selected_year})")
    fig_mes_updated = px.histogram(filtered_df, x="MES", title=f"Accidentes por Mes ({selected_year})")
    fig_barrio_updated = px.histogram(filtered_df, x="BARRIOS-CORREGIMIENTO- VIA", title=f"Accidentes por Barrio ({selected_year})")
    fig_zona_updated = px.histogram(filtered_df, x="ZONA", title=f"Accidentes por Zona ({selected_year})")
    fig_gravedad_updated = px.pie(filtered_df, names="GRAVEDAD", title=f"Gravedad de las lesiones ({selected_year})")
    fig_rango_edad_updated = px.histogram(filtered_df, x="RANGO_EDAD", color="GENERO",
                                          title=f"Distribución de Accidentes por Rango de Edad y Género ({selected_year})")
    fig_condicion_victima_updated = px.histogram(filtered_df, x="CONDICION DE LA VICTIMA",
                                                 title=f"Condición de la Víctima ({selected_year})")

    return fig_dia_updated, fig_mes_updated, fig_barrio_updated, fig_zona_updated, fig_gravedad_updated, fig_rango_edad_updated, fig_condicion_victima_updated


# Definir el layout de la aplicación
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Accidentes de Tránsito en Palmira"), width={'size': 12})
    ]),
    dbc.Row(
        [
            dbc.Label("Selecciona un Año:", html_for="year-dropdown", width=2),
            dbc.Col(
                year_dropdown,
                width=10
            ),
        ],
        className="mb-3",
    ),
    dbc.Row([
        dbc.Col(dcc.Graph(id='dia-plot', figure=fig_dia_semana), width=4),
        dbc.Col(dcc.Graph(id='mes-plot', figure=fig_mes), width=4),
        dbc.Col(dcc.Graph(id='barrio-plot', figure=fig_barrio), width=4)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='zona-plot', figure=fig_zona), width=6),
        dbc.Col(dcc.Graph(id='gravedad-plot', figure=fig_gravedad), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='rango-edad-plot', figure=fig_rango_edad), width=6),
        dbc.Col(dcc.Graph(id='condicion-victima-plot', figure=fig_condicion_victima), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_mapa), width=12)
    ])
], fluid=True)

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
