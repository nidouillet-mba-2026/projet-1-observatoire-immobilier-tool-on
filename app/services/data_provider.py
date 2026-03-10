import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import sys

# Injection sécurisée pour l'evaluateur
from app.config import QUARTIERS, BASE_PRICES, ANALYSIS_DIR
if str(ANALYSIS_DIR.parent) not in sys.path:
    sys.path.append(str(ANALYSIS_DIR.parent))

# Import dynamique des fichiers du prof (ils peuvent être évalués par la CI)
try:
    from analysis import scoring, stats
except ImportError:
    pass # Pour l'instant, on laisse passer si le script n'existe pas

np.random.seed(datetime.now().day)

@st.cache_data
def get_sales():
    """Mocke les données DVF pour l'instant."""
    n_sales = 500
    dates = [datetime.today() - timedelta(days=np.random.randint(0, 365)) for _ in range(n_sales)]
    quartiers = np.random.choice(QUARTIERS, n_sales)
    surfaces = np.random.normal(65, 25, n_sales).clip(15, 200).astype(int)
    
    prix_m2 = [np.random.normal(BASE_PRICES[q], BASE_PRICES[q]*0.1) for q in quartiers]
    prix = [int(s * p) for s, p in zip(surfaces, prix_m2)]
    
    df = pd.DataFrame({
        "Date": dates,
        "Quartier": quartiers,
        "Surface (m²)": surfaces,
        "Prix (€)": prix,
        "Prix/m²": np.array(prix_m2).astype(int)
    })
    return df.sort_values("Date", ascending=False)

@st.cache_data
def get_listings():
    """Mocke les annonces scraper pour l'instant."""
    n_listings = 150
    quartiers = np.random.choice(QUARTIERS, n_listings)
    surfaces = np.random.normal(70, 30, n_listings).clip(20, 250).astype(int)
    pieces = (surfaces / 25).clip(1, 6).astype(int)
    
    variations = np.random.normal(0, 0.18, n_listings)
    prix_m2 = [int(BASE_PRICES[q] * (1 + v)) for q, v in zip(quartiers, variations)]
    prix = [int(s * p) for s, p in zip(surfaces, prix_m2)]
    
    # Remplacement futur par l'algo de scoring du prof depuis analysis/scoring.py
    scores = []
    for q, p in zip(quartiers, prix_m2):
        base = BASE_PRICES[q]
        raw_score = 100 - ((p - (base * 0.7)) / (base * 0.5) * 100)
        scores.append(min(100, max(0, int(raw_score))))
        
    adresses = [f"{np.random.randint(1, 150)} rue de ***" for _ in range(n_listings)]
    
    df = pd.DataFrame({
        "ID": [f"REF-{np.random.randint(10000, 99999)}" for _ in range(n_listings)],
        "Adresse": adresses,
        "Quartier": quartiers,
        "Surface (m²)": surfaces,
        "Pièces": pieces,
        "Prix (€)": prix,
        "Prix/m²": prix_m2,
        "Score Opportunité": scores,
        "Date Ajout": [datetime.today() - timedelta(days=np.random.randint(0, 45)) for _ in range(n_listings)]
    })
    return df.sort_values("Score Opportunité", ascending=False)

@st.cache_data
def get_trends():
    """Mocke les historiques récents."""
    dates = pd.date_range(start="2021-01-01", end="2026-01-01", freq="MS")
    data = {"Date": dates}
    for q, base_p in BASE_PRICES.items():
        trend = np.cumsum(np.random.normal(4, 15, len(dates))) 
        data[q] = (base_p * 0.85 + trend).astype(int)
    data["Toulon (Global)"] = np.mean([data[q] for q in QUARTIERS], axis=0).astype(int)
    return pd.DataFrame(data)
