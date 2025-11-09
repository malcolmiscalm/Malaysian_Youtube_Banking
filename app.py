import dash
from dash import dcc, html, page_registry, page_container
import dash_bootstrap_components as dbc

import plotly.express as px     # pip install plotly==5.2.2
from plotly import graph_objs as go
from plotly.subplots import make_subplots
# this helps us get the theme settings
import plotly.io as plt_io

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.SPACELAB])
server = app.server

sidebar = dbc.Nav(
            [
                dbc.NavLink(
                    [
                        html.Div(children=page["name"], className="ms-2", style={'textAlign':'center'}),
                    ],
                    href=page["path"],
                    active="exact",
                )
                for page in dash.page_registry.values()
            ],
            vertical=True,
            pills=True,
            className="bg-light",
)

app.layout = dbc.Container([
    # The title is static
    dbc.Row([
        dbc.Col(html.Div("Malaysian_Youtube_Banking_Dashboard",
                         style={'fontSize':50, 'textAlign':'center'}))
    ]),

    html.Hr(),
    # Defining the width proportions of the sidebar and container
    dbc.Row(
        [
            dbc.Col(
                [
                    sidebar
                ], xs=4, sm=4, md=2, lg=2, xl=2, xxl=2),

            dbc.Col(
                [
                    dash.page_container
                ], xs=8, sm=8, md=10, lg=10, xl=10, xxl=10)
        ]
    )
], fluid=True)


if __name__ == "__main__":
    app.run(debug=False)
