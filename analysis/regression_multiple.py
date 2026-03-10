"""
regression lineaire multiple from scratch.
reference : joel grus, "data science from scratch", chapitre 14-15.

important : n'importez pas sklearn, numpy ou scipy pour ces fonctions.
"""
from analysis.stats import mean


def dot_product(v, w):
    """produit scalaire de deux vecteurs."""
    # on multiplie chaque element et on somme le tout
    return sum(v_i * w_i for v_i, w_i in zip(v, w))


def vector_sum(vectors):
    """somme de plusieurs vecteurs."""
    # on additionne tous les vecteurs element par element
    n = len(vectors[0])
    return [sum(vector[i] for vector in vectors) for i in range(n)]


def scalar_multiply(c, v):
    """multiplication d'un vecteur par un scalaire."""
    # on multiplie chaque element du vecteur par le scalaire
    return [c * v_i for v_i in v]


def vector_subtract(v, w):
    """soustraction de deux vecteurs."""
    # on soustrait element par element
    return [v_i - w_i for v_i, w_i in zip(v, w)]


def predict_multiple(beta, x_i):
    """
    predit y pour un vecteur de features x_i.
    beta[0] est l'intercept, beta[1:] sont les coefficients.
    """
    # on commence par l'intercept puis on ajoute chaque contribution
    return beta[0] + dot_product(beta[1:], x_i)


def error_multiple(beta, x_i, y_i):
    """erreur de prediction pour un point en regression multiple."""
    # l'erreur c'est toujours la difference entre reel et predit
    return y_i - predict_multiple(beta, x_i)


def sum_of_sqerrors_multiple(beta, x, y):
    """somme des erreurs au carre sur tous les points."""
    # on calcule l'erreur pour chaque point et on met au carre
    return sum(error_multiple(beta, x_i, y_i) ** 2 for x_i, y_i in zip(x, y))


def normalize_features(x):
    """normalise les features pour avoir mean=0 et std proche de 1."""
    num_features = len(x[0])
    n = len(x)

    # calcul des moyennes et ecarts-types pour chaque feature
    means = []
    stds = []

    for j in range(num_features):
        feature_vals = [x_i[j] for x_i in x]
        mean_j = mean(feature_vals)
        # calcul de l'ecart-type
        variance_j = sum((val - mean_j) ** 2 for val in feature_vals) / (n - 1)
        std_j = variance_j ** 0.5

        means.append(mean_j)
        stds.append(std_j if std_j > 0 else 1.0)  # evite division par zero

    # normalisation
    x_normalized = []
    for x_i in x:
        x_norm = [(x_i[j] - means[j]) / stds[j] for j in range(num_features)]
        x_normalized.append(x_norm)

    return x_normalized, means, stds


def least_squares_fit_multiple(x, y, learning_rate=0.001, num_iterations=5000):
    """
    trouve les coefficients beta qui minimisent la somme des erreurs au carre.
    utilise la descente de gradient avec normalisation des features.

    x : liste de listes (chaque sous-liste est un vecteur de features)
    y : liste de valeurs cibles
    """
    # normalisation des features pour stabiliser la convergence
    x_norm, means, stds = normalize_features(x)

    # nombre de features (sans compter l'intercept)
    num_features = len(x[0])

    # initialisation des coefficients a la moyenne de y pour l'intercept
    beta = [mean(y)] + [0.0] * num_features

    # descente de gradient
    for _ in range(num_iterations):
        # calcul du gradient pour chaque coefficient
        gradient = [0.0] * (num_features + 1)

        for x_i, y_i in zip(x_norm, y):
            err = error_multiple(beta, x_i, y_i)
            # gradient pour l'intercept
            gradient[0] += -2 * err
            # gradient pour chaque coefficient
            for j in range(num_features):
                gradient[j + 1] += -2 * err * x_i[j]

        # mise a jour des coefficients avec normalisation du gradient
        for j in range(len(beta)):
            beta[j] -= learning_rate * gradient[j] / len(x)

    # retour aux coefficients originaux (avant normalisation)
    beta_original = [beta[0]]
    for j in range(num_features):
        # on ajuste l'intercept pour compenser la normalisation
        beta_original[0] -= beta[j + 1] * means[j] / stds[j]
        # on ajuste les coefficients
        beta_original.append(beta[j + 1] / stds[j])

    return beta_original


def r_squared_multiple(beta, x, y):
    """
    coefficient de determination r² pour regression multiple.
    mesure la qualite de l'ajustement.
    """
    # somme des erreurs au carre du modele
    ss_res = sum_of_sqerrors_multiple(beta, x, y)
    # variation totale par rapport a la moyenne
    mean_y = mean(y)
    ss_tot = sum((y_i - mean_y) ** 2 for y_i in y)
    # r² mesure la part de variance expliquee
    return 1.0 - (ss_res / ss_tot)
