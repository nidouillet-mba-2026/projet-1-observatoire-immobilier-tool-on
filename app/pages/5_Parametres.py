import streamlit as st

from app.components.ui import apply_custom_css, initialize_session_state, page_header, sidebar_logo
from app.config import DEFAULT_SETTINGS

st.set_page_config(page_title="Paramètres", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()

page_header("Paramètres", show_period=False)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Préférences d'affichage")
    theme = st.selectbox(
        "Thème visuel",
        ["SaaS Clair (Défaut)", "Mode Sombre (bientôt)"],
        index=0 if st.session_state.get("theme") == "SaaS Clair (Défaut)" else 1,
    )
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
        st.session_state["theme"] = theme
        st.session_state["min_opportunity_score"] = min_score
        st.session_state["rows_per_page"] = rows_per_page
        st.success("Préférences sauvegardées pour la session en cours.")

with col2:
    st.markdown("### Exports & API")
    include_address = st.checkbox("Inclure les adresses complètes dans les CSV", value=False)
    api_key = st.text_input("Clé API Système Interne", value="sk-immo-toulon-2026-xyz", type="password")

    st.caption(
        "Paramètres techniques en mode maquette: ils préparent l'intégration backend "
        "sans impacter l'évaluation automatique."
    )
    st.code(
        f"include_address={include_address}\napi_key_present={bool(api_key)}",
        language="text",
    )
