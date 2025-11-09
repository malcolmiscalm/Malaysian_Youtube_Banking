# pages/page3.py

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import pickle
import pandas as pd
import plotly.express as px
import random

# ----------------------------------------------------------
# Page registration (multipage)
# ----------------------------------------------------------
dash.register_page(
    __name__,
    path="/comments",
    name="Comment Insights",
    title="YouTube Comment Insights"
)

# ----------------------------------------------------------
# Data loading
# ----------------------------------------------------------
with open('./Data/COLLATE/COMMENT_sentiment_deduplicated.pkl', 'rb') as fp:
    COLLATE_COMMENT = pickle.load(fp)

# Ensure correct dtypes
COLLATE_COMMENT["sentiment"] = COLLATE_COMMENT["sentiment"].astype(str)
COLLATE_COMMENT["Youtube_Handle"] = COLLATE_COMMENT["Youtube_Handle"].astype(str)
COLLATE_COMMENT["Youtube_Video_IDs"] = COLLATE_COMMENT["Youtube_Video_IDs"].astype(str)

# ----------------------------------------------------------
# Layout
# ----------------------------------------------------------
layout = dbc.Container([
    html.H2("💬 YouTube Comment Insights", className="text-center mt-4 mb-4"),

    # Dropdown selector
    dbc.Row([
        dbc.Col([
            html.Label("Select a YouTube Channel Handle:"),
            dcc.Dropdown(
                id="handle-dropdown",
                options=[{"label": h, "value": h} for h in sorted(COLLATE_COMMENT["Youtube_Handle"].unique())],
                value=None,
                placeholder="Select a YouTube handle...",
                className="mb-4"
            )
        ], width=6)
    ]),

    # Sentiment distribution chart
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="sentiment-bar-chart", figure={})
        ], width=12)
    ]),

    html.Hr(),

    # Comment samples
    dbc.Row([
        dbc.Col([
            html.H4("🎯 Sample Comments by Sentiment"),
            html.Div(id="sample-comments")
        ])
    ])
], fluid=True)

# ----------------------------------------------------------
# Callback
# ----------------------------------------------------------
@callback(
    Output("sentiment-bar-chart", "figure"),
    Output("sample-comments", "children"),
    Input("handle-dropdown", "value")
)
def update_comment_insights(selected_handle):
    if not selected_handle:
        return {}, html.P("Please select a YouTube handle to view insights.", className="text-muted")

    # -------------------------------------
    # 🧮 Sentiment aggregation
    # -------------------------------------
    grouped = (
        COLLATE_COMMENT.groupby(["Youtube_Handle", "sentiment"])
        .agg(comment_count=pd.NamedAgg(column="sentiment", aggfunc="count"))
    )

    if selected_handle not in grouped.index.get_level_values(0):
        return {}, html.P(f"No comments found for {selected_handle}.", className="text-danger")

    filtered_data = grouped.loc[selected_handle].reset_index()

    # -------------------------------------
    # 📊 Bar chart
    # -------------------------------------
    fig = px.bar(
        filtered_data,
        x="sentiment",
        y="comment_count",
        color="sentiment",
        title=f"Sentiment Distribution for {selected_handle}",
        text_auto=True,
        color_discrete_map={
            "positive": "#A2CB1C",
            "neutral": "#F7C948",
            "negative": "#DF1111"
        }
    )

    fig.update_layout(
        plot_bgcolor="#30404D",
        paper_bgcolor="#30404D",
        font=dict(color="white"),
        height=400
    )

    # -------------------------------------
    # 💬 Sample comments by sentiment
    # -------------------------------------
    samples_section = []
    sentiments = ["positive", "neutral", "negative"]

    df_selected = COLLATE_COMMENT[COLLATE_COMMENT["Youtube_Handle"] == selected_handle]

    for s in sentiments:
        df_sent = df_selected[df_selected["sentiment"] == s]
        if df_sent.empty:
            continue

        sampled_rows = df_sent.sample(min(5, len(df_sent)), random_state=random.randint(0, 9999))

        # Create a nice list of cards for each sentiment
        sentiment_color = {"positive": "#A2CB1C", "neutral": "#F7C948", "negative": "#DF1111"}[s]
        cards = []

        for _, row in sampled_rows.iterrows():
            video_url = f"https://www.youtube.com/watch?v={row['Youtube_Video_IDs']}"

            cards.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(row.get("translated_text", "(No translation)"), className="card-title"),
                        html.P(f"🗣 Original: {row.get('full_comment', '')}", className="card-text"),
                        html.P(f"🌐 Detected Language: {row.get('detected_lang', 'unknown')}", className="text-muted small"),
                        html.A("🎥 Watch Video", href=video_url, target="_blank", className="btn btn-outline-light btn-sm mt-2")
                    ])
                ], className="mb-3", style={"backgroundColor": "#3E4A56", "borderLeft": f"5px solid {sentiment_color}"})
            )

        samples_section.append(
            html.Div([
                html.H4(f"{s.capitalize()} Comments", style={"color": sentiment_color}),
                html.Div(cards)
            ], className="mb-4")
        )

    return fig, samples_section
