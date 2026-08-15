/* ============================================================
   Projet : "Réseau Sous Contrôle — Voir, Comprendre, Anticiper"
   Script de création de la base de données SQL Server
   et de la table de mesures QoS (échelle nationale)
   ============================================================ */

-- 1) Création de la base de données
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ReseauSousControle')
BEGIN
    CREATE DATABASE ReseauSousControle;
END
GO

USE ReseauSousControle;
GO

-- 2) Table de dimension : Régions
IF OBJECT_ID('dbo.Regions', 'U') IS NOT NULL DROP TABLE dbo.Regions;
CREATE TABLE dbo.Regions (
    id_region       INT IDENTITY(1,1) PRIMARY KEY,
    nom_region      NVARCHAR(100) NOT NULL UNIQUE
);
GO

-- 3) Table de dimension : Villes / Zones
IF OBJECT_ID('dbo.Villes', 'U') IS NOT NULL DROP TABLE dbo.Villes;
CREATE TABLE dbo.Villes (
    id_ville        INT IDENTITY(1,1) PRIMARY KEY,
    nom_ville       NVARCHAR(100) NOT NULL,
    id_region       INT NOT NULL FOREIGN KEY REFERENCES dbo.Regions(id_region),
    type_zone       NVARCHAR(50) NOT NULL,       -- urbain_dense, rural, urbain_sature, etc.
    CONSTRAINT UQ_Ville_Region UNIQUE (nom_ville, id_region)
);
GO

-- 4) Table de faits : Mesures (le cœur du benchmark drive-test)
IF OBJECT_ID('dbo.MesuresQoS', 'U') IS NOT NULL DROP TABLE dbo.MesuresQoS;
CREATE TABLE dbo.MesuresQoS (
    id_mesure               BIGINT PRIMARY KEY,
    campagne                NVARCHAR(10)      NOT NULL,
    horodatage               DATETIME2         NOT NULL,
    id_ville                INT               NOT NULL FOREIGN KEY REFERENCES dbo.Villes(id_ville),
    latitude                 DECIMAL(9,6)      NOT NULL,
    longitude                DECIMAL(9,6)      NOT NULL,
    operateur                NVARCHAR(20)      NOT NULL,
    technologie               NVARCHAR(5)       NOT NULL,      -- 2G/3G/4G/5G
    rsrp_dbm                 DECIMAL(6,1)      NOT NULL,
    rsrq_db                  DECIMAL(6,1)      NOT NULL,
    rssi_dbm                 DECIMAL(6,1)      NOT NULL,
    debit_descendant_mbps    DECIMAL(8,2)      NOT NULL,
    debit_montant_mbps       DECIMAL(8,2)      NOT NULL,
    appel_coupe               BIT               NOT NULL DEFAULT 0,
    anomalie                  BIT               NOT NULL DEFAULT 0,   -- étiquette de référence pour les modèles ML
    cell_id                   NVARCHAR(20)      NOT NULL
);
GO

-- 5) Index pour accélérer les requêtes fréquentes (filtrage par zone / techno / date)
CREATE INDEX IX_MesuresQoS_Ville        ON dbo.MesuresQoS(id_ville);
CREATE INDEX IX_MesuresQoS_Techno       ON dbo.MesuresQoS(technologie);
CREATE INDEX IX_MesuresQoS_Horodatage   ON dbo.MesuresQoS(horodatage);
CREATE INDEX IX_MesuresQoS_Campagne     ON dbo.MesuresQoS(campagne);
GO

/* ============================================================
   6) Chargement des données depuis le CSV
   Adapter le chemin du fichier selon l'environnement (local / serveur)
   ============================================================ */

