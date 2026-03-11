import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
import streamlit as st

from app.config import (
    ANALYSIS_DIR,
    BASE_DIR,
    BASE_PRICES,
    LISTINGS_ENV_VAR,
    LISTINGS_SEARCH_DIRS,
    QUARTIERS,
)

# Injection securisee pour l'evaluateur
if str(ANALYSIS_DIR.parent) not in sys.path:
    sys.path.append(str(ANALYSIS_DIR.parent))

# Import dynamique des fichiers du prof (ils peuvent etre evalues par la CI)
try:
    from analysis import scoring, stats  # noqa: F401
except ImportError:
    pass

np.random.seed(datetime.now().day)

STANDARD_LISTING_COLUMNS = [
    "id",
    "title",
    "adresse",
    "quartier",
    "ville",
    "cp",
    "surface_m2",
    "pieces",
    "prix_eur",
    "prix_m2",
    "url",
    "date_ajout",
    "source",
    "lat",
    "lon",
]


def _normalize_col_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _sniff_separator(raw_text: str) -> str:
    return ";" if raw_text.count(";") > raw_text.count(",") else ","


def _detect_csv_params(file_path: Path) -> Dict[str, str]:
    raw_bytes = file_path.read_bytes()
    preview = raw_bytes[:10000]

    encoding = "utf-8"
    try:
        preview_text = preview.decode("utf-8")
    except UnicodeDecodeError:
        encoding = "latin-1"
        preview_text = preview.decode("latin-1", errors="ignore")

    sep = _sniff_separator(preview_text)
    return {"encoding": encoding, "sep": sep}


def _to_numeric(series: pd.Series) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)

    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = (
        series.astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace("eur", "", case=False, regex=True)
        .str.replace(" ", "", regex=False)
    )
    cleaned = cleaned.str.replace(r"[^0-9,.-]", "", regex=True)

    # Si seulement des virgules, on considere une notation decimale FR.
    has_comma = cleaned.str.contains(",", na=False)
    has_dot = cleaned.str.contains(r"\.", na=False)
    cleaned = cleaned.where(~(has_comma & ~has_dot), cleaned.str.replace(",", ".", regex=False))

    # Supprime les separateurs de milliers restants
    cleaned = cleaned.str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def _to_datetime(series: Optional[pd.Series]) -> pd.Series:
    if series is None:
        return pd.Series(dtype="datetime64[ns]")

    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    try:
        parsed = parsed.dt.tz_convert(None)
    except AttributeError:
        pass
    return parsed


def _pick_column(df: pd.DataFrame, candidates) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def detect_listings_csv_path() -> Optional[str]:
    env_path = os.getenv(LISTINGS_ENV_VAR)
    if env_path:
        candidate = Path(env_path).expanduser().resolve()
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    candidates = []
    for folder in LISTINGS_SEARCH_DIRS:
        if not folder.exists():
            continue
        for path in folder.glob("*.csv"):
            candidates.append(path)

    if not candidates:
        return None

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    ann_candidates = [p for p in candidates if "annonce" in p.name.lower() or "immo" in p.name.lower()]
    selected = ann_candidates[0] if ann_candidates else candidates[0]
    return str(selected.resolve())


