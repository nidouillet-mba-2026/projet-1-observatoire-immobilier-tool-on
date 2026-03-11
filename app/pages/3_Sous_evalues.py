import numpy as np
import pandas as pd
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
from app.services.listings import load_listings


def _score_quartier(df: pd.DataFrame) -> pd.Series:
    if df.empty or "prix_m2" not in df.columns:
        return pd.Series(0, index=df.index)
    median_by_quartier = df.groupby("quartier")["prix_m2"].median()

    def score(row):
        median = median_by_quartier.get(row["quartier"], np.nan)
        if pd.isna(median) or median == 0 or pd.isna(row["prix_m2"]):
            return 0
        value = (median - row["prix_m2"]) / median * 100
        return max(0, min(100, value))

    return df.apply(score, axis=1)


def _available_cols(df: pd.DataFrame) -> list[str]:
    desired = [
        "id_annonce",
        "quartier",
        "surface_m2",
        "pieces",
        "prix",
        "prix_m2",
        "score_opportunite",
        "url",
    ]
    return [col for col in desired if col in df.columns]


st.set_page_config(page_title="Sous-évalués - ToolOn", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Annonces Sous-évaluées")

listings = load_listings()
if listings.empty:
    st.warning("Aucune donnée disponible dans le CSV sélectionné.")
    st.stop()

page_header(export_df=listings, export_filename="annonces_sous_evaluees.csv")
default_score = int(st.session_state.get("min_opportunity_score", 70))
min_score = st.slider("Filtre: Score d'opportunité minimum", 0, 100, default_score)

listings["score_opportunite"] = _score_quartier(listings)
filtered = listings[listings["score_opportunite"] >= min_score].copy()

col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Annonces retenues", len(filtered), None)
with col2:
    mean_score = filtered["score_opportunite"].mean()
    kpi_card("Score moyen", f"{mean_score:.1f}/100" if not np.isnan(mean_score) else "N/A", None)
with col3:
    best_score = filtered["score_opportunite"].max()
    kpi_card("Meilleur score", f"{best_score:.1f}/100" if not np.isnan(best_score) else "N/A", None)

section_title("Tableau détaillé")
if filtered.empty:
    st.info("Aucun bien ne dépasse ce seuil.")
else:
    cols = _available_cols(filtered)
    table = filtered[cols].copy()
    table = table.rename(
        columns={
            "id_annonce": "Référence",
            "surface_m2": "Surface (m²)",
            "prix": "Prix (€)",
            "prix_m2": "Prix/m²",
            "score_opportunite": "Score Opportunité",
        }
    )
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Prix (€)": st.column_config.NumberColumn("Prix Vente", format="%d €"),
            "Prix/m²": st.column_config.NumberColumn("Prix/m²", format="%d €/m²"),
            "Score Opportunité": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "URL": st.column_config.LinkColumn("Annonce"),
        },
        height=560,
    )
