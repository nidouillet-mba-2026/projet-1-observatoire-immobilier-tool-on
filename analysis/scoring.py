"""
Scoring immobilier from scratch
"""
from analysis.stats import mean, standard_deviation


def score_bien(prix, surface, nb_pieces, proximite_mer):
    """
    Score de 0 à 100 pour un bien immobilier.
    - prix : prix en euros
    - surface : surface en m²
    - nb_pieces : nombre de pièces
    - proximite_mer : distance en km (0 = bord de mer)
    """
    # Prix au m²
    prix_m2 = prix / surface if surface > 0 else float('inf')

    # Score prix (moins c'est cher, mieux c'est)
    score_prix = max(0, 100 - (prix_m2 / 50))

    # Score surface
    score_surface = min(100, surface / 2)

    # Score pièces
    score_pieces = min(100, nb_pieces * 20)

    # Score proximité mer
    score_mer = max(0, 100 - proximite_mer * 10)

    # Score final pondéré
    score = (
        score_prix * 0.4 +
        score_surface * 0.3 +
        score_pieces * 0.1 +
        score_mer * 0.2
    )
    return round(score, 2)


def classer_biens(biens):
    """
    Classe une liste de biens par score décroissant.
    biens : liste de dicts avec clés prix, surface, nb_pieces, proximite_mer
    """
    scored = []
    for b in biens:
        s = score_bien(b['prix'], b['surface'], b['nb_pieces'], b['proximite_mer'])
        scored.append({**b, 'score': s})
    return sorted(scored, key=lambda x: x['score'], reverse=True)
