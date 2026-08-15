# Réseau Sous Contrôle — Voir, Comprendre, Anticiper

Projet de Fin d'Année (PFA) — INPT (INE2, AMOA)
Réalisé chez **Maroc Telecom**, Direction Générale, Hay Riad (Rabat)
Encadrant entreprise : **M. Zakaria SOUKRAT**

## Objectif du projet

Construire une chaîne complète de supervision de la qualité de service (QoS) du réseau
mobile à l'échelle **nationale**, combinant :

- **Data Engineering** : nettoyage et structuration des données de campagnes de mesure terrain (benchmark / drive test)
- **Business Intelligence** : tableau de bord Power BI (carte nationale, comparaisons régionales, indicateurs)
- **Intelligence Artificielle** : prédiction de la qualité réseau et détection automatique des zones à risque (Machine Learning + exploration Deep Learning)

Voir le [cahier des charges complet](docs/Reseau_Sous_Controle_Cahier_des_charges.docx) pour le détail du contexte, des objectifs et de l'architecture.

## Architecture du projet

```
Données brutes (CSV)  →  Nettoyage Python (ETL)  →  Base SQL Server  →  Power BI
                                                            ↓
                                                  Modèles Machine Learning / Deep Learning
```

## Structure du dépôt

```
reseau-sous-controle/
├── data/
│   ├── raw/              # Données brutes (exports simulés de benchmark)
│   └── processed/        # Données nettoyées, prêtes pour SQL Server
├── sql/                  # Scripts de création et chargement de la base SQL Server
├── etl/                  # Scripts Python de génération et nettoyage des données
├── ml/                   # Modèles de Machine Learning et Deep Learning
├── powerbi/              # Fichier(s) Power BI (.pbix)
├── docs/                 # Cahier des charges et documentation
└── requirements.txt      # Dépendances Python
```

## Données

Le jeu de données couvre **11 régions** et **26 villes** du Maroc, sur **3 campagnes**
de mesure simulées (mai, juin, juillet 2026), pour un total d'environ **6 600 mesures**.

Chaque mesure contient : région, ville, position GPS, technologie (2G/3G/4G/5G),
indicateurs radio (RSRP, RSRQ, RSSI), débits mesurés, coupures d'appel, et une étiquette
d'anomalie utilisée comme référence pour l'évaluation des modèles Machine Learning.

> Données simulées de façon réaliste (cf. `etl/01_generate_simulated_data.py`), en l'absence
> d'accès à des données réelles de campagnes Maroc Telecom au moment de la rédaction.

## Avancement du projet

- [x] Cadrage et cahier des charges
- [x] Génération du jeu de données national simulé
- [x] Script de création de la base SQL Server
- [ ] Pipeline Python de nettoyage (ETL)
- [ ] Tableau de bord Power BI
- [ ] Module Machine Learning — prédiction de la qualité réseau
- [ ] Module Machine Learning — détection d'anomalies
- [ ] Module Deep Learning — comparaison avec le Machine Learning classique
- [ ] Rapport de stage final

## Installation

```bash
git clone <url-du-depot>
cd reseau-sous-controle
pip install -r requirements.txt
```

## Auteur

**Mohammed Houssam LAZREK** — INPT, filière INE2 AMOA
