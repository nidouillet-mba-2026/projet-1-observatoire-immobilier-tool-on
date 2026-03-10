import streamlit as st

from app.components.ui import (
    apply_custom_css,
    initialize_session_state,
    kpi_card,
    page_header,
    section_title,
    sidebar_logo,
)
from app.config import BASE_PRICES
from app.services.data_provider import get_listings
from app.services.metrics import filter_by_period

st.set_page_config(page_title="Sous-évalués", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()

period = st.session_state.get("periode", "12 derniers mois")
listings_df = filter_by_period(get_listings(), "Date Ajout", period)
page_header("Annonces Sous-évaluées", export_df=listings_df, export_filename="annonces_sous_evaluees.csv")

period = st.session_state.get("periode", "12 derniers mois")
listings_df = filter_by_period(get_listings(), "Date Ajout", period)
default_score = int(st.session_state.get("min_opportunity_score", 70))
min_score = st.slider("Filtre: Score d'opportunité minimum", 50, 100, default_score)

opps = listings_df[listings_df["Score Opportunité"] >= min_score].copy()

if opps.empty:
    st.info("Aucune annonce ne dépasse ce seuil.")
else:
    opps["Prix théorique/m²"] = opps["Quartier"].map(BASE_PRICES)
    opps["Sous-cote (%)"] = (
        ((opps["Prix théorique/m²"] - opps["Prix/m²"]) / opps["Prix théorique/m²"]).clip(lower=0) * 100
    ).round(1)

col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Annonces retenues", len(opps), None)
with col2:
    mean_discount = round(float(opps["Sous-cote (%)"].mean()), 1) if not opps.empty else 0.0
    kpi_card("Sous-cote moyenne", f"{mean_discount}%", None)
with col3:
    best_score = int(opps["Score Opportunité"].max()) if not opps.empty else 0
    kpi_card("Meilleur score", f"{best_score}/100", None)

section_title("Tableau détaillé")

if not opps.empty:
    st.dataframe(
        opps[[
            "ID",
            "Quartier",
            "Surface (m²)",
            "Prix (€)",
            "Prix/m²",
            "Prix théorique/m²",
            "Sous-cote (%)",
            "Score Opportunité",
        ]],
        column_config={
            "ID": st.column_config.TextColumn("Référence"),
            "Prix (€)": st.column_config.NumberColumn("Prix Vente", format="%d €"),
            "Prix/m²": st.column_config.NumberColumn("Prix/m²", format="%d €/m²"),
            "Prix théorique/m²": st.column_config.NumberColumn("Théorique", format="%d €/m²"),
            "Sous-cote (%)": st.column_config.ProgressColumn("Sous-cote", format="%.1f %%", min_value=0, max_value=40),
            "Score Opportunité": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
        },
        use_container_width=True,
        hide_index=True,
        height=520,
    )
