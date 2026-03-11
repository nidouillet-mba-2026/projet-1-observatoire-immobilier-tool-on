import re

import pandas as pd
import streamlit as st
from pathlib import Path

from app.components.ui import (
    apply_custom_css,
    initialize_session_state,
    kpi_card,
    section_title,
    sidebar_logo,
)
from analysis.regression import least_squares_fit
from analysis.scoring import enrich_listing_with_model
from analysis.knn import recommander_annonces

st.set_page_config(page_title="Recherche - ToolOn", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()

# Chargement des données
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def _find_csv() -> str | None:
    """Charge spécifiquement le fichier annonces_actuelles.csv"""
    # Priorité 1 : annonces_actuelles.csv
    for folder in [DATA_DIR, BASE_DIR]:
        if not folder.exists():
            continue
        target = folder / "annonces_actuelles.csv"
        if target.exists():
            return str(target)

    # Fallback : chercher d'autres fichiers d'annonces
    for folder in [DATA_DIR, BASE_DIR]:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True):
            if "annonce" in path.name.lower() or "immo" in path.name.lower():
                return str(path)
    return None


@st.cache_data
def train_regression_model() -> tuple[float, float]:
    """Entraîne le modèle de régression sur les données DVF."""
    # Charger le fichier DVF (transactions historiques), PAS les annonces
    dvf_path = DATA_DIR / "dvf_toulon.csv"
    if not dvf_path.exists():
        # Fallback sur le fichier brut si le nettoyé n'existe pas
        dvf_path = DATA_DIR / "DVF-83-Toulon-2024-2025Brut.csv"

    if not dvf_path.exists():
        return 0.0, 3000.0  # Valeurs par défaut si pas de DVF

    try:
        df_dvf = pd.read_csv(dvf_path, sep=';', encoding='utf-8')
        df_dvf.columns = [c.strip().lower() for c in df_dvf.columns]

        # Colonnes possibles pour surface et prix
        surface_col = None
        prix_col = None

        for col in ['surface_totale', 'surface_reelle_bati', 'surface_m2', 'surface']:
            if col in df_dvf.columns:
                surface_col = col
                break

        for col in ['valeur_fonciere', 'prix', 'montant']:
            if col in df_dvf.columns:
                prix_col = col
                break

        if not surface_col or not prix_col:
            return 0.0, 3000.0

        # Conversion en numérique
        df_dvf[surface_col] = pd.to_numeric(df_dvf[surface_col], errors='coerce')
        df_dvf[prix_col] = pd.to_numeric(df_dvf[prix_col], errors='coerce')

        # Filtrage des données valides
        df_clean = df_dvf[
            (df_dvf[surface_col].notna()) &
            (df_dvf[prix_col].notna()) &
            (df_dvf[surface_col] > 10) &  # Surface minimale
            (df_dvf[surface_col] < 500) &  # Surface maximale
            (df_dvf[prix_col] > 10000) &  # Prix minimal
            (df_dvf[prix_col] < 2_000_000)  # Prix maximal
        ].copy()

        if len(df_clean) < 10:
            return 0.0, 3000.0

        # Entraînement du modèle
        x = df_clean[surface_col].tolist()
        y = df_clean[prix_col].tolist()

        alpha, beta = least_squares_fit(x, y)
        return alpha, beta

    except Exception:
        return 0.0, 3000.0  # Valeurs par défaut en cas d'erreur


