import re
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.pap.fr"
SEARCH_URLS = [
    "https://www.pap.fr/annonce/vente-immobiliere-toulon-83-g43624",
    "https://www.pap.fr/annonce/vente-immobilier-toulon-83-g43624-2",
    "https://www.pap.fr/annonce/vente-immobilier-particulier-toulon-83-g43624-4",
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def extract_price(text: str):
    if not text:
        return None
    m = re.search(r"(\d[\d\s.]*)\s*€", text)
    if not m:
        return None
    value = m.group(1).replace(" ", "").replace(".", "")
    try:
        return int(value)
    except ValueError:
        return None

def extract_surface(text: str):
    if not text:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m²", text, re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None

def extract_rooms(text: str):
    if not text:
        return None
    m = re.search(r"(\d+)\s*pi[eè]ces?", text, re.IGNORECASE)
    return int(m.group(1)) if m else None

def get_page_html(page, url: str) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    return page.content()

def extract_listing_links_from_results(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/annonces/" in href or "/annonce/" in href:
            if href.startswith("http"):
                full_url = href
            else:
                full_url = BASE_URL + href
            links.add(full_url.split("?")[0])

    return sorted(links)

def extract_listing_data(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    page_text = clean_text(soup.get_text(" ", strip=True))

    h1 = soup.find("h1")
    title = clean_text(h1.get_text()) if h1 else ""

    price = extract_price(page_text)
    surface = extract_surface(page_text)
    pieces = extract_rooms(page_text)

    type_bien = ""
    lower = page_text.lower()
    if "appartement" in lower:
        type_bien = "Appartement"
    elif "maison" in lower:
        type_bien = "Maison"
    elif "studio" in lower:
        type_bien = "Studio"

    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = clean_text(meta_desc["content"])
    else:
        paragraphs = soup.find_all("p")
        description = clean_text(" ".join(p.get_text(" ", strip=True) for p in paragraphs[:5]))

    prix_m2 = round(price / surface, 2) if price and surface and surface > 0 else None

    return {
        "source": "PAP",
        "titre": title,
        "prix": price,
        "surface_m2": surface,
        "prix_m2": prix_m2,
        "ville": "Toulon" if "Toulon" in page_text else "",
        "quartier": "",
        "type_bien": type_bien,
        "pieces": pieces,
        "description": description,
        "url": url,
        "date_collecte": datetime.today().strftime("%Y-%m-%d"),
    }

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
        )
        page = context.new_page()

        all_links = set()

        for url in SEARCH_URLS:
            print(f"Résultats : {url}")
            html = get_page_html(page, url)
            links = extract_listing_links_from_results(html)
            print(f"  -> {len(links)} liens trouvés")
            all_links.update(links)
            time.sleep(random.uniform(2, 4))

        all_links = sorted(all_links)
        print(f"Total liens uniques : {len(all_links)}")

        rows = []
        for i, link in enumerate(all_links, start=1):
            try:
                print(f"[{i}/{len(all_links)}] {link}")
                html = get_page_html(page, link)
                row = extract_listing_data(html, link)
                if row["prix"] and row["surface_m2"]:
                    rows.append(row)
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"Erreur sur {link}: {e}")

        browser.close()

    df = pd.DataFrame(rows).drop_duplicates(subset=["url"])
    df = df[df["prix"].notna()]
    df = df[df["surface_m2"].notna()]
    df = df[df["prix"] <= 500000]

    df["parking"] = df["description"].fillna("").str.contains("parking", case=False)
    df["balcon"] = df["description"].fillna("").str.contains("balcon", case=False)
    df["terrasse"] = df["description"].fillna("").str.contains("terrasse", case=False)
    df["vue_mer"] = df["description"].fillna("").str.contains("vue mer", case=False)
    df["ascenseur"] = df["description"].fillna("").str.contains("ascenseur", case=False)

    output_path = "data/annonces_pap.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"CSV sauvegardé : {output_path}")
    print(df.head())
    print(df.shape)

if __name__ == "__main__":
    main()