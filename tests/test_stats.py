"""
tests unitaires pour analysis/stats.py
toutes les fonctions statistiques implementees from scratch
"""
import pytest
import math
from analysis.stats import (
    mean,
    median,
    variance,
    standard_deviation,
    covariance,
    correlation
)


class TestMean:
    """tests pour la fonction mean()"""

    def test_mean_liste_simple(self):
        """test sur une liste simple"""
        assert mean([1, 2, 3, 4, 5]) == 3.0

    def test_mean_liste_paire(self):
        """test avec nombre pair d'elements"""
        assert mean([2, 4, 6, 8]) == 5.0

    def test_mean_negatifs(self):
        """test avec nombres negatifs"""
        assert mean([-1, -2, -3]) == -2.0

    def test_mean_decimaux(self):
        """test avec decimaux"""
        result = mean([1.5, 2.5, 3.5])
        assert abs(result - 2.5) < 0.001


class TestMedian:
    """tests pour la fonction median()"""

    def test_median_impair(self):
        """test avec nombre impair d'elements"""
        assert median([1, 2, 3, 4, 5]) == 3

    def test_median_pair(self):
        """test avec nombre pair d'elements"""
        assert median([1, 2, 3, 4]) == 2.5

    def test_median_desordonne(self):
        """test avec liste desordonnee"""
        assert median([5, 1, 3, 2, 4]) == 3

    def test_median_duplicates(self):
        """test avec valeurs dupliquees"""
        assert median([1, 2, 2, 3]) == 2.0


class TestVariance:
    """tests pour la fonction variance()"""

    def test_variance_liste_simple(self):
        """test variance sur liste simple"""
        # variance de [1,2,3,4,5] = 2.5
        result = variance([1, 2, 3, 4, 5])
        assert abs(result - 2.5) < 0.001

    def test_variance_constante(self):
        """test variance d'une constante = 0"""
        result = variance([5, 5, 5, 5])
        assert abs(result - 0.0) < 0.001

    def test_variance_deux_valeurs(self):
        """test avec deux valeurs"""
        # variance de [1, 3] = 2.0
        result = variance([1, 3])
        assert abs(result - 2.0) < 0.001


class TestStandardDeviation:
    """tests pour la fonction standard_deviation()"""

    def test_std_liste_simple(self):
        """test ecart-type sur liste simple"""
        # std de [1,2,3,4,5] = sqrt(2.5) ≈ 1.58
        result = standard_deviation([1, 2, 3, 4, 5])
        expected = math.sqrt(2.5)
        assert abs(result - expected) < 0.001

    def test_std_constante(self):
        """test ecart-type d'une constante = 0"""
        result = standard_deviation([5, 5, 5, 5])
        assert abs(result - 0.0) < 0.001

    def test_std_relation_variance(self):
        """test que std = sqrt(variance)"""
        data = [2, 4, 6, 8, 10]
        var = variance(data)
        std = standard_deviation(data)
        assert abs(std - math.sqrt(var)) < 0.001


class TestCovariance:
    """tests pour la fonction covariance()"""

    def test_covariance_positive(self):
        """test covariance positive (x et y croissent ensemble)"""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        result = covariance(x, y)
        assert result > 0

    def test_covariance_negative(self):
        """test covariance negative (x croit, y decroit)"""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        result = covariance(x, y)
        assert result < 0

    def test_covariance_nulle(self):
        """test covariance nulle (pas de relation)"""
        x = [1, 2, 1, 2]
        y = [1, 1, 2, 2]
        result = covariance(x, y)
        # la covariance devrait etre proche de 0
        assert abs(result) < 0.5

    def test_covariance_symetrique(self):
        """test que cov(x,y) = cov(y,x)"""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 5, 4, 5]
        assert abs(covariance(x, y) - covariance(y, x)) < 0.001


class TestCorrelation:
    """tests pour la fonction correlation()"""

    def test_correlation_parfaite_positive(self):
        """test correlation parfaite +1"""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        result = correlation(x, y)
        assert abs(result - 1.0) < 0.001

    def test_correlation_parfaite_negative(self):
        """test correlation parfaite -1"""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        result = correlation(x, y)
        assert abs(result - (-1.0)) < 0.001

    def test_correlation_nulle(self):
        """test correlation nulle"""
        x = [1, 2, 1, 2, 1, 2]
        y = [1, 1, 2, 2, 1, 1]
        result = correlation(x, y)
        # devrait etre proche de 0
        assert abs(result) < 0.5

    def test_correlation_bornes(self):
        """test que correlation est entre -1 et 1"""
        x = [1, 2, 3, 4, 5, 6, 7]
        y = [2, 3, 5, 4, 6, 7, 8]
        result = correlation(x, y)
        assert -1.0 <= result <= 1.0

    def test_correlation_constante(self):
        """test avec une variable constante"""
        x = [1, 2, 3, 4, 5]
        y = [5, 5, 5, 5, 5]
        result = correlation(x, y)
        assert result == 0.0


class TestCasReels:
    """tests sur des cas d'usage reels"""

    def test_donnees_prix_surfaces(self):
        """test avec donnees realistes de prix et surfaces"""
        # simulation de donnees immobilieres
        surfaces = [50, 60, 70, 80, 90]
        prix = [150000, 180000, 210000, 240000, 270000]

        # la correlation devrait etre forte et positive
        corr = correlation(surfaces, prix)
        assert corr > 0.95

        # prix moyen
        prix_moyen = mean(prix)
        assert 200000 < prix_moyen < 230000

    def test_coherence_variance_std(self):
        """test coherence entre variance et ecart-type"""
        data = [100, 120, 140, 160, 180, 200]

        var = variance(data)
        std = standard_deviation(data)

        # std^2 doit etre proche de variance
        assert abs(std * std - var) < 0.001
