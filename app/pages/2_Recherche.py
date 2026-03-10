import streamlit as st

from app.components.ui import (
    apply_custom_css,
    initialize_session_state,
    kpi_card,
    page_header,
    section_title,
    sidebar_logo,
)
from app.config import QUARTIERS, SEARCH_SORT_OPTIONS
from app.services.data_provider import get_listings
from app.services.metrics import filter_by_period

st.set_page_config(page_title="Recherche", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()

period = st.session_state.get("periode", "12 derniers mois")
listings_df = filter_by_period(get_listings(), "Date Ajout", period)
page_header("Recherche d'Annonces", export_df=listings_df, export_filename="recherche_annonces.csv")

period = st.session_state.get("periode", "12 derniers mois")
listings_df = filter_by_period(get_listings(), "Date Ajout", period)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    quartiers = st.multiselect("Quartiers", options=QUARTIERS, default=[], placeholder="Tous")
with col2:
    budget_max = st.number_input("Budget Max (€)", min_value=50000, max_value=2000000, value=600000, step=25000)
with col3:
    surf_min = st.number_input("Surface Min (m²)", min_value=10, value=30, step=5)
with col4:
    min_score = st.slider("Score minimum", 0, 100, int(st.session_state.get("min_opportunity_score", 70)))
with col5:
    tri_option = st.selectbox("Trier par", SEARCH_SORT_OPTIONS)

mask = (
    (listings_df["Prix (€)"] <= budget_max)
    & (listings_df["Surface (m²)"] >= surf_min)
    & (listings_df["Score Opportunité"] >= min_score)
)
if quartiers:
    mask &= listings_df["Quartier"].isin(quartiers)

filtered = listings_df[mask].copy()

if tri_option == "Prix croissant":
    filtered.sort_values("Prix (€)", ascending=True, inplace=True)
elif tri_option == "Surface décroissante":
    filtered.sort_values("Surface (m²)", ascending=False, inplace=True)
else:
    filtered.sort_values("Score Opportunité", ascending=False, inplace=True)

col_kpi_1, col_kpi_2, col_kpi_3 = st.columns(3)
with col_kpi_1:
    kpi_card("Résultats", len(filtered), None)
with col_kpi_2:
    median_price = int(filtered["Prix (€)"].median()) if not filtered.empty else 0
    kpi_card("Prix médian", f"{median_price:,.0f} €".replace(",", " "), None)
with col_kpi_3:
    avg_score = round(float(filtered["Score Opportunité"].mean()), 1) if not filtered.empty else 0.0
    kpi_card("Score moyen", f"{avg_score}/100", None)

rows_per_page = int(st.session_state.get("rows_per_page", 12))
page_count = max(1, (len(filtered) + rows_per_page - 1) // rows_per_page)
current_page = st.number_input("Page", min_value=1, max_value=page_count, value=1, step=1)

start = (current_page - 1) * rows_per_page
end = start + rows_per_page
page_slice = filtered.iloc[start:end]

section_title(f"Résultats {start + 1}-{min(end, len(filtered))} sur {len(filtered)}")

if page_slice.empty:
    st.info("Aucune annonce disponible avec ces critères.")
else:
    for _, row in page_slice.iterrows():
        prix_str = f"{row['Prix (€)']:,.0f} €".replace(",", " ")
        score = int(row["Score Opportunité"])
        badge_class = "badge-excellent" if score > 75 else "badge-good" if score > 50 else "badge-neutral"

        st.markdown(
            f"""
        <div style="background: white; border-radius: 12px; padding: 1.2rem; margin-bottom: 0.8rem; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 1.05rem; font-weight: 600; color: #0f172a; margin-bottom: 0.3rem;">
                    {row['Quartier']} • <span style="color: #0ea5e9;">{row['Surface (m²)']} m²</span> • {row['Pièces']} pièces
                </div>
                <div style="color: #64748b; font-size: 0.875rem; display: flex; align-items: center; gap: 0.75rem;">
                    <span>{row['Adresse']}</span>
                    <span class='badge {badge_class}'>Score: {score}/100</span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.35rem; font-weight: 700; color: #0f172a;">{prix_str}</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">{row['Prix/m²']} €/m²</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
