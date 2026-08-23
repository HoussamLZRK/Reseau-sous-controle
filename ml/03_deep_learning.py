"""
Projet : "Réseau Sous Contrôle — Voir, Comprendre, Anticiper"
Module : Détection d'anomalies avec Deep Learning
Algorithme : Neural Network (Keras/TensorFlow)

Comparaison des 3 modèles :
1. Isolation Forest (unsupervised) : Precision 7.1%
2. Random Forest (supervised) : Precision 100.0%
3. Neural Network (deep learning) : Precision ?

Objectif : Voir si le Deep Learning peut matcher ou dépasser Random Forest
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score, roc_curve
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Sequential
from tensorflow.keras.callbacks import EarlyStopping
import pickle
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("DÉTECTION D'ANOMALIES — Deep Learning Neural Network")
print("=" * 80)

# ============================================================================
# 1) CHARGER LES DONNÉES
# ============================================================================

print("\n[1/7] Chargement des données...")

data = pd.read_csv('../data/processed/mesures_nettoyees.csv')

print(f"✓ Données chargées : {len(data)} mesures")

# ============================================================================
# 2) PRÉPARER LES FEATURES ET LABELS
# ============================================================================

print("\n[2/7] Préparation des features et labels...")

features = ['rsrp_dbm', 'rsrq_db', 'rssi_dbm', 'debit_descendant_mbps', 
            'debit_montant_mbps', 'appel_coupe', 'risque_saturation']

X = data[features].copy()
X = X.fillna(X.median())
y = data['anomalie'].values

print(f"✓ Features : {X.shape[1]} colonnes")
print(f"✓ Labels : {len(y)} mesures")
print(f"  Distribution des labels :")
print(f"    - Mesures normales (0) : {(y == 0).sum()} ({100*(y == 0).sum()/len(y):.1f}%)")
print(f"    - Anomalies (1) : {(y == 1).sum()} ({100*(y == 1).sum()/len(y):.1f}%)")

# ============================================================================
# 3) SPLIT TRAIN/TEST (80/20)
# ============================================================================

print("\n[3/7] Split train/test (80/20)...")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

print(f"✓ Données d'entraînement : {len(X_train)} mesures")
print(f"✓ Données de test : {len(X_test)} mesures")

# ============================================================================
# 4) NORMALISER LES DONNÉES
# ============================================================================

print("\n[4/7] Normalisation des données...")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"✓ Données normalisées")

# ============================================================================
# 5) CRÉER ET CONFIGURER LE MODÈLE NEURAL NETWORK
# ============================================================================

print("\n[5/7] Création du modèle Neural Network...")

# Architecture du réseau :
# Input (7) → Dense(32) → ReLU → Dropout(0.2) 
#          → Dense(16) → ReLU → Dropout(0.2)
#          → Dense(8) → ReLU
#          → Output(1) → Sigmoid (probabilité 0-1)

model = Sequential([
    layers.Dense(32, activation='relu', input_shape=(len(features),)),
    layers.Dropout(0.2),
    
    layers.Dense(16, activation='relu'),
    layers.Dropout(0.2),
    
    layers.Dense(8, activation='relu'),
    
    layers.Dense(1, activation='sigmoid')  # Sortie : probabilité 0-1
])

# Compiler le modèle
model.compile(
    optimizer='adam',
    loss='binary_crossentropy',  # Pour classification binaire (anomalie ou non)
    metrics=['accuracy', 'AUC']
)

print(f"✓ Modèle créé")
print(f"\nArchitecture du réseau :")
model.summary()

# ============================================================================
# 6) ENTRAÎNER LE MODÈLE
# ============================================================================

print("\n[6/7] Entraînement du modèle...")

# Callback pour arrêter l'entraînement si ça n'améliore plus
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Entraîner le modèle
history = model.fit(
    X_train_scaled, y_train,
    epochs=100,
    batch_size=32,
    validation_split=0.2,
    callbacks=[early_stop],
    verbose=0
)

print(f"✓ Modèle entraîné en {len(history.history['loss'])} epochs")

# ============================================================================
# 7) ÉVALUATION DU MODÈLE
# ============================================================================

print("\n[7/7] Évaluation du modèle...")

# Prédictions sur les données de test
y_pred_proba = model.predict(X_test_scaled, verbose=0).flatten()
y_pred = (y_pred_proba > 0.5).astype(int)

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
roc_auc = roc_auc_score(y_test, y_pred_proba)

print(f"\n  Métriques :")
print(f"  ┌─────────────────────────────────┐")
print(f"  │ Accuracy  : {accuracy:.4f} ({accuracy*100:.1f}%)         │")
print(f"  │ Precision : {precision:.4f} ({precision*100:.1f}%)         │")
print(f"  │ Recall    : {recall:.4f} ({recall*100:.1f}%)         │")
print(f"  │ F1-Score  : {f1_score:.4f}                   │")
print(f"  │ ROC-AUC   : {roc_auc:.4f}                   │")
print(f"  └─────────────────────────────────┘")

# ============================================================================
# 8) SAUVEGARDER LE MODÈLE
# ============================================================================

print(f"\n[SAUVEGARDE] Enregistrement du modèle...")

model.save('../ml/neural_network_model.h5')
print(f"  ✓ Modèle sauvegardé : neural_network_model.h5")

# ============================================================================
# 9) COMPARAISON DES 3 MODÈLES
# ============================================================================

print("\n" + "=" * 80)
print("COMPARAISON DES 3 MODÈLES")
print("=" * 80)

print(f"""
┌──────────────────────────────────────────────────────────────┐
│            ISOLATION FOREST (Unsupervised)                   │
├──────────────────────────────────────────────────────────────┤
│ Accuracy         : 86.7%                                     │
│ Precision        : 7.1%   ← TRÈS BAS                         │
│ Recall           : 15.0%                                     │
│ F1-Score         : 0.0962                                    │
│ Cas d'usage      : Exploration sans labels                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│             RANDOM FOREST (Supervised ML)                    │
├──────────────────────────────────────────────────────────────┤
│ Accuracy         : 95.5%                                     │
│ Precision        : 100.0% ← PARFAIT                          │
│ Recall           : 4.8%                                      │
│ F1-Score         : 0.0909                                    │
│ ROC-AUC          : 0.9006                                    │
│ Cas d'usage      : Production (fiabilité maximale)           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│          NEURAL NETWORK (Deep Learning)                      │
├──────────────────────────────────────────────────────────────┤
│ Accuracy         : {accuracy*100:.1f}%                                     │
│ Precision        : {precision*100:.1f}%                                    │
│ Recall           : {recall*100:.1f}%                                       │
│ F1-Score         : {f1_score:.4f}                                  │
│ ROC-AUC          : {roc_auc:.4f}                                  │
│ Cas d'usage      : Apprentissage complexe (non-linéaire)    │
└──────────────────────────────────────────────────────────────┘

VERDICT :
─────────
✓ Random Forest : Meilleure Precision (100%) → À préférer en production
✓ Neural Network : Peut matcher ou dépasser RF selon les données
✓ Isolation Forest : Utile pour l'exploration sans labels

RECOMMANDATION FINALE :
──────────────────────
→ Utiliser RANDOM FOREST en production (100% Precision)
→ Comparer avec Deep Learning pour les cas complexes
→ Isolation Forest pour l'exploration initiale
""")

print("=" * 80)