@st.cache_data
def load_raw_csv(path: str, alpha: float, beta: float) -> pd.DataFrame:
    """Charge le CSV directement en conservant toutes les colonnes natives."""
    file_path = Path(path)
    raw = file_path.read_bytes()[:10000]
    try:
        preview = raw.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        preview = raw.decode("latin-1", errors="ignore")
        encoding = "latin-1"
    sep = ";" if preview.count(";") > preview.count(",") else ","
    df = pd.read_csv(file_path, encoding=encoding, sep=sep)
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    numeric_cols = [
        "prix", "surface_m2", "prix_m2", "pieces", "chambres", "salles_de_bain",
        "nb_parkings", "etage", "nb_etages_immeuble", "surface_terrain_m2",
        "balcon", "terrasse", "jardin", "ascenseur", "cave",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Enrichissement avec le modèle de régression
    enriched_rows = []
    for _, row in df.iterrows():
        listing_dict = row.to_dict()
        # Adaptation pour la fonction d'enrichissement
        if "surface_m2" in listing_dict:
            listing_dict["surface"] = listing_dict["surface_m2"]
        enriched = enrich_listing_with_model(listing_dict, alpha, beta)
        enriched_rows.append(enriched)

    df_enriched = pd.DataFrame(enriched_rows)
    return df_enriched


def _ensure_id_column(df: pd.DataFrame) -> pd.DataFrame:
    if "id_annonce" in df.columns:
        return df
    for alias in ("id", "id_annonce", "idannonce", "reference", "ref"):
        if alias in df.columns:
            df["id_annonce"] = df[alias].astype(str)
            return df
    df["id_annonce"] = df.index.astype(str)
    return df


# Session state
if "open_tabs" not in st.session_state:
    st.session_state["open_tabs"] = []
if "cards_shown" not in st.session_state:
    st.session_state["cards_shown"] = 21


# Helpers
def _fmt_prix(val) -> str:
    try:
        return f"{int(float(val)):,} €".replace(",", "\u00a0")
    except (ValueError, TypeError):
        return "N/A"


def _fmt_num(val, suffix: str = "") -> str:
    try:
        v = float(val)
        if v != v:  # NaN
            return "N/A"
        return f"{int(v)}{suffix}" if v == int(v) else f"{v:.1f}{suffix}"
    except (ValueError, TypeError):
        return "N/A"


def _is_valid(val) -> bool:
    if val is None:
        return False
    try:
        if pd.isna(val):
            return False
    except (TypeError, ValueError):
        pass
    return str(val).strip().lower() not in ("", "nan", "none")


def _bool_label(val) -> str:
    if not _is_valid(val):
        return "N/A"
    return "Oui" if str(val).strip() in ("1", "1.0", "True", "true", "Oui", "oui") else "Non"


# Topbar avec bouton Recharger
theme = st.session_state.get("theme", "light")
col_title, col_toggle, col_reload = st.columns([5, 1, 1.2])
with col_title:
    st.markdown('<h1 class="header-title">Recherche d\'Annonces</h1>', unsafe_allow_html=True)
with col_toggle:
    lbl = "🌙" if theme == "light" else "☀️"
    help_txt = "Basculer en mode sombre" if theme == "light" else "Basculer en mode clair"
    if st.button(lbl, key="theme_toggle_btn", help=help_txt, use_container_width=True):
        st.session_state["theme"] = "dark" if theme == "light" else "light"
        st.rerun()
with col_reload:
    if st.button("↺ Recharger", key="reload_btn", use_container_width=True, help="Relire le fichier CSV"):
        st.cache_data.clear()
        st.session_state["cards_shown"] = 21
        st.rerun()
st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)

# Chargement
csv_path = _find_csv()
if csv_path is None:
    st.error("Aucun fichier CSV trouvé dans le dossier `data/`.")
    st.stop()

# Entraînement du modèle de régression
alpha, beta = train_regression_model()

df = load_raw_csv(csv_path, alpha, beta)
df = _ensure_id_column(df)

# Valeurs min/max pour les sliders
prix_vals = df["prix"].dropna()
surf_vals = df["surface_m2"].dropna()

prix_min_v = int(prix_vals.min()) if not prix_vals.empty else 0
prix_max_v = int(prix_vals.max()) if not prix_vals.empty else 1_000_000
if prix_min_v >= prix_max_v:
    prix_max_v = prix_min_v + 1

