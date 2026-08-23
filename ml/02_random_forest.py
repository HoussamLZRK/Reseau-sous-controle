"""
Projet : "Réseau Sous Contrôle — Voir, Comprendre, Anticiper"
Module : Détection d'anomalies avec Random Forest
Algorithme : Random Forest (supervised learning)

Différence avec Isolation Forest :
- IF : unsupervised (pas de labels nécessaires)
- RF : supervised (utilise les labels du CSV : colonne 'anomalie')

Résultat attendu : Precision BEAUCOUP plus haute (~75-80%)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score, roc_curve
import pickle
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("DÉTECTION D'ANOMALIES — Random Forest (Supervised)")
print("=" * 80)

# ============================================================================
# 1) CHARGER LES DONNÉES
# ============================================================================

print("\n[1/6] Chargement des données...")

data = pd.read_csv('../data/processed/mesures_nettoyees.csv')

print(f"✓ Données chargées : {len(data)} mesures")

# ============================================================================
# 2) PRÉPARER LES FEATURES ET LABELS
# ============================================================================

print("\n[2/6] Préparation des features et labels...")

# Features (caractéristiques)
features = ['rsrp_dbm', 'rsrq_db', 'rssi_dbm', 'debit_descendant_mbps', 
            'debit_montant_mbps', 'appel_coupe', 'risque_saturation']

X = data[features].copy()
X = X.fillna(X.median())

# Labels (cible) — c'est ce qu'on veut prédire
y = data['anomalie'].values

print(f"✓ Features : {X.shape[1]} colonnes")
print(f"✓ Labels : {len(y)} mesures")
print(f"  Distribution des labels :")
print(f"    - Mesures normales (0) : {(y == 0).sum()} ({100*(y == 0).sum()/len(y):.1f}%)")
print(f"    - Anomalies (1) : {(y == 1).sum()} ({100*(y == 1).sum()/len(y):.1f}%)")

# ============================================================================
# 3) SPLIT TRAIN/TEST (80% entraînement, 20% test)
# ============================================================================

print("\n[3/6] Split train/test (80/20)...")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

print(f"✓ Données d'entraînement : {len(X_train)} mesures")
print(f"✓ Données de test : {len(X_test)} mesures")

# ============================================================================
# 4) NORMALISER LES DONNÉES
# ============================================================================

print("\n[4/6] Normalisation des données...")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"✓ Données normalisées (moyenne=0, écart-type=1)")

# ============================================================================
# 5) ENTRAÎNER LE MODÈLE RANDOM FOREST
# ============================================================================

print("\n[5/6] Entraînement du modèle Random Forest...")

random_forest = RandomForestClassifier(
    n_estimators=100,        # 100 arbres de décision
    max_depth=20,            # profondeur maximale de chaque arbre
    min_samples_split=10,    # minimum de points pour splitter un nœud
    min_samples_leaf=5,      # minimum de points dans une feuille
    random_state=42,
    n_jobs=-1                # utiliser tous les CPU
)

# Entraîner sur les données d'entraînement
random_forest.fit(X_train_scaled, y_train)

print(f"✓ Modèle entraîné")

# Prédictions sur les données de test
y_pred = random_forest.predict(X_test_scaled)
y_pred_proba = random_forest.predict_proba(X_test_scaled)[:, 1]

# ============================================================================
# 6) ÉVALUATION DU MODÈLE
# ============================================================================

print("\n[6/6] Évaluation du modèle...")

# Matrice de confusion
tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

print(f"\n  Matrice de confusion :")
print(f"  ┌─────────────────────────────────┐")
print(f"  │ Vrais Négatifs (TN)  : {tn:>6} │")
print(f"  │ Faux Positifs (FP)   : {fp:>6} │")
print(f"  │ Faux Négatifs (FN)   : {fn:>6} │")
print(f"  │ Vrais Positifs (TP)  : {tp:>6} │")
print(f"  └─────────────────────────────────┘")

# Métriques
accuracy = (tp + tn) / (tp + tn + fp + fn)
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

# ROC-AUC
try:
    roc_auc = roc_auc_score(y_test, y_pred_proba)
except:
    roc_auc = 0

print(f"\n  Métriques :")
print(f"  ┌─────────────────────────────────┐")
print(f"  │ Accuracy  : {accuracy:.4f} ({accuracy*100:.1f}%)         │")
print(f"  │ Precision : {precision:.4f} ({precision*100:.1f}%)         │")
print(f"  │ Recall    : {recall:.4f} ({recall*100:.1f}%)         │")
print(f"  │ F1-Score  : {f1_score:.4f}                   │")
print(f"  │ ROC-AUC   : {roc_auc:.4f}                   │")
print(f"  └─────────────────────────────────┘")

# Feature importance (quelles colonnes sont les plus utiles)
print(f"\n  Feature importance (utilité de chaque feature) :")
feature_importance = pd.DataFrame({
    'Feature': features,
    'Importance': random_forest.feature_importances_
}).sort_values('Importance', ascending=False)

for idx, row in feature_importance.iterrows():
    print(f"    {row['Feature']:25s} : {row['Importance']:.4f}")

# ============================================================================
# 7) SAUVEGARDER LE MODÈLE
# ============================================================================

print(f"\n[SAUVEGARDE] Enregistrement du modèle...")

with open('../ml/random_forest_model.pkl', 'wb') as f:
    pickle.dump(random_forest, f)
print(f"  ✓ Modèle sauvegardé : random_forest_model.pkl")

# ============================================================================
# 8) COMPARAISON AVEC ISOLATION FOREST
# ============================================================================

print("\n" + "=" * 80)
print("COMPARAISON : Isolation Forest vs Random Forest")
print("=" * 80)

print(f"""
┌────────────────────────────────────────────────────────────┐
│                  ISOLATION FOREST (IF)                     │
├────────────────────────────────────────────────────────────┤
│ Type             : Unsupervised (pas de labels)            │
│ Accuracy         : 86.7%                                   │
│ Precision        : 7.1%  ← TRÈS BAS                        │
│ Recall           : 15.0%                                   │
│ F1-Score         : 0.0962                                  │
│ Avantage         : Rapide, pas besoin de labels            │
│ Inconvénient     : Peu fiable (beaucoup de faux positifs)  │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                   RANDOM FOREST (RF)                       │
├────────────────────────────────────────────────────────────┤
│ Type             : Supervised (utilise les labels)         │
│ Accuracy         : {accuracy*100:.1f}%                                   │
│ Precision        : {precision*100:.1f}%  ← BEAUCOUP MIEUX               │
│ Recall           : {recall*100:.1f}%                                   │
│ F1-Score         : {f1_score:.4f}                                  │
│ ROC-AUC          : {roc_auc:.4f}                                  │
│ Avantage         : BIEN PLUS FIABLE                        │
│ Inconvénient     : Nécessite des données étiquetées        │
└────────────────────────────────────────────────────────────┘

✓ CONCLUSION : Random Forest est BEAUCOUP PLUS PRÉCIS ! ({precision*100:.1f}% vs 7.1%)
→ À utiliser en production pour détecter les vraies anomalies
→ Isolation Forest utile pour l'exploration sans labels
""")

print("=" * 80)