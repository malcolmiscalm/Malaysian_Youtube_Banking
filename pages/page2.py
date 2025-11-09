# pages/page2.py

import dash
from dash import dcc, html, callback, Output, Input
import dash_bootstrap_components as dbc
import pickle
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as plt_io
import pandas as pd

# ----------------------------------------------------------
# Page registration (multipage)
# ----------------------------------------------------------
dash.register_page(
    __name__,
    path="/visuals",
    name="Likes & Views",
    title="YouTube Sentiment Visuals"
)

# ----------------------------------------------------------
# Data loading
# ----------------------------------------------------------
with open("./Data/COLLATE/MM.pkl", "rb") as fp:
    COLLATE_MM = pickle.load(fp)

# Ensure datetime type
COLLATE_MM["date"] = pd.to_datetime(COLLATE_MM["date"], errors="coerce")

# ----------------------------------------------------------
# Page layout
# ----------------------------------------------------------
layout = dbc.Container([
    html.H2("📊 YouTube Likes and Views Dashboard", className="text-center mt-4 mb-4"),

    # 🧭 Date picker + toggle row
    dbc.Row([
        dbc.Col([
            dcc.DatePickerRange(
                id="date-range-picker",
                display_format="YYYY-MM-DD",
                start_date=COLLATE_MM["date"].min().strftime("%Y-%m-%d"),
                end_date=COLLATE_MM["date"].max().strftime("%Y-%m-%d"),
                clearable=True,
                className="css_date_range_picker"
            )
        ], width=4),

        dbc.Col([
            dbc.RadioItems(
                id="sort-toggle",
                options=[
                    {"label": "Sort by Views", "value": "views"},
                    {"label": "Sort by Likes", "value": "likes"},
                ],
                value="views",
                inline=True,
                inputStyle={"margin-right": "5px"},
                labelStyle={"margin-right": "15px", "fontWeight": "bold"},
                className="mb-2"
            )
        ], width=4),

        dbc.Col([
            html.Div([
                html.H5("Number of Videos:", className="text-muted mb-1"),
                html.H3(id="dash-total-videos", className="fw-bold")
            ])
        ], width=4)
    ], className="mb-4 align-items-center"),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id="barline-fig", figure={})
        ], width=12)
    ])
], fluid=True)

# ----------------------------------------------------------
# Callback: update chart + KPIs
# ----------------------------------------------------------
@callback(
    Output("barline-fig", "figure"),
    Output("dash-total-videos", "children"),
    Input("date-range-picker", "start_date"),
    Input("date-range-picker", "end_date"),
    Input("sort-toggle", "value")
)
def update_barline_all(start_date, end_date, sort_by):
    # Filter by date
    df = COLLATE_MM[(COLLATE_MM["date"] >= start_date) & (COLLATE_MM["date"] <= end_date)]

    # Group and aggregate
    agg_df = (
        df.groupby("Youtube_Handle", as_index=False)
          .agg(
              Sum_Likes=("likes", "sum"),
              Sum_Views=("views", "sum"),
              Count_Videos=("Youtube_Handle", "count")
          )
    )

    # Sort by selected metric
    sort_col = "Sum_Views" if sort_by == "views" else "Sum_Likes"
    agg_df = agg_df.sort_values(sort_col, ascending=False)

    num_videos = int(agg_df["Count_Videos"].sum())

    # ------------------------------------
    # 🎨 Create Bar + Line figure
    # ------------------------------------
    red = "#DF1111"
    yellow = "#A2CB1C"
    dark = "#30404D"

    fig_barline = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar for views
    fig_barline.add_trace(
        go.Bar(
            x=agg_df["Youtube_Handle"],
            y=agg_df["Sum_Views"],
            name="Total Views",
            marker_color=red
        ),
        secondary_y=False
    )

    # Line for likes
    fig_barline.add_trace(
        go.Scatter(
            x=agg_df["Youtube_Handle"],
            y=agg_df["Sum_Likes"],
            name="Total Likes",
            mode="lines+markers",
            marker=dict(color=yellow, size=8)
        ),
        secondary_y=True
    )

    # ------------------------------------
    # Axes + Title
    # ------------------------------------
    fig_barline.update_xaxes(title_text="YouTube Channel Handle", tickangle=45)
    fig_barline.update_yaxes(
        title_text="Total Views",
        secondary_y=False,
        title_font_color=red,
        tickfont=dict(color=red)
    )
    fig_barline.update_yaxes(
        title_text="Total Likes",
        secondary_y=True,
        title_font_color=yellow,
        tickfont=dict(color=yellow)
    )

    title_suffix = "Views" if sort_by == "views" else "Likes"
    fig_barline.update_layout(
        title_text=f"Views vs Likes by YouTube Handle (Sorted by {title_suffix})",
        legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
        height=500,
        margin=dict(l=50, r=50, b=80, t=80),
        plot_bgcolor=dark,
        paper_bgcolor=dark,
        font=dict(color="white")
    )

    # Custom dark gridlines
    plt_io.templates["custom_dark"] = plt_io.templates["plotly_dark"]
    plt_io.templates["custom_dark"]["layout"]["paper_bgcolor"] = dark
    plt_io.templates["custom_dark"]["layout"]["plot_bgcolor"] = dark
    plt_io.templates["custom_dark"]["layout"]["yaxis"]["gridcolor"] = "#4f687d"
    plt_io.templates["custom_dark"]["layout"]["xaxis"]["gridcolor"] = "#4f687d"

    fig_barline.update_layout(template="custom_dark")

    return fig_barline, f"{num_videos:,}"
