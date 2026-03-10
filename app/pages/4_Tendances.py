import plotly.express as px
import streamlit as st

from app.components.ui import (
    apply_custom_css,
    initialize_session_state,
    kpi_card,
    page_header,
    section_title,
    sidebar_logo,
)
from app.config import QUARTIERS
from app.services.data_provider import get_trends
from app.services.metrics import compute_trend_insights

st.set_page_config(page_title="Tendances", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()

trends_df = get_trends().copy()
page_header("Évolution & Tendances", export_df=trends_df, export_filename="tendances_toulon.csv", show_period=False)

options = ["Toulon (Global)"] + QUARTIERS
selected = st.multiselect(
    "Lignes à afficher",
    options=options,
    default=["Toulon (Global)", "Mourillon", "Pont du Las"],
)

months_back = st.slider("Historique affiché (mois)", min_value=12, max_value=60, value=36, step=6)
plot_df = trends_df.sort_values("Date").tail(months_back)

if not selected:
    st.warning("Sélectionnez au moins une ligne de tendance.")
else:
    col1, col2, col3 = st.columns(3)
    main_series = selected[0]
    insight = compute_trend_insights(plot_df, main_series)
    with col1:
        kpi_card("Zone de référence", main_series, None)
    with col2:
        kpi_card("Dernier prix/m²", f"{insight['latest']} €", None)
    with col3:
        kpi_card("Variation annuelle", f"{insight['yoy_pct']}%", None)

    section_title("Courbes de prix")
    fig = px.line(
        plot_df,
        x="Date",
        y=selected,
        labels={"value": "Prix moyen/m² (€)", "variable": "Zone"},
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        margin=dict(t=20, l=8, r=8, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0, title_text=""),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#e2e8f0"),
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
