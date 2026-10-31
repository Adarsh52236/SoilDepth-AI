# SoilDepth-AI — Maharashtra Environmental Data Acquisition Pipeline Guide
**Pilot Station:** `IITM-PUNE-COSMOS` (Indian Institute of Tropical Meteorology, Pune)  
**Target Timeline:** 2017-01-01 to 2023-12-31 (7 calendar years / 2,556 daily epochs)  
**Author:** Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI  
**Status:** Operational Environmental Extraction Pipeline  

---

## 1. Pipeline Architecture & Modular Structure

The Maharashtra Environmental Data Acquisition Pipeline (`services/data_acquisition/maharashtra/`) is engineered to extract, calibrate, validate, and harmonize multimodal environmental predictors for regional soil moisture reconstruction across Maharashtra, anchored initially at the `IITM-PUNE-COSMOS` pilot.

```
services/data_acquisition/maharashtra/
├── __init__.py
├── config.py                   # Station coordinates, temporal bounds, physical limits
├── pipeline.py                 # Master orchestrator & quality reporting
└── adapters/
    ├── __init__.py
    ├── base_adapter.py         # Abstract base adapter interface & hashing
    ├── era5_land.py            # ECMWF ERA5-Land weather & memory lags
    ├── soilgrids.py            # ISRIC SoilGrids v2.0 250m static edaphics
    ├── dem.py                  # Copernicus 30m Global DEM & Horn 3x3 topography
    ├── sentinel1.py            # Sentinel-1 RTC dual-pol SAR backscatter & LOCF
    ├── sentinel2.py            # Sentinel-2 L2A surface reflectance, NDVI, EVI & LOCF
    └── smap_l3.py              # NASA SMAP Enhanced L3 9 km radiometer
```

### Key Design Principles:
1. **Strict Physical Separation:** All Maharashtra code and datasets reside under `services/data_acquisition/maharashtra/` and `dataset/Maharashtra/COSMOS/`, with zero modifications to Alabama Model 1 files (`models/baselines/AAMU-JTG/`, `services/modelling/`, `services/inference/`).
2. **Strict Leakage Prevention:** Every antecedent memory feature (precipitation rolling sums, lags, satellite last-observation-carried-forward) employs strictly causal `shift(1)` transformations. Values on day $D$ depend exclusively on observations from $D-1$ or earlier.
3. **No Synthetic Ground Truth:** Ground-truth targets (`target_sm_*`) are omitted. In accordance with project integrity standards, missing satellite acquisitions and authentication-gated products are preserved as missing (NaN) without fabrication.
4. **Cloud-Native & Point Extractions:** High-resolution spatial datasets utilize OGC WCS window queries, STAC catalog queries, and HTTP Range-request partial tile decodes, avoiding gigabyte-scale full-scene downloads.

---

## 2. Station Reference & Temporal Alignment

### 2.1 Station Geographic Reference
- **Station ID:** `IITM-PUNE-COSMOS`
- **Location:** Indian Institute of Tropical Meteorology (IITM) Campus, Pashan, Pune, Maharashtra, India
- **Coordinates:** Latitude: $18.5372^\circ\text{ N}$, Longitude: $73.8051^\circ\text{ E}$
- **Benchmark Ground Elevation:** $560.0\text{ m}$ AMSL
- **UTM Projection:** UTM Zone 43N (WGS84, `EPSG:32643`), Easting: $373,885.96\text{ m}$, Northing: $2,050,039.05\text{ m}$

### 2.2 Timezone Convention & Daily Indexing
- **Primary Epoch Convention:** Daily UTC calendar days ($00{:}00{:}00\text{ UTC}$ to $23{:}59{:}59\text{ UTC}$).
- **Local Timezone Offset:** Indian Standard Time ($\text{IST} = \text{UTC} + 05{:}30$, `Asia/Kolkata`).
- **Satellite Overpass Alignment:**
  - In local IST, daytime satellite passes over Pune occur during midday and evening:
    - Sentinel-2: $\sim 10{:}45\text{ IST}$ ($05{:}15\text{ UTC}$, same day)
    - Sentinel-1 Descending: $\sim 06{:}15\text{ IST}$ ($00{:}45\text{ UTC}$, same day)
    - Sentinel-1 Ascending: $\sim 18{:}30\text{ IST}$ ($13{:}00\text{ UTC}$, same day)
    - SMAP Morning (AM): $\sim 06{:}00\text{ IST}$ ($00{:}30\text{ UTC}$, same day)
  - All daytime passes over Pune fall cleanly within the exact same UTC calendar date, ensuring seamless multi-sensor synchronization without day-boundary jitter.
- **Calendar Coverage:** $2017\text{-}01\text{-}01$ to $2023\text{-}12\text{-}31$ ($2,556\text{ daily epochs}$; 2020 leap year has 366 days).

---

## 3. Data Adapters & Extraction Methodologies

