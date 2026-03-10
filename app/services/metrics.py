from datetime import datetime, timedelta
from typing import Optional, Tuple

import pandas as pd

from app.config import DEFAULT_PERIOD
from app.services.data_provider import get_listings, get_listings_metadata, get_sales


def _period_timedelta(period_str: str) -> Optional[timedelta]:
    if period_str == "30 derniers jours":
        return timedelta(days=30)
    if period_str == "3 derniers mois":
        return timedelta(days=90)
    if period_str == "12 derniers mois":
        return timedelta(days=365)
    return None


def _window_bounds(period_str: str) -> Tuple[datetime, datetime, datetime, datetime]:
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


def get_data_status(
    listings_df: pd.DataFrame,
    sales_df: Optional[pd.DataFrame] = None,
    trends_df: Optional[pd.DataFrame] = None,
    listings_metadata: Optional[dict] = None,
) -> dict:
    """Retourne un état des sources pour activer ou masquer les métriques."""
    status = {
        "has_real_listings": False,
        "has_dates": False,
        "has_quartier": False,
        "has_dvf": False,
        "has_trends": False,
        "score_ready": False,
        "score_source": "Listings",
    }

    if listings_metadata and listings_metadata.get("source") == "csv" and not listings_df.empty:
        status["has_real_listings"] = True

    if "date_ajout" in listings_df.columns and not listings_df["date_ajout"].empty:
        notna_pct = listings_df["date_ajout"].notna().mean()
        status["has_dates"] = notna_pct >= 0.3

    if "quartier" in listings_df.columns and not listings_df["quartier"].empty:
        notna_pct = listings_df["quartier"].notna().mean()
        status["has_quartier"] = notna_pct >= 0.5

    status["has_trends"] = bool(status["has_dates"] and trends_df is not None and not trends_df.empty)

    # TODO: détecter automatiquement un DVF réel vs mock lorsque la source est connectée
    status["has_dvf"] = False
    status["score_ready"] = status["has_quartier"] and (status["has_dvf"] or status["has_dates"])
    status["score_source"] = "DVF" if status["has_dvf"] else "Listings"
    return status


def filter_by_period(df: pd.DataFrame, date_col: str, period_str: str = DEFAULT_PERIOD) -> pd.DataFrame:
    """Filtre un DataFrame selon la periode UI. Retourne la source si date indisponible."""
    if df.empty or date_col not in df.columns:
        return df

    date_values = pd.to_datetime(df[date_col], errors="coerce")
    if date_values.notna().sum() == 0:
        return df

    now = datetime.now()
    if period_str == "Année en cours":
        limit = datetime(now.year, 1, 1)
    else:
        delta = _period_timedelta(period_str)
        if delta is None:
            return df
        limit = now - delta

    return df[date_values >= limit].copy()


