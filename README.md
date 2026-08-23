# Réseau Sous Contrôle — Voir, Comprendre, Anticiper

**Projet PFA (Stage de fin d'études) — Maroc Telecom**

Un système complet de **monitoring QoS** (Quality of Service) pour le réseau national marocain, avec :
- 📊 **Pipeline ETL** (Python)
- 🗄️ **Base de données** (SQL Server)
- 📈 **Dashboard interactif** (Power BI)
- 🤖 **3 modèles ML** comparés (détection d'anomalies)

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Données](#données)
4. [Modèles ML](#modèles-ml)
5. [Résultats](#résultats)
6. [Installation](#installation)
7. [Utilisation](#utilisation)
8. [Conclusions](#conclusions)

---

## 🎯 Vue d'ensemble

Ce projet analyse **6629 mesures de drive-test** collectées sur **26 villes** et **11 régions** du Maroc, couvrant 3 campagnes de mesure (mai, juin, juillet 2026).

**Objectif** : Détecter automatiquement les anomalies réseau et identifier les zones à surveiller en priorité.

---

## 🏗️ Architecture

```
Data Pipeline:

CSV Brut (6629 mesures)
        ↓
[ÉTAPE 1] Python ETL (Nettoyage & Transformation)
        ↓
Données nettoyées (6629 mesures, 22 colonnes)
        ↓
[ÉTAPE 2] SQL Server (Base de données + 19 Vues)
        ↓
Base ReseauSousControle (Tables + Views optimisées)
        ↓
[ÉTAPE 3] Power BI (Dashboard interactif)
        ↓
Tableau de bord professionnel (4 pages, filtres)
        ↓
[ÉTAPE 4] Machine Learning (3 modèles comparés)
        ↓
Modèles sauvegardés + Recommandations
```

---

## 📊 Données

### Source
- **Fichier** : `data/raw/benchmark_drivetest_national_maroc.csv`
- **Lignes** : 6629 mesures
- **Colonnes** : 18 (originales) + 4 (calculées) = 22 colonnes
- **Régions** : 11 (Oriental, Casablanca-Settat, Rabat-Salé-Kénitra, etc.)
- **Villes** : 26
- **Campagnes** : 3 (C1, C2, C3)

### Features principales
- `rsrp_dbm` : Puissance du signal (dBm)
- `rsrq_db` : Qualité du signal (dB)
- `rssi_dbm` : Signal d'interférence (dBm)
- `debit_descendant_mbps` : Débit download (Mbps)
- `debit_montant_mbps` : Débit upload (Mbps)
- `appel_coupe` : Indicateur de coupure d'appel (0/1)
- `anomalie` : Étiquette d'anomalie (0/1) — Ground Truth
- `risque_saturation` : Risque de saturation (0/1)

### Transformations Python
```python
# Colonnes calculées par le pipeline ETL
heure : Heure du jour (0-23)
jour_semaine : Jour de la semaine (Monday, Tuesday, etc.)
qualite_signal : Classification (Bonne/Moyenne/Faible)
risque_saturation : Détection de saturation
```

---

## 🤖 Modèles ML

### Modèle 1 : Isolation Forest (Unsupervised)

**Type** : Détection d'anomalies sans labels

**Architecture** : 100 arbres isolants (anomaly isolation trees)

**Performance** :
- Accuracy : 86.7%
- **Precision : 7.1%** ❌ (beaucoup de faux positifs)
- Recall : 15.0%
- F1-Score : 0.0962

**Cas d'usage** : Exploration de données, pas de labels disponibles

**Fichiers** :
- `ml/isolation_forest_model.pkl` — Modèle entraîné
- `ml/scaler.pkl` — Normalisation

---

### Modèle 2 : Random Forest (Supervised ML)

**Type** : Classification supervisée avec Random Forest

**Architecture** : 100 arbres de décision (max_depth=20)

**Performance** :
- Accuracy : 95.5%
- **Precision : 100.0%** ✅ (PARFAIT — zéro faux positif)
- Recall : 4.8%
- F1-Score : 0.0909
- ROC-AUC : 0.9006

**Feature Importance** (colonnes utiles) :
1. rsrq_db (31.17%) — Qualité du signal → Plus important
2. debit_descendant_mbps (21.21%) — Débits
3. rsrp_dbm (15.72%) — Puissance
4. risque_saturation (0.73%) — Moins important

**Cas d'usage** : Production (détection fiable)

**Fichiers** :
- `ml/random_forest_model.pkl` — Modèle entraîné

---

### Modèle 3 : Neural Network (Deep Learning)

**Type** : Réseau de neurones feedforward

**Architecture** :
```
Input (7) 
  ↓
Dense(32) + ReLU + Dropout(0.2)
  ↓
Dense(16) + ReLU + Dropout(0.2)
  ↓
Dense(8) + ReLU
  ↓
Output(1) + Sigmoid → Probabilité 0-1
```

**Entraînement** : 62 epochs (avec Early Stopping)

**Performance** :
- Accuracy : 95.7%
- Precision : 75.0%
- Recall : 14.3%
- F1-Score : 0.2400
- ROC-AUC : 0.8929

**Cas d'usage** : Apprentissage de patterns non-linéaires

**Fichiers** :
- `ml/neural_network_model.h5` — Modèle Keras

---

## 📈 Résultats

### Comparaison des 3 modèles

```
┌─────────────────────────────────────────────────────────────┐
│           ISOLATION FOREST (Unsupervised)                   │
├─────────────────────────────────────────────────────────────┤
│ Accuracy   : 86.7%                                          │
│ Precision  : 7.1%   ← TRÈS BAS (beaucoup de faux positifs) │
│ Recall     : 15.0%                                          │
│ F1-Score   : 0.0962                                         │
│ Utilité    : Exploration données                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            RANDOM FOREST (Supervised ML) ⭐ GAGNANT         │
├─────────────────────────────────────────────────────────────┤
│ Accuracy   : 95.5%                                          │
│ Precision  : 100.0% ← PARFAIT (zéro faux positif)          │
│ Recall     : 4.8%                                           │
│ F1-Score   : 0.0909                                         │
│ ROC-AUC    : 0.9006                                         │
│ Utilité    : PRODUCTION (fiabilité maximale)                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           NEURAL NETWORK (Deep Learning)                    │
├─────────────────────────────────────────────────────────────┤
│ Accuracy   : 95.7%                                          │
│ Precision  : 75.0%                                          │
│ Recall     : 14.3%                                          │
│ F1-Score   : 0.2400                                         │
│ ROC-AUC    : 0.8929                                         │
│ Utilité    : Patterns complexes                             │
└─────────────────────────────────────────────────────────────┘
```

### Anomalies détectées

**Random Forest** : 3 anomalies réelles sur 1326 mesures de test (très fiable)

Exemples d'anomalies détectées :
- **Rabat 5G** : Débits anormalement élevés (242-570 Mbps)
- **Salé 2G** : Débit très faible (0.02 Mbps)
- **Kénitra 4G** : Signal très faible (-90.4 dBm)

---

## 💾 SQL Server

### Views créées (19 au total)

| Vue | Utilité |
|---|---|
| `vw_Resume_Par_Region` | Résumé par région |
| `vw_Resume_Par_Ville` | Résumé par ville |
| `vw_Resume_Par_Technologie` | Débits par techno (2G/3G/4G/5G) |
| `vw_Resume_Region_Technologie` | Croisement région × techno |
| `vw_Zones_Risque` | Zones avec anomalies |
| `vw_Qualite_Signal_Par_Ville` | Qualité + coordonnées GPS |
| `vw_Resume_Par_Campagne` | Évolution entre campagnes |
| `vw_Resume_Ville_Technologie` | Croisement ville × techno |
| `vw_Resume_Par_Heure` | Patterns horaires |
| `vw_Dashboard_National` | Vue d'ensemble |
| `vw_Top10_Meilleures_Villes` | Top 10 meilleures zones |
| `vw_Top10_Pires_Villes` | Top 10 zones à surveiller |
| `vw_Anomalies_Par_Region` | Concentration anomalies |
| `vw_Matrice_Techno_Region` | Heatmap techno × région |
| `vw_Resume_Par_Jour_Semaine` | Patterns par jour |
| `vw_Zones_Critiques` | Score priorité intervention |
| `vw_Evolution_Campagnes` | Avant/après campagnes |
| `vw_Couverture_Nationale` | % bonne/moyenne/faible couverture |
| `vw_Sante_Generale_Reseau` | Santé globale réseau |

### Stored Procedures

- `sp_Recharger_Donnees` — Recharger le CSV
- `sp_Recalculer_KPIs` — Recalculer les KPIs
- `sp_Nettoyer_Doublons` — Supprimer les duplicatas
- `sp_Nettoyer_Mesures_Invalides` — Nettoyer données malpropres
- `sp_Verifier_Integrite_Base` — Vérifier intégrité

---

## 📊 Power BI Dashboard

### Pages

**Page 1 : Vue d'ensemble**
- 4 KPIs : 26 villes, Moyenne (santé), 6.629K mesures, 73% couverture
- Graphique débits par technologie
- Graphique évolution campagnes
- Filtres : Région, Technologie

**Page 2 : Régions**
- Graphique débits par région
- Graphique anomalies par région
- Tableau résumé par région

**Page 3 : Alertes**
- Tableau Top 10 pires villes (zones à surveiller)
- Tableau Top 10 meilleures villes (performances)

**Page 4 : Patterns**
- Graphique débits par heure (patterns horaires)
- Matrice technologie × région (heatmap)

---

## 🚀 Installation

### Prérequis
- Python 3.10+
- SQL Server Express + SSMS
- Power BI Desktop
- Git

### Étape 1 : Cloner le dépôt
```bash
git clone https://github.com/HoussamLZRK/Reseau-sous-controle.git
cd reseau-sous-controle
```

### Étape 2 : Installer les dépendances Python
```bash
pip install pandas numpy scikit-learn tensorflow sqlalchemy pyodbc --break-system-packages
```

### Étape 3 : Créer la base SQL Server
```bash
# Ouvrir SSMS et exécuter :
sql/create_and_load_db.sql
```

### Étape 4 : Ouvrir Power BI
```bash
# Ouvrir le fichier :
powerbi/Reseau_Sous_Controle_Dashboard.pbix
```

### Étape 5 : Entraîner les modèles ML
```bash
cd ml
python 01_anomaly_detection.py     # Isolation Forest
python 02_random_forest.py         # Random Forest
python 03_deep_learning.py         # Neural Network
```

---

## 📝 Utilisation

### Charger de nouvelles données
```python
# Modifier le chemin du CSV dans :
# ml/01_anomaly_detection.py
# ml/02_random_forest.py
# ml/03_deep_learning.py

data = pd.read_csv('chemin/vers/nouveau/csv.csv')
```

### Faire des prédictions
```python
import pickle

# Charger le meilleur modèle (Random Forest)
with open('ml/random_forest_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Normaliser les nouvelles données
with open('ml/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

X_new = scaler.transform(new_data)
predictions = model.predict(X_new)
```

---

## 🎓 Conclusions

### ✅ Recommandations

**1. En production** : Utiliser **Random Forest**
   - Precision 100% → Zéro faux positif
   - Rapide et interprétable
   - Prêt pour la production

**2. Pour exploration** : Isolation Forest (pas besoin de labels)
   - Utile pour l'exploration initiale
   - Rapide et sans données étiquetées

**3. Pour patterns complexes** : Neural Network
   - Peut capturer des relations non-linéaires
   - Mais Precision inférieure à Random Forest pour ce dataset

### 📊 KPIs Clés du Projet

- **6629 mesures** analysées
- **26 villes** couvertes
- **11 régions** mappées
- **3 modèles ML** comparés
- **100% Precision** (Random Forest)
- **95.5% Accuracy** (Random Forest)
- **19 vues SQL** créées
- **4 pages Power BI** interactives

### 🔮 Améliorations futures

1. Intégrer les prédictions du modèle dans Power BI
2. Ajouter un modèle LSTM pour séries temporelles
3. Implémenter une API Flask pour les prédictions en temps réel
4. Ajouter une carte géographique interactive
5. Mettre en place une alerting automatique

---

## 📞 Auteur

**Mohammed Houssam LAZREK**
- Étudiant INPT, filière INE2 AMOA
- Stage PFA : Maroc Telecom, Direction Générale
- Encadrant : Zakaria SOUKRAT

---

## 📄 Licence

Projet académique — Maroc Telecom (2026)

---

**Dernière mise à jour** : Août 2026
