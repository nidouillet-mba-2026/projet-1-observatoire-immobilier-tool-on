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

st.set_page_config(page_title="Recherche - ToolOn", layout="wide")

initialize_session_state()
apply_custom_css()
sidebar_logo()

# Chargement des données
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def _find_csv() -> str | None:
    for folder in [DATA_DIR, BASE_DIR]:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True):
            if "annonce" in path.name.lower() or "immo" in path.name.lower():
                return str(path)
    return None


@st.cache_data
def load_raw_csv(path: str) -> pd.DataFrame:
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
    # Calcul du score opportunité (écart au prix médian du quartier)
    if "prix_m2" in df.columns and "quartier" in df.columns:
        med_q = df.groupby("quartier")["prix_m2"].transform("median")
        raw_score = ((med_q - df["prix_m2"]) / med_q.clip(lower=1)) * 100
        df["score_opportunite"] = raw_score.clip(0, 100).round(0)
    else:
        df["score_opportunite"] = 0.0
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

df = load_raw_csv(csv_path)

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
    avg_s = round(float(flt["score_opportunite"].mean()), 1) if not flt.empty else 0.0
    kpi_card("Score moyen", f"{avg_s}/100", None)
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
    score_raw = bien.get("score_opportunite", 0)
    try:
        score_int = int(float(score_raw)) if _is_valid(score_raw) else 0
    except (ValueError, TypeError):
        score_int = 0
    badge_cls = "badge-excellent" if score_int > 75 else "badge-good" if score_int > 50 else "badge-neutral"

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
    <span class="badge {badge_cls}">Score&nbsp;: {score_int}/100</span>
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

    # Bouton annonce
    url = str(b.get("url", "")).strip()
    if url and url not in ("nan", "none", ""):
        st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
        st.link_button("Voir l'annonce →", url, type="primary")

    # Partie 2 : Opportunité marché (placeholder)
    st.markdown("<div class='topbar-divider'></div>", unsafe_allow_html=True)
    section_title("Opportunité marché")
    st.markdown(
        """
<div style="background:var(--card-bg);border:2px dashed var(--border-color);border-radius:12px;
            padding:2.5rem 2rem;text-align:center;color:var(--muted);">
  <div style="font-size:2rem;margin-bottom:0.5rem;"></div>
  <div style="font-size:0.95rem;font-weight:600;">Section à venir</div>
  <div style="font-size:0.82rem;margin-top:0.3rem;">
    L'analyse de l'opportunité marché sera complétée ultérieurement.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


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
