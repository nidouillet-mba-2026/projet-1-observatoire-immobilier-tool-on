import re
import time
import pandas as pd
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.bienici.com"
SEARCH_URL = "https://www.bienici.com/recherche/achat/toulon-83000"


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def extract_price(text: str):
    match = re.search(r"(\d[\d\s]*)\s*€", text)
    if not match:
        return None
    try:
        return int(match.group(1).replace(" ", ""))
    except ValueError:
        return None


def extract_surface(text: str):
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*m²", text, re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def extract_pieces(text: str):
    match = re.search(r"(\d+)\s*pi[eè]ces?", text, re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def extract_chambres(text: str):
    match = re.search(r"(\d+)\s*chambres?", text, re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def extract_quartier(text: str) -> str:
    match = re.search(r"Toulon\s*\(([^)]+)\)", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def detect_type(text: str) -> str:
    t = text.lower()
    if "appartement" in t:
        return "Appartement"
    if "maison" in t:
        return "Maison"
    if "studio" in t:
        return "Studio"
    return ""


def has_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in (text or "").lower()


def scroll_until_no_new_cards(page, card_selector="article.ad-overview", max_rounds=30, pause_ms=2000):
    previous_count = 0
    stable_rounds = 0

    for round_idx in range(max_rounds):
        current_count = page.locator(card_selector).count()
        print(f"[Scroll {round_idx+1}] cartes détectées : {current_count}")

        if current_count == previous_count:
            stable_rounds += 1
        else:
            stable_rounds = 0

        if stable_rounds >= 3:
            print("Le nombre de cartes ne bouge plus, arrêt du scroll.")
            break

        previous_count = current_count

        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(pause_ms)


def scrape_result_cards(page):
    page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    scroll_until_no_new_cards(page, card_selector="article.ad-overview", max_rounds=40, pause_ms=2200)

    cards = page.locator("article.ad-overview")
    count = cards.count()
    print(f"Nombre de cartes détectées : {count}")

    rows = []

    for i in range(count):
        try:
            card = cards.nth(i)
            card_text = clean_text(card.inner_text())

            link_locator = card.locator("a.detailedSheetLink").first
            href = link_locator.get_attribute("href")
            if not href:
                continue

            url = urljoin(BASE_URL, href)

            price = extract_price(card_text)
            surface = extract_surface(card_text)
            pieces = extract_pieces(card_text)
            quartier = extract_quartier(card_text)
            type_bien = detect_type(card_text)

            prix_m2 = None
            if price and surface and surface > 0:
                prix_m2 = round(price / surface, 2)

            rows.append({
                "source": "Bienici",
                "titre": card_text[:120],
                "prix": price,
                "surface_m2": surface,
                "prix_m2": prix_m2,
                "pieces": pieces,
                "type_bien": type_bien,
                "ville": "Toulon",
                "quartier": quartier,
                "description_carte": card_text,
                "url": url,
            })

        except Exception as e:
            print(f"Erreur carte {i}: {e}")

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(subset=["url"])
        df = df[df["prix"].notna()]
        df = df[df["surface_m2"].notna()]

    return df


def scrape_detail_page(page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)

    full_text = clean_text(page.locator("body").inner_text())

    description = ""
    try:
        description = clean_text(page.locator("body").inner_text())
    except:
        description = full_text

    chambres = extract_chambres(full_text)

    dpe = ""
    dpe_match = re.search(r"\bDPE\b\s*([A-G])", full_text, re.IGNORECASE)
    if dpe_match:
        dpe = dpe_match.group(1).upper()

    agence = ""
    try:
        agence = clean_text(page.locator("body").inner_text()[:300])
    except:
        agence = ""

    return {
        "description": description[:3000],
        "chambres": chambres,
        "parking": has_keyword(full_text, "parking"),
        "balcon": has_keyword(full_text, "balcon"),
        "terrasse": has_keyword(full_text, "terrasse"),
        "ascenseur": has_keyword(full_text, "ascenseur"),
        "vue_mer": has_keyword(full_text, "vue mer"),
        "jardin": has_keyword(full_text, "jardin"),
        "piscine": has_keyword(full_text, "piscine"),
        "dpe": dpe,
        "agence_hint": agence,
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
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()

        print(f"Ouverture : {SEARCH_URL}")
        df = scrape_result_cards(page)

        print(f"{len(df)} annonces de base récupérées")

        detail_rows = []
        for i, row in df.iterrows():
            try:
                print(f"[{i+1}/{len(df)}] {row['url']}")
                details = scrape_detail_page(page, row["url"])
                merged = {**row.to_dict(), **details}
                detail_rows.append(merged)
                time.sleep(2)
            except Exception as e:
                print(f"Erreur détail sur {row['url']}: {e}")
                detail_rows.append(row.to_dict())

        browser.close()

    final_df = pd.DataFrame(detail_rows)

    output_path = "data/annonces_bienici_details.csv"
    final_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"CSV sauvegardé : {output_path}")
    print(final_df.head())
    print(final_df.shape)


if __name__ == "__main__":
    main()