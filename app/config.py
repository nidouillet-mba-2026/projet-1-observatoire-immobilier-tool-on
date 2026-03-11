from pathlib import Path

# Chemins de base dynamiques pour lier le Dashboard a l'analyse du prof
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ANALYSIS_DIR = BASE_DIR / "analysis"

# Source annonces reelles
LISTINGS_ENV_VAR = "LISTINGS_CSV_PATH"
LISTINGS_SEARCH_DIRS = [DATA_DIR, BASE_DIR]

QUARTIERS = [
    "Mourillon",
    "Haute Ville",
    "Le Port",
    "La Rode",
    "Cap Brun",
    "Pont du Las",
    "Les Routes",
]

BASE_PRICES = {
    "Mourillon": 4500,
    "Haute Ville": 2800,
    "Le Port": 3200,
    "La Rode": 3000,
    "Cap Brun": 5500,
    "Pont du Las": 2200,
    "Les Routes": 2500,
}

PERIOD_OPTIONS = [
    "30 derniers jours",
    "3 derniers mois",
    "12 derniers mois",
    "Année en cours",
]
DEFAULT_PERIOD = "12 derniers mois"

SEARCH_SORT_OPTIONS = [
    "Score Opportunité",
    "Prix croissant",
    "Surface décroissante",
]

DEFAULT_SETTINGS = {
    "theme": "light",
    "min_opportunity_score": 70,
    "rows_per_page": 12,
}
