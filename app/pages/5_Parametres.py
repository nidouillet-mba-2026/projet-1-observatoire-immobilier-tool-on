import streamlit as st

from app.components.ui import apply_custom_css, initialize_session_state, page_header, sidebar_logo
from app.config import DEFAULT_SETTINGS
from app.services.data_provider import get_listings_metadata

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
    st.markdown("### Données & cache")
    if st.button("Rafraîchir les données", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache vidé. Les données seront rechargées au prochain calcul.")

    meta = get_listings_metadata()
    st.markdown("#### Diagnostic CSV annonces")
    st.write(f"Chemin utilisé: `{meta.get('csv_path') or 'Aucun'}`")
    st.write(f"Source active: `{meta.get('source')}`")
    st.write(f"Lignes chargées: `{meta.get('rows')}`")
    detected = meta.get("detected_columns") or []
    if detected:
        st.write(f"Colonnes détectées (CSV brut): `{', '.join(detected)}`")
    else:
        st.write(f"Colonnes standards actives: `{', '.join(meta.get('columns', []))}`")

    date_min = meta.get("date_min")
    date_max = meta.get("date_max")
    if date_min is not None and date_max is not None:
        st.write(f"Dates: `{date_min:%Y-%m-%d}` -> `{date_max:%Y-%m-%d}`")
    else:
        st.warning("Aucune date exploitable détectée dans les annonces.")
