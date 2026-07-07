# -------------------------------------------------------------------
# Dependencies
# -------------------------------------------------------------------
from dash import Dash, html, dcc, Input, Output, State, callback
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from pathlib import Path
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

from src.places import (
    load_places,
    get_place_options,
    merge_places_into_profiles,
    validate_places_against_profiles,
    get_map_df,
)

from src.profiles import (
    load_profiles,
    get_metric_options,
    get_scenario_options,
    get_default_scenario,
    filter_profile_comparison,
    build_profile_interpretation,
)

from assets.dashboard_theme import (
    ZONE_COLORS,
    ZONE_COLORS_MAP,
    SUMMER_COLOR,
    WINTER_COLOR,
    PAST_COLOR,
    FUTURE_COLOR,
    FUTURE2_COLOR,
)

app = Dash(__name__)
server = app.server

# -------------------------------------------------------------------
# Daten-Import und Zuweisung Variablen
# -------------------------------------------------------------------

# aktuelles App-Verzeichnis
PROJECT_ROOT = Path().resolve()

# Pfade definieren
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXPORT_DIR = PROJECT_ROOT / "exports"

# Import der Plots für Section C

monthly_warming_trends_df = pd.read_csv(
    PROCESSED_DIR / "monthly_warming_trends.csv"
)

heat_days_df = pd.read_csv(
    PROCESSED_DIR / "heat_days_by_zone.csv"
)

inversion_summer_df = pd.read_csv(
    PROCESSED_DIR / "inversion_summer_2003-08-08.csv"
)
inversion_winter_df = pd.read_csv(
    PROCESSED_DIR / "inversion_winter_2010-01-05.csv"
)

gdd_threshold_df = pd.read_csv(
    PROCESSED_DIR / "gdd_threshold_300.csv"
)

# Import der Daten für das Dashboard Section B
places_df = load_places()
profiles_df = load_profiles()

df = merge_places_into_profiles(profiles_df, places_df)

map_df = get_map_df(places_df)

metric_options = get_metric_options(df)

place_options = get_place_options(places_df)

scenario_options = get_scenario_options(df, "future")
default_scenario = get_default_scenario(df, "future")

# -------------------------------------------------------------------
# Settings für Dropdowns und Beschriftungen
# -------------------------------------------------------------------

# Settings für Karte Section B
default_place = place_options[0]["value"] if place_options else None
default_metric = "temperature_mean"

available_metrics = [opt["value"] for opt in metric_options]
if default_metric not in available_metrics and metric_options:
    default_metric = metric_options[0]["value"]

metric_labels = {
    "temperature_mean": "Durchschnittstemperatur",
    "hot_days_mean": "Anzahl Hitzetage pro Monat",
    "gdd": "Wärmesumme GDD"
}

scenario_labels = {
    "observed": "Beobachtet",
    "ref": "Referenz",
    "gwl1_5": "Erwärmung 1.5 °C",
    "gwl2_0": "Erwärmung 2.0 °C",
    "gwl2_5": "Erwärmung 2.5 °C",
    "gwl3_0": "Erwärmung 3.0 °C",
}

month_labels = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}

y_axis_labels = {
    "temperature_mean": "Grad Celsius",
    "hot_days_mean": "Tage",
    "gdd": "GDD",
}

#Settings für Map B und Section C
ZONE_COLORS_DE = {
    "Mittelland": ZONE_COLORS["Midlands"],
    "Voralpen": ZONE_COLORS["Pre-Alps"],
    "Alpen": ZONE_COLORS["Alps"],
}

month_map = {
    "Jan": "Jan",
    "Feb": "Feb",
    "Mar": "Mär",
    "Apr": "Apr",
    "May": "Mai",
    "Jun": "Jun",
    "Jul": "Jul",
    "Aug": "Aug",
    "Sep": "Sep",
    "Oct": "Okt",
    "Nov": "Nov",
    "Dec": "Dez",
}

SDG_13 = "#3F7E44"
SDG_15 = "#56C02B"
SDG_7 = "#FCC30B"
SDG_2 = "#DDA63A"
SDG_11 = "#FD9D24"

def apply_white_style(fig):

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#2d3a2d"),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        gridwidth=1,
        zeroline=False,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        gridwidth=1,
        zeroline=False,
    )

    return fig


# -------------------------------------------------------------------
# Funktionen für Plots und Elemente
# -------------------------------------------------------------------

# Plots Section C
def make_elevation_trend_plot(df):
    df = df.copy()
    df["month"] = df["month"].map(month_map)
    fig = go.Figure()

    zones = [
        ("Midlands", "Mittelland", ZONE_COLORS["Midlands"]),
        ("Pre-Alps", "Voralpen", ZONE_COLORS["Pre-Alps"]),
        ("Alps", "Alpen", ZONE_COLORS["Alps"]),
    ]

    for column_name, label, color in zones:
        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=df[column_name],
                mode="lines",
                name=label,
                line=dict(color=color, width=2.5),
                opacity=0.6,
            )
        )

    fig.add_hline(y=0, line=dict(width=0.8, color="grey"))

    fig.add_annotation(
        x="Apr",
        y=0.335,
        text="Stärkere Frühlingserwärmung<br>in den Voralpen",
        ax=-80,
        ay=-40,
        arrowhead=2,
        arrowwidth=1,
        arrowcolor="#888888",
        font=dict(size=11, color="#444444"),
        showarrow=True,
        align="left",
    )

    fig.add_annotation(
        x="Nov",
        y=0.295,
        text="Stärkere Wintererwärmung<br>im Mittelland",
        ax=-60,
        ay=-40,
        arrowhead=2,
        arrowwidth=1,
        arrowcolor="#888888",
        font=dict(size=11, color="#444444"),
        showarrow=False,
        align="left",
    )

    fig.add_annotation(
        x="Jul",
        y=0.395,
        text="Stärkere Sommererwärmung<br>im Mittelland",
        ax=-80,
        ay=0,
        showarrow=False,
        font=dict(size=11, color="#444444"),
        align="left",
    )

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.02,
        y=0.05,
        text="Werte zeigen Erwärmung pro Jahrzehnt, nicht absolute Temperatur.",
        showarrow=False,
        font=dict(size=11, color="#444444"),
        align="left",
    )

    fig.update_layout(
        title=None,
        height=440,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis_title=None,
        yaxis_title="Erwärmungstrend (°C pro Jahrzehnt)",
        dragmode=False,
        legend=dict(
            title="Höhenzone",
            x=0.995,
            y=0.995,
            xanchor="right",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.8)",
            borderwidth=0,
            font=dict(size=11),
            title_font=dict(size=12),
        )
    )

    fig.update_yaxes(
        range=[0.05, 0.42],
        gridcolor="rgba(0,0,0,0.12)",
        fixedrange=True,
    )

    fig.update_xaxes(
        categoryorder="array",
        title_standoff=22,
        fixedrange=True,
        categoryarray=[
            "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
            "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"
        ],
    )
    fig.update_traces(
        hovertemplate=
        "%{x}<br>"
        "%{y:.1f}"
        "<extra></extra>"
    )

    fig = apply_white_style(fig)
    return fig

