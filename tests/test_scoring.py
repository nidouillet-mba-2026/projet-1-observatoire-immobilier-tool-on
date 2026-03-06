"""
Tests unitaires pour analysis/scoring.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.scoring import score_bien, classer_biens


def test_score_bien_basique():
    score = score_bien(200000, 80, 4, 2)
    assert 0 <= score <= 100


def test_score_bien_bord_mer():
    score_mer = score_bien(200000, 80, 4, 0)
    score_loin = score_bien(200000, 80, 4, 10)
    assert score_mer > score_loin


def test_classer_biens():
    biens = [
        {'prix': 300000, 'surface': 60, 'nb_pieces': 3, 'proximite_mer': 5},
        {'prix': 150000, 'surface': 100, 'nb_pieces': 5, 'proximite_mer': 1},
        {'prix': 500000, 'surface': 40, 'nb_pieces': 2, 'proximite_mer': 20},
    ]
    result = classer_biens(biens)
    assert result[0]['score'] >= result[1]['score'] >= result[2]['score']


def test_score_surface_nulle():
    score = score_bien(200000, 0, 4, 2)
    assert score >= 0
