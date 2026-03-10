"""
tests unitaires pour analysis/regression.py
regression lineaire simple implementee from scratch
"""
import pytest
from analysis.regression import (
    predict,
    error,
    sum_of_sqerrors,
    least_squares_fit,
    r_squared
)


class TestPredict:
    """tests pour la fonction predict()"""

    def test_predict_positif(self):
        """test prediction avec coefficients positifs"""
        # y = 10 + 2*x, pour x=5 -> y=20
        assert predict(10, 2, 5) == 20

    def test_predict_negatif(self):
        """test avec pente negative"""
        # y = 100 - 5*x, pour x=10 -> y=50
        assert predict(100, -5, 10) == 50

    def test_predict_zero(self):
        """test avec x=0"""
        # y = 15 + 3*x, pour x=0 -> y=15
        assert predict(15, 3, 0) == 15

    def test_predict_decimaux(self):
        """test avec valeurs decimales"""
        result = predict(1.5, 2.5, 3.5)
        expected = 1.5 + 2.5 * 3.5
        assert abs(result - expected) < 0.001


class TestError:
    """tests pour la fonction error()"""

    def test_error_positif(self):
        """test erreur positive (sous-estimation)"""
        # prediction = 10, reel = 15 -> erreur = 5
        assert error(0, 1, 10, 15) == 5

    def test_error_negatif(self):
        """test erreur negative (sur-estimation)"""
        # prediction = 20, reel = 15 -> erreur = -5
        assert error(0, 1, 20, 15) == -5

    def test_error_nulle(self):
        """test erreur nulle (prediction parfaite)"""
        # y = 5 + 2*x, pour x=3, y=11
        assert error(5, 2, 3, 11) == 0


class TestSumOfSqerrors:
    """tests pour la fonction sum_of_sqerrors()"""

    def test_sse_modele_parfait(self):
        """test sse avec modele parfait"""
        x = [1, 2, 3]
        y = [3, 5, 7]  # y = 1 + 2*x
        sse = sum_of_sqerrors(1, 2, x, y)
        assert abs(sse - 0.0) < 0.001

    def test_sse_positif(self):
        """test que sse est toujours positif"""
        x = [1, 2, 3, 4]
        y = [2, 4, 5, 8]
        sse = sum_of_sqerrors(0, 2, x, y)
        assert sse >= 0

    def test_sse_calcul(self):
        """test calcul explicite de sse"""
        x = [1, 2]
        y = [3, 5]
        # predictions: 2 + 1*1 = 3, 2 + 1*2 = 4
        # erreurs: 0, 1
        # sse: 0^2 + 1^2 = 1
        sse = sum_of_sqerrors(2, 1, x, y)
        assert abs(sse - 1.0) < 0.001


class TestLeastSquaresFit:
    """tests pour la fonction least_squares_fit()"""

    def test_regression_parfaite(self):
        """test regression sur relation lineaire parfaite"""
        x = [1, 2, 3, 4, 5]
        y = [3, 5, 7, 9, 11]  # y = 1 + 2*x

        alpha, beta = least_squares_fit(x, y)

        # alpha devrait etre proche de 1
        assert abs(alpha - 1.0) < 0.001
        # beta devrait etre proche de 2
        assert abs(beta - 2.0) < 0.001

    def test_regression_pente_positive(self):
        """test que la pente est positive si correlation positive"""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]

        alpha, beta = least_squares_fit(x, y)
        assert beta > 0

    def test_regression_pente_negative(self):
        """test que la pente est negative si correlation negative"""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]

        alpha, beta = least_squares_fit(x, y)
        assert beta < 0

    def test_regression_passe_par_moyenne(self):
        """test que la droite passe par le point moyen"""
        from analysis.stats import mean

        x = [2, 4, 6, 8, 10]
        y = [3, 7, 11, 15, 19]

        alpha, beta = least_squares_fit(x, y)

        mean_x = mean(x)
        mean_y = mean(y)

        # la prediction pour mean_x doit etre mean_y
        predicted = predict(alpha, beta, mean_x)
        assert abs(predicted - mean_y) < 0.001


