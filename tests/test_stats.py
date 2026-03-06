"""
Tests unitaires pour analysis/stats.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.stats import mean, variance, correlation, median, standard_deviation


def test_mean_simple():
    assert mean([1, 2, 3, 4, 5]) == 3.0


def test_mean_deux_valeurs():
    assert mean([10, 20]) == 15.0


def test_variance_connue():
    result = variance([2, 4, 4, 4, 5, 5, 7, 9])
    assert abs(result - 4.0) < 0.1


def test_correlation_identique():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert abs(correlation(xs, xs) - 1.0) < 0.01


def test_median_impair():
    assert median([1, 2, 3]) == 2


def test_standard_deviation():
    result = standard_deviation([2, 4, 4, 4, 5, 5, 7, 9])
    assert abs(result - 2.0) < 0.1
