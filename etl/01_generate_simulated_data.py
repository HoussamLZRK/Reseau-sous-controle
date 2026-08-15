"""
Générateur de données simulées de benchmark (Drive Test) — Échelle NATIONALE (Maroc)
Simule un export type TEMS Investigation / Nemo Outdoor, agrégé sur plusieurs régions.
Projet : "Réseau Sous Contrôle — Voir, Comprendre, Anticiper"
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ---------------------------------------------------------
# 1. Régions et villes du Maroc avec coordonnées GPS approximatives
#    "type" influence le profil de qualité réseau simulé
# ---------------------------------------------------------
zones = {
    # Rabat-Salé-Kénitra
    "Rabat":        {"lat": 34.0209, "lon": -6.8416, "region": "Rabat-Salé-Kénitra", "type": "urbain_dense"},
    "Salé":         {"lat": 34.0531, "lon": -6.7985, "region": "Rabat-Salé-Kénitra", "type": "urbain_moyen"},
    "Kénitra":      {"lat": 34.2610, "lon": -6.5802, "region": "Rabat-Salé-Kénitra", "type": "urbain_moyen"},

    # Casablanca-Settat
    "Casablanca":   {"lat": 33.5731, "lon": -7.5898, "region": "Casablanca-Settat", "type": "urbain_sature"},  # forte densité
    "Mohammedia":   {"lat": 33.6862, "lon": -7.3831, "region": "Casablanca-Settat", "type": "urbain_moyen"},
    "Settat":       {"lat": 33.0010, "lon": -7.6166, "region": "Casablanca-Settat", "type": "semi_urbain"},

    # Marrakech-Safi
    "Marrakech":    {"lat": 31.6295, "lon": -7.9811, "region": "Marrakech-Safi", "type": "urbain_dense"},
    "Safi":         {"lat": 32.2994, "lon": -9.2372, "region": "Marrakech-Safi", "type": "semi_urbain"},
    "Essaouira":    {"lat": 31.5085, "lon": -9.7595, "region": "Marrakech-Safi", "type": "cotier_saisonnier"},

    # Fès-Meknès
    "Fès":          {"lat": 34.0181, "lon": -5.0078, "region": "Fès-Meknès", "type": "urbain_dense"},
    "Meknès":       {"lat": 33.8935, "lon": -5.5473, "region": "Fès-Meknès", "type": "urbain_moyen"},
    "Ifrane":       {"lat": 33.5228, "lon": -5.1106, "region": "Fès-Meknès", "type": "rural"},

    # Tanger-Tétouan-Al Hoceïma
    "Tanger":       {"lat": 35.7595, "lon": -5.8340, "region": "Tanger-Tétouan-Al Hoceïma", "type": "urbain_sature"},
    "Tétouan":      {"lat": 35.5785, "lon": -5.3684, "region": "Tanger-Tétouan-Al Hoceïma", "type": "urbain_moyen"},
    "Al Hoceïma":   {"lat": 35.2517, "lon": -3.9372, "region": "Tanger-Tétouan-Al Hoceïma", "type": "rural"},

    # Oriental
    "Oujda":        {"lat": 34.6814, "lon": -1.9086, "region": "Oriental", "type": "urbain_dense"},
    "Nador":        {"lat": 35.1681, "lon": -2.9287, "region": "Oriental", "type": "urbain_sature"},  # cas du rapport
    "Berkane":      {"lat": 34.9218, "lon": -2.3200, "region": "Oriental", "type": "urbain_moyen"},

    # Souss-Massa
    "Agadir":       {"lat": 30.4278, "lon": -9.5981, "region": "Souss-Massa", "type": "urbain_dense"},
    "Taroudant":    {"lat": 30.4703, "lon": -8.8770, "region": "Souss-Massa", "type": "rural"},

    # Béni Mellal-Khénifra
    "Béni Mellal":  {"lat": 32.3373, "lon": -6.3498, "region": "Béni Mellal-Khénifra", "type": "semi_urbain"},
    "Khénifra":     {"lat": 32.9394, "lon": -5.6694, "region": "Béni Mellal-Khénifra", "type": "rural"},

    # Drâa-Tafilalet
    "Errachidia":   {"lat": 31.9314, "lon": -4.4241, "region": "Drâa-Tafilalet", "type": "rural"},
    "Ouarzazate":   {"lat": 30.9335, "lon": -6.9370, "region": "Drâa-Tafilalet", "type": "rural"},

    # Guelmim-Oued Noun
    "Guelmim":      {"lat": 28.9870, "lon": -10.0574, "region": "Guelmim-Oued Noun", "type": "rural"},

    # Laâyoune-Sakia El Hamra
    "Laâyoune":     {"lat": 27.1418, "lon": -13.1873, "region": "Laâyoune-Sakia El Hamra", "type": "semi_urbain"},
}

technologies = ["2G", "3G", "4G", "5G"]
tech_weights = [0.08, 0.17, 0.55, 0.20]  # répartition réaliste, 5G en croissance

# ---------------------------------------------------------
# 2. Génération d'une mesure selon la techno et le profil de zone
# ---------------------------------------------------------
def generate_measurement(tech, zone_type):
    base_ranges = {
        "2G": {"rsrp": (-100, -75), "rsrq": (-12, -6), "dl": (0.02, 0.1), "ul": (0.01, 0.05)},
        "3G": {"rsrp": (-105, -80), "rsrq": (-14, -7), "dl": (0.5, 6), "ul": (0.2, 2)},
        "4G": {"rsrp": (-110, -75), "rsrq": (-16, -6), "dl": (5, 120), "ul": (2, 40)},
        "5G": {"rsrp": (-105, -70), "rsrq": (-15, -5), "dl": (50, 600), "ul": (20, 150)},
    }
    r = base_ranges[tech]
    rsrp = np.random.uniform(*r["rsrp"])
    rsrq = np.random.uniform(*r["rsrq"])
    rssi = rsrp + np.random.uniform(3, 8)
    dl = np.random.uniform(*r["dl"])
    ul = np.random.uniform(*r["ul"])
    call_drop = 0
    anomalie = 0  # étiquette utile plus tard pour évaluer les modèles ML

    if zone_type == "rural":
        rsrp -= np.random.uniform(5, 15)
        dl *= np.random.uniform(0.3, 0.6)
        call_drop = np.random.choice([0, 1], p=[0.90, 0.10])

    if zone_type == "urbain_sature":
        rsrp -= np.random.uniform(2, 6)
        rsrq -= np.random.uniform(3, 8)
        dl *= np.random.uniform(0.15, 0.4)
        call_drop = np.random.choice([0, 1], p=[0.85, 0.15])
        anomalie = np.random.choice([0, 1], p=[0.7, 0.3])

    if zone_type == "cotier_saisonnier":
        dl *= np.random.uniform(0.5, 1.0)
        call_drop = np.random.choice([0, 1], p=[0.95, 0.05])

    if zone_type in ("urbain_dense", "urbain_moyen", "semi_urbain"):
        call_drop = np.random.choice([0, 1], p=[0.97, 0.03])

    # Bruit aléatoire additionnel (points aberrants isolés, ~1.5% des mesures)
    if np.random.rand() < 0.015:
        dl *= np.random.uniform(0.05, 0.2)
        rsrp -= np.random.uniform(10, 20)
        anomalie = 1

    return round(rsrp, 1), round(rsrq, 1), round(rssi, 1), round(dl, 2), round(ul, 2), int(call_drop), int(anomalie)


# ---------------------------------------------------------
# 3. Génération du trajet national (plusieurs campagnes / dates)
# ---------------------------------------------------------
rows = []
point_id = 1
campaign_dates = [
    datetime(2026, 5, 5, 8, 0, 0),
    datetime(2026, 6, 9, 8, 0, 0),
    datetime(2026, 7, 14, 8, 0, 0),
]

operateur = "IAM"

for campagne_num, start_time in enumerate(campaign_dates, start=1):
    current_time = start_time
    for zone_name, info in zones.items():
        n_points = np.random.randint(60, 110)
        for _ in range(n_points):
            tech = np.random.choice(technologies, p=tech_weights)
            rsrp, rsrq, rssi, dl, ul, call_drop, anomalie = generate_measurement(tech, info["type"])

            lat = info["lat"] + np.random.uniform(-0.015, 0.015)
            lon = info["lon"] + np.random.uniform(-0.015, 0.015)

            current_time += timedelta(seconds=np.random.randint(3, 12))

            rows.append({
                "id_mesure": point_id,
                "campagne": f"C{campagne_num}",
                "horodatage": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "region": info["region"],
                "ville": zone_name,
                "type_zone": info["type"],
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "operateur": operateur,
                "technologie": tech,
                "rsrp_dbm": rsrp,
                "rsrq_db": rsrq,
                "rssi_dbm": rssi,
                "debit_descendant_mbps": dl,
                "debit_montant_mbps": ul,
                "appel_coupe": call_drop,
                "anomalie": anomalie,
                "cell_id": f"{zone_name[:3].upper()}-{np.random.randint(1, 8)}",
            })
            point_id += 1

df = pd.DataFrame(rows)

output_path = "/mnt/user-data/outputs/benchmark_drivetest_national_maroc.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Nombre total de mesures générées : {len(df)}")
print(f"Nombre de régions couvertes : {df['region'].nunique()}")
print(f"Nombre de villes couvertes : {df['ville'].nunique()}")
print(f"Nombre de campagnes : {df['campagne'].nunique()}")
print("\nRépartition par région :")
print(df['region'].value_counts())
print(f"\nFichier exporté : {output_path}")