def build_market_summary(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Resume marche depuis DVF (colonnes historiques)."""
    if sales_df.empty or "Quartier" not in sales_df.columns:
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


def build_listing_market_summary(listings_df: pd.DataFrame) -> pd.DataFrame:
    if listings_df.empty or "quartier" not in listings_df.columns:
        return pd.DataFrame(columns=["Quartier", "Annonces", "Prix médian", "Prix moyen"])

    summary = (
        listings_df.groupby("quartier")
        .agg(
            annonces=("id", "count"),
            prix_median=("prix_m2", "median"),
            prix_moyen=("prix_m2", "mean"),
        )
        .reset_index()
        .rename(columns={"quartier": "Quartier", "annonces": "Annonces", "prix_median": "Prix médian", "prix_moyen": "Prix moyen"})
    )

    summary["Prix médian"] = summary["Prix médian"].round(0).astype(int)
    summary["Prix moyen"] = summary["Prix moyen"].round(0).astype(int)
    return summary.sort_values("Annonces", ascending=False)


def compute_opportunity_scores(
    listings_df: pd.DataFrame,
    sales_df: Optional[pd.DataFrame] = None,
    status: Optional[dict] = None,
) -> pd.DataFrame:
    """Calcule un score 0..100 selon reference quartier (DVF prioritaire, sinon listings)."""
    if listings_df.empty:
        out = listings_df.copy()
        out["score_opportunite"] = []
        out["prix_reference_m2"] = []
        return out

    listings = listings_df.copy()
    listings["quartier"] = listings["quartier"].fillna("Inconnu").replace("", "Inconnu")

    status = status or get_data_status(listings, sales_df)
    if not status["score_ready"]:
        listings["score_opportunite"] = pd.Series(pd.NA, index=listings.index, dtype="Int64")
        listings["prix_reference_m2"] = pd.Series(pd.NA, index=listings.index, dtype="float")
        listings["score_source"] = status["score_source"]
        return listings

    ref_by_quartier = None
    if sales_df is not None and not sales_df.empty and {"Quartier", "Prix/m²"}.issubset(sales_df.columns):
        ref_by_quartier = sales_df.groupby("Quartier")["Prix/m²"].median()

    if ref_by_quartier is None or ref_by_quartier.empty:
        ref_by_quartier = listings.groupby("quartier")["prix_m2"].median()

    global_ref = float(listings["prix_m2"].median()) if listings["prix_m2"].notna().any() else 1.0

    listings["prix_reference_m2"] = listings["quartier"].map(ref_by_quartier)
    listings["prix_reference_m2"] = listings["prix_reference_m2"].fillna(global_ref)
    listings["prix_reference_m2"] = listings["prix_reference_m2"].where(listings["prix_reference_m2"] > 0, global_ref)

    raw_score = ((listings["prix_reference_m2"] - listings["prix_m2"]) / listings["prix_reference_m2"]) * 100
    listings["score_opportunite"] = raw_score.clip(lower=0, upper=100).round(0).astype(int)
    listings["score_source"] = status["score_source"]

    return listings


def build_listing_trend(listings_df: pd.DataFrame) -> pd.DataFrame:
    """Tendance mensuelle prix/m2 depuis les annonces reelles."""
    if listings_df.empty or "date_ajout" not in listings_df.columns:
        return pd.DataFrame(columns=["Date", "Prix m² médian", "Volume"])

    trend = listings_df.copy()
    trend["date_ajout"] = pd.to_datetime(trend["date_ajout"], errors="coerce")
    trend = trend[trend["date_ajout"].notna()].copy()
    if trend.empty:
        return pd.DataFrame(columns=["Date", "Prix m² médian", "Volume"])

    trend["Date"] = trend["date_ajout"].dt.to_period("M").dt.to_timestamp()
    out = (
        trend.groupby("Date")
        .agg(
            **{
                "Prix m² médian": ("prix_m2", "median"),
                "Volume": ("id", "count"),
            }
        )
        .reset_index()
        .sort_values("Date")
    )
    out["Prix m² médian"] = out["Prix m² médian"].round(0)
    return out


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


def get_kpis(
    period_str: str = DEFAULT_PERIOD,
    listings_metadata: Optional[dict] = None,
    trends_df: Optional[pd.DataFrame] = None,
) -> dict:
    """KPIs globaux: listings reels prioritaire, DVF en fallback/appoint."""
    listings_df = get_listings().copy()
    sales_df = get_sales().copy()

    listings_period = filter_by_period(listings_df, "date_ajout", period_str)
    sales_available = not sales_df.empty and {"Date", "Prix/m²"}.issubset(sales_df.columns)

    if sales_available:
        sales_period = filter_by_period(sales_df, "Date", period_str)
    else:
        sales_period = pd.DataFrame()

    dated_listings = listings_df.copy()
    dated_listings["date_ajout"] = pd.to_datetime(dated_listings["date_ajout"], errors="coerce")

    current_start, current_end, previous_start, previous_end = _window_bounds(period_str)
    current_listings = dated_listings[
        (dated_listings["date_ajout"] >= current_start) & (dated_listings["date_ajout"] <= current_end)
    ]
    previous_listings = dated_listings[
        (dated_listings["date_ajout"] >= previous_start) & (dated_listings["date_ajout"] < previous_end)
    ]

    current_median_listings = (
        float(current_listings["prix_m2"].median())
        if not current_listings.empty
        else float(listings_period["prix_m2"].median()) if not listings_period.empty else 0.0
    )

    # Proxy d'evolution: 30 jours glissants vs 30 jours precedents
    now = datetime.now()
    cur_30_start = now - timedelta(days=30)
    prev_30_start = now - timedelta(days=60)
    cur_30 = dated_listings[(dated_listings["date_ajout"] >= cur_30_start) & (dated_listings["date_ajout"] <= now)]
    prev_30 = dated_listings[
        (dated_listings["date_ajout"] >= prev_30_start) & (dated_listings["date_ajout"] < cur_30_start)
    ]
    current_median_30 = float(cur_30["prix_m2"].median()) if not cur_30.empty else 0.0
    previous_median_30 = float(prev_30["prix_m2"].median()) if not prev_30.empty else 0.0

    if sales_available and not sales_period.empty:
        prix_median = int(float(sales_period["Prix/m²"].median()))
    else:
        prix_median = int(round(current_median_listings)) if current_median_listings > 0 else 0

    metadata = listings_metadata or get_listings_metadata()
    trends = trends_df if (trends_df is not None and not trends_df.empty) else build_listing_trend(listings_df)
    status = get_data_status(listings_df, sales_df, trends_df=trends, listings_metadata=metadata)

    return {
        "ventes_dvf": int(len(sales_period)) if sales_available else 0,
        "dvf_loaded": bool(sales_available and not sales_period.empty),
        "annonces_actives": int(len(listings_period)),
        "prix_median": prix_median,
        "prix_source": "DVF" if status["has_dvf"] else "Listings",
        "delai_vente": 45 if status["has_dvf"] else None,
        "trend_ventes": 0.0,
        "trend_annonces": _variation_pct(len(current_listings), len(previous_listings)),
        "trend_prix": _variation_pct(current_median_30, previous_median_30) if status["has_dates"] else None,
        "trend_delai": 0.0,
        "data_status": status,
    }
