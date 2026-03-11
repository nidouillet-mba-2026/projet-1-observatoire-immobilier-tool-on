import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

from app.components.ui import (
    apply_custom_css,
    get_plotly_template,
    initialize_session_state,
    page_header,
    section_title,
    sidebar_logo,
    topbar,
)

CSV_PATHS = [Path("data/Annonce_immo.csv"), Path("Annonce_immo.csv")]


def _load_dataset() -> pd.DataFrame:
    for path in CSV_PATHS:
        if not path.exists():
            continue
        for encoding in ("utf-8", "latin-1"):
            try:
                return pd.read_csv(path, sep=";", encoding=encoding, on_bad_lines="skip")
            except Exception:
                continue
    return pd.DataFrame()


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["prix", "surface_m2", "prix_m2"]
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = pd.Series(pd.NA, index=df.index)
    if "prix_m2" in df.columns and "prix" in df.columns and "surface_m2" in df.columns:
        missing = df["prix_m2"].isna() & df["prix"].gt(0) & df["surface_m2"].gt(0)
        df.loc[missing, "prix_m2"] = df.loc[missing, "prix"] / df.loc[missing, "surface_m2"]
    for col in ["type_bien", "quartier", "id_annonce"]:
        if col not in df.columns:
            df[col] = pd.Series("" if col != "id_annonce" else range(len(df)), index=df.index)
    df["type_bien"] = df["type_bien"].astype(str).str.lower().str.strip()
    df["quartier"] = df["quartier"].fillna("Inconnu").astype(str)
    mask = pd.Series(True, index=df.index)
    if "prix" in df.columns:
        mask &= df["prix"] > 0
    if "surface_m2" in df.columns:
        mask &= df["surface_m2"] > 0
    return df[mask].copy()


def _min_max(values):
    if values is None or values.empty:
        return 0, 0
    return float(values.min()), float(values.max())


