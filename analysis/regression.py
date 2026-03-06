"""
Regression lineaire from scratch - sans numpy
"""
from analysis.stats import mean, variance, correlation, standard_deviation


def least_squares_fit(x, y):
    beta = correlation(x, y) * standard_deviation(y) / standard_deviation(x)
    alpha = mean(y) - beta * mean(x)
    return alpha, beta


def r_squared(alpha, beta, x, y):
    y_pred = [alpha + beta * xi for xi in x]
    ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
    ss_tot = sum((yi - mean(y)) ** 2 for yi in y)
    if ss_tot == 0:
        return 1.0
    return 1 - ss_res / ss_tot