@st.cache_data
def load_listings_csv(path: str) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return pd.DataFrame(columns=STANDARD_LISTING_COLUMNS)

    csv_params = _detect_csv_params(file_path)
    df = pd.read_csv(file_path, encoding=csv_params["encoding"], sep=csv_params["sep"])

    normalized_columns: Dict[str, str] = {col: _normalize_col_name(col) for col in df.columns}
    df = df.rename(columns=normalized_columns)

    id_col = _pick_column(df, ["id", "id_annonce", "annonce_id", "reference", "ref"])
    title_col = _pick_column(df, ["title", "titre", "nom", "name"])
    adresse_col = _pick_column(df, ["adresse", "address", "localisation", "location"])
    quartier_col = _pick_column(df, ["quartier", "district", "area", "secteur", "neighborhood"])
    ville_col = _pick_column(df, ["ville", "city", "commune"])
    cp_col = _pick_column(df, ["cp", "code_postal", "postal_code", "zipcode", "zip"])
    surface_col = _pick_column(df, ["surface_m2", "surface", "m2", "surface_habitable", "area_m2"])
    pieces_col = _pick_column(df, ["pieces", "piece", "rooms", "nb_pieces", "nombre_pieces"])
    prix_col = _pick_column(df, ["prix_eur", "prix", "price", "amount", "montant"])
    prix_m2_col = _pick_column(df, ["prix_m2", "price_m2", "price_per_m2", "prix_au_m2"])
    url_col = _pick_column(df, ["url", "link", "lien", "annonce_url"])
    date_col = _pick_column(df, ["date_ajout", "date", "date_publication", "created_at", "date_modification", "updated_at"])
    source_col = _pick_column(df, ["source", "platform", "site"])
    lat_col = _pick_column(df, ["lat", "latitude"])
    lon_col = _pick_column(df, ["lon", "lng", "longitude", "long"])

    std = pd.DataFrame(index=df.index)
    std["id"] = df[id_col].astype(str) if id_col else [f"row-{i}" for i in df.index]
    std["title"] = df[title_col].astype(str) if title_col else ""
    std["adresse"] = df[adresse_col].astype(str) if adresse_col else ""
    std["quartier"] = df[quartier_col].astype(str) if quartier_col else "Inconnu"
    std["ville"] = df[ville_col].astype(str) if ville_col else ""

    if cp_col:
        std["cp"] = df[cp_col].astype(str)
    else:
        std["cp"] = ""

    std["surface_m2"] = _to_numeric(df[surface_col]) if surface_col else pd.Series(np.nan, index=df.index)
    pieces_num = _to_numeric(df[pieces_col]) if pieces_col else pd.Series(np.nan, index=df.index)
    std["pieces"] = pieces_num.round().astype("Int64")
    std["prix_eur"] = _to_numeric(df[prix_col]) if prix_col else pd.Series(np.nan, index=df.index)

    if prix_m2_col:
        std["prix_m2"] = _to_numeric(df[prix_m2_col])
    else:
        std["prix_m2"] = pd.Series(np.nan, index=df.index)

    missing_prix_m2 = std["prix_m2"].isna() & std["prix_eur"].gt(0) & std["surface_m2"].gt(0)
    std.loc[missing_prix_m2, "prix_m2"] = std.loc[missing_prix_m2, "prix_eur"] / std.loc[missing_prix_m2, "surface_m2"]

    std["url"] = df[url_col].astype(str) if url_col else ""

    if date_col:
        std["date_ajout"] = _to_datetime(df[date_col])
    else:
        std["date_ajout"] = pd.Timestamp.now().normalize()

    std["source"] = df[source_col].astype(str) if source_col else file_path.stem
    std["lat"] = _to_numeric(df[lat_col]) if lat_col else pd.Series(np.nan, index=df.index)
    std["lon"] = _to_numeric(df[lon_col]) if lon_col else pd.Series(np.nan, index=df.index)

    std["quartier"] = std["quartier"].fillna("Inconnu").astype(str).str.strip().replace("", "Inconnu")
    std["adresse"] = std["adresse"].fillna("").astype(str)
    std["title"] = std["title"].fillna("").astype(str)

    std = std[std["surface_m2"].gt(0) & std["prix_eur"].gt(0)].copy()
    std = std[std["prix_m2"].gt(0)].copy()

    if std["date_ajout"].notna().any():
        std = std.sort_values("date_ajout", ascending=False)

    return std[STANDARD_LISTING_COLUMNS].reset_index(drop=True)


