"""
============================================================
 Projet : Réseau Sous Contrôle — Voir, Comprendre, Anticiper
 Étape 2 : Pipeline ETL — Nettoyage et transformation
============================================================

Ce script lit les données brutes de benchmark (data/raw/), les nettoie,
calcule des indicateurs utiles, et produit un fichier propre dans
data/processed/, prêt à être chargé dans SQL Server et exploité dans
Power BI ou par les modules de Machine Learning.

Étapes réalisées :
    1. Chargement des données brutes
    2. Vérification et nettoyage (valeurs manquantes, doublons, incohérences)
    3. Enrichissement (nouvelles colonnes utiles à l'analyse)
    4. Calcul d'indicateurs agrégés (résumés par ville / technologie)
    5. Export des fichiers nettoyés
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ------------------------------------------------------------------
# Chemins des fichiers (entrée brute -> sortie nettoyée)
# ------------------------------------------------------------------
RAW_PATH = Path("data/raw/benchmark_drivetest_national_maroc.csv")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_MESURES = PROCESSED_DIR / "mesures_nettoyees.csv"
OUTPUT_RESUME_VILLE = PROCESSED_DIR / "resume_par_ville.csv"
OUTPUT_RESUME_TECHNO = PROCESSED_DIR / "resume_par_technologie.csv"


def charger_donnees(chemin: Path) -> pd.DataFrame:
    """Étape 1 : Charge le fichier CSV brut dans un tableau de données (DataFrame)."""
    df = pd.read_csv(chemin, encoding="utf-8-sig")
    print(f"[1/5] Données chargées : {len(df)} lignes, {len(df.columns)} colonnes.")
    return df


def nettoyer_donnees(df: pd.DataFrame) -> pd.DataFrame:
    """Étape 2 : Nettoie les données (doublons, valeurs manquantes, incohérences)."""
    n_avant = len(df)

    # 2.1 Suppression des doublons exacts (même mesure enregistrée deux fois)
    df = df.drop_duplicates(subset=["id_mesure"])

    # 2.2 Suppression des lignes sans coordonnées GPS (mesure inexploitable sans position)
    df = df.dropna(subset=["latitude", "longitude"])

    # 2.3 Vérification que les coordonnées GPS sont bien dans les limites du Maroc
    #     (latitude entre ~27 et ~36, longitude entre ~-14 et ~-1)
    df = df[(df["latitude"].between(20, 37)) & (df["longitude"].between(-18, 0))]

    # 2.4 Correction des technologies mal orthographiées ou en minuscules
    df["technologie"] = df["technologie"].astype(str).str.upper().str.strip()
    technos_valides = ["2G", "3G", "4G", "5G"]
    df = df[df["technologie"].isin(technos_valides)]

    # 2.5 Suppression des débits négatifs ou nuls (impossibles physiquement)
    df = df[(df["debit_descendant_mbps"] > 0) & (df["debit_montant_mbps"] > 0)]

    # 2.6 Conversion de l'horodatage en vrai format de date/heure
    df["horodatage"] = pd.to_datetime(df["horodatage"], errors="coerce")
    df = df.dropna(subset=["horodatage"])

    n_apres = len(df)
    n_supprimees = n_avant - n_apres
    print(f"[2/5] Nettoyage terminé : {n_supprimees} lignes supprimées "
          f"({n_supprimees / n_avant:.1%}), {n_apres} lignes conservées.")
    return df


def enrichir_donnees(df: pd.DataFrame) -> pd.DataFrame:
    """Étape 3 : Ajoute des colonnes utiles calculées à partir des données existantes."""

    # 3.1 Extraction de l'heure et du jour de la semaine (utile pour Power BI et le ML)
    df["heure"] = df["horodatage"].dt.hour
    df["jour_semaine"] = df["horodatage"].dt.day_name()

    # 3.2 Étiquette de qualité simple, basée sur des seuils classiques du métier
    #     (sert de repère lisible pour Power BI, en complément du RSRP brut)
    def classer_qualite(rsrp):
        if rsrp >= -80:
            return "Bonne"
        elif rsrp >= -100:
            return "Moyenne"
        else:
            return "Faible"

    df["qualite_signal"] = df["rsrp_dbm"].apply(classer_qualite)

    # 3.3 Indicateur simple de risque de saturation :
    #     signal correct mais débit très faible = signature d'une cellule surchargée
    df["risque_saturation"] = (
        (df["rsrp_dbm"] >= -95) & (df["debit_descendant_mbps"] < 10)
    ).astype(int)

    print("[3/5] Enrichissement terminé : colonnes 'heure', 'jour_semaine', "
          "'qualite_signal' et 'risque_saturation' ajoutées.")
    return df


def calculer_indicateurs(df: pd.DataFrame):
    """Étape 4 : Calcule des tableaux de synthèse (agrégations) par ville et par technologie."""

    resume_ville = df.groupby(["region", "ville"]).agg(
        nb_mesures=("id_mesure", "count"),
        debit_moyen_dl=("debit_descendant_mbps", "mean"),
        debit_moyen_ul=("debit_montant_mbps", "mean"),
        rsrp_moyen=("rsrp_dbm", "mean"),
        taux_coupure_pct=("appel_coupe", lambda x: x.mean() * 100),
        taux_anomalie_pct=("anomalie", lambda x: x.mean() * 100),
    ).reset_index().round(2)

    resume_techno = df.groupby("technologie").agg(
        nb_mesures=("id_mesure", "count"),
        debit_moyen_dl=("debit_descendant_mbps", "mean"),
        debit_moyen_ul=("debit_montant_mbps", "mean"),
        rsrp_moyen=("rsrp_dbm", "mean"),
        taux_coupure_pct=("appel_coupe", lambda x: x.mean() * 100),
    ).reset_index().round(2)

    print(f"[4/5] Indicateurs calculés : {len(resume_ville)} villes, "
          f"{len(resume_techno)} technologies résumées.")
    return resume_ville, resume_techno


def exporter_resultats(df, resume_ville, resume_techno):
    """Étape 5 : Sauvegarde les fichiers nettoyés et les résumés."""
    df.to_csv(OUTPUT_MESURES, index=False, encoding="utf-8-sig")
    resume_ville.to_csv(OUTPUT_RESUME_VILLE, index=False, encoding="utf-8-sig")
    resume_techno.to_csv(OUTPUT_RESUME_TECHNO, index=False, encoding="utf-8-sig")
    print(f"[5/5] Fichiers exportés dans '{PROCESSED_DIR}/' :")
    print(f"       - {OUTPUT_MESURES.name}")
    print(f"       - {OUTPUT_RESUME_VILLE.name}")
    print(f"       - {OUTPUT_RESUME_TECHNO.name}")


def main():
    print("=" * 60)
    print("PIPELINE ETL — Réseau Sous Contrôle")
    print("=" * 60)

    df = charger_donnees(RAW_PATH)
    df = nettoyer_donnees(df)
    df = enrichir_donnees(df)
    resume_ville, resume_techno = calculer_indicateurs(df)
    exporter_resultats(df, resume_ville, resume_techno)

    print("=" * 60)
    print("Pipeline terminé avec succès.")
    print("=" * 60)


if __name__ == "__main__":
    main()
