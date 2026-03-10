# resultats de l'analyse de regression

## donnees

- **source** : dvf (demandes de valeurs foncieres) 2024-2025, toulon (insee 83137)
- **transactions initiales** : 4050
- **transactions apres nettoyage** : 3610 (89.1% de retention)
- **methode de nettoyage** : detection automatique des outliers avec iqr (interquartile range)

### statistiques descriptives

```
surface (m²)
  moyenne : 70.94 m²
  mediane : 63.00 m²
  min-max : 10.00 - 132.50 m²

prix (euros)
  moyenne : 213,925 euros
  mediane : 157,235 euros
  min-max : 20,000 - 500,000 euros

prix au m² (euros)
  moyenne : 3,069 euros/m²
  mediane : 2,766 euros/m²
```

## modeles de regression

### 1. regression lineaire simple (surface uniquement)

**formule** : `prix = 8,228 + 2,682 * surface`

**performance** :
- r² = 0.4198 (41.98% de variance expliquee)
- correlation = 0.6480

**interpretation** :
- coefficient surface : 2,682 euros/m²
- ordonnee origine : 8,228 euros (prix de base)

### 2. regression lineaire multiple (surface + type de bien)

**formule** : `prix = 22,035 + 2,271 * surface + 122,934 * is_maison`

**performance** :
- r² = 0.5463 (54.63% de variance expliquee)
- gain vs regression simple : +12.64 points

**interpretation** :
- coefficient surface : 2,271 euros/m²
- coefficient maison : +122,934 euros (prime pour une maison vs appartement)
- ordonnee origine : 22,035 euros

**exemple de predictions pour 70 m²** :
- appartement : 180,975 euros (2,585 euros/m²)
- maison : 303,909 euros (4,341 euros/m²)
- difference : 122,934 euros

### 3. regression lineaire multiple complete (surface + type + code postal) ⭐

**formule** : `prix = 14,545 + 2,275 * surface + 130,584 * is_maison + 17,630 * is_cp83000 + (-7,442) * is_cp83200`

**performance** :
- r² = 0.5602 (56.02% de variance expliquee)
- gain vs modele 2 : +1.39 points
- gain total vs regression simple : +14.04 points

**interpretation** :
- coefficient surface : 2,275 euros/m²
- coefficient maison : +130,584 euros (prime maison vs appartement)
- effet quartier 83000 (centre) : +17,630 euros vs 83100 (reference)
- effet quartier 83200 (est) : -7,442 euros vs 83100 (reference)

**hierarchie des quartiers** (a surface et type egaux) :
1. 83000 (centre-ville) : le plus cher
2. 83100 (ouest) : reference (baseline)
3. 83200 (est) : le moins cher
4. ecart max entre quartiers : 25,072 euros

**exemple de predictions pour un appartement de 70 m²** :
- 83000 (centre) : 188,816 euros
- 83100 (ouest) : 171,186 euros
- 83200 (est) : 163,744 euros

## algorithmes implementes (from scratch)

### fichier : `analysis/stats.py`
- `mean()` : moyenne arithmetique
- `median()` : valeur mediane
- `variance()` : variance echantillonnale
- `standard_deviation()` : ecart-type
- `covariance()` : covariance entre deux variables
- `correlation()` : coefficient de pearson

### fichier : `analysis/regression.py`
- `predict()` : prediction y = alpha + beta * x
- `error()` : erreur de prediction
- `sum_of_sqerrors()` : somme des erreurs au carre (ssr)
- `least_squares_fit()` : regression lineaire simple par moindres carres
- `r_squared()` : coefficient de determination

### fichier : `analysis/regression_multiple.py`
- `predict_multiple()` : prediction avec plusieurs variables
- `error_multiple()` : erreur en regression multiple
- `sum_of_sqerrors_multiple()` : ssr pour regression multiple
- `normalize_features()` : normalisation des variables (mean=0, std=1)
- `least_squares_fit_multiple()` : regression multiple par descente de gradient
- `r_squared_multiple()` : r² pour regression multiple

### fichier : `data/cleaning_advanced.py`
- detection automatique des outliers avec methode iqr
- filtrage intelligent des transactions aberrantes
- agregation des lots multiples (cave, parking, etc.)

## ameliorations realisees

1. **nettoyage avance des donnees** : +3.3 points de r² (0.386 → 0.420)
2. **ajout du type de bien** : +12.6 points de r² (0.420 → 0.546)
3. **ajout du code postal** : +1.4 points de r² (0.546 → 0.560)
4. **gain total** : +17.4 points de r² (0.386 → 0.560)

## pour aller plus loin

### ameliorations possibles :
- creer des variables derivees (prix moyen du quartier, distance centre-ville)
- implementer regression polynomiale (surface²)
- ajouter des variables temporelles (mois, annee)
- implementer regularisation (ridge, lasso) from scratch
- ajouter interactions (surface * type, surface * quartier)

### limitations actuelles :
- 56.0% de variance expliquee : il reste 44.0% de variance non capturee
- variables manquantes importantes : etat du bien, etage, balcon, parking, vue mer
- modele lineaire : pourrait beneficier de non-linearites
- effet quartier faible a toulon (1.4% d'ecart) : structure de prix homogene
