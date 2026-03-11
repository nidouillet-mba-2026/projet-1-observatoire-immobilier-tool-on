import json
import math
import os
import time
import pandas as pd
import requests

API_URL = "https://www.bienici.com/realEstateAds.json"

# IMPORTANT :
# Récupère ces 2 valeurs depuis ton navigateur si elles expirent
ACCESS_TOKEN = "12MfiMDpihXZCab8HtllJYAxVXc+baQXmWjoPNS2SQM=:69aea21eef075600b474b40a"
REQUEST_ID = "69aea21eef075600b474b40a"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.bienici.com/recherche/achat/toulon-83000",
    "X-Requested-With": "XMLHttpRequest",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY5YWVhMjFlZWYwNzU2MDBiNDc0YjQwYSIsImlzUmVnaXN0ZXJlZCI6ZmFsc2UsImlhdCI6MTc3MzEzMzQwMH0.nlE1wFiPStQKmRlijv8ItKWhex1hToA-vSOmnikPsAQ",
}

BASE_FILTERS = {
    "size": 24,
    "from": 0,
    "filterType": "buy",
    "propertyType": ["house", "flat", "loft", "castle", "townhouse"],
    "page": 1,
    "sortBy": "relevance",
    "sortOrder": "desc",
    "onTheMarket": [True],
    "zoneIdsByTypes": {
        "zoneIds": ["-35280"]
    }
}


def bool_to_int(value):
    return 1 if value else 0


def safe_get(dct, *keys, default=None):
    current = dct
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def fetch_page(page_num: int, page_size: int = 24):
    filters = BASE_FILTERS.copy()
    filters["size"] = page_size
    filters["from"] = (page_num - 1) * page_size
    filters["page"] = page_num

    params = {
        "filters": json.dumps(filters, separators=(",", ":")),
        "extensionType": "extendedIfNoResult",
        "enableGoogleStructuredDataAggregates": "true",
        "leadingCount": 2,
        "access_token": ACCESS_TOKEN,
        "id": REQUEST_ID,
    }

    response = requests.get(API_URL, headers=HEADERS, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def ad_to_row(ad: dict) -> dict:
    district = ad.get("district") or {}

    return {
        "id": ad.get("id"),
        "source": "Bienici",
        "title": ad.get("title"),
        "description": ad.get("description"),
        "price": ad.get("price"),
        "surface_m2": ad.get("surfaceArea"),
        "price_m2": ad.get("pricePerSquareMeter"),
        "rooms": ad.get("roomsQuantity"),
        "bedrooms": ad.get("bedroomsQuantity"),
        "bathrooms": ad.get("bathroomsQuantity"),
        "property_type": ad.get("propertyType"),
        "city": ad.get("city"),
        "postal_code": ad.get("postalCode"),
        "district_name": district.get("libelle"),
        "district_full_name": district.get("name"),
        "latitude_blur": safe_get(ad, "blurInfo", "position", "lat"),
        "longitude_blur": safe_get(ad, "blurInfo", "position", "lon"),
        "has_balcony": bool_to_int(ad.get("hasBalcony")),
        "has_terrace": bool_to_int(ad.get("hasTerrace")),
        "has_garden": bool_to_int(ad.get("hasGarden")),
        "has_elevator": bool_to_int(ad.get("hasElevator")),
        "has_cellar": bool_to_int(ad.get("hasCellar")),
        "parking_places": ad.get("parkingPlacesQuantity"),
        "floor": ad.get("floor"),
        "floor_quantity": ad.get("floorQuantity"),
        "land_surface_m2": ad.get("landSurfaceArea"),
        "heating": ad.get("heating"),
        "energy_class": ad.get("energyClassification"),
        "ghg_class": ad.get("greenhouseGazClassification"),
        "energy_value": ad.get("energyValue"),
        "ghg_value": ad.get("greenhouseGazValue"),
        "new_property": bool_to_int(ad.get("newProperty")),
        "account_type": ad.get("accountType"),
        "ad_created_by_pro": bool_to_int(ad.get("adCreatedByPro")),
        "publication_date": ad.get("publicationDate"),
        "modification_date": ad.get("modificationDate"),
        "on_the_market": bool_to_int(safe_get(ad, "status", "onTheMarket")),
        "is_highlighted": bool_to_int(safe_get(ad, "status", "highlighted")),
        "is_exclusive_sale_mandate": bool_to_int(ad.get("isExclusiveSaleMandate")),
        "fees_charged_to": ad.get("feesChargedTo"),
        "price_without_fees": ad.get("priceWithoutFees"),
        "reference": ad.get("reference"),
        "url": f"https://www.bienici.com/annonce/vente/toulon/{ad.get('propertyType','bien')}/{ad.get('id')}"
    }


def main():
    print("Récupération de la première page...")
    first_page = fetch_page(page_num=1, page_size=24)

    total = first_page.get("total", 0)
    per_page = first_page.get("perPage", 24)
    ads = first_page.get("realEstateAds", [])

    print(f"Total annoncé par l'API : {total}")
    print(f"Annonces par page : {per_page}")

    all_rows = [ad_to_row(ad) for ad in ads]

    total_pages = math.ceil(total / per_page)
    print(f"Nombre total de pages : {total_pages}")

    for page_num in range(2, total_pages + 1):
        try:
            print(f"Page {page_num}/{total_pages}")
            data = fetch_page(page_num=page_num, page_size=per_page)
            ads = data.get("realEstateAds", [])
            all_rows.extend(ad_to_row(ad) for ad in ads)
            time.sleep(0.4)
        except Exception as e:
            print(f"Erreur page {page_num}: {e}")

    df = pd.DataFrame(all_rows)

    if not df.empty:
        df = df.drop_duplicates(subset=["id"])
        df = df[df["city"].fillna("").str.lower().eq("toulon")]
        df = df[df["price"].notna()]
        df = df[df["surface_m2"].notna()]

    BASE_DIR = os.path.dirname(__file__)
    output_path = os.path.join(BASE_DIR, "annonces_bienici_api_toulon.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"CSV sauvegardé : {output_path}")
    print(df.head())
    print(df.shape)


if __name__ == "__main__":
    main()