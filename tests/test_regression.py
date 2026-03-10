from analysis.regression import least_squares_fit, r_squared


def test_least_squares_fit_line():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [3.0, 5.0, 7.0, 9.0, 11.0]

    alpha, beta = least_squares_fit(x, y)

    assert abs(alpha - 1.0) < 0.01
    assert abs(beta - 2.0) < 0.01


def test_r_squared_perfect():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [3.0, 5.0, 7.0, 9.0, 11.0]

    alpha, beta = least_squares_fit(x, y)

    assert abs(r_squared(alpha, beta, x, y) - 1.0) < 0.01