surf_min_v = int(surf_vals.min()) if not surf_vals.empty else 0
surf_max_v = int(surf_vals.max()) if not surf_vals.empty else 500
if surf_min_v >= surf_max_v:
    surf_max_v = surf_min_v + 1

p_max = int(df["pieces"].dropna().max()) if "pieces" in df.columns and df["pieces"].notna().any() else 10
if p_max < 1:
    p_max = 1

# Filtres principaux
section_title("Filtres")
f1, f2, f3, f4, f5 = st.columns(5)
with f1:
    prix_range = st.slider(
        "Prix (€)", prix_min_v, prix_max_v, (prix_min_v, prix_max_v),
        step=max(1, (prix_max_v - prix_min_v) // 200),
        format="%d €",
    )
with f2:
    types_opts = sorted(df["type_bien"].dropna().unique().tolist()) if "type_bien" in df.columns else []
    type_sel = st.multiselect("Type de logement", types_opts, placeholder="Tous")
with f3:
    surf_range = st.slider(
        "Surface (m²)", surf_min_v, surf_max_v, (surf_min_v, surf_max_v),
        step=max(1, (surf_max_v - surf_min_v) // 100),
        format="%d m²",
    )
with f4:
    pieces_range = st.slider("Nb pièces", 0, p_max, (0, p_max))
with f5:
    q_opts = sorted([q for q in df["quartier"].dropna().unique() if str(q).strip()]) if "quartier" in df.columns else []
    quartiers_sel = st.multiselect("Quartier", q_opts, placeholder="Tous")

# Filtres avancés
with st.expander("Filtres avancés"):
    fa1, fa2, fa3 = st.columns([1, 1, 3])
    with fa1:
        sdb_max = int(df["salles_de_bain"].dropna().max()) if "salles_de_bain" in df.columns and df["salles_de_bain"].notna().any() else 5
        sdb_min = st.number_input("Salles de bain (min)", min_value=0, max_value=max(sdb_max, 1), value=0)
    with fa2:
        ch_max = int(df["chambres"].dropna().max()) if "chambres" in df.columns and df["chambres"].notna().any() else 8
        chamb_min = st.number_input("Chambres (min)", min_value=0, max_value=max(ch_max, 1), value=0)
    with fa3:
        dpe_all = ["A", "B", "C", "D", "E", "F", "G"]
        st.markdown("**DPE**")
        dpe_cols_ui = st.columns(7)
        dpe_sel = []
        for di, dv in enumerate(dpe_all):
            with dpe_cols_ui[di]:
                if st.checkbox(dv, value=True, key=f"dpe_{dv}"):
                    dpe_sel.append(dv)

#  Tri
col_tri, _ = st.columns([2, 4])
with col_tri:
    tri = st.selectbox(
        "Trier par",
        ["Score opportunité", "Prix croissant", "Prix décroissant"],
    )

# Application des filtres 
flt = df.copy()
flt = flt[flt["prix"].between(prix_range[0], prix_range[1], inclusive="both")]
flt = flt[flt["surface_m2"].between(surf_range[0], surf_range[1], inclusive="both")]
if pieces_range != (0, p_max):
    flt = flt[flt["pieces"].fillna(0).between(pieces_range[0], pieces_range[1])]
if type_sel:
    flt = flt[flt["type_bien"].isin(type_sel)]
if quartiers_sel:
    flt = flt[flt["quartier"].isin(quartiers_sel)]
if sdb_min > 0 and "salles_de_bain" in flt.columns:
    flt = flt[flt["salles_de_bain"].fillna(0) >= sdb_min]
if chamb_min > 0 and "chambres" in flt.columns:
    flt = flt[flt["chambres"].fillna(0) >= chamb_min]
if len(dpe_sel) < 7 and "classe_energie" in df.columns:
    flt = flt[flt["classe_energie"].isin(dpe_sel) | flt["classe_energie"].isna()]

if tri == "Prix croissant":
    flt = flt.sort_values("prix", ascending=True)
elif tri == "Prix décroissant":
    flt = flt.sort_values("prix", ascending=False)
else:
    flt = flt.sort_values("score_opportunite", ascending=False)
flt = flt.reset_index(drop=True)

# KPIs
st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
with k1:
    kpi_card("Résultats", len(flt), None)
with k2:
    med = int(flt["prix"].median()) if not flt.empty and flt["prix"].notna().any() else 0
    kpi_card("Prix médian", f"{med:,} €".replace(",", "\u00a0"), None)
with k3:
    # Compter les biens sous-évalués
    nb_opportunites = len(flt[flt["categorie"] == "opportunite"]) if "categorie" in flt.columns else 0
    kpi_card("Biens sous-évalués", f"{nb_opportunites}", None)
st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

# ── Onglets 
open_tabs = st.session_state["open_tabs"]  # list[dict] : {id_annonce, titre}

tab_labels = ["Résultats"]
for t in open_tabs:
    short = t["titre"][:22] + "…" if len(t["titre"]) > 22 else t["titre"]
    tab_labels.append(f"🏠 {short}")

tabs_ui = st.tabs(tab_labels)
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)


# ── Rendu d'une card ──────────────────────────────────────────────────────────
def render_card(bien: pd.Series, card_key: str) -> None:
    type_bien = str(bien.get("type_bien", "")).strip()
    icon = "🏠" if "maison" in type_bien.lower() else "🏢"
    titre = str(bien.get("titre", "Bien immobilier"))
    titre_display = titre[:55] + "…" if len(titre) > 55 else titre
    prix_str = _fmt_prix(bien.get("prix"))
    surf_str = _fmt_num(bien.get("surface_m2"), " m²")
    quartier = str(bien.get("quartier", "")).strip()

    # Récupération de la catégorie du modèle de régression
    categorie = str(bien.get("categorie", "")).strip().lower()
    ecart_pct = bien.get("ecart_pct", 0)

    # Badge selon la catégorie du modèle
    if categorie == "opportunite":
        badge_cls = "badge-excellent"
        badge_text = f"Sous-évalué ({abs(round(ecart_pct))}%)"
    elif categorie == "surevalue":
        badge_cls = "badge-neutral"
        badge_text = f"Sur-évalué (+{abs(round(ecart_pct))}%)"
    elif categorie == "prix_marche":
        badge_cls = "badge-good"
        badge_text = f"Prix marché ({round(ecart_pct):+.0f}%)"
    else:
        badge_cls = "badge-good"
        badge_text = "Non classifié"

    st.markdown(
        f"""
<div style="background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;
            padding:1rem;margin-bottom:0.25rem;min-height:170px;">
  <div style="font-size:1.6rem;line-height:1;">{icon}</div>
  <div style="font-weight:600;font-size:0.85rem;color:var(--text-color);
              margin:0.35rem 0;min-height:2.6em;line-height:1.3;overflow:hidden;">{titre_display}</div>
  <div style="font-size:1.1rem;font-weight:700;color:var(--accent);">{prix_str}</div>
  <div style="font-size:0.78rem;color:var(--muted);margin-top:0.2rem;">
    {surf_str} &nbsp;·&nbsp; {type_bien} &nbsp;·&nbsp; {quartier}
  </div>
  <div style="margin-top:0.5rem;">
    <span class="badge {badge_cls}" style="font-size:0.7rem;">{badge_text}</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Voir la fiche", key=card_key, use_container_width=True, type="primary"):
        bid = str(bien.get("id_annonce", ""))
        if bid not in [t["id_annonce"] for t in st.session_state["open_tabs"]]:
            st.session_state["open_tabs"].append({"id_annonce": bid, "titre": titre[:40]})
        st.rerun()


# Rendu d'une fiche 
def render_fiche(bien_id: str) -> None:
    rows = df[df["id_annonce"] == bien_id]
    if rows.empty:
        st.error("Fiche introuvable.")
        return
    b = rows.iloc[0]

    # Bouton fermer
    col_f, _ = st.columns([2, 6])
    with col_f:
        if st.button("✕ Fermer cet onglet", key=f"close_{bien_id}", type="secondary"):
            st.session_state["open_tabs"] = [
                t for t in st.session_state["open_tabs"] if t["id_annonce"] != bien_id
            ]
            st.rerun()

    st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)

    # Partie 1 : Informations
    section_title("Informations du logement")

    def _row_html(label: str, value) -> str:
        if not _is_valid(value):
            return ""
        return (
            f'<div style="display:flex;padding:0.45rem 0;'
            f'border-bottom:1px solid var(--border-color);">'
            f'<div style="width:46%;font-size:0.82rem;color:var(--muted);font-weight:500;">{label}</div>'
            f'<div style="width:54%;font-size:0.87rem;color:var(--text-color);font-weight:600;">{value}</div>'
            f"</div>"
        )

    date_pub = str(b.get("date_publication", ""))[:10] if _is_valid(b.get("date_publication")) else None

    # Titre affiché au-dessus des variables
    titre_fiche = str(b.get("titre", "")).strip()
    if titre_fiche and titre_fiche.lower() != "nan":
        st.markdown(
            f'<div style="font-size:1.25rem;font-weight:700;color:var(--text-color);'
            f'margin:0.75rem 0 1rem 0;line-height:1.4;">{titre_fiche}</div>',
            unsafe_allow_html=True,
        )

    col_info_a, col_info_b = st.columns(2)

    fields_left = [
        ("Prix",            _fmt_prix(b.get("prix"))),
        ("Prix / m²",       _fmt_prix(b.get("prix_m2"))),
        ("Surface",         _fmt_num(b.get("surface_m2"), " m²")),
        ("Pièces",          _fmt_num(b.get("pieces"))),
        ("Chambres",        _fmt_num(b.get("chambres"))),
        ("Salles de bain",  _fmt_num(b.get("salles_de_bain"))),
        ("Type de bien",    b.get("type_bien")),
        ("Ville",           b.get("ville")),
        ("Quartier",        b.get("quartier")),
        ("Code postal",     b.get("code_postal")),
    ]
    fields_right = [
        ("Balcon",              _bool_label(b.get("balcon"))),
        ("Terrasse",            _bool_label(b.get("terrasse"))),
        ("Jardin",              _bool_label(b.get("jardin"))),
        ("Ascenseur",           _bool_label(b.get("ascenseur"))),
        ("Cave",                _bool_label(b.get("cave"))),
        ("Nombre de parkings",  _fmt_num(b.get("nb_parkings"))),
        ("Étage",               _fmt_num(b.get("etage"))),
        ("Nb étages immeuble",  _fmt_num(b.get("nb_etages_immeuble"))),
        ("Surface terrain",     _fmt_num(b.get("surface_terrain_m2"), " m²")),
        ("Date de l'annonce",   date_pub),
        ("ID annonce",          b.get("id_annonce")),
        ("DPE",                 b.get("classe_energie")),
        ("GES",                 b.get("classe_ges")),
    ]

    html_left = "".join(_row_html(l, v) for l, v in fields_left)
    html_right = "".join(_row_html(l, v) for l, v in fields_right)

    with col_info_a:
        st.markdown(
            f'<div style="border-radius:8px;padding:0.25rem 0.5rem;">{html_left}</div>',
            unsafe_allow_html=True,
        )
    with col_info_b:
        st.markdown(
            f'<div style="border-radius:8px;padding:0.25rem 0.5rem;">{html_right}</div>',
            unsafe_allow_html=True,
        )

    # Description
    desc = b.get("description", "")
    if _is_valid(desc):
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        section_title("Description")
        desc_clean = re.sub(r"<[^>]+>", " ", str(desc).replace("<br>", "\n").replace("<br/>", "\n"))
        st.markdown(
            f'<div style="background:var(--card-bg);border:1px solid var(--border-color);'
            f'border-radius:8px;padding:1rem;font-size:0.875rem;color:var(--text-color);'
            f'line-height:1.6;">{desc_clean}</div>',
            unsafe_allow_html=True,
        )

    # Caractéristiques détectées depuis la description
    infos_desc = b.get("infos_description", {})
    if infos_desc and isinstance(infos_desc, dict):
        st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
        section_title("Caractéristiques détectées")

        # Construction des badges pour les équipements
        badges_html = []

        # Équipements principaux
        if infos_desc.get("vue_mer"):
            badges_html.append('<span class="badge badge-excellent" style="margin:0.25rem;">Vue mer</span>')
        if infos_desc.get("terrasse"):
            badges_html.append('<span class="badge badge-good" style="margin:0.25rem;">Terrasse</span>')
        if infos_desc.get("balcon"):
            badges_html.append('<span class="badge badge-good" style="margin:0.25rem;">Balcon</span>')
        if infos_desc.get("parking"):
            badges_html.append('<span class="badge badge-good" style="margin:0.25rem;">Parking</span>')
        if infos_desc.get("garage"):
            badges_html.append('<span class="badge badge-good" style="margin:0.25rem;">Garage</span>')
        if infos_desc.get("ascenseur"):
            badges_html.append('<span class="badge badge-good" style="margin:0.25rem;">Ascenseur</span>')
        if infos_desc.get("piscine"):
            badges_html.append('<span class="badge badge-excellent" style="margin:0.25rem;">Piscine</span>')

        # État du bien
        if infos_desc.get("renove"):
            badges_html.append('<span class="badge badge-excellent" style="margin:0.25rem;">Rénové</span>')
        if infos_desc.get("travaux"):
            badges_html.append('<span class="badge badge-neutral" style="margin:0.25rem;">Travaux à prévoir</span>')

        # Qualités
        if infos_desc.get("lumineux"):
            badges_html.append('<span class="badge badge-good" style="margin:0.25rem;">Lumineux</span>')
        if infos_desc.get("calme"):
            badges_html.append('<span class="badge badge-good" style="margin:0.25rem;">Calme</span>')

        # Étage
        if infos_desc.get("dernier_etage"):
            badges_html.append('<span class="badge badge-good" style="margin:0.25rem;">Dernier étage</span>')
        elif infos_desc.get("etage") is not None:
            etage_num = infos_desc.get("etage")
            badges_html.append(f'<span class="badge badge-neutral" style="margin:0.25rem;">Étage {etage_num}</span>')

        if badges_html:
            st.markdown(
                f"""
<div style="background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;
            padding:1.25rem;">
  <div style="font-size:0.85rem;color:var(--muted);margin-bottom:0.75rem;">
    Informations extraites automatiquement de la description
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:0.25rem;">
    {"".join(badges_html)}
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            st.info("Aucune caractéristique spécifique détectée dans la description.")

    # Bouton annonce
    url = str(b.get("url", "")).strip()
    if url and url not in ("nan", "none", ""):
        st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
        st.link_button("Voir l'annonce →", url, type="primary")

    # Partie 2 : Analyse du marché
    st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)
    section_title("Analyse du marché")

    # Récupération des données du modèle
    prix_estime = b.get("prix_estime", 0)
    ecart_absolu = b.get("ecart_absolu", 0)
    ecart_pct = b.get("ecart_pct", 0)
    categorie = str(b.get("categorie", "")).strip()
    insight = str(b.get("insight", "Analyse non disponible."))

    # Couleur selon la catégorie
    if categorie == "opportunite":
        cat_color = "#2E7D32"  # Vert
        cat_label = "Sous-évalué"
    elif categorie == "surevalue":
        cat_color = "#D32F2F"  # Rouge
        cat_label = "Sur-évalué"
    elif categorie == "prix_marche":
        cat_color = "#1976D2"  # Bleu
        cat_label = "Prix marché"
    else:
        cat_color = "#757575"  # Gris
        cat_label = "Non classifié"

    # Affichage de l'analyse
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(
            f"""
<div style="background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;
            padding:1.5rem;height:100%;">
  <div style="font-size:0.9rem;font-weight:600;color:var(--muted);margin-bottom:1rem;">
    Classification
  </div>
  <div style="text-align:center;padding:3rem 0;">
    <div style="font-size:1.5rem;font-weight:700;color:{cat_color};">
      {cat_label}
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(
            f"""
<div style="background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;
            padding:1.5rem;height:100%;">
  <div style="font-size:0.9rem;font-weight:600;color:var(--muted);margin-bottom:1rem;">
    Analyse de prix
  </div>
  <div style="display:flex;justify-content:space-between;padding:0.7rem 0;
              border-bottom:1px solid var(--border-color);">
    <span style="color:var(--muted);font-size:0.85rem;">Prix annoncé</span>
    <span style="color:var(--text-color);font-weight:600;font-size:0.9rem;">
      {_fmt_prix(b.get("prix"))}
    </span>
  </div>
  <div style="display:flex;justify-content:space-between;padding:0.7rem 0;
              border-bottom:1px solid var(--border-color);">
    <span style="color:var(--muted);font-size:0.85rem;">Prix estimé (modèle)</span>
    <span style="color:var(--text-color);font-weight:600;font-size:0.9rem;">
      {_fmt_prix(prix_estime)}
    </span>
  </div>
  <div style="display:flex;justify-content:space-between;padding:0.7rem 0;
              border-bottom:1px solid var(--border-color);">
    <span style="color:var(--muted);font-size:0.85rem;">Écart absolu</span>
    <span style="color:{cat_color};font-weight:700;font-size:0.9rem;">
      {ecart_absolu:+.0f} €
    </span>
  </div>
  <div style="display:flex;justify-content:space-between;padding:0.7rem 0;">
    <span style="color:var(--muted);font-size:0.85rem;">Écart relatif</span>
    <span style="color:{cat_color};font-weight:700;font-size:1.1rem;">
      {ecart_pct:+.1f}%
    </span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # Insight
    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div style="background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;
            padding:1.5rem;">
  <div style="font-size:0.9rem;font-weight:600;color:var(--muted);margin-bottom:0.75rem;">
    Analyse
  </div>
  <div style="font-size:0.9rem;color:var(--text-color);line-height:1.6;">
    {insight}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Partie 3 : Recommandations KNN
    st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)
    section_title("Biens similaires (recommandations)")

    def clean_dict(d):
        """Nettoie un dictionnaire en remplaçant les NaN par None."""
        cleaned = {}
        for key, value in d.items():
            if pd.isna(value):
                cleaned[key] = None
            else:
                cleaned[key] = value
        return cleaned

    # Récupération des recommandations
    try:
        # Préparer le catalogue (tous les biens sauf le bien actuel)
        df_catalogue = df[df["id_annonce"] != bien_id]
        catalogue_annonces = [clean_dict(row) for _, row in df_catalogue.iterrows()]

        if len(catalogue_annonces) > 0:
            # Obtenir les recommandations
            bien_dict = clean_dict(b.to_dict())
            recommendations = recommander_annonces(bien_dict, catalogue_annonces, k=6)

            if recommendations:
                st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

                # Affichage en grille 3 colonnes
                n_reco = len(recommendations)
                n_rows = (n_reco + 2) // 3

                for row_i in range(n_rows):
                    cols = st.columns(3)
                    for col_i, col in enumerate(cols):
                        idx = row_i * 3 + col_i
                        if idx < n_reco:
                            distance, similarite, reco = recommendations[idx]

                            with col:
                                reco_type = str(reco.get("type_bien", "")).strip()
                                reco_icon = "🏠" if "maison" in reco_type.lower() else "🏢"
                                reco_titre = str(reco.get("titre", "Bien immobilier"))
                                reco_titre_short = reco_titre[:40] + "…" if len(reco_titre) > 40 else reco_titre
                                reco_prix = _fmt_prix(reco.get("prix"))
                                reco_surf = _fmt_num(reco.get("surface_m2"), " m²")
                                reco_quartier = str(reco.get("quartier", "")).strip()

                                # Badge de similarité
                                if similarite > 80:
                                    sim_cls = "badge-excellent"
                                elif similarite > 60:
                                    sim_cls = "badge-good"
                                else:
                                    sim_cls = "badge-neutral"

                                st.markdown(
                                    f"""
<div style="background:var(--card-bg);border:1px solid var(--border-color);border-radius:12px;
            padding:1rem;margin-bottom:0.5rem;min-height:160px;">
  <div style="font-size:1.4rem;line-height:1;">{reco_icon}</div>
  <div style="font-weight:600;font-size:0.8rem;color:var(--text-color);
              margin:0.3rem 0;min-height:2.4em;line-height:1.2;overflow:hidden;">{reco_titre_short}</div>
  <div style="font-size:1rem;font-weight:700;color:var(--accent);">{reco_prix}</div>
  <div style="font-size:0.75rem;color:var(--muted);margin-top:0.2rem;">
    {reco_surf} · {reco_quartier}
  </div>
  <div style="margin-top:0.4rem;">
    <span class="badge {sim_cls}" style="font-size:0.65rem;">Similarité : {similarite:.0f}%</span>
  </div>
</div>
""",
                                    unsafe_allow_html=True,
                                )

                                # Bouton pour ouvrir la fiche
                                reco_id = str(reco.get("id_annonce", ""))
                                if st.button("Voir la fiche", key=f"reco_{bien_id}_{reco_id}", use_container_width=True, type="secondary"):
                                    if reco_id not in [t["id_annonce"] for t in st.session_state["open_tabs"]]:
                                        st.session_state["open_tabs"].append({"id_annonce": reco_id, "titre": reco_titre[:40]})
                                    st.rerun()
            else:
                st.info("Aucune recommandation disponible pour ce bien.")
        else:
            st.info("Pas assez de biens dans le catalogue pour générer des recommandations.")

    except Exception as e:
        st.warning(f"Impossible de générer les recommandations : {str(e)}")


# Onglet 0 : Résultats 
with tabs_ui[0]:
    cards_shown = st.session_state.get("cards_shown", 21)
    page_slice = flt.head(cards_shown)

    section_title(f"Résultats : {len(flt)} bien(s) trouvé(s)")

    if page_slice.empty:
        st.info("Aucun bien ne correspond aux critères sélectionnés.")
    else:
        n = len(page_slice)
        n_grid_rows = (n + 2) // 3
        for row_i in range(n_grid_rows):
            c1, c2, c3 = st.columns(3)
            for col_i, col_widget in enumerate([c1, c2, c3]):
                idx = row_i * 3 + col_i
                if idx < n:
                    bien_row = page_slice.iloc[idx]
                    safe_id = str(bien_row.get("id_annonce", idx)).replace("-", "_").replace(".", "_")
                    with col_widget:
                        render_card(bien_row, card_key=f"card_{safe_id}_{idx}")

        if cards_shown < len(flt):
            remaining = len(flt) - cards_shown
            more = min(21, remaining)
            col_more, _, _ = st.columns(3)
            with col_more:
                if st.button(
                    f"⬇ Charger {more} résultats de plus ({remaining} restants)",
                    key="load_more",
                    use_container_width=True,
                ):
                    st.session_state["cards_shown"] = cards_shown + 21
                    st.rerun()

# ── Onglets fiches ────────────────────────────────────────────────────────────
for i, tab_data in enumerate(open_tabs):
    with tabs_ui[i + 1]:
        render_fiche(tab_data["id_annonce"])