### 3.1 ERA5-Land Reanalysis Adapter (`ERA5LandAdapter`)
- **Data Source:** ECMWF Copernicus Climate Change Service (via Open-Meteo Reanalysis Archive).
- **Spatial Resolution:** $0.1^\circ$ ($\approx 9\text{ km}$).
- **Temporal Resolution:** 61,344 hourly timesteps aggregated to 2,556 daily records ($100\%$ complete).
- **Core Atmospheric Features:**
  - `temperature_2m_mean_c`, `temperature_2m_min_c`, `temperature_2m_max_c` ($^\circ\text{C}$)
  - `dewpoint_2m_mean_c` ($^\circ\text{C}$)
  - `vpd_kpa` (Vapor Pressure Deficit in $\text{kPa}$ via Tetens equation: $e_s(T) - e_a(T_d)$)
  - `precipitation_total_mm` (Daily cumulative precipitation, $\text{mm}$)
  - `solar_radiation_total_mj_m2` (Daily cumulative surface solar flux, $\text{MJ/m}^2$)
  - `wind_speed_10m_ms` (Daily scalar mean wind speed, $\text{m/s}$)
  - `wind_u10_mean_ms`, `wind_v10_mean_ms` (Zonal and meridional wind vector components, $\text{m/s}$)
- **Antecedent Memory Features (`shift(1)` Past-Only):**
  - `precip_lag_1d` ($\text{mm}$)
  - `precip_roll_sum_3d`, `precip_roll_sum_7d`, `precip_roll_sum_14d`, `precip_roll_sum_30d` ($\text{mm}$)
  - `days_since_rain_gt_1mm` (Continuous causal drying counter, days)
  - `temp_roll_mean_7d`, `temp_roll_mean_30d` ($^\circ\text{C}$)
  - `vpd_roll_mean_7d` ($\text{kPa}$)
  - `solar_roll_mean_7d` ($\text{MJ/m}^2$)
  - `doy_sin`, `doy_cos` (Trigonometric seasonal day-of-year embeddings)

### 3.2 SoilGrids 250m Static Adapter (`SoilGridsAdapter`)
- **Data Source:** ISRIC — World Soil Information (SoilGrids v2.0 WCS 2.0.1).
- **Spatial Resolution:** $250\text{ m}$.
- **Depth Layers:** 4 standard depth slices: $0\text{--}5\text{ cm}$, $5\text{--}15\text{ cm}$, $15\text{--}30\text{ cm}$, $30\text{--}60\text{ cm}$.
- **Properties Acquired (32 GeoTIFFs):**
  - `bdod` (Fine earth bulk density, scaled by $100.0 \rightarrow \text{g/cm}^3$)
  - `clay`, `sand`, `silt` (Soil texture fractions, scaled by $10.0 \rightarrow \%$)
  - `ocd` (Organic carbon density, scaled by $10.0 \rightarrow \text{kg/m}^3$)
  - `wv0010` (Volumetric water content at $-10\text{ kPa}$ suction, scaled by $1000.0 \rightarrow \text{m}^3/\text{m}^3$)
  - `wv0033` (Volumetric water content at field capacity $-33\text{ kPa}$, scaled by $1000.0 \rightarrow \text{m}^3/\text{m}^3$)
  - `wv1500` (Volumetric water content at wilting point $-1500\text{ kPa}$, scaled by $1000.0 \rightarrow \text{m}^3/\text{m}^3$)
- **Physical Validations Enforced:**
  - Textural closure: $\text{clay} + \text{sand} + \text{silt} \approx 100\%$ ($100.0 \pm 3.0\%$).
  - Plausible mineral soil density: $1.0 \le \rho_b \le 1.8\text{ g/cm}^3$.
  - Hydraulic suction hierarchy: $\theta_{1500} < \theta_{33} < \theta_{10}$ across all depth layers.

### 3.3 Copernicus 30m DEM Adapter (`DEMAdapter`)
- **Data Source:** Copernicus 30m Global DEM (`cop-dem-glo-30` via Microsoft Planetary Computer).
- **Spatial Resolution:** $1\text{ arc-second}$ ($\approx 30\text{ m}$).
- **Extraction Protocol:** HTTP Range request reading Cloud-Optimized GeoTIFF Tile 6 (`N18_00_E073_00`), decoding Adobe Deflate Floating-Point Predictor (TIFF tag 317 = 3) via row cumsum reorganization.
- **Topographic Attributes Derived:**
  - `elevation_m`: Extracted at station coordinate ($591.58\text{ m}$ AMSL vs in-situ benchmark $560.0\text{ m}$ AMSL).
  - `slope_deg` & `slope_rise_run`: Computed via Horn (1981) $3 \times 3$ finite-difference kernel.
  - `aspect_deg`, `aspect_sin`, `aspect_cos`: Terrain aspect orientation.