def make_heat_days_plot(df):
    fig = go.Figure()

    zones = [
        ("Midlands", "Mittelland", ZONE_COLORS["Midlands"]),
        ("Pre-Alps", "Voralpen", ZONE_COLORS["Pre-Alps"]),
        ("Alps", "Alpen", ZONE_COLORS["Alps"]),
    ]

    for column_name, label, color in zones:
        fig.add_trace(
            go.Scatter(
                x=df["year"],
                y=df[column_name],
                mode="lines",
                name=label,
                line=dict(color=color, width=2.5),
            )
        )

    fig.add_annotation(
        x=2003,
        y=35,
        text="2003: extreme<br>europäische Hitzewelle",
        ax=-80,
        ay=-40,
        arrowhead=2,
        arrowwidth=1,
        arrowcolor="#888888",
        font=dict(size=11, color="#444444"),
        showarrow=True,
        align="left"
    )

    fig.update_layout(
        title=None,
        height=440,
        margin=dict(l=50, r=20, t=20, b=50),
        xaxis_title=None,
        yaxis_title="Anzahl Hitzetage",
        legend_title_text="Höhenzone",
        dragmode=False,
        legend=dict(
            x=0.995,
            y=0.995,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.8)",
            borderwidth=0,
            font=dict(size=11),
            title_font=dict(size=12),
        ),
    )

    fig.update_xaxes(
        gridcolor="rgba(0,0,0,0.08)",
        title_standoff=14,
        fixedrange=True,
    )

    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0.12)",
        title_standoff=14,
        fixedrange=True,
    )

    fig.update_traces(
        hovertemplate=
        "%{x}<br>"
        "%{y:.1f}"
        "<extra></extra>"
    )

    fig = apply_white_style(fig)
    return fig

