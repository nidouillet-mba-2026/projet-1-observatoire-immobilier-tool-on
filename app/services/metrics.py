from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from app.config import DEFAULT_PERIOD
from app.services.data_provider import get_listings, get_sales


def _period_timedelta(period_str: str) -> Optional[timedelta]:
    if period_str == "30 derniers jours":
        return timedelta(days=30)
    if period_str == "3 derniers mois":
        return timedelta(days=90)
    if period_str == "12 derniers mois":
        return timedelta(days=365)
    return None


def filter_by_period(df: pd.DataFrame, date_col: str, period_str: str = DEFAULT_PERIOD) -> pd.DataFrame:
    """Filtre un DataFrame selon la periode UI."""
    if df.empty or date_col not in df.columns:
        return df

    now = datetime.now()
    date_values = pd.to_datetime(df[date_col])

    if period_str == "Année en cours":
        limit = datetime(now.year, 1, 1)
    else:
        delta = _period_timedelta(period_str)
        if delta is None:
            return df
        limit = now - delta

    return df[date_values >= limit].copy()


def _window_bounds(period_str: str) -> tuple[datetime, datetime, datetime, datetime]:
    now = datetime.now()

    if period_str == "Année en cours":
        current_start = datetime(now.year, 1, 1)
        current_end = now
        previous_start = datetime(now.year - 1, 1, 1)
        previous_end = datetime(now.year - 1, now.month, min(now.day, 28), now.hour, now.minute, now.second)
        return current_start, current_end, previous_start, previous_end

    delta = _period_timedelta(period_str) or timedelta(days=365)
    current_start = now - delta
    current_end = now
    previous_start = current_start - delta
    previous_end = current_start
    return current_start, current_end, previous_start, previous_end


def _variation_pct(current_value: float, previous_value: float) -> float:
    if previous_value <= 0:
        return 0.0
    return round(((current_value - previous_value) / previous_value) * 100, 1)


def get_kpis(period_str: str = DEFAULT_PERIOD) -> dict:
    sales_df = get_sales().copy()
    listings_df = get_listings().copy()

    sales_df["Date"] = pd.to_datetime(sales_df["Date"])
    listings_df["Date Ajout"] = pd.to_datetime(listings_df["Date Ajout"])

    current_start, current_end, previous_start, previous_end = _window_bounds(period_str)

    current_sales = sales_df[(sales_df["Date"] >= current_start) & (sales_df["Date"] <= current_end)]
    previous_sales = sales_df[(sales_df["Date"] >= previous_start) & (sales_df["Date"] < previous_end)]

    current_listings = listings_df[
        (listings_df["Date Ajout"] >= current_start) & (listings_df["Date Ajout"] <= current_end)
    ]
    previous_listings = listings_df[
        (listings_df["Date Ajout"] >= previous_start) & (listings_df["Date Ajout"] < previous_end)
    ]

    current_median = int(current_sales["Prix/m²"].median()) if not current_sales.empty else 0
    previous_median = int(previous_sales["Prix/m²"].median()) if not previous_sales.empty else 0

    return {
        "ventes_dvf": len(current_sales),
        "annonces_actives": len(current_listings),
        "prix_median": current_median,
        "delai_vente": 45,
        "trend_ventes": _variation_pct(len(current_sales), len(previous_sales)),
        "trend_annonces": _variation_pct(len(current_listings), len(previous_listings)),
        "trend_prix": _variation_pct(current_median, previous_median),
        "trend_delai": -3.2,
    }


def build_market_summary(sales_df: pd.DataFrame) -> pd.DataFrame:
    if sales_df.empty:
        return pd.DataFrame(columns=["Quartier", "Volume", "Prix médian", "Prix moyen"])

    summary = (
        sales_df.groupby("Quartier")
        .agg(
            Volume=("Prix (€)", "count"),
            prix_median=("Prix/m²", "median"),
            prix_moyen=("Prix/m²", "mean"),
        )
        .reset_index()
        .rename(columns={"prix_median": "Prix médian", "prix_moyen": "Prix moyen"})
    )

    summary["Prix médian"] = summary["Prix médian"].round(0).astype(int)
    summary["Prix moyen"] = summary["Prix moyen"].round(0).astype(int)
    return summary.sort_values("Volume", ascending=False)


def compute_trend_insights(trends_df: pd.DataFrame, series_name: str) -> dict:
    if trends_df.empty or series_name not in trends_df.columns:
        return {"latest": 0, "yoy_pct": 0.0, "delta_abs": 0}

    ordered = trends_df.sort_values("Date").copy()
    latest = float(ordered[series_name].iloc[-1])

    if len(ordered) > 12:
        previous = float(ordered[series_name].iloc[-13])
    else:
        previous = float(ordered[series_name].iloc[0])

    yoy_pct = _variation_pct(latest, previous)
    delta_abs = int(round(latest - previous))

    return {"latest": int(round(latest)), "yoy_pct": yoy_pct, "delta_abs": delta_abs}
