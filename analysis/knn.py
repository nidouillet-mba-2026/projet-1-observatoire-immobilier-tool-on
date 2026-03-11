"""
Système de recommandation k-NN pour biens immobiliers.
Référence : Joel Grus, "Data Science From Scratch", chapitre 12 (k-nearest neighbors).
"""
import math


def distance_euclidienne(v1, v2):
    """
    Calcule la distance euclidienne entre deux vecteurs.
    Reference: Grus ch.12
    """
    if len(v1) != len(v2):
        raise ValueError("Les vecteurs doivent avoir la même dimension")

    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


def normaliser_features(data, stats=None):
    """
    Normalise les features avec min-max scaling : (x - min) / (max - min).
    Permet de mettre toutes les variables sur la même échelle.

    Retourne:
    - data normalisée
    - stats (pour dénormaliser plus tard si besoin)
    """
    if not data:
        return [], None

    num_features = len(data[0])

    # Calcul des stats si pas fournies
    if stats is None:
        stats = []
        for i in range(num_features):
            values = [row[i] for row in data]
            min_val = min(values)
            max_val = max(values)
            stats.append((min_val, max_val))

    # Normalisation
    data_norm = []
    for row in data:
        row_norm = []
        for i, val in enumerate(row):
            min_val, max_val = stats[i]
            if max_val - min_val == 0:
                row_norm.append(0.0)  # Si constante, on met 0
            else:
                row_norm.append((val - min_val) / (max_val - min_val))
        data_norm.append(row_norm)

    return data_norm, stats


def safe_float(value, default=0.0):
    """Convertit une valeur en float de manière sécurisée."""
    import math
    try:
        if value is None:
            return default
        # Gestion des NaN pandas
        if hasattr(value, '__float__'):
            result = float(value)
            if math.isnan(result):
                return default
            return result
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Convertit une valeur en int de manière sécurisée."""
    import math
    try:
        if value is None:
            return default
        # Gestion des NaN pandas
        if hasattr(value, '__float__'):
            float_val = float(value)
            if math.isnan(float_val):
                return default
            return int(float_val)
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_bool(value):
    """Convertit une valeur en booléen de manière sécurisée."""
    import math
    try:
        if value is None:
            return False
        # Gestion des NaN pandas
        if hasattr(value, '__float__'):
            float_val = float(value)
            if math.isnan(float_val):
                return False
        # Si c'est déjà un booléen
        if isinstance(value, bool):
            return value
        # Si c'est un nombre
        if isinstance(value, (int, float)):
            return value != 0
        # Si c'est une string
        return str(value).strip().lower() in ('1', 'true', 'oui', 'yes')
    except (ValueError, TypeError):
        return False


def annonce_vers_vecteur(annonce):
    """
    Convertit une annonce en vecteur de features pour k-NN.

    Features sélectionnées (13 dimensions):
    1. surface (m2)
    2. prix (euros)
    3. prix au m2
    4. nombre de pièces
    5. nombre de chambres
    6. type (0=appartement, 1=maison)
    7-9. code postal (one-hot : 83000, 83100, 83200)
    10. balcon (0/1)
    11. terrasse (0/1)
    12. nombre de parkings
    13. ascenseur (0/1)
    """
    # Encodage du type
    type_bien = str(annonce.get('type_bien', annonce.get('type', ''))).lower()
    type_num = 1.0 if 'maison' in type_bien else 0.0

    # Encodage one-hot du code postal
    code_postal = str(annonce.get('code_postal', ''))
    is_83000 = 1.0 if code_postal == '83000' else 0.0
    is_83100 = 1.0 if code_postal == '83100' else 0.0
    is_83200 = 1.0 if code_postal == '83200' else 0.0

    # Récupération des valeurs avec gestion des NaN
    surface = safe_float(annonce.get('surface_m2', annonce.get('surface', 0)))
    prix = safe_float(annonce.get('prix', 0))
    prix_m2 = safe_float(annonce.get('prix_m2', 0))

    # Calcul prix_m2 si manquant
    if prix_m2 == 0 and surface > 0 and prix > 0:
        prix_m2 = prix / surface

    pieces = safe_int(annonce.get('pieces', 0))
    chambres = safe_int(annonce.get('chambres', 0))

    # Equipements (conversion en booléen puis float)
    balcon = float(safe_bool(annonce.get('balcon', 0)))
    terrasse = float(safe_bool(annonce.get('terrasse', 0)))
    parking = safe_int(annonce.get('nb_parkings', annonce.get('parking', 0)))
    ascenseur = float(safe_bool(annonce.get('ascenseur', 0)))

    return [
        surface,
        prix,
        prix_m2,
        float(pieces),
        float(chambres),
        type_num,
        is_83000,
        is_83100,
        is_83200,
        balcon,
        terrasse,
        float(parking),
        ascenseur
    ]


def knn_similaires(bien_recherche, catalogue, k=5, normaliser=True):
    """
    Trouve les k biens les plus similaires au bien recherché.

    Args:
        bien_recherche : vecteur de features du bien cible
        catalogue : liste de tuples (vecteur_features, annonce_complete)
        k : nombre de voisins à retourner
        normaliser : normaliser les features avant calcul distance

    Retourne:
        liste des k annonces les plus similaires avec leur distance
    """
    # Extraction des vecteurs
    vecteurs = [item[0] for item in catalogue]

    # Normalisation si demandée
    if normaliser:
        tous_vecteurs = [bien_recherche] + vecteurs
        vecteurs_norm, _ = normaliser_features(tous_vecteurs)
        bien_norm = vecteurs_norm[0]
        catalogue_norm = vecteurs_norm[1:]
    else:
        bien_norm = bien_recherche
        catalogue_norm = vecteurs

    # Calcul des distances
    distances = []
    for i, vecteur_norm in enumerate(catalogue_norm):
        dist = distance_euclidienne(bien_norm, vecteur_norm)
        distances.append((dist, catalogue[i][1]))  # (distance, annonce)

    # Tri par distance croissante et sélection des k premiers
    distances.sort(key=lambda x: x[0])

    return distances[:k]


def recommander_annonces(bien_reference, catalogue_annonces, k=5):
    """
    Recommande k annonces similaires à un bien de référence.

    Args:
        bien_reference : dict de l'annonce de référence
        catalogue_annonces : liste des annonces disponibles
        k : nombre de recommandations

    Retourne:
        liste des k meilleures recommandations avec leur similarité
    """
    # Création du vecteur de recherche
    vecteur_recherche = annonce_vers_vecteur(bien_reference)

    # Création du catalogue vectorisé
    catalogue = [(annonce_vers_vecteur(a), a) for a in catalogue_annonces]

    # Recherche des k plus proches voisins
    resultats = knn_similaires(vecteur_recherche, catalogue, k=k)

    # Calcul du score de similarité (0-100%)
    resultats_avec_score = []
    for distance, annonce in resultats:
        # Score de similarité inversé : plus la distance est faible, plus le score est élevé
        similarite = max(0, (1 - min(distance, 1)) * 100)
        resultats_avec_score.append((distance, similarite, annonce))

    return resultats_avec_score
