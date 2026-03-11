from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

CSV_PATHS = [
    Path("data/annonces_actuelles.csv"),
    Path("donnees/annonces_actuelles.csv"),
    Path("annonces_actuelles.csv"),
]


def _locate_csv_path() -> Optional[Path]:
    for candidate in CSV_PATHS:
        if candidate.exists():
            return candidate
    return None


@st.cache_data
def load_listings() -> pd.DataFrame:
    path = _locate_csv_path()
    if path is None:
        return pd.DataFrame()

    for encoding in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(path, sep=";", encoding=encoding)
            break
        except Exception:
            continue
    else:
        return pd.DataFrame()

    for column in ("prix", "surface_m2", "prix_m2"):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        else:
            df[column] = pd.NA

    if {"prix", "surface_m2", "prix_m2"}.issubset(df.columns):
        missing = df["prix_m2"].isna() & df["prix"].gt(0) & df["surface_m2"].gt(0)
        df.loc[missing, "prix_m2"] = df.loc[missing, "prix"] / df.loc[missing, "surface_m2"]

    mask = (df["prix"] > 0) & (df["surface_m2"] > 0)
    df = df[mask].copy()

    if "quartier" in df.columns:
        df["quartier"] = df["quartier"].fillna("Inconnu").astype(str)
    else:
        df["quartier"] = "Inconnu"

    if "id_annonce" not in df.columns:
        df["id_annonce"] = df.index.astype(str)

    return df


def get_listings_csv_path() -> Optional[str]:
    path = _locate_csv_path()
    return str(path) if path is not None else None