-- 6.1) Table de staging (réception brute du CSV, sans contraintes)
IF OBJECT_ID('dbo.Staging_Mesures', 'U') IS NOT NULL DROP TABLE dbo.Staging_Mesures;
CREATE TABLE dbo.Staging_Mesures (
    id_mesure               BIGINT,
    campagne                NVARCHAR(10),
    horodatage               DATETIME2,
    region                    NVARCHAR(100),
    ville                     NVARCHAR(100),
    type_zone                 NVARCHAR(50),
    latitude                  DECIMAL(9,6),
    longitude                 DECIMAL(9,6),
    operateur                 NVARCHAR(20),
    technologie                NVARCHAR(5),
    rsrp_dbm                  DECIMAL(6,1),
    rsrq_db                   DECIMAL(6,1),
    rssi_dbm                  DECIMAL(6,1),
    debit_descendant_mbps     DECIMAL(8,2),
    debit_montant_mbps        DECIMAL(8,2),
    appel_coupe                BIT,
    anomalie                   BIT,
    cell_id                    NVARCHAR(20)
);
GO

-- 6.2) Import du CSV (à exécuter depuis SQL Server Management Studio,
--       en remplaçant le chemin par l'emplacement réel du fichier)
BULK INSERT dbo.Staging_Mesures
FROM 'C:\Data\benchmark_drivetest_national_maroc.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '0x0a',
    CODEPAGE = '65001'   -- UTF-8
);
GO

-- 6.3) Peuplement de la table Regions à partir du staging
INSERT INTO dbo.Regions (nom_region)
SELECT DISTINCT region FROM dbo.Staging_Mesures
WHERE region NOT IN (SELECT nom_region FROM dbo.Regions);
GO

-- 6.4) Peuplement de la table Villes à partir du staging
INSERT INTO dbo.Villes (nom_ville, id_region, type_zone)
SELECT DISTINCT s.ville, r.id_region, s.type_zone
FROM dbo.Staging_Mesures s
JOIN dbo.Regions r ON r.nom_region = s.region
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.Villes v WHERE v.nom_ville = s.ville AND v.id_region = r.id_region
);
GO

-- 6.5) Peuplement de la table de faits MesuresQoS
INSERT INTO dbo.MesuresQoS (
    id_mesure, campagne, horodatage, id_ville, latitude, longitude,
    operateur, technologie, rsrp_dbm, rsrq_db, rssi_dbm,
    debit_descendant_mbps, debit_montant_mbps, appel_coupe, anomalie, cell_id
)
SELECT
    s.id_mesure, s.campagne, s.horodatage, v.id_ville, s.latitude, s.longitude,
    s.operateur, s.technologie, s.rsrp_dbm, s.rsrq_db, s.rssi_dbm,
    s.debit_descendant_mbps, s.debit_montant_mbps, s.appel_coupe, s.anomalie, s.cell_id
FROM dbo.Staging_Mesures s
JOIN dbo.Villes v ON v.nom_ville = s.ville
JOIN dbo.Regions r ON r.nom_region = s.region AND r.id_region = v.id_region;
GO

/* ============================================================
   7) Quelques requêtes utiles pour vérifier / exploiter la base
   ============================================================ */

-- Nombre de mesures par région
SELECT r.nom_region, COUNT(*) AS nb_mesures
FROM dbo.MesuresQoS m
JOIN dbo.Villes v ON v.id_ville = m.id_ville
JOIN dbo.Regions r ON r.id_region = v.id_region
GROUP BY r.nom_region
ORDER BY nb_mesures DESC;

-- Débit moyen et taux de coupure par technologie
SELECT
    technologie,
    AVG(debit_descendant_mbps) AS debit_moyen_dl,
    AVG(CAST(appel_coupe AS FLOAT)) * 100 AS taux_coupure_pct
FROM dbo.MesuresQoS
GROUP BY technologie
ORDER BY debit_moyen_dl DESC;

-- Villes avec le plus d'anomalies détectées (candidates prioritaires)
SELECT TOP 10 v.nom_ville, r.nom_region, COUNT(*) AS nb_anomalies
FROM dbo.MesuresQoS m
JOIN dbo.Villes v ON v.id_ville = m.id_ville
JOIN dbo.Regions r ON r.id_region = v.id_region
WHERE m.anomalie = 1
GROUP BY v.nom_ville, r.nom_region
ORDER BY nb_anomalies DESC;
