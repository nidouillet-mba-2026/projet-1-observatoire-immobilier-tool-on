"""
Scoring des biens immobiliers.

Objectif :
- comparer prix predit vs prix annonce
- identifier les opportunites
- classifier les biens :
    * opportunite
    * prix_marche
    * surevalue
- extraire quelques informations utiles depuis la description
"""

import re
from analysis.regression import predict


def safe_float(value, default=0.0) -> float:
    """Convertit une valeur en float de maniere defensive."""
    try:
        if value is None:
            return float(default)
        if isinstance(value, str):
            value = value.replace("€", "").replace(" ", "").replace(",", ".")
        return float(value)
    except (ValueError, TypeError):
        return float(default)


def price_difference(predicted_price: float, listed_price: float) -> float:
    """
    Retourne l'ecart absolu :
    prix_annonce - prix_predit
    Negatif = annonce moins chere que prevu
    Positif = annonce plus chere que prevu
    """
    predicted_price = safe_float(predicted_price)
    listed_price = safe_float(listed_price)
    return listed_price - predicted_price


def price_difference_pct(predicted_price: float, listed_price: float) -> float:
    """
    Retourne l'ecart relatif en pourcentage :
    ((prix_annonce - prix_predit) / prix_predit) * 100

    Negatif = sous le prix predit
    Positif = au-dessus du prix predit
    """
    predicted_price = safe_float(predicted_price)
    listed_price = safe_float(listed_price)

    if predicted_price <= 0:
        return 0.0

    return ((listed_price - predicted_price) / predicted_price) * 100


def classify_listing(
    predicted_price: float,
    listed_price: float,
    opportunity_threshold: float = -8.0,
    overpriced_threshold: float = 8.0,
) -> str:
    """
    Classe un bien selon l'ecart relatif entre prix predit et prix annonce.
    """
    predicted_price = safe_float(predicted_price)
    listed_price = safe_float(listed_price)

    if predicted_price <= 0:
        return "inclassable"

    gap_pct = price_difference_pct(predicted_price, listed_price)

    if gap_pct <= opportunity_threshold:
        return "opportunite"
    elif gap_pct >= overpriced_threshold:
        return "surevalue"
    else:
        return "prix_marche"


def opportunity_score(predicted_price: float, listed_price: float) -> float:
    """
    Score d'opportunite sur 100.
    50 = neutre
    > 50 = interessant
    < 50 = moins interessant
    """
    gap_pct = price_difference_pct(predicted_price, listed_price)

    score = 50 - gap_pct

    if score < 0:
        return 0.0
    if score > 100:
        return 100.0
    return round(score, 2)


def is_opportunity(predicted_price: float, listed_price: float, threshold: float = -8.0) -> bool:
    """Retourne True si le bien est considere comme une opportunite."""
    return price_difference_pct(predicted_price, listed_price) <= threshold


