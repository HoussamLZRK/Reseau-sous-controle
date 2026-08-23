"""
Projet : "Réseau Sous Contrôle — Voir, Comprendre, Anticiper"
Module : Détection d'anomalies dans les mesures QoS
Algorithme : Isolation Forest (unsupervised learning)

Utilité : Identifier automatiquement les mesures anormales (débits très bas, signal faible, etc.)
sans avoir besoin d'étiquettes (labels) préexistantes.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score
import pickle
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("DÉTECTION D'ANOMALIES — Isolation Forest")
print("=" * 80)

# ============================================================================
# 1) CHARGER LES DONNÉES DEPUIS LE CSV NETTOYÉ
# ============================================================================

print("\n[1/5] Chargement des données...")

data = pd.read_csv('../data/processed/mesures_nettoyees.csv')

print(f"✓ Données chargées : {len(data)} mesures")
print(f"  Colonnes disponibles : {data.shape[1]}")

# ============================================================================
# 2) PRÉPARER LES FEATURES (caractéristiques) POUR LE MODÈLE
# ============================================================================

print("\n[2/5] Préparation des features...")

# Sélectionner les colonnes numériques pertinentes pour la détection d'anomalies
features = ['rsrp_dbm', 'rsrq_db', 'rssi_dbm', 'debit_descendant_mbps', 
            'debit_montant_mbps', 'appel_coupe', 'risque_saturation']

# Créer une copie des données avec uniquement les features
X = data[features].copy()

# Vérifier les valeurs manquantes
print(f"  Valeurs manquantes par colonne :")
print(X.isnull().sum())

# Remplir les valeurs manquantes avec la médiane (valeur centrale)
X = X.fillna(X.median())

print(f"✓ Features préparées : {X.shape[0]} mesures × {X.shape[1]} colonnes")
print(f"  Colonnes : {list(features)}")

# ============================================================================
# 3) NORMALISER LES DONNÉES (StandardScaler)
# ============================================================================

print("\n[3/5] Normalisation des données...")

# StandardScaler met toutes les colonnes sur la même échelle (moyenne=0, écart-type=1)
# Pourquoi ? Isolation Forest fonctionne mieux quand toutes les variables sont comparables
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"✓ Données normalisées")
print(f"  Moyenne après normalisation : {X_scaled.mean():.4f}")
print(f"  Écart-type après normalisation : {X_scaled.std():.4f}")

# ============================================================================
# 4) ENTRAÎNER LE MODÈLE ISOLATION FOREST
# ============================================================================

print("\n[4/5] Entraînement du modèle Isolation Forest...")

# contamination = pourcentage d'anomalies attendues
# On estime qu'environ 10% des mesures sont anormales
isolation_forest = IsolationForest(
    contamination=0.10,      # 10% d'anomalies
    random_state=42,         # seed pour reproductibilité
    n_estimators=100         # nombre d'arbres de décision
)

# Entraîner le modèle
predictions = isolation_forest.fit_predict(X_scaled)

# -1 = anomalie, +1 = normal
n_anomalies = (predictions == -1).sum()
n_normal = (predictions == 1).sum()

print(f"✓ Modèle entraîné")
print(f"  Anomalies détectées : {n_anomalies} ({100*n_anomalies/len(predictions):.1f}%)")
print(f"  Mesures normales : {n_normal} ({100*n_normal/len(predictions):.1f}%)")

# ============================================================================
# 5) ÉVALUATION DU MODÈLE (comparer avec les étiquettes du CSV)
# ============================================================================

print("\n[5/5] Évaluation du modèle...")

# Prendre la colonne 'anomalie' du CSV comme référence (ground truth)
y_true = data['anomalie'].values

# Convertir les prédictions : -1 → 1 (anomalie), +1 → 0 (normal)
y_pred = (predictions == -1).astype(int)

# Matrice de confusion
tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

print(f"\n  Matrice de confusion :")
print(f"  ┌─────────────────────────────────┐")
print(f"  │ Vrais Négatifs (TN)  : {tn:>6} │")
print(f"  │ Faux Positifs (FP)   : {fp:>6} │")
print(f"  │ Faux Négatifs (FN)   : {fn:>6} │")
print(f"  │ Vrais Positifs (TP)  : {tp:>6} │")
print(f"  └─────────────────────────────────┘")

# Calcul des métriques
accuracy = (tp + tn) / (tp + tn + fp + fn)
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

print(f"\n  Métriques :")
print(f"  ┌─────────────────────────────────┐")
print(f"  │ Accuracy  : {accuracy:.4f} ({accuracy*100:.1f}%)         │")
print(f"  │ Precision : {precision:.4f} ({precision*100:.1f}%)         │")
print(f"  │ Recall    : {recall:.4f} ({recall*100:.1f}%)         │")
print(f"  │ F1-Score  : {f1_score:.4f}                   │")
print(f"  └─────────────────────────────────┘")

# ============================================================================
# 6) SAUVEGARDER LE MODÈLE ET LE SCALER
# ============================================================================

print(f"\n[SAUVEGARDE] Enregistrement du modèle et du scaler...")

# Sauvegarder le modèle entraîné
with open('../ml/isolation_forest_model.pkl', 'wb') as f:
    pickle.dump(isolation_forest, f)
print(f"  ✓ Modèle sauvegardé : isolation_forest_model.pkl")

# Sauvegarder le scaler (important pour normaliser les futures données)
with open('../ml/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
print(f"  ✓ Scaler sauvegardé : scaler.pkl")

# ============================================================================
# 7) CRÉER UN DATAFRAME DE RÉSULTATS
# ============================================================================

print(f"\n[RÉSULTATS] Création du fichier de résultats...")

# Ajouter les prédictions au dataframe original
results = data.copy()
results['anomaly_predicted'] = predictions
results['is_anomaly'] = y_pred

# Garder seulement les anomalies détectées
anomalies_df = results[results['is_anomaly'] == 1][
    ['id_mesure', 'ville', 'technologie', 'rsrp_dbm', 'debit_descendant_mbps', 
     'anomalie', 'is_anomaly']
].head(20)

print(f"  Top 20 anomalies détectées :")
print(anomalies_df.to_string(index=False))

# Sauvegarder tous les résultats
results.to_csv('../data/processed/anomaly_detection_results.csv', index=False)
print(f"\n  ✓ Résultats complets sauvegardés : anomaly_detection_results.csv")

# ============================================================================
# 8) RÉSUMÉ FINAL
# ============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ FINAL")
print("=" * 80)
print(f"""
✓ Modèle Isolation Forest entraîné et sauvegardé
✓ {n_anomalies} anomalies détectées sur {len(data)} mesures
✓ Accuracy : {accuracy*100:.1f}%
✓ Fichiers générés :
  - isolation_forest_model.pkl (le modèle)
  - scaler.pkl (pour normaliser les futures données)
  - anomaly_detection_results.csv (résultats complets)

Prochaines étapes :
→ Créer un script pour utiliser ce modèle sur de nouvelles données
→ Intégrer les prédictions dans Power BI
→ Comparer avec d'autres algorithmes (Random Forest, Deep Learning)
""")

print("=" * 80)