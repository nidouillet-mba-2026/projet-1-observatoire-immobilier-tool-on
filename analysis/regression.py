"""
Regression lineaire simple from scratch.
Reference : Joel Grus, "Data Science From Scratch", chapitre 14.

IMPORTANT : N'importez pas sklearn, numpy ou scipy pour ces fonctions.
"""
import csv
from analysis.stats import mean, variance, covariance


def predict(alpha: float, beta: float, x_i: float) -> float:
    """Predit y pour une valeur x : y = alpha + beta * x."""
    # on applique la formule de la droite y = alpha + beta * x
    return alpha + beta * x_i


def error(alpha: float, beta: float, x_i: float, y_i: float) -> float:
    """Calcule l'erreur de prediction pour un point."""
    # l'erreur c'est la difference entre la valeur reelle et la prediction
    return y_i - predict(alpha, beta, x_i)


def sum_of_sqerrors(alpha: float, beta: float, x: list, y: list) -> float:
    """Somme des erreurs au carre sur tous les points."""
    # on calcule l'erreur pour chaque point et on met au carre pour eviter les annulations
    return sum(error(alpha, beta, x_i, y_i) ** 2 for x_i, y_i in zip(x, y))


def least_squares_fit(x: list[float], y: list[float]) -> tuple[float, float]:
    """
    Trouve alpha et beta qui minimisent la somme des erreurs au carre.
    Retourne (alpha, beta) tels que y ≈ alpha + beta * x.
    """
    # beta mesure la pente de la droite
    beta = covariance(x, y) / variance(x)
    # alpha est l'ordonnee a l'origine pour que la droite passe par le centre des donnees
    alpha = mean(y) - beta * mean(x)
    return alpha, beta


def r_squared(alpha: float, beta: float, x: list, y: list) -> float:
    """
    Coefficient de determination R².
    R² = 1 - (SS_res / SS_tot)
    1.0 = ajustement parfait, 0.0 = le modele n'explique rien.
    """
    # on calcule la somme des erreurs au carre du modele
    ss_res = sum_of_sqerrors(alpha, beta, x, y)
    # on calcule la variation totale par rapport a la moyenne
    mean_y = mean(y)
    ss_tot = sum((y_i - mean_y) ** 2 for y_i in y)
    # r_squared mesure la part de variance expliquee par le modele
    return 1.0 - (ss_res / ss_tot)
