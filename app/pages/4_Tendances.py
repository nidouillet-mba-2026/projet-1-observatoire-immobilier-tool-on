import plotly.express as px
import streamlit as st

from app.components.ui import (
    apply_custom_css,
    get_plotly_template,
    initialize_session_state,
    kpi_card,
    page_header,
    section_title,
    sidebar_logo,
    topbar,
)
from app.services.data_provider import get_listings
from app.services.metrics import build_listing_trend, compute_trend_insights

st.set_page_config(page_title="Tendances", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Évolution & Tendances")

listings_df = get_listings().copy()
trend_df = build_listing_trend(listings_df)

page_header(export_df=trend_df, export_filename="tendances_listings.csv", show_period=False)

if trend_df.empty:
    st.info("Pas de dates exploitables dans le CSV: tendances indisponibles.")
else:
    months_back = st.slider(
        "Historique affiché (mois)",
        min_value=1,
        max_value=len(trend_df),
        value=min(24, len(trend_df)),
        step=1,
    )
    plot_df = trend_df.sort_values("Date").tail(months_back)

    insight = compute_trend_insights(plot_df, "Prix m² médian")

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Dernier prix/m²", f"{insight['latest']} €", None)
    with col2:
        kpi_card("Variation annuelle", f"{insight['yoy_pct']}%", None)
    with col3:
        latest_volume = int(plot_df["Volume"].iloc[-1]) if not plot_df.empty else 0
        kpi_card("Volume dernier mois", latest_volume, None)

    section_title("Courbe des prix médians mensuels")
    fig = px.line(
        plot_df,
        x="Date",
        y="Prix m² médian",
        labels={"Prix m² médian": "Prix moyen/m² (€)"},
    )
    fig.update_layout(
        template=get_plotly_template(),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        margin=dict(t=20, l=8, r=8, b=8),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#e2e8f0"),
        height=430,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    section_title("Volume d'annonces par mois")
    fig_vol = px.bar(plot_df, x="Date", y="Volume", color_discrete_sequence=["#0ea5e9"])
    fig_vol.update_layout(
        template=get_plotly_template(),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, l=8, r=8, b=8),
        height=260,
    )
    st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": False})
