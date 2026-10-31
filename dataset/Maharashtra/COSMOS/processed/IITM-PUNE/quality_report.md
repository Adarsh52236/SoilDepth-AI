# SoilDepth-AI — Maharashtra Phase 2C Environmental Data Quality Report

**Pilot Station:** `IITM-PUNE-COSMOS` (IITM Pune COSMOS-India Station)  
**Coordinates:** Latitude `18.5372^\circ\text{ N}`, Longitude `73.8051^\circ\text{ E}`  
**Benchmark Elevation:** `560.0\text{ m}` AMSL  
**Timeline:** `2017-01-01` to `2023-12-31` (2556 chronological daily epochs)  
**Timezone Convention:** `UTC (00:00:00 to 23:59:59 UTC daily epochs)`  
**Report Generated:** `2026-10-31T06:45:28.874027+00:00` UTC  

---

## 1. Executive Summary & Acquisition Status

In accordance with SoilDepth-AI Phase 2C integrity audit standards, environmental predictor datasets were verified, calibrated, and audited for the `IITM-PUNE-COSMOS` pilot station. Raw observation missingness is strictly distinguished from imputed LOCF features.

| Dataset / Modality | Primary Source | Spatial Res. | Temporal Res. | Raw Obs (Coverage / Missing) | Processed LOCF Cov. | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **ERA5-Land Weather** | ECMWF C3S via Open-Meteo | 0.1° (~9 km) | Hourly -> Daily | 2,556 days (100% / 0%) | 100.0% | **ACQUIRED** |
| **SoilGrids 250m** | ISRIC OGC WCS 2.0.1 | 250 m | Static baseline | 32 GeoTIFFs (100% / 0%) | 100.0% | **ACQUIRED** |
| **Copernicus DEM** | Copernicus GLO-30 / PC | 30 m (1") | Static baseline | 1 Tile (100% / 0%) | 100.0% | **ACQUIRED** |
| **Sentinel-1 SAR** | ESA Copernicus / PC STAC | 10 m | 6–12 day revisit | 175 days (6.85% / 93.15%) | 99.73% | **ACQUIRED** |
| **Sentinel-2 Optical** | ESA Copernicus / PC STAC | 10–20 m | 5-day revisit | 299 days (11.70% / 88.30%) | 98.44% | **ACQUIRED** |
| **SMAP L3 Radiometer** | NASA NSIDC / Earthdata | 9 km | Daily | 0 days (0.0% / 100.0%) | 0.0% | **AWAITING_AUTH** |

> **Critical QA Distinction:** 0% missingness in forward-filled features is **never** reported as equivalent to 100% actual satellite observation coverage. Raw satellite observations occur at 5–12 day revisit intervals; intermediate days are LOCF forward-filled with explicit observation source dates and staleness indicators.

---

## 2. Dataset Specifics & Physical Validations

### 2.1 ERA5-Land Reanalysis
- **Daily Epochs:** 2,556 days (61,344 hourly timesteps with zero gaps and zero duplicates).
- **Completeness:** 100.0% (`incomplete_days = 0`).
- **Temperature:** Min `15.075^\circ\text{C}`, Max `32.538^\circ\text{C}`.
- **Precipitation:** Max daily rainfall `133.3\text{ mm}`.
- **Deep Soil Moisture:** **Zero** ERA5-Land deep soil moisture variables (`swvl1`, `swvl2`, `swvl3`, `swvl4`) are ingested or present in features.
- **Antecedent Memory:** Strictly past-only `shift(1)` applied to precipitation lags (1d, 3d, 7d, 14d, 30d), rolling temperatures, VPD, and solar radiation.

### 2.2 SoilGrids 250m Static Properties & Derived Hydraulics
- **Raster Count:** 32 individual GeoTIFF tiles acquired via OGC WCS.
- **Mass Balance Closure:**
  - 0–5 cm: Clay + Sand + Silt = 100.00%
  - 5–15 cm: Clay + Sand + Silt = 100.00%
  - 15–30 cm: Clay + Sand + Silt = 100.00%
  - 30–60 cm: Clay + Sand + Silt = 100.00%
- **Hydraulic Suction Hierarchy:** Verified across all depth layers (wilting point < field capacity < gravitational drainage).
- **Derived Pedotransfer Features:** Explicitly distinguished from downloaded properties via `derived_` prefix (`derived_awc_*`, `derived_field_capacity_*`, `derived_wilting_point_*`, `derived_drainable_porosity_*`).

### 2.3 Copernicus 30m Global DEM & Elevation Audit
- **Extracted Elevation (Nearest Pixel):** `591.58\text{ m}` AMSL.
- **Sub-Pixel Bilinear Elevation:** `590.64\text{ m}` AMSL.
- **Independent Elevation Benchmark:** `590.0\text{ m}` AMSL (Independent SRTM 90m / Copernicus 90m via Open-Meteo).
- **Benchmark Offset Analysis:** Station nominal metadata quotes Pune city elevation (560.0 m AMSL). The physical station at Pashan is located on the foothill plateau of Vetal Hill / Pashan hills where true terrain elevation is 590–592 m AMSL. The DEM extraction is mathematically and physically verified.

### 2.4 Sentinel-1 SAR & Sentinel-2 Optical Missingness
- **Sentinel-1:** 175 distinct acquisition dates cataloged. Raw missingness is 93.15%. Past-only LOCF forward-fill applied with a 30-day maximum staleness threshold (`s1_is_stale`). Observation source dates recorded in `s1_observation_source_date`.
- **Sentinel-2:** 455 total passes, 299 clear acquisitions retained after conservative Scene Classification Layer (SCL) cloud/shadow filtering. Raw missingness is 88.30%. Past-only LOCF forward-fill applied with a 45-day maximum staleness threshold (`s2_is_stale`). Observation source dates recorded in `s2_observation_source_date`.

### 2.5 SMAP L3 Radiometer Status
- **Status:** **AWAITING_AUTH**.
- **NASA CMR Hits:** Granules confirmed available on NASA Earthdata CMR (`SPL3SMP_E.006`).
- **Integrity Rule:** Zero synthetic data fabricated. All SMAP columns preserved as unpopulated NaN with `smap_has_valid_retrieval = False`. SMAP L4 is strictly not used.

---

## 3. Leakage Prevention & Audit Verification

1. **Chronological Alignment:** Monotonic increasing UTC daily sequence (2,556 rows, zero duplicates, zero gaps).
2. **Strictly Past-Only Feature Engineering:** Every antecedent predictor uses `shift(1)` so inference at day $D$ depends strictly on $D-1$ or earlier.
3. **Zero Target Leakage:** No ground-sensor observations or proxy targets are included in predictor matrices.
4. **Physical Boundaries:** All environmental features adhere to thermodynamic and physical bounds.
