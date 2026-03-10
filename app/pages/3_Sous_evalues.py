import streamlit as st

from app.components.ui import (
    apply_custom_css,
    initialize_session_state,
    kpi_card,
    page_header,
    section_title,
    sidebar_logo,
    topbar,
)
from app.services.data_provider import get_listings, get_sales
from app.services.metrics import compute_opportunity_scores, filter_by_period

st.set_page_config(page_title="Sous-évalués", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Annonces Sous-évaluées")

period = st.session_state.get("periode", "12 derniers mois")
base_listings = get_listings()
listings_df = filter_by_period(base_listings, "date_ajout", period)
scored_df = compute_opportunity_scores(listings_df, get_sales())

page_header(export_df=scored_df, export_filename="annonces_sous_evaluees.csv")

period = st.session_state.get("periode", "12 derniers mois")
listings_df = filter_by_period(base_listings, "date_ajout", period)
scored_df = compute_opportunity_scores(listings_df, get_sales())

default_score = int(st.session_state.get("min_opportunity_score", 70))
min_score = st.slider("Filtre: Score d'opportunité minimum", 0, 100, default_score)

opps = scored_df[scored_df["score_opportunite"] >= min_score].copy()

col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Annonces retenues", len(opps), None)
with col2:
    mean_discount = round(float(opps["score_opportunite"].mean()), 1) if not opps.empty else 0.0
    kpi_card("Score moyen", f"{mean_discount}/100", None)
with col3:
    best_score = int(opps["score_opportunite"].max()) if not opps.empty else 0
    kpi_card("Meilleur score", f"{best_score}/100", None)

section_title("Tableau détaillé")

if opps.empty:
    st.info("Aucune annonce ne dépasse ce seuil.")
else:
    display = opps[[
        "id",
        "quartier",
        "surface_m2",
        "pieces",
        "prix_eur",
        "prix_m2",
        "prix_reference_m2",
        "score_opportunite",
        "url",
    ]].copy()

    display = display.rename(
        columns={
            "id": "Référence",
            "quartier": "Quartier",
            "surface_m2": "Surface (m²)",
            "pieces": "Pièces",
            "prix_eur": "Prix (€)",
            "prix_m2": "Prix/m²",
            "prix_reference_m2": "Réf quartier €/m²",
            "score_opportunite": "Score Opportunité",
            "url": "URL",
        }
    )

    st.dataframe(
        display,
        column_config={
            "Prix (€)": st.column_config.NumberColumn("Prix Vente", format="%d €"),
            "Prix/m²": st.column_config.NumberColumn("Prix/m²", format="%d €/m²"),
            "Réf quartier €/m²": st.column_config.NumberColumn("Référence", format="%d €/m²"),
            "Score Opportunité": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "URL": st.column_config.LinkColumn("Annonce"),
        },
        use_container_width=True,
        hide_index=True,
        height=560,
    )
