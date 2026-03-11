"""
page tendances - evolution des prix dvf (transactions historiques)
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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


@st.cache_data
def load_dvf_data():
    """charge les donnees dvf brutes"""
    dvf_path = Path("data/DVF-83-Toulon-2024-2025Brut.csv")

    if not dvf_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(dvf_path, sep=';', encoding='utf-8', low_memory=False)

    # conversion des colonnes
    df['date_mutation'] = pd.to_datetime(df['date_mutation'], format='%d/%m/%Y', errors='coerce')
    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'], errors='coerce')
    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'], errors='coerce')
    df['code_postal'] = df['code_postal'].astype(str)

    # filtrage des donnees valides
    df = df[
        df['date_mutation'].notna() &
        df['valeur_fonciere'].notna() &
        (df['valeur_fonciere'] > 0) &
        (df['type_local'].notna())
    ].copy()

    # calcul prix au m2
    df['prix_m2'] = df.apply(
        lambda row: row['valeur_fonciere'] / row['surface_reelle_bati']
        if pd.notna(row['surface_reelle_bati']) and row['surface_reelle_bati'] > 0
        else None,
        axis=1
    )

    return df


def build_trend_chart(df: pd.DataFrame, metric: str = "prix_median") -> go.Figure:
    """construit le graphique d'evolution temporelle"""
    if df.empty:
        return go.Figure()

    df = df.copy()
    df['mois'] = df['date_mutation'].dt.to_period('M').dt.to_timestamp()

    if metric == "prix_median":
        # prix median par mois
        trend = df.groupby('mois')['valeur_fonciere'].median().reset_index()
        trend.columns = ['Date', 'Prix médian']

        fig = px.line(
            trend,
            x='Date',
            y='Prix médian',
            template=get_plotly_template(),
            labels={'Prix médian': 'Prix médian (€)', 'Date': 'Date'},
        )
        fig.update_traces(line_color='#2E7D32', line_width=3)

    elif metric == "prix_m2_median":
        # prix/m2 median par mois
        trend = df[df['prix_m2'].notna()].groupby('mois')['prix_m2'].median().reset_index()
        trend.columns = ['Date', 'Prix/m² médian']

        fig = px.line(
            trend,
            x='Date',
            y='Prix/m² médian',
            template=get_plotly_template(),
            labels={'Prix/m² médian': 'Prix/m² médian (€)', 'Date': 'Date'},
        )
        fig.update_traces(line_color='#1976D2', line_width=3)

    else:  # volume
        # volume de transactions par mois
        trend = df.groupby('mois').size().reset_index()
        trend.columns = ['Date', 'Volume']

        fig = px.bar(
            trend,
            x='Date',
            y='Volume',
            template=get_plotly_template(),
            labels={'Volume': 'Nombre de transactions', 'Date': 'Date'},
        )
        fig.update_traces(marker_color='#F57C00')

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        margin=dict(l=0, r=0, t=20, b=0),
    )

    return fig


def format_currency(value):
    """formate un nombre en devise"""
    if pd.isna(value):
        return "N/A"
    return f"{int(value):,}".replace(',', ' ') + " €"


# configuration de la page
st.set_page_config(page_title="Tendances DVF - ToolOn", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()
topbar("Tendances du Marché (DVF)")

# chargement des donnees
df_dvf = load_dvf_data()

if df_dvf.empty:
    st.error("Impossible de charger les données DVF. Vérifiez que le fichier `data/DVF-83-Toulon-2024-2025Brut.csv` existe.")
    st.stop()

page_header(
    export_df=df_dvf,
    export_filename="dvf_tendances.csv",
    show_period=False
)

# === FILTRES ===
st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)
section_title("🔍 Filtres")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    codes_postaux = sorted(df_dvf['code_postal'].unique())
    selected_cp = st.multiselect(
        "Code postal",
        options=codes_postaux,
        default=codes_postaux,
        help="Filtrer par code postal"
    )

with filter_col2:
    types_bien = sorted(df_dvf['type_local'].dropna().unique())
    selected_types = st.multiselect(
        "Type de bien",
        options=types_bien,
        default=types_bien,
        help="Filtrer par type de bien"
    )