def make_inversion_plot(summer_df, winter_df):
    fig = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.12,
    )

    fig.add_trace(
        go.Scatter(
            x=summer_df["elevation"],
            y=summer_df["temperature"],
            mode="markers",
            name="Sommer",
            marker=dict(color=SUMMER_COLOR, size=3, opacity=0.35),
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=winter_df["elevation"],
            y=winter_df["temperature"],
            mode="markers",
            name="Winter",
            marker=dict(color=WINTER_COLOR, size=3, opacity=0.55),
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    # Annotationen
    # Titel (beide Spalten gleich, nur xref unterscheidet sich)
    fig.add_annotation(
        x=0.5, y=1.06,
        xref="x domain", yref="paper",
        yanchor="bottom",  # Text wächst nach OBEN weg
        text="<b>Sommer: normaler<br>Temperaturgradient</b>",
        showarrow=False,
        font=dict(size=14, color="#2d3a2d"),
        align="center",
    )

    # Untertitel
    fig.add_annotation(
        x=0.5, y=1.06,
        xref="x domain", yref="paper",
        yanchor="top",  # Text wächst nach UNTEN weg
        text="<i>Typische Sommerbedingungen</i>",
        showarrow=False,
        font=dict(size=10, color="gray"),
        align="center",
    )

    # Titel (beide Spalten gleich, nur xref unterscheidet sich)
    fig.add_annotation(
        x=0.5, y=1.06,
        xref="x2 domain", yref="paper",
        yanchor="bottom",  # Text wächst nach OBEN weg
        text="<b>Winter:<br>Temperaturinversion</b>",
        showarrow=False,
        font=dict(size=14, color="#2d3a2d"),
        align="center",
    )

    # Untertitel
    fig.add_annotation(
        x=0.5, y=1.06,
        xref="x2 domain", yref="paper",
        yanchor="top",  # Text wächst nach UNTEN weg
        text="<i>Typische winterliche Inversionslage</i>",
        showarrow=False,
        font=dict(size=10, color="gray"),
        align="center",
    )


    fig.add_annotation(
        x=2000,
        y=15,
        text="Temperatur nimmt<br>mit der Höhe ab",
        ax=-90,
        ay=-30,
        arrowhead=2,
        arrowcolor="#888888",
        font=dict(size=11, color="#444444"),
        row=1,
        col=1,
    )

    fig.add_annotation(
        x=620,
        y=-9.5,
        text="Kalte Luft sammelt sich<br>im Mittelland",
        ax=380,
        ay=-11.6,  # Textposition (auch Datenkoordinaten!)
        axref="x2",
        ayref="y2",
        yanchor="top" if False else "auto",  # ay positiv = Text unterhalb der Pfeilspitze
        arrowhead=2,
        arrowwidth=1,
        arrowcolor="#888888",
        font=dict(size=11, color="#444444"),
        row=1,
        col=2,
        align="right",
    )

    fig.add_annotation(
        x=3100, y=-4.5,
        text="Temperatur sinkt<br>langsamer mit der Höhe",
        showarrow=False,
        xanchor="right",
        font=dict(size=11, color="#444444"),
        row=1, col=2,
        align="right",
    )
    #Beschriftungen Höhenzonen
    # Zonenlabels dichter an die Achse
    for x_pos, label in [(350, "Mittelland"), (1100, "Voralpen"), (2300, "Alpen")]:
        for col in [1, 2]:
            fig.add_annotation(
                x=x_pos,
                y=-0.07,  # vorher -0.12
                yanchor="top",
                xref=f"x{col if col > 1 else ''}",
                yref="paper",
                text=label,
                showarrow=False,
                font=dict(size=9, color="gray"),
            )


    fig.update_layout(
        title=None,
        height=550,
        margin=dict(l=50, r=20, t=120, b=100),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#2d3a2d"),
        dragmode=False,
    )

    fig.update_xaxes(
        range=[0, 3200],
        title_text="Höhe über Meer (m)",
        title_standoff=30,              # Abstand Ticks → Titel in px
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
        fixedrange=True,
    )

    fig.update_yaxes(
        title_text="Temperatur (°C)",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
        fixedrange=True,
    )

    fig.update_traces(
        hovertemplate=
        "%{x:.1f}<br>"
        "%{y:.1f}"
        "<extra></extra>"
    )

    fig = apply_white_style(fig)
    return fig

def make_gdd_threshold_plot(df):
    def day_number_to_date_label(day_num):
        date = datetime(2001, 1, 1) + timedelta(days=int(day_num) - 1)
        return date.strftime("%d %b")

    df = df.copy()
    df["date_label"] = df["day_of_year"].apply(day_number_to_date_label)
    df["date_label_rolling"] = df["day_of_year_rolling"].apply(day_number_to_date_label)

    fig = go.Figure()

    zones = [
        ("Midlands", "Mittelland", ZONE_COLORS["Midlands"], "solid"),
        ("Pre-Alps", "Voralpen", ZONE_COLORS["Pre-Alps"], "dash"),
        ("Alps", "Alpen", ZONE_COLORS["Alps"], "dashdot"),
    ]

    # Raw yearly values: light background context
    for column_name, label, color, dash in zones:
        zone_data = df[df["zone"] == column_name]

        fig.add_trace(
            go.Scatter(
                x=zone_data["year"],
                y=zone_data["day_of_year"],
                customdata=zone_data["date_label"],
                mode="lines",
                name=f"{label} jährlich",
                line=dict(color=color, width=1),
                opacity=0.25,
                showlegend=False,
                hovertemplate=
                "%{x}<br>"
                "Datum: %{customdata}<br>"
                "Tag im Jahr: %{y:.0f}"
                "<extra></extra>",
            )
        )

    # Rolling trend lines
    for column_name, label, color, dash in zones:
        zone_data = df[df["zone"] == column_name]

        fig.add_trace(
            go.Scatter(
                x=zone_data["year"],
                y=zone_data["day_of_year_rolling"],
                customdata=zone_data["date_label_rolling"],
                mode="lines",
                name=label,
                line=dict(
                    color=color,
                    width=3,
                    dash=dash,
                ),
                hovertemplate=
                "%{x}<br>"
                "Datum: %{customdata}<br>"
                "Tag im Jahr: %{y:.0f}"
                "<extra></extra>",
            )
        )

    fig.add_annotation(
        x=2010,
        y=153,
        text=(
            "Jede Linie zeigt, wann 300 GDD<br>"
            "im Frühling erreicht werden."
        ),
        ax=-130,
        ay=55,
        arrowhead=2,
        arrowwidth=1,
        arrowcolor="#888888",
        font=dict(size=11, color="#444444"),
        showarrow=True,
    )

    fig.add_annotation(
        x=1989,
        y=135,
        text="Frühere Wärme kann<br>Pflanzenwachstum vorverlegen",
        ax=-80,
        ay=-45,
        arrowhead=2,
        arrowwidth=1,
        arrowcolor="#888888",
        font=dict(size=11, color="#444444"),
        showarrow=True,
    )

    fig.add_annotation(
        x=1950,
        y=200,
        text="Höher im Diagramm bedeutet früher im Jahr.",
        showarrow=False,
        font=dict(size=11, color="#444444"),
        xanchor="left",
    )

    fig.update_layout(
        title=None,
        height=440,
        margin=dict(l=60, r=20, t=20, b=55),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_title=None,
        yaxis_title="Datum, an dem 300 GDD erreicht werden",
        legend_title_text="Höhenzone",
        dragmode=False,
        legend=dict(
            x=0.995,
            y=0.2,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.8)",
            borderwidth=0,
            font=dict(size=11),
            title_font=dict(size=12),
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
        title_standoff=14,
        fixedrange=True
    )

    fig.update_yaxes(
        autorange="reversed",
        tickmode="array",
        tickvals=[120, 150, 180, 210, 240],
        ticktext=["30 Apr", "30 Mai", "29 Jun", "29 Jul", "28 Aug"],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
        title_standoff=14,
        fixedrange=True
    )

    fig = apply_white_style(fig)
    return fig


# Funktionen für die Textelemente in Section C und E
def info_text_box(title, paragraphs, note=None):
    paragraph_elements = []

    for p in paragraphs:
        if isinstance(p, str):
            paragraph_elements.append(html.P(p))
        else:
            paragraph_elements.append(html.P(p))

    children = [
        html.P(title, className="content-title"),
        *paragraph_elements,
    ]

    if note:
        children.append(html.Div(note, className="small-note"))

    return html.Div(
        className="analysis-text-card",
        children=children,
    )


def mini_info_box(title, paragraphs):
    return html.Div(
        className="mini-info-card",
        children=[
            html.P(title, className="content-title"),
            *[html.P(p) for p in paragraphs],
        ],
    )

def sdg_relevance(midlands, prealps, alps):
    return html.Div(
        className="sdg-zone-rating",
        children=[
            html.P("Besonders relevant für", className="mini-title"),
            html.Div([html.Span("Mittelland"), html.Span(midlands)]),
            html.Div([html.Span("Voralpen"), html.Span(prealps)]),
            html.Div([html.Span("Alpen"), html.Span(alps)]),
        ],
    )


def sdg_card(img, title, text, rating, color):
    return html.Div(
        className="sdg-wide-card",
        style={"borderLeft": f"12px solid {color}"},
        children=[
            html.Div(
                className="sdg-logo-col",
                children=[
                    html.Img(src=img, className="sdg-icon"),
                    html.P(title, className="content-title"),
                ],
            ),
            html.Div(text, className="sdg-card-text"),
            rating,
        ],
    )

# Interaktive Karte Section B
def build_map_figure(map_df, selected_place_id=None):
    plot_df = map_df.copy()

    if plot_df.empty:
        fig = px.scatter_map()
        fig.update_layout(title="Keine Ortsdaten vorhanden")
        return fig

    place_type_labels = {
        "city": "Stadt",
        "tourism": "Tourismusort",
        "mountain": "Bergort",
    }

    plot_df["place_type_label"] = (
        plot_df["place_type"].map(place_type_labels).fillna(plot_df["place_type"])
        if "place_type" in plot_df.columns
        else ""
    )

    fig = px.scatter_map(
        plot_df,
        lat="lat",
        lon="lon",
        color="zone_label",
        color_discrete_map=ZONE_COLORS_DE,
        custom_data=["place_id", "place_name", "zone_label", "canton", "place_type_label", "elevation_m"],
        zoom=6.6,
        center={"lat": 46.8, "lon": 8.2},
        map_style="open-street-map",
    )

    fig.update_traces(
        marker={"size": 12},
        hovertemplate=(
            "<b>%{customdata[1]}</b><br>"
            "%{customdata[2]}<br>"
            "Kanton %{customdata[3]}<br>"
            "%{customdata[5]:.0f} m ü. M.<br>"
            "<extra></extra>"
        ),
    )

    if selected_place_id:
        selected_df = plot_df[plot_df["place_id"] == selected_place_id]

        if not selected_df.empty:
            fig.add_trace(
                px.scatter_map(
                    selected_df,
                    lat="lat",
                    lon="lon",
                    color="zone_label",
                    color_discrete_map=ZONE_COLORS_DE,
                    custom_data=["place_id", "place_name", "zone_label", "canton", "place_type_label", "elevation_m"],
                    zoom=6.6,
                    center={"lat": 46.8, "lon": 8.2},
                    map_style="open-street-map",
                ).data[0]
            )

            fig.data[-1].marker.size = 20
            fig.data[-1].hovertemplate = (
                "<b>%{customdata[1]}</b><br>"
                "%{customdata[2]}<br>"
                "Kanton %{customdata[3]}<br>"
                "%{customdata[5]:.0f} m ü. M.<br>"
                "<extra></extra>"
            )


    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=0, b=0),
        map=dict(
            style="open-street-map",
            center={"lat": 46.8, "lon": 8.2},
            zoom=6.6,
        ),
        showlegend=False,
    )

    return fig


# -------------------------------------------------------------------
# Layout und Text pro Section
# -------------------------------------------------------------------

