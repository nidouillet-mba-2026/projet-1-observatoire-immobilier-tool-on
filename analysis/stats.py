"""
Fonctions statistiques from scratch.
Reference : Joel Grus, "Data Science From Scratch", chapitre 5.

IMPORTANT : N'importez pas numpy, pandas ou statistics pour ces fonctions.
Implementez-les avec du Python pur (listes, boucles, math).
"""

import math


def mean(xs: list[float]) -> float:
    """Retourne la moyenne d'une liste de nombres."""
    if len(xs) == 0:
        raise ValueError("La liste xs ne doit pas etre vide")
    return sum(xs) / len(xs)


def median(xs: list[float]) -> float:
    """Retourne la mediane d'une liste de nombres."""
    if len(xs) == 0:
        raise ValueError("La liste xs ne doit pas etre vide")

    xs_sorted = sorted(xs)
    n = len(xs_sorted)
    mid = n // 2

    if n % 2 == 1:
        return xs_sorted[mid]
    else:
        return (xs_sorted[mid - 1] + xs_sorted[mid]) / 2


def variance(xs: list[float]) -> float:
    """Retourne la variance d'une liste de nombres."""
    if len(xs) == 0:
        raise ValueError("La liste xs ne doit pas etre vide")

    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def standard_deviation(xs: list[float]) -> float:
    """Retourne l'ecart-type d'une liste de nombres."""
    return math.sqrt(variance(xs))


def covariance(xs: list[float], ys: list[float]) -> float:
    """Retourne la covariance entre deux series."""
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("xs et ys ne doivent pas etre vides")

    if len(xs) != len(ys):
        raise ValueError("xs et ys doivent avoir la meme longueur")

    mean_x = mean(xs)
    mean_y = mean(ys)

    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / len(xs)


def correlation(xs: list[float], ys: list[float]) -> float:
    """
    Retourne le coefficient de correlation de Pearson entre deux series.
    Retourne 0 si l'une des series a un ecart-type nul.
    """
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("xs et ys ne doivent pas etre vides")

    if len(xs) != len(ys):
        raise ValueError("xs et ys doivent avoir la meme longueur")

    std_x = standard_deviation(xs)
    std_y = standard_deviation(ys)

    if std_x == 0 or std_y == 0:
        return 0

    return covariance(xs, ys) / (std_x * std_y)