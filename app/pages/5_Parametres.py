import pandas as pd
import streamlit as st
from typing import Optional

from app.components.ui import apply_custom_css, initialize_session_state, page_header, sidebar_logo, topbar
from app.config import DEFAULT_SETTINGS
from app.services.listings import get_listings_csv_path, load_listings


def _get_metadata(df: pd.DataFrame, path: Optional[str]) -> dict:
    if df.empty:
        return {
            "path": path or "-",
            "rows": 0,
            "cols": [],
            "quartiers": 0,
            "min_price": None,
            "max_price": None,
            "missing": {},
        }
    key_cols = ["prix", "surface_m2", "prix_m2", "type_bien"]
    missing = {col: f"{df[col].isna().mean() * 100:.1f}%" for col in key_cols if col in df.columns}
    return {
        "path": path or "-",
        "rows": len(df),
        "cols": list(df.columns),
        "quartiers": df["quartier"].nunique() if "quartier" in df.columns else 0,
        "min_price": df["prix"].min() if "prix" in df.columns else None,
        "max_price": df["prix"].max() if "prix" in df.columns else None,
        "missing": missing,
    }


st.set_page_config(page_title="Paramètres - ToolOn", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Paramètres")
page_header(show_period=False)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Préférences d'affichage")
    st.text_input("Thème visuel", value="Géré par le toggle en haut à droite", disabled=True)
    min_score = st.slider(
        "Seuil d'alerte sous-évaluation (score)",
        min_value=50,
        max_value=95,
        value=int(st.session_state.get("min_opportunity_score", DEFAULT_SETTINGS["min_opportunity_score"])),
    )
    rows_per_page = st.select_slider(
        "Résultats par page",
        options=[6, 9, 12, 15, 20],
        value=int(st.session_state.get("rows_per_page", DEFAULT_SETTINGS["rows_per_page"])),
    )
    if st.button("Sauvegarder les préférences", type="primary", use_container_width=True):
        st.session_state["min_opportunity_score"] = min_score
        st.session_state["rows_per_page"] = rows_per_page
        st.success("Préférences sauvegardées pour la session en cours.")

with col2:
    st.markdown("### Données & cache")
    if st.button("Rafraîchir les données", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache vidé. Les données seront rechargées au prochain calcul.")
    df = load_listings()
    meta = _get_metadata(df, get_listings_csv_path())
    st.markdown("#### Diagnostic CSV annonces")
    st.write(f"Chemin utilisé: `{meta['path']}`")
    st.write(f"Lignes chargées: `{meta['rows']}`")
    st.write(f"Colonnes détectées: `{', '.join(meta['cols'])}`")
    st.write(f"Quartiers uniques: `{meta['quartiers']}`")
    if meta["min_price"] is not None and meta["max_price"] is not None:
        st.write(
            f"Prix: `{int(meta['min_price']):,}` → `{int(meta['max_price']):,}`".replace(
                ",", " "
            )
        )
    if meta["missing"]:
        st.write("Colonne(s) manquante(s)/taux de valeurs manquantes:")
        for col, pct in meta["missing"].items():
            st.write(f"- `{col}`: {pct}")
