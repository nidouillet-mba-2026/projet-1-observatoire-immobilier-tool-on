import plotly.express as px
import streamlit as st

from app.components.ui import (
    apply_custom_css,
    get_plotly_template,
    initialize_session_state,
    page_header,
    section_title,
    sidebar_logo,
    topbar,
)
from app.config import QUARTIERS
from app.services.data_provider import get_sales
from app.services.metrics import build_market_summary, filter_by_period

st.set_page_config(page_title="Marché - NidDouillet", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Analyse du Marché (DVF)")

period = st.session_state.get("periode", "12 derniers mois")
sales_df = filter_by_period(get_sales(), "Date", period)
page_header(export_df=sales_df, export_filename="marche_dvf.csv")

period = st.session_state.get("periode", "12 derniers mois")
sales_df = filter_by_period(get_sales(), "Date", period)

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        quartiers = st.multiselect("Quartiers", options=QUARTIERS, default=QUARTIERS)
    with c2:
        min_surface, max_surface = st.slider("Surface (m²)", 15, 200, (30, 120))
    with c3:
        price_range = st.slider("Prix/m²", 1200, 8000, (1800, 6000), step=100)

filtered_sales = sales_df[
    (sales_df["Quartier"].isin(quartiers))
    & (sales_df["Surface (m²)"].between(min_surface, max_surface))
    & (sales_df["Prix/m²"].between(price_range[0], price_range[1]))
]

section_title(f"{len(filtered_sales)} transaction(s) filtrée(s)")

if filtered_sales.empty:
    st.info("Aucune donnée pour ces filtres.")
else:
    tab1, tab2, tab3 = st.tabs(["Distribution", "Volume mensuel", "Tableau quartier"])

    with tab1:
        fig = px.box(
            filtered_sales,
            x="Quartier",
            y="Prix/m²",
            color="Quartier",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_layout(
            template=get_plotly_template(),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tab2:
        monthly = filtered_sales.copy()
        monthly["Mois"] = monthly["Date"].dt.to_period("M").astype(str)
        monthly_volume = monthly.groupby("Mois", as_index=False).size().rename(columns={"size": "Transactions"})
        fig_month = px.bar(monthly_volume, x="Mois", y="Transactions", color_discrete_sequence=["#0ea5e9"])
        fig_month.update_layout(
            template=get_plotly_template(),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="",
            height=420,
        )
        st.plotly_chart(fig_month, use_container_width=True, config={"displayModeBar": False})

    with tab3:
        recap = build_market_summary(filtered_sales)
        st.dataframe(recap, use_container_width=True, hide_index=True)