app.layout = html.Div(
    className="page",
    children=[

        dcc.Store(id="store-selected-location"),
        dcc.Store(id="store-climate-data"),

        # SECTION A ---------------------------------------------------
        html.Section(
            id="section-a",
            className="section hero-section",
            children=[
                html.Div(
                    className="wide-image-wrap hero-image-wrap",
                    children=[
                        html.Img(
                            src="/assets/aniket-unsplash_small.jpg",
                            className="wide-image hero-image",
                        )
                    ]
                ),
                html.Div(
                    className="hero-layout",
                    children=[
                        html.Div(
                            className="hero-main",
                            children=[
                                html.H1("Das Klima vor deiner Haustüre"),
                                html.H2(
                                    "Wie verändert sich unser Alltag, unsere Umgebung und die regionale Lebensmittelproduktion?"
                                ),
                                html.P(
                                    "Klimaveränderungen machen sich in deinem Umfeld direkt bemerkbar: "
                                    "Hitzetage im Sommer, frühere Pflanzenentwicklung im Frühling, "
                                    "weniger Schnee im Winter, ein veränderter Wasserhaushalt und "
                                    "Extremwetter-Ereignisse stellen dich und die Natur vor neue Herausforderungen."
                                ),
                                html.P(
                                    "Landwirtschaft und Ökosysteme, Gesundheit und Energieversorgung sowie Ernährungssicherheit "
                                    "beschäftigen nicht nur Experten, sondern zunehmend auch Gemeinden, Firmen und dein Umfeld."
                                ),
                                html.P(
                                    "Herausforderungen in diesen Bereichen bewegen uns nicht überall gleich: Die Auswirkungen unterscheiden sich je nach "
                                    "Region und Höhenlage."
                                ),

                                html.Div(
                                    className="toc-card",
                                    children=[
                                        html.P("Was dich erwartet", className="content-title"),
                                        html.Div(
                                            className="toc-links",
                                            children=[
                                                html.A("Interaktive Schweizerkarte",
                                                       href="#section-b"),
                                                html.A("Klima Knowhow",
                                                       href="#section-c"),
                                                html.A("Einordnung Alltag und Lebensmittelproduktion",
                                                       href="#section-d"),
                                                html.A("UN-Nachhaltigkeitsziele im Kontext",
                                                       href="#section-e"),
                                            ],
                                        ),

                                    ],
                                ),
                                html.Div(
                                    "Starte mit einem Ort auf der Schweizerkarte oder lies zuerst die Story aus Effingen.",
                                    className="start-note section-lead section-lead-small",
                                ),


                            ],
                        ),
                    ],
                ),



                html.Div(
                    className="intro-block farm-story-card",
                    children=[
                        html.Div(
                            className="intro-text",
                            children=[
                                html.P("Landwirtschaftstory", className="kicker"),
                                html.P("Wenn das Heu knapp wird", className="article-title"),
                                html.P(
                                    "Wie Klimawandel auf einem kleinen Hof im Fricktal spürbar wird",
                                    className="subtitle",
                                ),
                                html.P(
                                    "Ein Beispiel aus Effingen im aargauischen Fricktal zeigt, wie sich "
                                    "solche Entwicklungen auf einen kleinen Landwirtschaftsbetrieb auswirken können. "
                                    "Eine globale Herausforderung wird zu einem lokalen und existenziellen Problem: "
                                    "Das Futter wird knapp."
                                ),


                                html.P("Die Lieferung", className="content-title"),
                                html.P(
                                    "Motorenlärm und ein dumpfes Rumpeln durchdringen die nachmittägliche Stille auf "
                                    "dem Hof von Mathias. Auf der angrenzenden Weide halten imposante "
                                    "schwarz-glänzende Angus-Rinder beim Kauen inne und blicken neugierig in "
                                    "Richtung des herannahenden Traktors. Mathias begrüsst den Kollegen erleichtert "
                                    "per Handschlag und die beiden machen sich sogleich daran, die Heuballen abzuladen."
                                ),
                                html.P("Was war passiert?", className="content-title"),
                                html.P(
                                    "Schon der Frühling war ausgesprochen trocken und heiss gewesen, der Sommer sowieso. "
                                    "Dies hatte dazu geführt, dass der Ertrag der Grasflächen viel zu tief ausgefallen "
                                    "war. Mathias musste befürchten, dass die Heuvorräte für seine Herde von rund 80 "
                                    "Tieren nicht über den Winter reichen würden. Über eine Futterbörse stiess er schliesslich "
                                    "auf das Angebot seines Berufskollegen aus der Region Luzern und liess mehrere Heuballen anliefern."
                                ),
                                html.P("Regionale Unterschiede", className="content-title"),
                                html.P(
                                    "Auf den ersten Blick erscheint das überraschend. Die Bewirtschaftung steiler "
                                    "Wiesen in den Voralpen und Alpen ist oft aufwendiger als im Mittelland. "
                                    "Und weshalb wächst in einer höher gelegenen Region genügend Futter, während es "
                                    "im Mittelland knapp wird?"
                                ),
                                html.P(
                                    "Die Klimaerwärmung macht sich in allen Höhenzonen bemerkbar. Je nach Jahreszeit "
                                    "und Höhenlage fallen die Veränderungen jedoch unterschiedlich stark aus. "
                                ),
                                html.P(
                                    "Auf der interaktiven Karte kannst du prüfen, ob ähnliche Muster auch an anderen "
                                    "Orten sichtbar werden."
                                ),
                            ],
                        ),

                        html.Div(
                            className="hero-video-card intro-video",
                            children=[
                                html.P("Hinter den Kulissen", className="kicker"),
                                html.P(
                                    "Landwirt Mathias vom Bollhof Effingen im Kurzporträt",
                                    className="content-title",
                                ),
                                html.P("Ein Video von 'Leimenhof on Tour'", className="video-caption"),
                                html.Iframe(
                                    src="https://www.youtube.com/embed/VwEjDaPDEXI",
                                    className="intro-video-frame",
                                    allow=(
                                        "accelerometer; autoplay; clipboard-write; encrypted-media; "
                                        "gyroscope; picture-in-picture; web-share"
                                    ),
                                ),
                                html.P(
                                    "Wir begleiten Mathias, seine Partnerin Marina sowie zwei Tiere ihrer "
                                    "Angus-Beef-Zucht an einen Stiermarkt.",
                                    className="video-caption",
                                ),
                            ],
                        ),
                    ],
                ),

            ],
        ),

        # SECTION B ---------------------------------------------------
        html.Section(
            id="section-b",
            className="section map-section",
            children=[
                html.Div(
                    className="content-block",
                    children=[
                        html.P("Interaktive Karte", className="kicker"),
                        html.H2("Erkunde deine Region"),
                        html.P(
                            "Wähle einen Ort und vergleiche, wie sich Temperatur, Hitzetage "
                            "oder Wärmesumme unter verschiedenen Erwärmungsszenarien verändern.",
                            className="subtitle",
                        ),
                    ]
                ),

                html.Div(
                    className="map-chart-grid",
                    children=[
                        html.Div(id="map-container"),
                        html.Div(id="chart-container"),
                    ],
                ),

                html.Div(
                    className="map-controls",
                    children=[
                        html.Div(
                            className="control-group",
                            children=[
                                html.Label("Ort auswählen"),
                                dcc.Dropdown(
                                    id="place-dropdown",
                                    options=place_options,
                                    value=default_place,
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-group",
                            children=[
                                html.Label("Metrik auswählen"),
                                dcc.Dropdown(
                                    id="metric-dropdown",
                                    options=metric_options,
                                    value="temperature_mean",
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-group",
                            children=[
                                html.Label("Szenario auswählen"),
                                dcc.Dropdown(
                                    id="scenario-dropdown",
                                    options=scenario_options,
                                    value=default_scenario,
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-group",
                            children=[
                                html.Label("Szenario 2 auswählen (optional)"),
                                dcc.Dropdown(
                                    id="scenario-2-dropdown",
                                    options=scenario_options,
                                    value=None,
                                    clearable=True,
                                    placeholder="Optional auswählen",
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="analysis-block",
                    children=[

                        # Links: Karte
                        html.Div(
                            className="analysis-visual-card",
                            children=[
                                dcc.Graph(
                                    id="places-map",
                                    figure=build_map_figure(map_df, default_place),
                                    config={"displayModeBar": False, "scrollZoom": True},
                                    style={"height": "550px"},
                                )
                            ],
                        ),

                        # Rechts: Plot und Text
                        html.Div(
                            className="analysis-visual-card",
                            children=[
                                dcc.Graph(
                                    id="monthly-profile-plot",
                                    config={"displayModeBar": False},
                                    style={"height": "380px"},
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    id="insight-row",
                    className="insight-row",
                    children=[
                        html.Div(
                            className="insight-card place-description-card",
                            children=[
                                html.P("Ortsprofil", className="content-title"),
                                html.Div(id="place-description"),
                            ],
                        ),
                        html.Div(
                            className="insight-card interpretation-card",
                            children=[
                                html.P("Was zeigt die Grafik?", className="content-title"),
                                html.Div(id="profile-interpretation"),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="map-help-card",
                    children=[
                        html.P("Begriffe kurz erklärt", className="content-title"),
                        html.Div(
                            className="map-help-grid",
                            children=[
                                html.Div(
                                    className="map-help-item",
                                    children=[
                                        html.Div("🌡", className="map-help-icon"),
                                        html.Div(
                                            children=[
                                                html.P("Hitzetage", className="mini-title"),
                                                html.P("Tage mit mindestens 30 °C Tagesmaximum"),
                                            ]
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="map-help-item",
                                    children=[
                                        html.Div("🌱", className="map-help-icon"),
                                        html.Div(
                                            children=[
                                                html.P("Wärmesumme GDD", className="mini-title"),
                                                html.P(
                                                    "Aufsummierte Wärme oberhalb von 5 °C, "
                                                    "ein Mass für die Pflanzenentwicklung"
                                                ),
                                            ]
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="map-help-item",
                                    children=[
                                        html.Div("⛰", className="map-help-icon"),
                                        html.Div(
                                            children=[
                                                html.P("Höhenzonen", className="mini-title"),
                                                html.P(
                                                    "Mittelland bis 700 m, Voralpen 700–1500 m, "
                                                    "Alpen ab 1500 m"
                                                ),
                                            ]
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="map-help-item",
                                    children=[
                                        html.Div("📈", className="map-help-icon"),
                                        html.Div(
                                            children=[
                                                html.P("Szenarien", className="mini-title"),
                                                html.P(
                                                    "Mögliche Klimazustände bei 1.5 °C, 2.0 °C, "
                                                    "2.5 °C oder 3.0 °C globaler Erwärmung"
                                                ),
                                            ]
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),


            ],
        ),

        # SECTION C ---------------------------------------------------
        html.Section(
            id="section-c",
            className="section story-section wave-right section-c",
            children=[
                html.Div(
                    className="wide-image-wrap",
                    children=[
                        html.Img(
                            src="/assets/ballmoos.jpg",
                            className="wide-image",
                        )
                    ]
                ),
                html.Div(
                    className="section-header",
                    children=[
                        html.P("Klima Knowhow", className="kicker"),
                        html.H2("Warum verändert sich die Schweiz nicht überall gleich?"),
                        html.P(
                            "Bevor wir einzelne Auswirkungen betrachten, lohnt sich ein Blick auf einige wichtige Zusammenhänge.",
                            className="subtitle",
                        ),
                    ],
                ),
                html.Div(
                    className="mini-info-grid",
                    children=[
                        mini_info_box(
                            "Klimaszenarien CH2025: Ein Blick in die Zukunft",
                            [
                                "Die Schweizer Klimaszenarien zeigen, wie sich das Klima bei verschiedenen globalen Erwärmungsniveaus verändern könnte. Im Dashboard werden vier Szenarien betrachtet: 1.5°C, 2°C, 2.5°C und 3°C globale Erwärmung gegenüber dem vorindustriellen Klima.",
                                "Die Szenarien beschreiben nicht ein bestimmtes Jahr, sondern den Klimazustand, der sich einstellt, sobald dieses Erwärmungsniveau erreicht wird. Die Abkürzung GWL steht für 'Global Warming Level' (globales Erwärmungsniveau).",
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="analysis-block",
                    children=[
                        info_text_box(
                            "Das Mittelland erwärmt sich im Winter und Sommer stärker",
                            [
                                "Diese Darstellung zeigt, wie sich die Erwärmung je nach Jahreszeit und Höhenzone unterscheidet.",
                                "Die Werte auf der y-Achse zeigen Erwärmungstrends in °C pro Jahrzehnt und keine absoluten Temperaturen.",
                                html.P([
                                    "Im Mittelland fällt die Erwärmung besonders im Winter und Sommer auf. "
                                    "Die stärkere Wintererwärmung wird mit dem Rückgang von Hochnebel und ",
                                    html.A("Inversionslagen", href="#inversions", className="text-link"),
                                    " in Verbindung gebracht.",
                                ]),
                                html.P([
                                    "In den Voralpen zeigt sich eine ausgeprägte Frühlingserwärmung, "
                                    "die zu einem früheren ",
                                    html.A("Vegetationsbeginn", href="#gdd300", className="text-link"),
                                    " führen kann.",
                                ]),
                                html.P([
                                    "Die starke Sommererwärmung im Mittelland steht zudem im Zusammenhang "
                                    "mit der Zunahme von ",
                                    html.A("Hitzetagen", href="#heatdays", className="text-link"),
                                    ".",
                                ]),
                            ],
                            note=(
                                "Die tiefsten Werte zeigen sich im Februar und September. Beide liegen in saisonalen Übergangsphasen, "
                                "in denen Wetterlagen häufig wechseln und keine Jahreszeit dominiert."
                            ),
                        ),
                        html.Div(
                            className="analysis-visual-card",
                            children=[
                                dcc.Graph(
                                    id="elevation-zones-plot",
                                    figure=make_elevation_trend_plot(monthly_warming_trends_df),
                                    config={"displayModeBar": False, "scrollZoom": False,},
                                    style={"width": "100%", "height": "440px"},
                                )
                            ],
                        ),
                    ],
                ),
                html.Div(
                    id="heatdays",
                    className="analysis-block",
                    children=[
                        info_text_box(
                            "Hitzetage nehmen vor allem in tiefen Lagen zu",
                            [
                                "Diese Darstellung zeigt die jährliche Anzahl Hitzetage in den verschiedenen Höhenzonen.",
                                "Ein Hitzetag ist ein Tag mit einer Höchsttemperatur von mindestens 30 °C.",
                                "Im Mittelland treten Hitzetage am häufigsten auf und haben seit den 1980er-Jahren deutlich zugenommen. In den Voralpen kommen sie seltener vor, zeigen aber ebenfalls einen steigenden Trend.",
                                "Die Alpen verzeichnen im betrachteten Zeitraum keine Hitzetage.",
                                "Der markante Ausschlag im Jahr 2003 steht für den aussergewöhnlichen Hitzesommer, der in vielen Teilen Europas 14 aufeinanderfolgende Hitzetage im August und weitere Wetter-Anomalien brachte.",
                            ],
                            note="Als weiteren interessanten Punkt sehen wir, dass es in den Alpen bislang noch keine Hitzetage im Sinne der Definition von mindestens 30 °C gab.",
                        ),
                        html.Div(
                            className="analysis-visual-card",
                            children=[
                                dcc.Graph(
                                    id="heat-days-plot",
                                    figure=make_heat_days_plot(heat_days_df),
                                    config={"displayModeBar": False, "scrollZoom": False,},
                                    style={"width": "100%", "height": "440px"},
                                )
                            ],
                        ),
                    ],
                ),
                html.Div(
                    id="inversions",
                    className="analysis-block",
                    children=[
                        info_text_box(
                            "Inversionslagen: Die Kälte bleibt im Tal",
                            [
                                "Normalerweise nimmt die Temperatur mit zunehmender Höhe ab. Die linke Grafik zeigt eine typische Situation an einem Sommertag.",
                                "An manchen Wintertagen ist es jedoch umgekehrt: Kalte Luft bleibt in den tieferen Lagen liegen, während in höheren Lagen wärmere Luft zu finden ist. Dies wird als Inversionslage bezeichnet.",
                                "Über der kalten Luft bildet sich häufig eine Schicht aus Hochnebel.",
                                "Im Schweizer Mittelland treten solche Nebellagen heute seltener auf als früher.",
                                "Dieser Rückgang wird mit der besonders starken Wintererwärmung im Mittelland in Verbindung gebracht, die bereits in Abbildung 2 sichtbar wurde."
                            ],

                            note=(
                                "Der Vergleich zeigt, wie sich Temperatur und Höhe normalerweise zueinander verhalten und wie sich dieses Muster bei einer Inversionslage verändert."
                            ),
                        ),
                        html.Div(
                            className="analysis-visual-card",
                            children=[
                                dcc.Graph(
                                    id="inversion-plot",
                                    figure=make_inversion_plot(inversion_summer_df, inversion_winter_df),
                                    config={"displayModeBar": False, "scrollZoom": False,},
                                    style={"width": "100%", "height": "550px"},
                                )
                            ],
                        ),

                    ],
                ),
                html.Div(
                    id="gdd300",
                    className="analysis-block",
                    children=[
                        info_text_box(
                            "Pflanzen erreichen Wärmeschwelle früher im Jahr",
                            [
                                "Growing Degree Days (GDD) beschreiben die aufsummierte Wärme oberhalb von 5 °C. Sie werden unter anderem in der Landwirtschaft und im Weinbau verwendet, um die Entwicklung von Pflanzen abzuschätzen.",
                                "Der Schwellenwert von 300 GDD steht für eine frühe Phase der Vegetationsperiode und eignet sich deshalb gut für den Vergleich zwischen den Höhenzonen.",
                                "In allen Höhenzonen wird dieser Wert heute früher im Jahr erreicht. Eine frühere Pflanzenentwicklung kann die Anfälligkeit junger Pflanzen gegenüber Spätfrost und Hagel erhöhen.",
                            ],
                            note="300 GDD bedeuten je nach Pflanzenart und Region ganz unterschiedliche Wachstumsphasen, z.B. Austrieb, Blüte oder eine Übergangsphase.",
                        ),
                        html.Div(
                            className="analysis-visual-card",
                            children=[
                                dcc.Graph(
                                    id="gdd-threshold-plot",
                                    figure=make_gdd_threshold_plot(gdd_threshold_df),
                                    config={"displayModeBar": False, "scrollZoom": False,},
                                    style={"width": "100%", "height": "440px"},
                                )
                            ],
                        ),
                    ],
                ),

                html.Div(
                    className="mini-info-grid",
                    children=[
                        mini_info_box(
                            "Frühere Schneeschmelze und ihre Folgen",
                            [
                                "Wenn der Schnee früher schmilzt, erwärmen sich die Böden bereits zu Beginn des Jahres. Ohne die helle Schneedecke wird mehr Sonnenenergie aufgenommen und weniger reflektiert.",
                                "Dadurch beginnt die Vegetationsperiode früher und Pflanzen treiben früher aus. Junge Pflanzen können dadurch häufiger von Spätfrost betroffen sein. Zudem steht im Sommer oft weniger Wasser aus der Schneeschmelze zur Verfügung.",
                            ],
                        ),
                    ],
                ),
            ],
        ),

        # SECTION D ---------------------------------------------------

        html.Section(
            id="section-d",
            className="section impact-section",
            children=[
                html.Div(
                    className="section-header",
                    children=[
                        html.P("Auswirkungen", className="kicker"),
                        html.H2("Von Klimadaten zu spürbaren Veränderungen"),
                        html.P(
                            "Die bisherigen Beispiele zeigen, dass sich die Klimaerwärmung je nach Höhenlage "
                            "unterschiedlich ausprägt.",
                            className="subtitle",
                        ),
                        html.P(
                            "Doch welche Folgen ergeben sich daraus für Menschen, Pflanzen und die "
                            "regionale Lebensmittelproduktion?"
                        ),
                    ],
                ),

                html.Div(
                    className="impact-card-grid",
                    children=[
                        html.Div(
                            className="impact-card",
                            children=[
                                html.Div(
                                    className="impact-card-layout",
                                    children=[
                                        html.Div(
                                            className="impact-card-media",
                                            children=[
                                                html.Img(
                                                    src="/assets/bern.jpg",
                                                    className="impact-card-image",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="impact-card-content",
                                            children=[
                                                html.P("Gesundheit und Energieversorgung", className="content-title"),
                                                html.P(
                                                    "Mehr Hitzetage belasten besonders ältere Menschen, Kinder und Personen mit Vorerkrankungen. "
                                                    "Gleichzeitig steigt an heissen Tagen der Kühlbedarf in Gebäuden, während Trockenperioden die "
                                                    "Wasserführung von Flüssen und damit die Wasserkraft und die Kühlung von Kernkraftwerken beeinflussen können."
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="impact-card",
                            children=[
                                html.Div(
                                    className="impact-card-layout",
                                    children=[
                                        html.Div(
                                            className="impact-card-media",
                                            children=[
                                                html.Img(
                                                    src="/assets/Applebloom.jpg",
                                                    className="impact-card-image",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="impact-card-content",
                                            children=[
                                                html.P("Garten und Pflanzen", className="content-title"),
                                                html.P(
                                                    "Frühere Wärme lässt Pflanzen früher austreiben und verlängert die Vegetationsperiode. "
                                                    "Das kann Chancen für neue Anbausorten eröffnen, erhöht aber auch das Risiko, dass junge Triebe durch späten Frost "
                                                    "geschädigt werden. In trockenen Sommern steigt zudem der Bewässerungsbedarf."
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="impact-card",
                            children=[
                                html.Div(
                                    className="impact-card-layout",
                                    children=[
                                        html.Div(
                                            className="impact-card-media",
                                            children=[
                                                html.Img(
                                                    src="/assets/Oberburg.jpg",
                                                    className="impact-card-image",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="impact-card-content",
                                            children=[
                                                html.P("Lebensmittelsicherheit und Landwirtschaft", className="content-title"),
                                                html.P(
                                                    "Für die Landwirtschaft zählt nicht nur die Jahresmitteltemperatur, sondern die Kombination aus "
                                                    "Wärme, Wasserverfügbarkeit und Extremereignissen. Sie beeinflusst, welche Kulturen geeignet sind, "
                                                    "wann geerntet wird und ob genügend Futter für Nutztiere wächst."
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),

                html.Div(
                    className="takeaway-card",
                    children=[
                        html.P("Was nehme ich mit?", className="content-title"),
                        html.P(
                            "Klimawandel wirkt nicht überall gleich. Entscheidend ist, wann und wo sich Temperatur, Wasserverfügbarkeit "
                            "und Extremereignisse verändern. Deshalb müssen Klimadaten regional, saisonal und nach Höhenlage betrachtet werden."
                        ),
                    ],
                ),
            ],
        ),
        # SECTION E ---------------------------------------------------
        html.Section(
            id="section-e",
            className="section sdg-section",
            children=[
                html.Div(
                    className="wide-image-wrap",
                    children=[
                        html.Img(
                            src="/assets/Nebelmeer.png",
                            className="wide-image",
                        )
                    ]
                ),
                html.Div(
                    className="section-header",
                    children=[
                        html.P("Globale Einordnung", className="kicker"),
                        html.H2("Die Nachhaltigkeitsziele der UNO im Kontext"),
                        html.P(
                            "Die 17 Sustainable Development Goals (SDGs) definieren messbare Ziele "
                            "im Bereich Klima, Ernährung, Energie und Gesundheit.",
                            className="subtitle",
                        ),
                        html.P(
                            "Die SDGs dienen vielen Ländern als Leitplanke bei der Umsetzung gesellschaftlich relevanter Ziele, "
                            "so auch in der Schweiz. Die Auswertungen der Klimadaten lassen sich in einen Zusammenhang mit den SDGs stellen und überraschenderweise "
                            "ist auch in den Nachhaltigkeitszielen eine Unterscheidung nach Höhenzonen erkennbar. "
                        ),
                        html.P(
                            "Wir nehmen 5 der 17 SDGs genauer unter die Lupe und analysieren, welche "
                            "Herausforderungen noch gemeistert werden müssen, aber auch welche Chancen sich eröffnen und welche Massnahmen angezeigt sind."
                        ),
                    ],
                ),
                html.Div(
                    className="sdg-wide-list",
                    children=[
                        sdg_card(
                        "/assets/sdg-13.png",
                        "SDG 13 – Klimaschutz",
                            html.Div([
                                html.P(
                                    "Warum schaffen wärmere Winter trotz mehr Sonnenstunden neue Herausforderungen?",
                                    className="sdg-lead"
                                ),
                                html.P(
                                    "Die Auswertungen zeigen, dass sich das Mittelland im Winter stärker erwärmt als die "
                                    "anderen Höhenzonen, vermutlich aufgrund des Rückgangs der Inversionslagen und "
                                    "damit des Hochnebels als schützende Schicht. Obwohl sich viele von uns "
                                    "über wärmere Temperaturen und mehr Sonnenlicht freuen, gibt es eine Kehrseite: Der "
                                    "Trockenstress für Pflanzen und Tiere nimmt zu. Ein bewusster Umgang "
                                    "mit Wasser wird deshalb auch für Privathaushalte immer wichtiger."
                                ),
                                html.P(
                                    "Gleichzeitig ist dieses Dashboard ein Beispiel dafür, wie wichtig verständlich aufbereitete "
                                    "Klimadaten für den allgemeinen Wissensaufbau sind, ein weiteres Thema des SDG 13, nebst "
                                    "der Förderung von durchdachten Anpassungen an den Klimawandel und seiner Folgen."
                                ),
                            ]),
                            sdg_relevance( "●●●", "●●", "●●"), #Wird durch eine Funktion erzeugt
                            SDG_13,
                        ),
                        sdg_card(
                            "/assets/sdg-15.png",
                            "SDG 15 – Leben an Land",
                            html.Div([
                                html.P(
                                    "Längere Vegetationsperioden: Welche Chancen und Risiken bergen sie?",
                                    className="sdg-lead"
                                ),
                                html.P(
                                    "In den Voralpen beginnt der Frühling früher als noch vor "
                                    "wenigen Jahren. Für uns Menschen bedeutet dies, dass Wanderwege "
                                    "und Alpenpässe früher zugänglich werden und sich der Ski-Tourismus hin zu Wander- und Bike-Aktivitäten verlagert."
                                ),
                                html.P(
                                    "Auch Pflanzen reagieren auf die zusätzlichen warmen Tage. Die Vegetationsperiode "
                                    "verlängert sich und eröffnet Chancen für neue Anbausorten oder höhere Erträge. "
                                    "Gleichzeitig steigt das Risiko, dass junge Triebe durch Spätfrost oder Hagel "
                                    "geschädigt werden und an Trockenstress leiden. "
                                ),
                                html.P(
                                    "Diese Veränderungen betreffen die Stabilität ganzer Ökosysteme und genau hier setzt das "
                                    "SDG 15 an: Es widmet sich dem Schutz von Böden, Lebensräumen und der Biodiversität "
                                    "Die Agrar- und Klimaforschung beschäftigt sich intensiv mit der "
                                    "Frage, wie die Landwirtschaft auf diese ökologischen Veränderungen reagieren kann."
                                ),
                            ]),
                            sdg_relevance("●", "●●●", "●●●"),
                            SDG_15,
                        ),
                        sdg_card(
                            "/assets/sdg-7.png",
                            "SDG 7 – Bezahlbare und saubere Energie",
                            html.Div([
                                html.P(
                                    "Warum verändern wärmere Sommer auch unsere Energieversorgung?",
                                    className="sdg-lead"
                                ),
                                html.P(
                                    "An heissen Sommertagen steigt der Bedarf an Kühlung von Innenräumen. Gleichzeitig "
                                    "nehmen Hitzetage im Mittelland deutlich zu. "
                                    "Was zunächst wie ein Komfortproblem erscheint, kann langfristig Auswirkungen auf "
                                    "die Energieversorgung haben."
                                ),
                                html.P(
                                    "Dabei spielt die Situation in den Bergen ebenfalls eine wichtige Rolle. Veränderungen der Schneemenge, der Gletscher "
                                    "und des Wasserhaushalts beeinflussen die Verfügbarkeit von Wasser für die Produktion "
                                    "von Wasserkraft und für die Kühlung von Kernkraftwerken. "
                                ),
                                html.P(
                                    "Das SDG 7 verfolgt das Ziel einer sicheren und nachhaltigen Energieversorgung auch unter "
                                    "veränderten klimatischen Bedingungen. Gleichzeitig passt die saisonale Verfügbarkeit von Sonnenenergie immer besser zu "
                                    "einem Energiebedarf, der sich von Heizleistungen im Winter in Richtung Kühlleistungen im "
                                    "Sommer verschiebt."
                                ),
                            ]),
                            sdg_relevance( "●●", "●●", "●●●"),
                            SDG_7,
                        ),
                        sdg_card(
                            "/assets/sdg-2.png",
                            "SDG 2 – Kein Hunger",
                            html.Div([
                                html.P(
                                    "Wie beeinflusst die Klimaerwärmung unsere Lebensmittelproduktion?",
                                    className="sdg-lead"
                                ),
                                html.P(
                                    "Obwohl die Schweiz aktuell nicht von Hunger betroffen ist, gewinnt die Widerstandsfähigkeit der "
                                    "Landwirtschaft gegenüber Trockenheit, Hitze und Extremereignissen an Bedeutung."
                                ),
                                html.P(
                                    "Landwirte müssen ihre Anbaumethoden laufend an veränderte klimatische Bedingungen "
                                    "anpassen. Massnahmen hängen stark von den lokalen Gegebenheiten "
                                    "und der Höhenlage ab. Neue Kulturen werden möglich, gleichzeitig verändern sich Wasserbedarf, "
                                    "Schädlingsdruck und Erntezeitpunkt. Eine sichere und nachhaltige Lebensmittelproduktion steht im Zentrum des SDG 2."
                                ),
                                html.P(
                                    "Agrarforschung und nachhaltige Landwirtschaft helfen dabei, die Versorgungssicherheit auch unter "
                                    "veränderten Klimabedingungen zu gewährleisten. "
                                ),
                            ]),
                            sdg_relevance( "●●", "●●●", "●●"),
                            SDG_2,
                        ),
                        sdg_card(
                            "/assets/sdg-11.png",
                            "SDG 11 – Nachhaltige Städte und Gemeinden",
                            html.Div([
                                html.P(
                                    "Wie reagieren Städte und Bergregionen auf steigende Temperaturen?",
                                    className="sdg-lead"
                                ),
                                html.P(
                                    "Die steigende Zahl von Hitzetagen im Mittelland stellen die Städte vor "
                                    "Herausforderungen und unterstreicht die Notwendigkeit von Massnahmen, "
                                    "insbesondere die Kühlung von städtischen Zentren. "
                                    "Die Anpassung von Städten und Siedlungsräumen an veränderte Umweltbedingungen "
                                    "gehört zu den Kernaufgaben des SDG 11."
                                ),
                                html.P(
                                    "Während eine verdichtete Siedlungsentwicklung in den Voralpen und Alpen dazu beiträgt, "
                                    "den Flächenverbrauch zu begrenzen und den Lebensraum in Bergregionen zu erhalten, "
                                    "zeigt sich in den Städten des Mittellands ein anderes Bild: Dort werden "
                                    "ausreichend Grün- und Freiflächen benötigt, um Hitzeinseln zu reduzieren und die "
                                    "Lebensqualität auch an heissen Sommertagen zu erhalten. "
                                ),
                            ]),
                            sdg_relevance( "●●●", "●", "●"),
                            SDG_11,
                        ),
                    ],
                ),

                html.Div(
                    className="sources",
                    children=[
                        html.P("Daten und Quellen", className="content-title"),
                        html.P(
                            "MeteoSchweiz Klimaszenarien CH2025 und weitere Inhalte, E-OBS HOM Klimadaten, eigene Auswertungen, "
                            "UNO Nachhaltigkeitsziele, Bundesamt für Statistik, Bundesamt für wirtschaftliche Landesversorgung BWL, "
                            "European Environment Agency EEA, SwissNAMES3D."
                        ),
                        html.P(
                            "Bild 1: Foto von Aniket Bhattacharya auf Unsplash. "
                            "Bild 2: SRF Meteo, Wetterbild des Monats April 2024, Ballmoos BE, Tobias Messerli. "
                            "Bild 3: SRF Meteo, Wetterbild des Monats Juli 2022, Bern, Tobias Messerli."
                            "Bild 4: Fotografie: Daniela Fischer, Apfelblüte in Buchs AG."
                            "Bild 5: SRF Meteo, Wetterbild des Monats Juni 2026, Oberburg BE, Tobias Messerli."
                            "Bild 6: Fotografie: Daniela Fischer, Blick von Crans-Montana Richtung Süden."
                        ),
                        html.P(
                            "Entwickelt im Rahmen des Klimadaten Open Learning Frühlingssemester 2026"
                        ),

                    ]
                ),
            ],
        ),
    ]
)


# -------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------

@callback(
    Output("place-dropdown", "value"),
    Input("places-map", "clickData"),
    prevent_initial_call=True,
)
def update_place_dropdown_from_map(click_data):
    if not click_data:
        raise PreventUpdate

    points = click_data.get("points", [])
    if not points:
        raise PreventUpdate

    custom_data = points[0].get("customdata")
    if not custom_data:
        raise PreventUpdate

    return custom_data[0]


@callback(
    Output("store-selected-location", "data"),
    Output("place-description", "children"),
    Input("place-dropdown", "value"),

)
def update_selected_location(place_id):

    if not place_id:
        return None, "", "insight-row only-interpretation"

    selected = places_df[places_df["place_id"] == place_id]

    if selected.empty:
        return None, "", "insight-row only-interpretation"

    row = selected.iloc[0]
    place_name = row["place_name"]
    description = row.get("short_description", "")

    if pd.isna(description) or not str(description).strip():
        description = (
            "Für diesen Ort ist kein individuelles Ortsprofil hinterlegt."
        )

    return (
        {
            "location_id": place_id,
            "name": place_name,
        },
        description,
    )


@callback(
    Output("places-map", "figure"),
    Input("store-selected-location", "data"),
)
def update_places_map(location):
    selected_place_id = location["location_id"] if location else default_place
    return build_map_figure(
        map_df,
        selected_place_id,
    )


# Callback für den Linienplot Section B
@callback(
    Output("monthly-profile-plot", "figure"),
    Output("profile-interpretation", "children"),
    Input("store-selected-location", "data"),
    Input("metric-dropdown", "value"),
    Input("scenario-dropdown", "value"),
    Input("scenario-2-dropdown", "value"),
)
def update_monthly_profile(location, metric, scenario, scenario_2):
    if not location or not metric or not scenario:
        fig = px.line()
        fig.update_layout(
            title="Bitte Ort, Metrik und Szenario auswählen",
            xaxis_title="Monat",
            yaxis_title="Wert",
            height=380,
        )
        return fig, ""

    if scenario_2 == scenario:
        scenario_2 = None

    place_id = location["location_id"]

    plot_df = filter_profile_comparison(
        df=df,
        place_id=place_id,
        metric=metric,
        future_scenario=scenario,
        future_scenario_2=scenario_2,
    )

    plot_df = plot_df.drop_duplicates(subset=["comparison_label", "month"])

    # Hitzetage von Anteil -> Anzahl Tage umrechnen
    if metric == "hot_days_mean":
        days_in_month = {
            1: 31,
            2: 28,
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30,
            12: 31,
        }

        plot_df = plot_df.copy()

        plot_df["value"] = (
                plot_df["value"]
                * plot_df["month"].map(days_in_month)
        )

    if plot_df.empty:
        fig = px.line()
        fig.update_layout(
            title="Keine Daten für diese Auswahl vorhanden",
            xaxis_title="Monat",
            yaxis_title="Wert",
            height=380,
        )
        return fig, "Für diese Auswahl sind keine Daten vorhanden."

    place_name = plot_df["place_name"].iloc[0]

    fig = px.line(
        plot_df,
        x="month",
        y="value",
        color="comparison_label",
        markers=True,
    )
    future_traces = [
        trace for trace in fig.data
        if "Zukunft" in trace.name
    ]

    for i, trace in enumerate(future_traces):
        color = FUTURE_COLOR if i == 0 else FUTURE2_COLOR
        trace.line.color = color
        trace.marker.color = color

    for trace in fig.data:
        if "Vergangenheit" in trace.name:
            trace.line.color = PAST_COLOR
            trace.marker.color = PAST_COLOR

    fig.update_layout(
        title=f"{place_name} – {metric_labels.get(metric, metric)}",
        xaxis_title=None,
        yaxis_title=y_axis_labels.get(metric, None),
        legend_title_text="Vergleich",
        margin=dict(l=40, r=20, t=80, b=20),
        height=380,
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=[month_labels[m] for m in range(1, 13)],
    )

    fig.update_traces(
        hovertemplate=
        "%{x}<br>"
        "%{y:.1f}"
        "<extra></extra>"
    )

    fig = apply_white_style(fig)
    interpretation = build_profile_interpretation(plot_df, metric)

    return fig, interpretation

if __name__ == "__main__":
    app.run(debug=True)
