"""
Regression lineaire simple from scratch.
Reference : Joel Grus, "Data Science From Scratch", chapitre 14.
"""

from analysis.stats import mean, variance, covariance


def predict(alpha: float, beta: float, x_i: float) -> float:
    """Predit y pour une valeur x : y = alpha + beta * x."""
    return alpha + beta * x_i


def error(alpha: float, beta: float, x_i: float, y_i: float) -> float:
    """Calcule l'erreur de prediction pour un point."""
    return y_i - predict(alpha, beta, x_i)


def sum_of_sqerrors(alpha: float, beta: float, x: list, y: list) -> float:
    """Somme des erreurs au carre sur tous les points."""
    if len(x) != len(y):
        raise ValueError("x et y doivent avoir la meme longueur")

    return sum(error(alpha, beta, x_i, y_i) ** 2 for x_i, y_i in zip(x, y))


def least_squares_fit(x: list[float], y: list[float]) -> tuple[float, float]:
    """
    Trouve alpha et beta qui minimisent la somme des erreurs au carre.
    Retourne (alpha, beta) tels que y ≈ alpha + beta * x.
    """
    if len(x) == 0 or len(y) == 0:
        raise ValueError("x et y ne doivent pas etre vides")
    if len(x) != len(y):
        raise ValueError("x et y doivent avoir la meme longueur")

    var_x = variance(x)
    if var_x == 0:
        raise ValueError("La variance de x ne peut pas etre nulle")

    beta = covariance(x, y) / var_x
    alpha = mean(y) - beta * mean(x)

    return alpha, beta


def r_squared(alpha: float, beta: float, x: list, y: list) -> float:
    """
    Coefficient de determination R².
    R² = 1 - (SS_res / SS_tot)
    1.0 = ajustement parfait, 0.0 = le modele n'explique rien.
    """
    if len(x) == 0 or len(y) == 0:
        raise ValueError("x et y ne doivent pas etre vides")
    if len(x) != len(y):
        raise ValueError("x et y doivent avoir la meme longueur")

    ss_res = sum_of_sqerrors(alpha, beta, x, y)
    mean_y = mean(y)
    ss_tot = sum((y_i - mean_y) ** 2 for y_i in y)

    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0

    return 1 - (ss_res / ss_tot)