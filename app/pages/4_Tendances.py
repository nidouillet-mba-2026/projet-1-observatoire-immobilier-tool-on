import pandas as pd
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
from app.services.listings import load_listings


def _build_trend(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "date_publication" not in df.columns or "prix_m2" not in df.columns:
        return pd.DataFrame()
    df["date_publication"] = pd.to_datetime(df["date_publication"], errors="coerce")
    df = df[df["date_publication"].notna()].copy()
    if df.empty:
        return pd.DataFrame()
    df["Date"] = df["date_publication"].dt.to_period("M").dt.to_timestamp()
    trend = (
        df.groupby("Date")["prix_m2"]
        .median()
        .reset_index()
        .rename(columns={"prix_m2": "Prix m² médian"})
        .sort_values("Date")
    )
    return trend


def _volume(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "date_publication" not in df.columns:
        return pd.DataFrame()
    df["date_publication"] = pd.to_datetime(df["date_publication"], errors="coerce")
    df = df[df["date_publication"].notna()].copy()
    if df.empty:
        return pd.DataFrame()
    df["Date"] = df["date_publication"].dt.to_period("M").dt.to_timestamp()
    volume = df.groupby("Date")["id_annonce"].count().reset_index().rename(columns={"id_annonce": "Volume"})
    return volume


def _format_currency(value):
    return f"{int(value):,}".replace(",", " ") + " €" if not pd.isna(value) else "N/A"


st.set_page_config(page_title="Tendances - ToolOn", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Évolution & Tendances")

listings = load_listings()
trend_df = _build_trend(listings)
volume_df = _volume(listings)
page_header(export_df=trend_df if not trend_df.empty else listings, export_filename="tendances_listings.csv", show_period=False)

if trend_df.empty:
    st.info("Pas de dates exploitables: tendances indisponibles.")
else:
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    latest = trend_df.iloc[-1]["Prix m² médian"]
    prev = trend_df.iloc[-13]["Prix m² médian"] if len(trend_df) > 12 else trend_df.iloc[0]["Prix m² médian"]
    pct = ((latest - prev) / prev * 100) if prev else 0
    kpi_card("Dernier prix/m²", _format_currency(latest), None)
    kpi_card("Variation annuelle", f"{pct:.1f}%", None)
    latest_volume = volume_df["Volume"].iloc[-1] if not volume_df.empty else 0
    kpi_card("Volume dernier mois", int(latest_volume), None)

    section_title("Courbe des prix médians mensuels")
    fig = px.line(
        trend_df,
        x="Date",
        y="Prix m² médian",
        template=get_plotly_template(),
        labels={"Date": "Date", "Prix m² médian": "Prix moyen/m² (€)"},
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    section_title("Volume d'annonces par mois")
    fig_vol = px.bar(
        volume_df,
        x="Date",
        y="Volume",
        template=get_plotly_template(),
        labels={"Volume": "Nb annonces"},
    )
    fig_vol.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": False})
