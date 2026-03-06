"""
Module de scoring immobilier développé pour identifier les opportunités
sur le marché en combinant plusieurs critères métier :
- prix au m²
- surface
- nombre de pièces
- proximité de la mer

L'objectif est d'obtenir un score global (0 à 100) permettant de comparer
facilement plusieurs biens immobiliers.
"""

# On importe la fonction predict définie dans le module de régression
# qui permet d'estimer le prix d'un bien à partir de sa surface.
from analysis.regression import predict


def score_bien(prix, surface, nb_pieces, proximite_mer):
    """
    Calcule un score global entre 0 et 100 pour un bien immobilier.

    Le score repose sur plusieurs critères :
    - le prix au m² (plus il est bas, plus le bien est intéressant)
    - la surface
    - le nombre de pièces
    - la proximité de la mer

    Chaque critère est pondéré pour refléter son importance relative.
    """

    # Calcul du prix au m².
    # On protège aussi contre une division par zéro si la surface vaut 0.
    prix_m2 = prix / surface if surface > 0 else float("inf")

    # Score basé sur le prix : un prix au m² faible est considéré plus attractif.
    score_prix = max(0, 100 - (prix_m2 / 50))

    # Score basé sur la surface : plus la surface est grande, plus le score augmente.
    score_surface = min(100, surface / 2)

    # Score basé sur le nombre de pièces.
    score_pieces = min(100, nb_pieces * 20)

    # Score basé sur la proximité de la mer :
    # plus la distance est faible, plus le score est élevé.
    score_mer = max(0, 100 - proximite_mer * 10)

    # Combinaison pondérée des différents scores.
    score = (
        score_prix * 0.4 +
        score_surface * 0.3 +
        score_pieces * 0.1 +
        score_mer * 0.2
    )

    # On arrondit le score final à deux décimales pour plus de lisibilité.
    return round(score, 2)


def classifier_prix(prix_annonce, prix_estime):
    """
    Compare le prix d'une annonce avec le prix estimé par le modèle.

    Cette fonction permet de classer un bien en trois catégories :
    - opportunite : le prix est nettement inférieur au prix estimé
    - prix_marche : le prix est cohérent avec l'estimation
    - surevalue : le bien semble trop cher par rapport au modèle
    """

    # Si le modèle retourne une estimation non valide, on ne peut pas classer.
    if prix_estime <= 0:
        return "inclassable"

    # Calcul de l'écart relatif entre le prix annoncé et le prix estimé.
    ecart_relatif = (prix_annonce - prix_estime) / prix_estime

    # Si le prix est au moins 10% inférieur au prix estimé → opportunité.
    if ecart_relatif <= -0.10:
        return "opportunite"

    # Si l'écart est dans une marge de ±10% → prix du marché.
    elif ecart_relatif <= 0.10:
        return "prix_marche"

    # Sinon le bien est considéré comme surévalué.
    else:
        return "surevalue"


def expliquer_categorie(categorie):
    """
    Retourne une explication simple de la catégorie attribuée au bien.

    Cette fonction permet d'ajouter une interprétation métier directement
    exploitable dans le dashboard ou lors de l'analyse.
    """

    if categorie == "opportunite":
        return "Prix inférieur à l'estimation du modèle : bien potentiellement sous-évalué."
    elif categorie == "prix_marche":
        return "Prix cohérent avec l'estimation du modèle."
    elif categorie == "surevalue":
        return "Prix supérieur à l'estimation du modèle : bien potentiellement surévalué."
    else:
        return "Catégorie non déterminée."


def enrichir_bien_avec_modele(bien, alpha, beta):
    """
    Enrichit un bien immobilier avec des informations supplémentaires
    issues du modèle de régression.

    On ajoute :
    - le prix estimé à partir de la surface
    - la catégorie métier (opportunité, marché, surévalué)
    - une explication simple de cette catégorie
    - le score global du bien
    """

    # Estimation du prix à partir du modèle de régression linéaire.
    prix_estime = predict(alpha, beta, bien["surface"])

    # Calcul du score global du bien.
    score = score_bien(
        bien["prix"],
        bien["surface"],
        bien["nb_pieces"],
        bien["proximite_mer"]
    )

    # Classification du bien en fonction de l'écart entre prix réel et estimé.
    categorie = classifier_prix(bien["prix"], prix_estime)

    # On ajoute également une explication textuelle pour rendre
    # le résultat plus compréhensible côté métier.
    explication = expliquer_categorie(categorie)

    # On retourne un dictionnaire enrichi avec toutes les informations utiles.
    return {
        **bien,
        "prix_estime": round(prix_estime, 2),
        "categorie": categorie,
        "explication": explication,
        "score": score
    }


def classer_biens(biens):
    """
    Classe une liste de biens immobiliers en fonction de leur score.

    Les biens avec le score le plus élevé sont considérés comme
    les plus intéressants selon les critères définis.
    """

    scored = []

    # On calcule le score de chaque bien.
    for b in biens:
        s = score_bien(
            b["prix"],
            b["surface"],
            b["nb_pieces"],
            b["proximite_mer"]
        )

        # On ajoute le score dans la structure du bien.
        scored.append({**b, "score": s})

    # On retourne la liste triée par score décroissant.
    return sorted(scored, key=lambda x: x["score"], reverse=True)