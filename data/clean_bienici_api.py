import os
import pandas as pd
import numpy as np


BASE_DIR = os.path.dirname(__file__)
INPUT_FILE = os.path.join(BASE_DIR, "annonces_bienici_api_toulon.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "annonces_bienici_clean.csv")


PROPERTY_TYPE_MAP = {
    "flat": "Appartement",
    "house": "Maison",
    "loft": "Loft",
    "castle": "Château",
    "townhouse": "Maison de ville",
}


def clean_text(value, max_len=None):
    if pd.isna(value):
        return None
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    text = " ".join(text.split())
    if max_len:
        return text[:max_len]
    return text


def main():
    df = pd.read_csv(INPUT_FILE)

    # 1. Sélection des colonnes utiles
    cols_to_keep = [
        "id",
        "title",
        "description",
        "price",
        "surface_m2",
        "price_m2",
        "rooms",
        "bedrooms",
        "bathrooms",
        "property_type",
        "city",
        "postal_code",
        "district_name",
        "has_balcony",
        "has_terrace",
        "has_garden",
        "has_elevator",
        "has_cellar",
        "parking_places",
        "floor",
        "floor_quantity",
        "land_surface_m2",
        "energy_class",
        "ghg_class",
        "publication_date",
        "modification_date",
        "fees_charged_to",
        "price_without_fees",
        "new_property",
        "account_type",
        "ad_created_by_pro",
        "url",
    ]

    existing_cols = [col for col in cols_to_keep if col in df.columns]
    df = df[existing_cols].copy()

    # 2. Renommage en français
    rename_map = {
        "id": "id_annonce",
        "title": "titre",
        "description": "description",
        "price": "prix",
        "surface_m2": "surface_m2",
        "price_m2": "prix_m2",
        "rooms": "pieces",
        "bedrooms": "chambres",
        "bathrooms": "salles_de_bain",
        "property_type": "type_bien",
        "city": "ville",
        "postal_code": "code_postal",
        "district_name": "quartier",
        "has_balcony": "balcon",
        "has_terrace": "terrasse",
        "has_garden": "jardin",
        "has_elevator": "ascenseur",
        "has_cellar": "cave",
        "parking_places": "nb_parkings",
        "floor": "etage",
        "floor_quantity": "nb_etages_immeuble",
        "land_surface_m2": "surface_terrain_m2",
        "energy_class": "classe_energie",
        "ghg_class": "classe_ges",
        "publication_date": "date_publication",
        "modification_date": "date_modification",
        "fees_charged_to": "frais_a_charge",
        "price_without_fees": "prix_hors_frais",
        "new_property": "bien_neuf",
        "account_type": "type_compte",
        "ad_created_by_pro": "annonce_pro",
        "url": "url",
    }
    df.rename(columns=rename_map, inplace=True)

    # 3. Nettoyage texte
    if "titre" in df.columns:
        df["titre"] = df["titre"].apply(lambda x: clean_text(x, max_len=120))

    if "description" in df.columns:
        df["description"] = df["description"].apply(lambda x: clean_text(x, max_len=500))

    # 4. Standardisation type de bien
    if "type_bien" in df.columns:
        df["type_bien"] = df["type_bien"].map(PROPERTY_TYPE_MAP).fillna(df["type_bien"])

    # 5. Nettoyage numérique
    numeric_cols = [
        "prix",
        "surface_m2",
        "prix_m2",
        "pieces",
        "chambres",
        "salles_de_bain",
        "nb_parkings",
        "etage",
        "nb_etages_immeuble",
        "surface_terrain_m2",
        "prix_hors_frais",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6. Nettoyage booléens
    bool_cols = [
        "balcon",
        "terrasse",
        "jardin",
        "ascenseur",
        "cave",
        "bien_neuf",
        "annonce_pro",
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    # 7. Filtrage utile pour le projet
    if "ville" in df.columns:
        df = df[df["ville"].fillna("").str.lower() == "toulon"]

    if "prix" in df.columns:
        df = df[df["prix"].notna()]
        df = df[df["prix"] > 0]

    if "surface_m2" in df.columns:
        df = df[df["surface_m2"].notna()]
        df = df[df["surface_m2"] > 0]

    # Budget NidDouillet : max 450k
    if "prix" in df.columns:
        df = df[df["prix"] <= 450000]

    # Garder maisons/appartements principalement
    if "type_bien" in df.columns:
        df = df[df["type_bien"].isin(["Appartement", "Maison", "Loft", "Maison de ville"])]

    # 8. Recalcul du prix/m² si besoin
    if {"prix", "surface_m2", "prix_m2"}.issubset(df.columns):
        df["prix_m2"] = np.where(
            (df["prix"].notna()) & (df["surface_m2"].notna()) & (df["surface_m2"] > 0),
            (df["prix"] / df["surface_m2"]).round(2),
            np.nan,
        )

    # 9. Suppression doublons
    if "id_annonce" in df.columns:
        df.drop_duplicates(subset=["id_annonce"], inplace=True)
    elif "url" in df.columns:
        df.drop_duplicates(subset=["url"], inplace=True)

    # 10. Tri lisible
    sort_cols = [c for c in ["quartier", "prix"] if c in df.columns]
    if sort_cols:
        df.sort_values(sort_cols, inplace=True)

    # 11. Export
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"CSV nettoyé sauvegardé : {OUTPUT_FILE}")
    print(df.head())
    print(df.shape)


if __name__ == "__main__":
    main()