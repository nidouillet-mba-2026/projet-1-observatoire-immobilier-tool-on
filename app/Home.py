import plotly.express as px
import pandas as pd
import streamlit as st
from pathlib import Path

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

CSV_CANDIDATES = [
    Path("data/Annonce_immo.csv"),
    Path("Annonce_immo.csv"),
]


def _load_annonces_csv() -> pd.DataFrame:
    for candidate in CSV_CANDIDATES:
        if not candidate.exists():
            continue
        for encoding in ("utf-8", "latin-1"):
            try:
                df = pd.read_csv(candidate, sep=";", encoding=encoding, on_bad_lines="skip")
                df["source_file"] = str(candidate)
                return df
            except Exception:
                continue
    return pd.DataFrame()


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _fmt_currency(value, suffix=" €"):
    if pd.isna(value):
        return "N/A"
    return f"{int(round(value)):,}".replace(",", " ") + suffix


def _fmt_price_m2(value):
    if pd.isna(value):
        return "N/A"
    return f"{int(round(value)):,}".replace(",", " ") + " €/m²"


st.set_page_config(page_title="Accueil - ToolOn", layout="wide", initial_sidebar_state="expanded")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Vue d'ensemble")

raw_df = _load_annonces_csv()
full_count = len(raw_df)

if not raw_df.empty:
    df = raw_df.copy()
    for col in ("prix", "surface_m2", "prix_m2"):
        if col in df.columns:
            df[col] = _to_numeric(df[col])
    if "prix_m2" in df.columns:
        inferred = df["prix_m2"].isna() & df["prix"].gt(0) & df["surface_m2"].gt(0)
        df.loc[inferred, "prix_m2"] = df.loc[inferred, "prix"] / df.loc[inferred, "surface_m2"]
    if "type_bien" in df.columns:
        df["type_bien"] = df["type_bien"].astype(str).str.lower().str.strip()
    mask = pd.Series(True, index=df.index)
    if "prix" in df.columns:
        mask &= df["prix"] > 0
    if "surface_m2" in df.columns:
        mask &= df["surface_m2"] > 0
    df = df[mask].copy()
else:
    df = pd.DataFrame()

ignored_count = full_count - len(df)

def _safe_count(cond):
    return int(cond.sum()) if cond is not None else 0

nb_logements = len(df)
prix_moyen = df["prix"].mean() if "prix" in df.columns and not df["prix"].dropna().empty else None
prix_m2_median = df["prix_m2"].median() if "prix_m2" in df.columns and not df["prix_m2"].dropna().empty else None
prix_m2_moyen = df["prix_m2"].mean() if "prix_m2" in df.columns and not df["prix_m2"].dropna().empty else None
maisons_cond = df["type_bien"].str.contains("maison", na=False) if "type_bien" in df.columns else None
apparts_cond = df["type_bien"].str.contains("appart", na=False) if "type_bien" in df.columns else None
nb_maisons = _safe_count(maisons_cond)
nb_apparts = _safe_count(apparts_cond)

page_header(export_df=df, export_filename="annonces_real.csv")

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Nb de logements", f"{nb_logements:,}".replace(",", " "))
with col2:
    kpi_card("Prix moyen", _fmt_currency(prix_moyen))
with col3:
    kpi_card("Prix médian / m²", _fmt_price_m2(prix_m2_median))
with col4:
    kpi_card("Prix moyen / m²", _fmt_price_m2(prix_m2_moyen))

col5, col6 = st.columns(2)
with col5:
    kpi_card("Nb de maisons", f"{nb_maisons}")
with col6:
    kpi_card("Nb d'appartements", f"{nb_apparts}")

st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

section_title("Répartition des biens par prix")
if df.empty or "prix" not in df.columns or df["prix"].dropna().empty:
    st.info("Données prix manquantes pour construire l'histogramme.")
else:
    max_price = float(df["prix"].max())
    if max_price <= 0:
        st.info("Valeurs prix invalides.")
    else:
        bin_count = min(12, max(4, int(max_price // 50000)))
        step = max(50000, int(round(max_price / bin_count / 50000) * 50000))
        bins = list(range(0, int(step * (bin_count + 1)), step))
        if bins[-1] < max_price:
            bins.append(int(max_price + step))
        df["price_bin"] = pd.cut(df["prix"], bins=bins, include_lowest=True)
        counts = df["price_bin"].value_counts().sort_index()
        labels = [f"{int(interval.left):,} - {int(interval.right):,}".replace(",", " ") for interval in counts.index]
        fig = px.bar(x=labels, y=counts.values, template=get_plotly_template(), labels={"y": "Nombre de biens", "x": "Prix"})
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

if ignored_count > 0:
    st.caption(f"Lignes ignorées après filtrage: {ignored_count}")

if "date_publication" in raw_df.columns:
    dates = pd.to_datetime(raw_df["date_publication"], errors="coerce")
    if dates.notna().any():
        st.caption(f"Publications: {dates.min().strftime('%Y-%m-%d')} → {dates.max().strftime('%Y-%m-%d')}")