def _min_max_norm(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(0, index=series.index)
    min_val = series.min()
    max_val = series.max()
    if min_val == max_val:
        return pd.Series(0.5, index=series.index)
    return (series - min_val) / (max_val - min_val)


def _score_quartiers(table: pd.DataFrame) -> pd.DataFrame:
    price_norm = _min_max_norm(table["prix_m2"])
    surface_norm = _min_max_norm(table["surface_m2"])
    volume_norm = _min_max_norm(table["nb_biens"])
    score = 0.5 * (1 - price_norm) + 0.3 * surface_norm + 0.2 * volume_norm
    table["score_qp"] = (score * 100).round(1)
    return table


def _format_currency(value):
    if pd.isna(value):
        return "N/A"
    return f"{int(round(value)):,}".replace(",", " ") + " €"


def _format_m2(value):
    if pd.isna(value):
        return "N/A"
    return f"{int(round(value)):,}".replace(",", " ") + " €/m²"


df_raw = _load_dataset()
df_clean = _normalize(df_raw)

price_min, price_max = _min_max(df_clean["prix"] if "prix" in df_clean.columns else pd.Series(dtype=float))
budget_max = min(450000, price_max) if price_max > 0 else 450000
budget_min = price_min if price_min > 0 else 0
surface_min, surface_max = _min_max(df_clean["surface_m2"] if "surface_m2" in df_clean.columns else pd.Series(dtype=float))

quartiers_available = (
    df_clean["quartier"].value_counts().index.tolist() if "quartier" in df_clean.columns else []
)
default_quartiers = quartiers_available[:6]
types = ["tous"]
if "type_bien" in df_clean.columns:
    types += sorted(df_clean["type_bien"].dropna().unique())

st.set_page_config(page_title="Marché - ToolOn", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Analyse du Marché")
page_header(export_df=df_clean, export_filename="marche_annonces.csv")

st.markdown(
    "<div class='section-title'>Jeu de données : annonces Toulon ≤ 450 000 € (déjà filtrées)</div>",
    unsafe_allow_html=True,
)
if price_max > 0:
    st.caption(f"Prix observés : {int(price_min):,} € → {int(price_max):,} €".replace(",", " "))

with st.container():
    col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
    with col1:
        budget = st.slider("Budget max (€)", min_value=int(budget_min), max_value=int(budget_max or 450000), value=int(budget_max or 450000), step=25000)
    with col2:
        st.selectbox("Type de bien", options=types, index=0, key="type_filter")
    with col3:
        st.slider(
            "Surface (m²)",
            min_value=int(surface_min or 0),
            max_value=int(surface_max or 200),
            value=(int(surface_min or 0), int(surface_max or 200)),
            key="surface_range",
        )
    with col4:
        if "pieces" in df_clean.columns:
            st.slider(
                "Pièces",
                min_value=int(df_clean["pieces"].min()) if df_clean["pieces"].notna().any() else 0,
                max_value=int(df_clean["pieces"].max()) if df_clean["pieces"].notna().any() else 6,
                value=(1, int(df_clean["pieces"].max()) if df_clean["pieces"].notna().any() else 6),
                key="pieces_range",
            )
        else:
            st.markdown("<br>", unsafe_allow_html=True)

quartiers_selected = st.multiselect(
    "Quartiers", options=quartiers_available, default=default_quartiers, key="quartiers_filter"
)

filtered = df_clean.copy()
if "prix" in filtered.columns:
    filtered = filtered[filtered["prix"] <= budget]
if "surface_m2" in filtered.columns:
    surf_low, surf_high = st.session_state.get("surface_range", (surface_min or 0, surface_max or 200))
    filtered = filtered[filtered["surface_m2"].between(surf_low, surf_high)]
if "type_bien" in filtered.columns and st.session_state.get("type_filter", "tous") != "tous":
    filtered = filtered[filtered["type_bien"] == st.session_state["type_filter"]]
if "pieces" in filtered.columns and "pieces_range" in st.session_state:
    p_low, p_high = st.session_state["pieces_range"]
    filtered = filtered[filtered["pieces"].between(p_low, p_high)]
if quartiers_selected:
    filtered = filtered[filtered["quartier"].isin(quartiers_selected)]

kpi_cols = st.columns(5)
metrics = {
    "Nb biens": len(filtered),
    "Prix médian": _format_currency(filtered["prix"].median() if "prix" in filtered.columns else pd.NA),
    "Prix/m² médian": _format_m2(filtered["prix_m2"].median() if "prix_m2" in filtered.columns else pd.NA),
    "Surface médiane": f"{int(filtered['surface_m2'].median()) if 'surface_m2' in filtered.columns and filtered['surface_m2'].dropna().any() else 'N/A'} m²",
    "Nb quartiers": filtered["quartier"].nunique() if "quartier" in filtered.columns else 0,
}
for col, (label, value) in zip(kpi_cols, metrics.items()):
        col.markdown(f"**{label}**")
        col.markdown(f"<h2>{value}</h2>", unsafe_allow_html=True)

if filtered.empty:
    st.warning("Aucune annonce compatible avec les filtres sélectionnés.")
else:
    quart_summary = filtered.groupby("quartier").agg(
        nb_biens=("id_annonce", "count"),
        prix_median=("prix", "median") if "prix" in filtered.columns else ("prix", "median"),
        prix_m2=("prix_m2", "median") if "prix_m2" in filtered.columns else ("prix", "median"),
        surface_m2=("surface_m2", "median") if "surface_m2" in filtered.columns else ("prix", "median"),
    )
    if "balcon" in filtered.columns:
        quart_summary["balcon_pct"] = filtered.groupby("quartier")["balcon"].mean() * 100
    if "terrasse" in filtered.columns:
        quart_summary["terrasse_pct"] = filtered.groupby("quartier")["terrasse"].mean() * 100
    if "jardin" in filtered.columns:
        quart_summary["jardin_pct"] = filtered.groupby("quartier")["jardin"].mean() * 100
    quart_summary = quart_summary.reset_index()
    quart_summary = quart_summary.fillna(0)
    quart_summary = _score_quartiers(quart_summary)
    quart_summary = quart_summary.sort_values("score_qp", ascending=False)

    section_title("Comparatif quartiers")
    column_conf = {
        "nb_biens": st.column_config.NumberColumn("Nombre"),
        "prix_median": st.column_config.NumberColumn("Prix médian", format="%d €"),
        "prix_m2": st.column_config.NumberColumn("€/m²", format="%d €/m²"),
        "surface_median": st.column_config.NumberColumn("Surface médiane", format="%d m²"),
        "score_qp": st.column_config.NumberColumn("Score Q/P", format="%.1f"),
    }
    for pct in ("balcon_pct", "terrasse_pct", "jardin_pct"):
        if pct in quart_summary.columns:
            column_conf[pct] = st.column_config.NumberColumn(
    pct.replace("_", " ").title(),
    format="%.1f%%"
)
    st.dataframe(
        quart_summary,
        use_container_width=True,
        hide_index=True,
        column_config=column_conf,
    )

    section_title("Visualisations")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        fig = px.bar(
            quart_summary,
            x="quartier",
            y="prix_m2",
            template=get_plotly_template(),
            labels={"quartier": "Quartier", "prix_m2": "Prix/m² médian"},
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with chart_cols[1]:
        fig_count = px.bar(
            quart_summary,
            x="quartier",
            y="nb_biens",
            template=get_plotly_template(),
            labels={"quartier": "Quartier", "nb_biens": "Nb biens"},
        )
        fig_count.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_count, use_container_width=True, config={"displayModeBar": False})

    if len(filtered) <= 1500 and "prix" in filtered.columns and "surface_m2" in filtered.columns:
        scatter = px.scatter(
            filtered,
            x="surface_m2",
            y="prix",
            color="quartier" if "quartier" in filtered.columns else None,
            template=get_plotly_template(),
            labels={"surface_m2": "Surface (m²)", "prix": "Prix (€)"},
        )
        st.plotly_chart(scatter, use_container_width=True, config={"displayModeBar": False})

    section_title("Recommandations")
    st.markdown(
        "- Top 5 quartiers meilleur rapport qualité/prix (score)\n"
        "- Top 5 quartiers les moins chers au m²\n"
        "- Top 5 quartiers avec le plus d'offres"
    )
    with st.container():
        rec_col1, rec_col2, rec_col3 = st.columns(3)
        rec_col1.write(quart_summary.head(5)[["quartier", "score_qp"]])
        rec_col2.write(quart_summary.sort_values("prix_m2").head(5)[["quartier", "prix_m2"]])
        rec_col3.write(quart_summary.sort_values("nb_biens", ascending=False).head(5)[["quartier", "nb_biens"]])
