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
from app.services.data_provider import get_listings, get_sales, get_trends
from app.services.metrics import (
    build_market_summary,
    compute_trend_insights,
    filter_by_period,
    get_kpis,
)

st.set_page_config(page_title="Accueil - NidDouillet", layout="wide", initial_sidebar_state="expanded")

initialize_session_state()
apply_custom_css()
sidebar_logo()

period = st.session_state.get("periode", "12 derniers mois")
listings_df = filter_by_period(get_listings(), "Date Ajout", period)
page_header("Vue d'ensemble", export_df=listings_df, export_filename="accueil_annonces.csv")

# Le selecteur du header peut changer la periode: on relit la valeur puis recalcule.
period = st.session_state.get("periode", "12 derniers mois")
sales_df = filter_by_period(get_sales(), "Date", period)
listings_df = filter_by_period(get_listings(), "Date Ajout", period)
trends_df = get_trends()
kpis = get_kpis(period)

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Ventes Actées (DVF)", f"{kpis['ventes_dvf']}", kpis["trend_ventes"])
with col2:
    kpi_card("Annonces Actives", f"{kpis['annonces_actives']}", kpis["trend_annonces"])
with col3:
    kpi_card("Prix Médian / m²", f"{kpis['prix_median']} €", kpis["trend_prix"])
with col4:
    kpi_card("Délai de Vente", f"{kpis['delai_vente']} j", kpis["trend_delai"])

st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    section_title("Prix moyen par quartier (€/m²)")
    if sales_df.empty:
        st.info("Aucune donnée sur la période sélectionnée.")
    else:
        avg_price = (
            sales_df.groupby("Quartier")["Prix/m²"]
            .mean()
            .reset_index()
            .sort_values("Prix/m²", ascending=True)
        )
        fig = px.bar(
            avg_price,
            x="Prix/m²",
            y="Quartier",
            orientation="h",
            color_discrete_sequence=["#0ea5e9"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="",
            yaxis_title="",
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_chart2:
    section_title("Tendance globale")
    insight = compute_trend_insights(trends_df, "Toulon (Global)")
    st.caption(
        f"Dernier niveau: {insight['latest']} €/m² | Variation annuelle: {insight['yoy_pct']}% "
        f"({insight['delta_abs']} €/m²)"
    )
    fig2 = px.line(trends_df, x="Date", y="Toulon (Global)", color_discrete_sequence=["#10b981"])
    fig2.update_layout(
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
    top_opps = listings_df.sort_values("Score Opportunité", ascending=False).head(5).copy()
    if top_opps.empty:
        st.info("Aucune annonce disponible.")
    else:
        top_opps["Prix (€)"] = top_opps["Prix (€)"].apply(lambda x: f"{x:,.0f} €".replace(",", " "))
        top_opps["Prix/m²"] = top_opps["Prix/m²"].apply(lambda x: f"{x} €")
        st.dataframe(
            top_opps[["Quartier", "Surface (m²)", "Pièces", "Prix (€)", "Prix/m²", "Score Opportunité"]],
            use_container_width=True,
            hide_index=True,
        )

with col_bottom_2:
    section_title("Résumé marché par quartier")
    summary = build_market_summary(sales_df).head(7)
    if summary.empty:
        st.info("Aucune vente disponible.")
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)