def extract_features_from_description(description: str) -> dict:
    """
    Extrait quelques informations simples depuis la description.
    Version legere sans IA externe, basee sur des mots-cles.
    """
    if not description:
        description = ""

    text = description.lower()

    features = {
        "parking": False,
        "garage": False,
        "balcon": False,
        "terrasse": False,
        "ascenseur": False,
        "vue_mer": False,
        "etage": None,
        "dernier_etage": False,
        "travaux": False,
        "renove": False,
        "lumineux": False,
        "calme": False,
        "piscine": False,
    }

    parking_keywords = ["parking", "stationnement", "place de parking"]
    garage_keywords = ["garage", "box ferme", "box fermé", "box"]
    balcon_keywords = ["balcon"]
    terrasse_keywords = ["terrasse"]
    ascenseur_keywords = ["ascenseur"]
    vue_mer_keywords = ["vue mer", "aperçu mer", "apercu mer", "vue sur mer"]
    travaux_keywords = ["travaux", "a renover", "à rénover", "renovation", "rafraichir", "rafraîchir"]
    renove_keywords = ["renove", "rénové", "refait a neuf", "refait à neuf", "neuf"]
    lumineux_keywords = ["lumineux", "lumineuse", "belle luminosite", "belle luminosité"]
    calme_keywords = ["calme", "sans vis-a-vis", "sans vis-à-vis"]
    piscine_keywords = ["piscine"]

    features["parking"] = any(word in text for word in parking_keywords)
    features["garage"] = any(word in text for word in garage_keywords)
    features["balcon"] = any(word in text for word in balcon_keywords)
    features["terrasse"] = any(word in text for word in terrasse_keywords)
    features["ascenseur"] = any(word in text for word in ascenseur_keywords)
    features["vue_mer"] = any(word in text for word in vue_mer_keywords)
    features["travaux"] = any(word in text for word in travaux_keywords)
    features["renove"] = any(word in text for word in renove_keywords)
    features["lumineux"] = any(word in text for word in lumineux_keywords)
    features["calme"] = any(word in text for word in calme_keywords)
    features["piscine"] = any(word in text for word in piscine_keywords)
    features["dernier_etage"] = "dernier etage" in text or "dernier étage" in text

    patterns = [
        r"(\d+)\s*e?\s*etage",
        r"(\d+)\s*e?\s*étage",
        r"au\s+(\d+)\s*e?\s*etage",
        r"au\s+(\d+)\s*e?\s*étage",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                features["etage"] = int(match.group(1))
                break
            except ValueError:
                pass

    return features


def generate_listing_insight(predicted_price: float, listed_price: float, description: str = "") -> str:
    """
    Genere un court commentaire utile pour un conseiller immobilier.
    """
    category = classify_listing(predicted_price, listed_price)
    gap_pct = round(price_difference_pct(predicted_price, listed_price), 2)
    features = extract_features_from_description(description)

    extras = []
    if features["vue_mer"]:
        extras.append("vue mer")
    if features["terrasse"]:
        extras.append("terrasse")
    if features["balcon"]:
        extras.append("balcon")
    if features["parking"]:
        extras.append("parking")
    if features["garage"]:
        extras.append("garage")
    if features["ascenseur"]:
        extras.append("ascenseur")
    if features["renove"]:
        extras.append("bien renove")
    if features["travaux"]:
        extras.append("travaux a prevoir")

    extras_text = ""
    if extras:
        extras_text = " Atouts/indices detectes : " + ", ".join(extras) + "."

    if category == "opportunite":
        return (
            f"Bien affiche environ {abs(gap_pct)}% sous le prix estime : opportunite interessante."
            f"{extras_text}"
        )
    elif category == "surevalue":
        return (
            f"Bien affiche environ {abs(gap_pct)}% au-dessus du prix estime : prix potentiellement surevalue."
            f"{extras_text}"
        )
    elif category == "prix_marche":
        return (
            f"Bien affiche dans une zone proche du prix estime ({gap_pct}% d'ecart) : prix coherent avec le marche."
            f"{extras_text}"
        )
    else:
        return "Impossible de classifier ce bien de maniere fiable."


def score_bien(prix, surface, nb_pieces=0, proximite_mer=None):
    """
    Calcule un score global entre 0 et 100 pour un bien immobilier.
    Conservee pour rester compatible avec les tests.
    """
    prix = safe_float(prix)
    surface = safe_float(surface)
    nb_pieces = safe_float(nb_pieces, 0)

    if surface <= 0:
        prix_m2 = 0.0
    else:
        prix_m2 = prix / surface

    if prix_m2 <= 0:
        score_prix = 0.0
    else:
        score_prix = max(0.0, 100.0 - (prix_m2 / 50.0))

    score_surface = min(100.0, surface / 2.0)
    score_pieces = min(100.0, nb_pieces * 20.0)

    if proximite_mer is None:
        score_mer = 50.0
    else:
        proximite_mer = safe_float(proximite_mer, 0)
        score_mer = max(0.0, 100.0 - proximite_mer * 10.0)

    score = (
        score_prix * 0.4 +
        score_surface * 0.3 +
        score_pieces * 0.1 +
        score_mer * 0.2
    )

    return round(score, 2)


def classer_biens(biens):
    """
    Classe une liste de biens immobiliers selon leur score global.
    """
    biens_scored = []

    for bien in biens:
        score = score_bien(
            prix=bien.get("prix", 0),
            surface=bien.get("surface", 0),
            nb_pieces=bien.get("nb_pieces", 0),
            proximite_mer=bien.get("proximite_mer", None),
        )
        biens_scored.append({**bien, "score": score})

    return sorted(biens_scored, key=lambda x: x["score"], reverse=True)


def enrich_listing_with_model(listing: dict, alpha: float, beta: float) -> dict:
    """
    Enrichit une annonce avec :
    - prix estime
    - ecart absolu
    - ecart relatif en %
    - categorie
    - score d'opportunite
    - insight
    """
    surface = safe_float(listing.get("surface", 0))
    listed_price = safe_float(listing.get("prix", listing.get("price", 0)))
    description = listing.get("description", "")

    predicted_price = predict(alpha, beta, surface)

    return {
        **listing,
        "prix_estime": round(predicted_price, 2),
        "ecart_absolu": round(price_difference(predicted_price, listed_price), 2),
        "ecart_pct": round(price_difference_pct(predicted_price, listed_price), 2),
        "categorie": classify_listing(predicted_price, listed_price),
        "score_opportunite": opportunity_score(predicted_price, listed_price),
        "insight": generate_listing_insight(predicted_price, listed_price, description),
        "infos_description": extract_features_from_description(description),
    }