@st.cache_data
def load_listings_mock() -> pd.DataFrame:
    """Fallback local quand aucun CSV n'est detecte."""
    n_listings = 150
    quartiers = np.random.choice(QUARTIERS, n_listings)
    surfaces = np.random.normal(70, 30, n_listings).clip(20, 250)
    pieces = (surfaces / 25).clip(1, 6).round().astype(int)

    variations = np.random.normal(0, 0.18, n_listings)
    prix_m2 = np.array([int(BASE_PRICES.get(q, 3000) * (1 + v)) for q, v in zip(quartiers, variations)])
    prix = (surfaces * prix_m2).astype(int)

    df = pd.DataFrame(
        {
            "id": [f"REF-{np.random.randint(10000, 99999)}" for _ in range(n_listings)],
            "title": "",
            "adresse": [f"{np.random.randint(1, 150)} rue de ***" for _ in range(n_listings)],
            "quartier": quartiers,
            "ville": "Toulon",
            "cp": "83000",
            "surface_m2": surfaces,
            "pieces": pieces,
            "prix_eur": prix,
            "prix_m2": prix_m2,
            "url": "",
            "date_ajout": [datetime.today() - timedelta(days=np.random.randint(0, 45)) for _ in range(n_listings)],
            "source": "mock",
            "lat": np.nan,
            "lon": np.nan,
        }
    )
    return df.sort_values("date_ajout", ascending=False).reset_index(drop=True)


@st.cache_data
def get_sales() -> pd.DataFrame:
    """Mock des donnees DVF (fallback tant que DVF reel non branche)."""
    n_sales = 500
    dates = [datetime.today() - timedelta(days=np.random.randint(0, 365)) for _ in range(n_sales)]
    quartiers = np.random.choice(QUARTIERS, n_sales)
    surfaces = np.random.normal(65, 25, n_sales).clip(15, 200).astype(int)

    prix_m2 = [np.random.normal(BASE_PRICES[q], BASE_PRICES[q] * 0.1) for q in quartiers]
    prix = [int(s * p) for s, p in zip(surfaces, prix_m2)]

    df = pd.DataFrame(
        {
            "Date": dates,
            "Quartier": quartiers,
            "Surface (m²)": surfaces,
            "Prix (€)": prix,
            "Prix/m²": np.array(prix_m2).astype(int),
        }
    )
    return df.sort_values("Date", ascending=False)


@st.cache_data
def get_listings() -> pd.DataFrame:
    """Retourne les annonces reelles (CSV) avec fallback mock."""
    csv_path = detect_listings_csv_path()
    if csv_path:
        listings = load_listings_csv(csv_path)
        if not listings.empty:
            return listings

    return load_listings_mock()


@st.cache_data
def get_listings_metadata() -> Dict[str, object]:
    """Diagnostics pour la page Parametres."""
    csv_path = detect_listings_csv_path()
    using_csv = False

    detected_columns = []
    if csv_path:
        csv_file = Path(csv_path)
        try:
            csv_params = _detect_csv_params(csv_file)
            raw_df = pd.read_csv(csv_file, encoding=csv_params["encoding"], sep=csv_params["sep"], nrows=5)
            detected_columns = list(raw_df.columns)
        except Exception:
            detected_columns = []

        df = load_listings_csv(csv_path)
        using_csv = not df.empty
    else:
        df = load_listings_mock()

    if not using_csv and csv_path:
        # CSV trouve mais inexploitable
        source_name = "csv_vide"
    elif using_csv:
        source_name = "csv"
    else:
        source_name = "mock"

    date_min = None
    date_max = None
    if "date_ajout" in df.columns and df["date_ajout"].notna().any():
        date_min = pd.to_datetime(df["date_ajout"], errors="coerce").min()
        date_max = pd.to_datetime(df["date_ajout"], errors="coerce").max()

    return {
        "source": source_name,
        "csv_path": csv_path or "",
        "rows": int(len(df)),
        "columns": list(df.columns),
        "detected_columns": detected_columns,
        "date_min": date_min,
        "date_max": date_max,
    }


@st.cache_data
def get_trends() -> pd.DataFrame:
    """Compat legacy: courbe mock si necessaire."""
    dates = pd.date_range(start="2021-01-01", end="2026-01-01", freq="MS")
    data = {"Date": dates}
    for q, base_p in BASE_PRICES.items():
        trend = np.cumsum(np.random.normal(4, 15, len(dates)))
        data[q] = (base_p * 0.85 + trend).astype(int)
    data["Toulon (Global)"] = np.mean([data[q] for q in QUARTIERS], axis=0).astype(int)
    return pd.DataFrame(data)
