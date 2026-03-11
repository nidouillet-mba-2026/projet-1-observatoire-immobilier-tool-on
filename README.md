# Projet 1 : Observatoire du Marché Immobilier Toulonnais

## Objectif

Construire une application web déployée permettant d'analyser le marché immobilier toulonnais en temps réel à partir d'annonces immobilières réelles et de données de transactions publiques.

Le projet combine :
- collecte automatisée d'annonces immobilières
- algorithmes statistiques implémentés **from scratch**
- modèles de régression
- scoring d'opportunité immobilière
- visualisations interactives via un dashboard web

L'application permet notamment de :
- analyser les prix immobiliers par quartier
- détecter des biens sous-évalués
- suivre l'évolution du marché
- comparer des biens similaires

---

## Evaluation automatique

A chaque `git push`, le CI évalue automatiquement le projet.

Consultez : **GitHub → Actions → dernier workflow → Job Summary**

**Score CI : jusqu'à 55 / 100**

Les **45 points restants sont évalués lors de la soutenance**.

---

## Structure du projet

```
.
├── analysis/
│   ├── stats.py          <- Statistiques from scratch
│   ├── regression.py     <- Régression linéaire from scratch
│   ├── knn.py            <- Recommandation k-NN
│   └── scoring.py        <- Scoring d'opportunité immobilière
│
├── app/
│   ├── streamlit_app.py  <- Dashboard principal Streamlit
│   ├── config.py         <- Configuration de l'application
│   │
│   ├── components/
│   │   └── ui.py         <- Composants UI réutilisables
│   │
│   ├── pages/
│   │   ├── 1_Marche.py
│   │   ├── 2_Recherche.py
│   │   ├── 4_Tendances.py
│   │   └── 5_Parametres.py
│   │
│   └── services/
│       ├── metrics.py
│       ├── export.py
│       └── listings.py
│
├── data/
│   ├── dvf_toulon.csv              <- Données DVF (transactions)
│   ├── annonces_actuelles.csv      <- Annonces principales
│   ├── annonces_bienici_clean.csv  <- Annonces Bienici nettoyées
│   ├── annonces_pap.csv            <- Annonces PAP
│   │
│   ├── scrape_bienici.py           <- Script scraping Bienici
│   ├── fetch_bienici_api.py        <- Script API Bienici
│   ├── scrape_pap.py               <- Script scraping PAP
│   └── clean_bienici_api.py        <- Script nettoyage données
│
├── tests/
│   ├── test_stats.py
│   ├── test_regression.py
│   └── test_auto_eval.py
│
├── requirements.txt
└── README.md
```

---

## Installation

Cloner le projet :

```bash
git clone <votre-url>
cd <votre-repo>
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

## Lancement local

Depuis la racine du projet :

```bash
streamlit run app/streamlit_app.py
```

L'application sera accessible sur :

```
http://localhost:8501
```

---

## Application déployée

**URL :** https://projet-1-observatoire-immobilier-tool-on-mljs5z2ctwygrwatx8cau.streamlit.app

---

## Répartition du travail

| Membre | Rôle | Contributions principales |
|--------|------|---------------------------|
| Joé Paday | Data Engineer | Scraping des annonces immobilières, récupération API Bienici, nettoyage des données, préparation des datasets |
| Jérémy Indelicato | Data Scientist | Implémentation des algorithmes statistiques from scratch, régression linéaire, k-NN et scoring |
| Mody Hady Barry | AI Engineer | Analyse des données et intégration des modèles |
| Sandro Antonietti / Mathis Galloul | Frontend / DevOps | Développement du dashboard Streamlit, visualisations interactives, architecture de l'application |

---

## Collecte des données

### Scraping des annonces immobilières

Les annonces sont collectées automatiquement via des scripts Python.

**Sources :**
- Bienici
- PAP (Particulier à Particulier)

**Les scripts permettent :**
- récupération automatisée des annonces
- extraction des caractéristiques (prix, surface, quartier, équipements)
- nettoyage et normalisation des données
- génération d'un dataset exploitable par l'application

**Scripts principaux :**
- `scrape_bienici.py`
- `fetch_bienici_api.py`
- `scrape_pap.py`
- `clean_bienici_api.py`

**Les données collectées incluent notamment :**
- prix
- surface
- nombre de pièces
- nombre de chambres
- quartier
- équipements (balcon, terrasse, parking, ascenseur, etc.)
- description textuelle
- lien vers l'annonce originale

---

## Données utilisées

### DVF (Demandes de Valeurs Foncières)

Transactions immobilières réelles issues du registre fiscal français.

**Source :**
https://files.data.gouv.fr/geo-dvf/latest/csv/83/

**Ces données servent à :**
- entraîner le modèle de régression
- estimer les prix de marché

### Annonces immobilières

Annonces collectées automatiquement via scraping.

**Sources :**
- Bienici
- PAP

**Date de collecte :** 10/03/2026

---

## Dashboard Streamlit

L'application web permet d'explorer les données via plusieurs pages.

### Home

Vue d'ensemble du marché :
- nombre total de biens
- prix moyen
- prix médian au m²
- répartition maisons / appartements
- distribution des prix

### Marché

Analyse par quartier :
- prix moyen au m²
- score qualité / prix
- graphiques interactifs Plotly
- recommandations de biens

### Recherche

Recherche avancée avec filtres :
- budget
- surface
- type de bien
- nombre de pièces
- équipements

Affichage en cartes avec fiche détaillée.

**Biens sous-évalués**

Détection automatique des opportunités.

Chaque bien reçoit un score d'opportunité de 0 à 100 basé sur :
- le prix estimé par la régression
- l'écart avec le prix annoncé

### Tendances

Analyse temporelle du marché :
- évolution mensuelle du prix au m²
- volume d'annonces
- variation annuelle

---

## Algorithmes implémentés from scratch

Conformément aux consignes du projet, les algorithmes ont été implémentés sans utiliser les fonctions statistiques de numpy ou pandas.

### Statistiques de base

**Implémentées dans :** `analysis/stats.py`

**Fonctions :**
- `mean`
- `median`
- `variance`
- `standard_deviation`
- `covariance`
- `correlation`

Utilisées pour analyser les prix immobiliers.

### Régression linéaire

**Implémentée dans :** `analysis/regression.py`

Permet d'estimer le prix d'un bien en fonction de sa surface.

**Formule :**
```
prix = alpha + beta × surface
```

Le modèle est entraîné sur les données DVF.

### Système de recommandation k-NN

**Implémenté dans :** `analysis/knn.py`

Permet de recommander des biens similaires.

Chaque bien est représenté par un vecteur de **13 caractéristiques** :
- surface
- prix
- prix/m²
- pièces
- chambres
- type de bien
- code postal
- équipements (balcon, terrasse, parking, ascenseur)

### Scoring d'opportunité

**Implémenté dans :** `analysis/scoring.py`

Classe chaque bien :
- **opportunité**
- **prix marché**
- **surévalué**

Basé sur l'écart entre :
- prix annoncé
- vs
- prix prédit par la régression

---

## Tests

Les fonctions sont testées via **pytest**.

Tests présents dans : `tests/`

**Exemples :**
- `test_stats.py`
- `test_regression.py`

---

## Requirements

```
streamlit
pandas
numpy
plotly
requests
beautifulsoup4
lxml
python-dateutil
pytest
python-dotenv
playwright
```

**Installation :**

```bash
pip install -r requirements.txt
```

---

## Références

**Joel Grus** — *Data Science From Scratch*
- Chapitre 5 — Statistics
- Chapitre 12 — k-NN
- Chapitre 14 — Linear Regression

---
