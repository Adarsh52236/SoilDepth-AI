# SoilDepth-AI — Maharashtra Environmental Data Quality Report

**Station:** `MPKV-RAHURI-CAAST` (MPKV Rahuri CAAST Precision Agriculture Network)  
**District / Region:** `Ahmednagar` (Western Maharashtra)  
**Coordinates:** Latitude `19.3932^\circ\text{ N}`, Longitude `74.6475^\circ\text{ E}`  
**Benchmark Elevation:** `512.0\text{ m}` AMSL  
**Timeline:** `2017-01-01` to `2023-12-31` (2556 chronological daily epochs)  
**Timezone Convention:** `UTC (00:00:00 to 23:59:59 UTC daily epochs)`  
**Report Generated:** `2026-10-31T07:08:31.270405+00:00` UTC  

---

## 1. Executive Summary & Acquisition Status

In accordance with SoilDepth-AI multi-station expansion standards, environmental predictor datasets were verified, calibrated, and audited for `MPKV-RAHURI-CAAST`. Raw observation missingness is strictly distinguished from imputed LOCF features.

| Dataset / Modality | Primary Source | Spatial Res. | Temporal Res. | Raw Obs (Coverage / Missing) | Processed LOCF Cov. | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **ERA5-Land Weather** | ECMWF C3S via Open-Meteo | 0.1° (~9 km) | Hourly -> Daily | 2556 days (100% / 0%) | 100.0% | **ACQUIRED** |
| **SoilGrids 250m** | ISRIC OGC WCS 2.0.1 | 250 m | Static baseline | 32 GeoTIFFs (100% / 0%) | 100.0% | **ACQUIRED** |
| **Copernicus DEM** | Copernicus GLO-30 / PC | 30 m (1") | Static baseline | 1 Tile (100% / 0%) | 100.0% | **ACQUIRED** |
| **Sentinel-1 SAR** | ESA Copernicus / PC STAC | 10 m | 6–12 day revisit | 174 days (6.81% / 93.19%) | 99.69% | **ACQUIRED** |
| **Sentinel-2 Optical** | ESA Copernicus / PC STAC | 10–20 m | 5-day revisit | 306 days (11.97% / 88.03%) | 98.83% | **ACQUIRED** |
| **SMAP L3 Radiometer** | NASA NSIDC / Earthdata | 9 km | Daily | 0 days (0.0% / 100.0%) | 0.0% | **AWAITING_AUTH** |

> **Critical QA Distinction:** 0% missingness in forward-filled features is **never** reported as equivalent to 100% actual satellite observation coverage. Raw satellite observations occur at 5–12 day revisit intervals; intermediate days are LOCF forward-filled with explicit observation source dates and staleness indicators.

---

## 2. Dataset Specifics & Physical Validations

### 2.1 ERA5-Land Reanalysis
- **Daily Epochs:** 2556 days (61344 hourly timesteps with zero gaps and zero duplicates).
- **Completeness:** 100.0% (`incomplete_days = 0`).
- **Temperature:** Min `16.108^\circ\text{C}`, Max `36.271^\circ\text{C}`.
- **Precipitation:** Max daily rainfall `167.1\text{ mm}`.
- **Deep Soil Moisture:** **Zero** ERA5-Land deep soil moisture variables (`swvl1`, `swvl2`, `swvl3`, `swvl4`) are ingested or present in features.
- **Antecedent Memory:** Strictly past-only `shift(1)` applied to precipitation lags (1d, 3d, 7d, 14d, 30d), rolling temperatures, VPD, and solar radiation.

### 2.2 SoilGrids 250m Static Properties & Derived Hydraulics
- **Raster Count:** 32 individual GeoTIFF tiles acquired via OGC WCS.
- **Mass Balance Closure:** Verified across all depth layers (Clay + Sand + Silt = 100.00% +- 1.0%).
- **Hydraulic Suction Hierarchy:** Verified across all depth layers (wilting point < field capacity < gravitational drainage).
- **Derived Pedotransfer Features:** Explicitly distinguished from downloaded properties via `derived_` prefix (`derived_awc_*`, `derived_field_capacity_*`, `derived_wilting_point_*`, `derived_drainable_porosity_*`).

### 2.3 Copernicus 30m Global DEM & Elevation Audit
- **Extracted Elevation (Nearest Pixel):** `514.52\text{ m}` AMSL.
- **Sub-Pixel Bilinear Elevation:** `514.68\text{ m}` AMSL.
- **Independent Elevation Benchmark:** `515.0\text{ m}` AMSL.
- **Benchmark Offset Analysis:** Station benchmark is 512.0m. Copernicus DEM 30m measured elevation is 514.52m (offset +2.52m). Subpixel bilinear is 514.68m, independent SRTM/Copernicus is 515.0m.

### 2.4 Sentinel-1 SAR & Sentinel-2 Optical Missingness
- **Sentinel-1:** 174 distinct acquisition dates cataloged. Raw missingness is 93.19%. Past-only LOCF forward-fill applied with a 30-day maximum staleness threshold (`s1_is_stale`).
- **Sentinel-2:** 306 clear acquisitions retained after conservative SCL cloud/shadow filtering. Raw missingness is 88.03%. Past-only LOCF forward-fill applied with a 45-day maximum staleness threshold (`s2_is_stale`).

### 2.5 SMAP L3 Radiometer Status
- **Status:** **AWAITING_AUTH**.
- **Integrity Rule:** Zero synthetic data fabricated. All SMAP columns preserved as unpopulated NaN with `smap_has_valid_retrieval = False`. SMAP L4 is strictly not used.

---

## 3. Leakage Prevention & Audit Verification

1. **Chronological Alignment:** Monotonic increasing UTC daily sequence (2556 rows, zero duplicates, zero gaps).
2. **Strictly Past-Only Feature Engineering:** Every antecedent predictor uses `shift(1)` so inference at day $D$ depends strictly on $D-1$ or earlier.
3. **Zero Target Leakage:** No ground-sensor observations or proxy targets are included in predictor matrices.
4. **Physical Boundaries:** All environmental features adhere to thermodynamic and physical bounds.
