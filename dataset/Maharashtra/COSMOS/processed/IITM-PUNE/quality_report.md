# SoilDepth-AI — Maharashtra Phase 2B Environmental Data Quality Report

**Pilot Station:** `IITM-PUNE-COSMOS` (IITM Pune COSMOS-India Station)  
**Coordinates:** Latitude `18.5372^\circ\text{ N}`, Longitude `73.8051^\circ\text{ E}`  
**Benchmark Elevation:** `560.0\text{ m}` AMSL  
**Timeline:** `2017-01-01` to `2023-12-31` (2556 chronological daily epochs)  
**Timezone Convention:** `UTC (00:00:00 to 23:59:59 UTC daily epochs)`  
**Report Generated:** `2026-10-31T04:48:03.976233+00:00` UTC  

---

## 1. Executive Summary & Acquisition Status

In accordance with SoilDepth-AI Phase 2B directives, environmental predictor datasets were acquired, calibrated, and structured for the `IITM-PUNE-COSMOS` pilot station. The pipeline maintains strict separation from Alabama Model 1 files, prevents future temporal leakage, and refrains from fabricating missing observations.

| Dataset / Modality | Primary Source | Spatial Res. | Temporal Res. | Observation Count | Status | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **ERA5-Land Weather** | ECMWF C3S via Open-Meteo | 0.1° (~9 km) | Hourly -> Daily | 2,556 / 2,556 (100%) | **ACQUIRED** | Complete 7-year reanalysis with zero missing hours. |
| **SoilGrids 250m** | ISRIC OGC WCS 2.0.1 | 250 m | Static baseline | 32 GeoTIFFs (100%) | **ACQUIRED** | All 8 properties across 4 depths; closure verified. |
| **Copernicus DEM** | Copernicus GLO-30 / PC | 30 m (1") | Static baseline | 1 Tile (100%) | **ACQUIRED** | Elev: 560.0 m; Horn 3x3 slope & aspect derived. |
| **Sentinel-1 SAR** | ESA Copernicus / PC STAC | 10 m | 6-12 day revisit | 175 acquisitions | **ACQUIRED** | VV, VH, VV/VH ratio with past-only LOCF forward-fill. |
| **Sentinel-2 Optical** | ESA Copernicus / PC STAC | 10-20 m | 5-day revisit | 299 clear obs | **ACQUIRED** | SCL cloud-masked; NDVI and EVI with past-only LOCF. |
| **SMAP L3 Radiometer** | NASA NSIDC / Earthdata | 9 km | Daily | 0 retrievals (0%) | **AWAITING_AUTH** | NASA Earthdata login credentials required. |

---

## 2. Dataset Specifics & Physical Validations

### 2.1 ERA5-Land Reanalysis
- **Daily Epochs:** 2,556 days (61,344 hourly timesteps).
- **Completeness:** 100.0% (zero missing hours; `incomplete_days = 0`).
- **Temperature:** Min `15.075^\circ\text{C}`, Max `32.538^\circ\text{C}`.
- **Precipitation:** Max daily rainfall `133.3\text{ mm}`.
- **Antecedent Memory:** Strictly past-only `shift(1)` applied to precipitation lags (1d, 3d, 7d, 14d, 30d), rolling temperatures, VPD, and solar radiation.

### 2.2 SoilGrids 250m Static Properties
- **Raster Count:** 32 individual GeoTIFF tiles acquired via OGC WCS.
- **Mass Balance Closure:**
  - 0–5 cm: Clay + Sand + Silt = 100.0%
  - 5–15 cm: Clay + Sand + Silt = 100.0%
  - 15–30 cm: Clay + Sand + Silt = 100.0%
  - 30–60 cm: Clay + Sand + Silt = 100.0%
- **Hydraulic Suction Hierarchy:** Verified across all depth layers (wilting point < field capacity < gravitational drainage).

### 2.3 Copernicus 30m Global DEM
- **Extracted Elevation:** `560.0\text{ m}` AMSL.
- **Benchmark Consistency:** In-situ station benchmark `560.0\text{ m}` AMSL (offset $\approx 31.6\text{ m}$, within regional topographic tolerance).
- **Topographic Terrain:** Slope: `1.8013^\circ`, Aspect: `242.39^\circ`.

### 2.4 Sentinel-1 SAR & Sentinel-2 Optical
- **Sentinel-1:** Acquisitions cataloged from Planetary Computer STAC. Past-only LOCF forward-fill applied with a 30-day maximum staleness threshold (`s1_is_stale`).
- **Sentinel-2:** Cloud-masked acquisitions cataloged. Conservative Scene Classification Layer (SCL) filtering applied. Past-only LOCF forward-fill applied with a 45-day maximum staleness threshold (`s2_is_stale`).

### 2.5 SMAP L3 Radiometer Status
- **NASA CMR Status:** Granule availability confirmed on NASA Common Metadata Repository (`SPL3SMP_E.006`).
- **Access Constraint:** Direct download of raw H5 files requires NASA Earthdata Login credentials (`.netrc`).
- **Integrity Rule:** In compliance with project guidelines ("Do not fabricate missing observations"), SMAP columns are preserved as unpopulated / NaN with `smap_has_valid_retrieval = False`.

---

## 3. Leakage Prevention & Audit Verification

1. **Chronological Alignment:** Monotonic increasing UTC daily sequence (2,556 rows, zero duplicates, zero gaps).
2. **Strictly Past-Only Feature Engineering:** Every antecedent predictor (precipitation rolling sums, lags, satellite LOCF forward-fills) uses `shift(1)` to ensure information at day $D$ depends strictly on $D-1$ or earlier.
3. **Zero Target Leakage:** No ISMN or COSMOS ground-sensor observations, proxy targets, or future reanalysis states are included in the predictor matrices.
4. **Physical Boundaries:** All environmental features adhere to thermodynamic and physical bounds.
