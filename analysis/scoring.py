import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def load_data(filepath):
    """Charge les données immobilières"""
    df = pd.read_csv(filepath)
    return df

def train_model(df):
    """Entraîne un modèle de prédiction de prix"""
    # Variables utilisées pour prédire
    features = ['surface', 'nb_pieces', 'code_postal']
    target = 'prix'
    
    df_clean = df[features + [target]].dropna()
    
    X = df_clean[features]
    y = df_clean[target]
    
    model = LinearRegression()
    model.fit(X, y)
    
    return model, df_clean

def predict_prices(model, df):
    """Prédit les prix et calcule le scoring"""
    features = ['surface', 'nb_pieces', 'code_postal']
    
    df['prix_predit'] = model.predict(df[features])
    df['ecart'] = df['prix'] - df['prix_predit']
    df['ecart_pct'] = (df['ecart'] / df['prix_predit']) * 100
    
    return df

def classify_bien(ecart_pct):
    """Classifie un bien : opportunité / prix marché / surévalué"""
    if ecart_pct < -10:
        return 'opportunité'
    elif ecart_pct > 10:
        return 'surévalué'
    else:
        return 'prix marché'

def score_biens(df):
    """Applique la classification à tous les biens"""
    df['scoring'] = df['ecart_pct'].apply(classify_bien)
    return df
