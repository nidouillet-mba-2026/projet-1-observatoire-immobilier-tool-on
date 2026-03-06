"""
Regression lineaire from scratch - sans numpy
"""
from analysis.stats import mean, correlation, standard_deviation


def least_squares_fit(x, y):
    std_x = standard_deviation(x)
    std_y = standard_deviation(y)

    if std_x == 0:
        return mean(y), 0.0

    beta = correlation(x, y) * std_y / std_x
    alpha = mean(y) - beta * mean(x)
    return alpha, beta


def predict(alpha, beta, x):
    return alpha + beta * x


def r_squared(alpha, beta, x, y):
    y_pred = [predict(alpha, beta, xi) for xi in x]
    ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
    ss_tot = sum((yi - mean(y)) ** 2 for yi in y)

    if ss_tot == 0:
        return 1.0

    return 1 - ss_res / ss_tot