class TestRSquared:
    """tests pour la fonction r_squared()"""

    def test_r_squared_parfait(self):
        """test r² = 1 pour modele parfait"""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]

        alpha, beta = least_squares_fit(x, y)
        r2 = r_squared(alpha, beta, x, y)

        assert abs(r2 - 1.0) < 0.001

    def test_r_squared_bornes(self):
        """test que r² est entre 0 et 1"""
        x = [1, 2, 3, 4, 5, 6, 7]
        y = [2, 3, 5, 4, 6, 7, 8]

        alpha, beta = least_squares_fit(x, y)
        r2 = r_squared(alpha, beta, x, y)

        assert 0.0 <= r2 <= 1.0

    def test_r_squared_mauvais_modele(self):
        """test r² faible pour mauvais modele"""
        x = [1, 2, 3, 4, 5]
        y = [5, 3, 7, 2, 9]  # donnees aleatoires

        alpha, beta = least_squares_fit(x, y)
        r2 = r_squared(alpha, beta, x, y)

        # r² devrait etre faible
        assert r2 < 0.5

    def test_r_squared_relation_correlation(self):
        """test relation entre r² et correlation"""
        from analysis.stats import correlation

        x = [1, 2, 3, 4, 5]
        y = [1.5, 3.5, 5.5, 7.5, 9.5]

        alpha, beta = least_squares_fit(x, y)
        r2 = r_squared(alpha, beta, x, y)
        corr = correlation(x, y)

        # r² = correlation^2 pour regression simple
        assert abs(r2 - corr**2) < 0.001


class TestRegressionComplete:
    """tests d'integration sur un cas complet"""

    def test_workflow_complet(self):
        """test workflow complet de regression"""
        # donnees prix immobilier fictives
        surfaces = [30, 40, 50, 60, 70, 80, 90, 100]
        prix = [100000, 130000, 160000, 190000, 220000, 250000, 280000, 310000]

        # entrainement du modele
        alpha, beta = least_squares_fit(surfaces, prix)

        # verification pente positive
        assert beta > 0

        # verification r² eleve (bonne correlation)
        r2 = r_squared(alpha, beta, surfaces, prix)
        assert r2 > 0.95

        # test prediction
        surface_test = 55
        prix_predit = predict(alpha, beta, surface_test)

        # le prix predit doit etre entre 160k et 190k
        assert 160000 < prix_predit < 190000

    def test_cas_immobilier_reel(self):
        """test avec donnees immobilieres realistes"""
        # cas simplifie d'estimation immobiliere
        # prix ≈ 50000 + 2500 * surface
        surfaces = [40, 50, 60, 70, 80]
        prix = [150000, 175000, 200000, 225000, 250000]

        alpha, beta = least_squares_fit(surfaces, prix)

        # alpha devrait etre proche de 50000
        assert 40000 < alpha < 60000

        # beta devrait etre proche de 2500 euros/m²
        assert 2000 < beta < 3000

        # r² devrait etre excellent
        r2 = r_squared(alpha, beta, surfaces, prix)
        assert r2 > 0.99

    def test_minimisation_erreur(self):
        """test que least_squares minimise bien l'erreur"""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 5, 4, 5]

        # calcul des coefficients optimaux
        alpha_opt, beta_opt = least_squares_fit(x, y)
        sse_opt = sum_of_sqerrors(alpha_opt, beta_opt, x, y)

        # test avec autres coefficients
        sse_autre = sum_of_sqerrors(alpha_opt + 1, beta_opt, x, y)

        # l'erreur optimale doit etre inferieure
        assert sse_opt < sse_autre


class TestCasLimites:
    """tests sur les cas limites"""

    def test_deux_points(self):
        """test regression avec seulement 2 points"""
        x = [1, 2]
        y = [3, 5]

        alpha, beta = least_squares_fit(x, y)

        # la droite doit passer exactement par les 2 points
        assert abs(predict(alpha, beta, 1) - 3) < 0.001
        assert abs(predict(alpha, beta, 2) - 5) < 0.001

    def test_variance_nulle_x(self):
        """test avec x constants (devrait echouer ou retourner erreur)"""
        x = [5, 5, 5, 5]
        y = [1, 2, 3, 4]

        # cette regression n'a pas de sens (variance x = 0)
        # on s'attend a une erreur ou un resultat invalide
        with pytest.raises(ZeroDivisionError):
            alpha, beta = least_squares_fit(x, y)