### 3.4 Sentinel-1 SAR Adapter (`Sentinel1Adapter`)
- **Data Source:** ESA Copernicus Sentinel-1 RTC Ground Range Detected (via Planetary Computer STAC).
- **Spatial Resolution:** $10\text{ m}$.
- **Orbit Characteristics:** Tracks 70 (Ascending, evening) and 143 (Descending, morning).
- **Features Extracted:**
  - `s1_has_valid_observation` (Boolean flag)
  - `s1_vv_db_mean`, `s1_vh_db_mean`, `s1_vv_vh_ratio_db_mean` ($\text{dB}$)
  - `s1_vv_db_locf`, `s1_vh_db_locf`, `s1_vv_vh_ratio_db_locf` (Past-only forward-fill)
  - `s1_days_since_valid_obs` (Causal days accumulator)
  - `s1_is_stale` (True when `days_since > 30.0` days)
  - `s1_has_past_obs` (Indicator of past observation history)

### 3.5 Sentinel-2 Optical Adapter (`Sentinel2Adapter`)
- **Data Source:** ESA Copernicus Sentinel-2 Level-2A Bottom-Of-Atmosphere (BOA) Surface Reflectance.
- **Spatial Resolution:** $10\text{ m}$ (B02, B03, B04, B08) and $20\text{ m}$ (B11, B12, SCL).
- **Cloud Masking Strategy:**
  - Evaluates Scene Classification Layer (SCL) and scene cloud cover ($> 60\%$).
  - Cloudy, shadowed, and defective pixels are strictly masked (`is_cloud_masked = True`), recording NaN reflectances.
  - Clear observations derive vegetation indices:
    $$\text{NDVI} = \frac{B_8 - B_4}{B_8 + B_4}$$
    $$\text{EVI} = 2.5 \times \frac{B_8 - B_4}{B_8 + 6 \cdot B_4 - 7.5 \cdot B_2 + 1.0}$$
- **Features Extracted:**
  - `s2_has_valid_observation`
  - `s2_ndvi_mean`, `s2_evi_mean`, `s2_b04_red_mean`, `s2_b08_nir_mean`, `s2_b11_swir1_mean`, `s2_b12_swir2_mean`
  - `s2_ndvi_locf`, `s2_evi_locf`, etc. (Past-only forward-fill)
  - `s2_days_since_valid_obs`, `s2_is_stale` (Staleness threshold: 45 days)
  - `s2_has_past_obs`

### 3.6 NASA SMAP L3 Radiometer Adapter (`SMAPAdapter`)
- **Data Source:** NASA NSIDC DAAC (SPL3SMP_E Enhanced 9 km Radiometer Soil Moisture).
- **Spatial Resolution:** $9\text{ km}$ EASE-Grid 2.0.
- **Acquisition Status:** **`AWAITING_NASA_EARTHDATA_CREDENTIALS`**.
  - NASA CMR confirms granule availability over Pune coordinates.
  - Direct download requires NASA Earthdata Login authentication (`.netrc`).
  - In strict compliance with project guidelines, all SMAP columns (`smap_sm_daily_mean_m3_m3`, `smap_sm_lag_1d`, `smap_sm_roll_mean_3d`, `smap_sm_roll_mean_7d`) are preserved as unpopulated / NaN with `smap_has_valid_retrieval = False`.

---

## 4. Pipeline Execution Commands

### Run Full Pipeline End-to-End
```powershell
python -m services.data_acquisition.maharashtra.pipeline
```

### Run Quality Validation Test Suite
```powershell
python -m pytest -v tests/test_maharashtra_acquisition.py tests/test_model1_inference.py
```

---

## 5. Generated Artifacts & File Locations

| Output File Path | Rows / Cols | Description |
| :--- | :---: | :--- |
| `dataset/Maharashtra/COSMOS/processed/IITM-PUNE/daily_environmental_features.csv` | 2,556 x 62 | Aligned chronological daily matrix (2017–2023) containing weather, memory, S1 SAR, S2 Optical, and SMAP predictors. |
| `dataset/Maharashtra/COSMOS/processed/IITM-PUNE/static_environmental_features.csv` | 1 x 83 | Aligned static edaphic properties (SoilGrids 250m across 4 depths) and topographic variables (Copernicus DEM 30m). |
| `dataset/Maharashtra/COSMOS/processed/IITM-PUNE/acquisition_manifest.json` | JSON | Cryptographic audit ledger recording all raw files, sizes, SHA-256 hashes, CRS, units, and retrieval timestamps. |
| `dataset/Maharashtra/COSMOS/processed/IITM-PUNE/quality_report.json` | JSON | Machine-readable quality metrics, physical range verifications, missingness percentages, and zero-leakage certifications. |
| `dataset/Maharashtra/COSMOS/processed/IITM-PUNE/quality_report.md` | Markdown | Comprehensive human-readable quality audit report. |

