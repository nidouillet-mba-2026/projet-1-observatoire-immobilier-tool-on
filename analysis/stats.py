"""
Statistiques from scratch - sans numpy
"""

def mean(xs):
    if len(xs) == 0:
        raise ValueError("La liste xs ne peut pas être vide.")
    return sum(xs) / len(xs)


def median(xs):
    if len(xs) == 0:
        raise ValueError("La liste xs ne peut pas être vide.")
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2
    return float(s[mid])


def variance(xs):
    if len(xs) == 0:
        raise ValueError("La liste xs ne peut pas être vide.")
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def standard_deviation(xs):
    return variance(xs) ** 0.5


def covariance(xs, ys):
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("Les listes xs et ys ne peuvent pas être vides.")
    if len(xs) != len(ys):
        raise ValueError("Les listes xs et ys doivent avoir la même taille.")

    m_x = mean(xs)
    m_y = mean(ys)
    return sum((x - m_x) * (y - m_y) for x, y in zip(xs, ys)) / len(xs)


def correlation(xs, ys):
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("Les listes xs et ys ne peuvent pas être vides.")
    if len(xs) != len(ys):
        raise ValueError("Les listes xs et ys doivent avoir la même taille.")

    std_x = standard_deviation(xs)
    std_y = standard_deviation(ys)

    if std_x == 0 or std_y == 0:
        return 0.0

    return covariance(xs, ys) / (std_x * std_y)