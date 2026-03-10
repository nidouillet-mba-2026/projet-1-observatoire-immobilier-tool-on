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
from app.services.data_provider import get_listings, get_sales, get_listings_metadata
from app.services.metrics import (
    build_listing_market_summary,
    build_listing_trend,
    compute_opportunity_scores,
    compute_trend_insights,
    filter_by_period,
    get_kpis,
)

st.set_page_config(page_title="Accueil - NidDouillet", layout="wide", initial_sidebar_state="expanded")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Vue d'ensemble")

period = st.session_state.get("periode", "12 derniers mois")
base_listings = get_listings()
listings_df = filter_by_period(base_listings, "date_ajout", period)
scored_listings = compute_opportunity_scores(listings_df, get_sales())

page_header(export_df=scored_listings, export_filename="accueil_annonces.csv")

period = st.session_state.get("periode", "12 derniers mois")
listings_df = filter_by_period(base_listings, "date_ajout", period)
scored_listings = compute_opportunity_scores(listings_df, get_sales())
trend_df = build_listing_trend(base_listings)
kpis = get_kpis(period)
meta = get_listings_metadata()

if meta.get("source") != "csv":
    st.info("Mode fallback actif: les annonces proviennent d'un jeu mock car le CSV réel est absent ou inexploitable.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Annonces actives", f"{kpis['annonces_actives']}", kpis["trend_annonces"])
with col2:
    kpi_card("Prix médian / m²", f"{kpis['prix_median']} €", kpis["trend_prix"])
with col3:
    avg_score = round(float(scored_listings["score_opportunite"].mean()), 1) if not scored_listings.empty else 0.0
    kpi_card("Score opportunité moyen", f"{avg_score}/100", None)
with col4:
    source_label = "CSV réel" if meta.get("source") == "csv" else "Fallback mock"
    kpi_card("Source annonces", source_label, None)

st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    section_title("Prix moyen par quartier (€/m²)")
    if scored_listings.empty or "quartier" not in scored_listings.columns:
        st.info("Aucune donnée exploitable pour le graphique par quartier.")
    else:
        avg_price = (
            scored_listings.groupby("quartier")["prix_m2"]
            .mean()
            .reset_index()
            .sort_values("prix_m2", ascending=True)
        )
        fig = px.bar(
            avg_price,
            x="prix_m2",
            y="quartier",
            orientation="h",
            color_discrete_sequence=["#0ea5e9"],
            labels={"prix_m2": "Prix/m²", "quartier": "Quartier"},
        )
        fig.update_layout(
            template=get_plotly_template(),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="",
            yaxis_title="",
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_chart2:
    section_title("Tendance prix annonces")
    if trend_df.empty:
        st.info("Pas de dates exploitables: tendances indisponibles.")
    else:
        insight = compute_trend_insights(trend_df, "Prix m² médian")
        st.caption(
            f"Dernier niveau: {insight['latest']} €/m² | Variation annuelle: {insight['yoy_pct']}% "
            f"({insight['delta_abs']} €/m²)"
        )
        fig2 = px.line(trend_df, x="Date", y="Prix m² médian", color_discrete_sequence=["#10b981"])
        fig2.update_layout(
            template=get_plotly_template(),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="",
            yaxis_title="",
            height=320,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

col_bottom_1, col_bottom_2 = st.columns([1.1, 1.2])
with col_bottom_1:
    section_title("Top 5 biens sous-évalués")
    top_opps = scored_listings.sort_values("score_opportunite", ascending=False).head(5).copy()
    if top_opps.empty:
        st.info("Aucune annonce disponible.")
    else:
        display = top_opps[["quartier", "surface_m2", "pieces", "prix_eur", "prix_m2", "score_opportunite"]].copy()
        display = display.rename(
            columns={
                "quartier": "Quartier",
                "surface_m2": "Surface (m²)",
                "pieces": "Pièces",
                "prix_eur": "Prix (€)",
                "prix_m2": "Prix/m²",
                "score_opportunite": "Score Opportunité",
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)

with col_bottom_2:
    section_title("Résumé marché par quartier")
    summary = build_listing_market_summary(scored_listings).head(8)
    if summary.empty:
        st.info("Aucune donnée quartier disponible.")
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)