with filter_col3:
    # filtre surface
    if df_dvf['surface_reelle_bati'].notna().any():
        min_surf = int(df_dvf['surface_reelle_bati'].min())
        max_surf = int(df_dvf['surface_reelle_bati'].max())
        surface_range = st.slider(
            "Surface (m²)",
            min_value=min_surf,
            max_value=max_surf,
            value=(min_surf, max_surf),
            help="Filtrer par surface"
        )
    else:
        surface_range = None

# application des filtres
df_filtered = df_dvf[
    (df_dvf['code_postal'].isin(selected_cp)) &
    (df_dvf['type_local'].isin(selected_types))
].copy()

if surface_range:
    df_filtered = df_filtered[
        (df_filtered['surface_reelle_bati'] >= surface_range[0]) &
        (df_filtered['surface_reelle_bati'] <= surface_range[1])
    ]

# === KPIs ===
st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    total_transactions = len(df_filtered)
    kpi_card("Transactions", f"{total_transactions:,}".replace(',', ' '), None)

with kpi_col2:
    prix_median = df_filtered['valeur_fonciere'].median()
    kpi_card("Prix médian", format_currency(prix_median), None)

with kpi_col3:
    if df_filtered['prix_m2'].notna().any():
        prix_m2_median = df_filtered['prix_m2'].median()
        kpi_card("Prix/m² médian", format_currency(prix_m2_median), None)
    else:
        kpi_card("Prix/m² médian", "N/A", None)

with kpi_col4:
    # variation sur 12 derniers mois si possible
    if len(df_filtered) > 0:
        df_sorted = df_filtered.sort_values('date_mutation')
        date_max = df_sorted['date_mutation'].max()
        date_12m_ago = date_max - pd.DateOffset(months=12)

        df_recent = df_sorted[df_sorted['date_mutation'] >= date_12m_ago]
        df_old = df_sorted[df_sorted['date_mutation'] < date_12m_ago]

        if len(df_recent) > 0 and len(df_old) > 0:
            prix_recent = df_recent['valeur_fonciere'].median()
            prix_old = df_old['valeur_fonciere'].median()
            variation = ((prix_recent - prix_old) / prix_old * 100)
            kpi_card("Variation 12 mois", f"{variation:+.1f}%", None)
        else:
            kpi_card("Variation 12 mois", "N/A", None)
    else:
        kpi_card("Variation 12 mois", "N/A", None)

# === GRAPHIQUE PRINCIPAL : PRIX MEDIAN ===
st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)
section_title("📈 Évolution du prix médian des transactions")

if len(df_filtered) > 0:
    fig_prix = build_trend_chart(df_filtered, metric="prix_median")
    st.plotly_chart(fig_prix, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("Aucune donnée disponible avec les filtres sélectionnés.")

# === GRAPHIQUE : PRIX AU M2 ===
st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)
section_title("📊 Évolution du prix/m² médian")

if len(df_filtered[df_filtered['prix_m2'].notna()]) > 0:
    fig_m2 = build_trend_chart(df_filtered, metric="prix_m2_median")
    st.plotly_chart(fig_m2, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("Pas assez de données de surface disponibles.")

# === GRAPHIQUE : VOLUME ===
st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)
section_title("📦 Volume de transactions par mois")

if len(df_filtered) > 0:
    fig_volume = build_trend_chart(df_filtered, metric="volume")
    st.plotly_chart(fig_volume, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("Aucune donnée disponible.")

# === TABLEAU DETAILS PAR CP ===
st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)
section_title("📍 Détails par code postal")

if len(df_filtered) > 0:
    stats_cp = df_filtered.groupby('code_postal').agg({
        'valeur_fonciere': ['count', 'median', 'mean'],
        'prix_m2': 'median'
    }).round(0)

    stats_cp.columns = ['Nb transactions', 'Prix médian', 'Prix moyen', 'Prix/m² médian']
    stats_cp = stats_cp.sort_values('Nb transactions', ascending=False)

    # formatage
    for col in ['Prix médian', 'Prix moyen', 'Prix/m² médian']:
        stats_cp[col] = stats_cp[col].apply(lambda x: format_currency(x))

    st.dataframe(stats_cp, use_container_width=True)
else:
    st.info("Aucune donnée disponible.")
