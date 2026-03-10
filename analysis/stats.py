"""
fonctions statistiques faites maison. 
référence : joel grus, "data science from scratch", chapitre 5. [cite: 65, 66]
"""
import math

def mean(xs: list[float]) -> float:
    """donne la moyenne d'une liste de chiffres."""
    # on additionne tout et on divise par le nombre d'éléments [cite: 68]
    return sum(xs) / len(xs)

def median(xs: list[float]) -> float:
    """trouve la valeur qui coupe la liste en deux."""
    # d'abord on trie la liste pour y voir plus clair [cite: 68]
    n = len(xs)
    sorted_xs = sorted(xs)
    midpoint = n // 2

    if n % 2 == 1:
        # si c'est impair, on prend pile l'élément du milieu [cite: 68]
        return sorted_xs[midpoint]
    else:
        # si c'est pair, on fait la moyenne des deux chiffres du centre [cite: 68]
        lo = midpoint - 1
        hi = midpoint
        return (sorted_xs[lo] + sorted_xs[hi]) / 2

def variance(xs: list[float]) -> float:
    """calcule la variance pour voir comment les chiffres s'étalent."""
    # on mesure l'écart moyen par rapport à la moyenne [cite: 68]
    n = len(xs)
    if n < 2:
        return 0.0
    mu = mean(xs)
    # on fait la somme des écarts au carré et on divise [cite: 68]
    return sum((x - mu) ** 2 for x in xs) / (n - 1)

def standard_deviation(xs: list[float]) -> float:
    """donne l'écart-type, c'est plus facile à lire que la variance."""
    # c'est simplement la racine carrée de la variance [cite: 68]
    return math.sqrt(variance(xs))


def covariance(xs: list[float], ys: list[float]) -> float:
    """regarde si deux séries de chiffres ont tendance à varier ensemble."""
    # on vérifie si x et y grimpent ou descendent en même temps [cite: 69]
    n = len(xs)
    if n < 2:
        return 0.0
    mu_x = mean(xs)
    mu_y = mean(ys)
    return sum((x - mu_x) * (y - mu_y) for x, y in zip(xs, ys)) / (n - 1)

def correlation(xs: list[float], ys: list[float]) -> float:
    """
    calcule le coefficient de pearson (entre -1 et 1). [cite: 69]
    """
    # c'est le rapport entre la covariance et les écarts-types [cite: 69]
    stdev_x = standard_deviation(xs)
    stdev_y = standard_deviation(ys)
    if stdev_x > 0 and stdev_y > 0:
        return covariance(xs, ys) / (stdev_x * stdev_y)
    else:
        # si l'une des listes est toute plate, la corrélation est nulle [cite: 69]
        return 0