# SoilDepth-AI — Maharashtra Data Readiness Report

**Author:** Senior Geospatial Data Engineer & ML Pipeline Architect, SoilDepth-AI  
**Report Date:** 2026-11-04  
**Target Domain:** Maharashtra State, India  
**Branch:** `integration/model1-maharashtra-completion`  
**Status:** COMPREHENSIVE DATA ENGINEERING AUDIT  

---

## 1. Executive Summary

This report establishes the verified state of data engineering and acquisition readiness across Maharashtra for SoilDepth-AI Model 1.

Key findings:
1. **Multi-Modal Environmental Predictors:** Completely extracted and verified for pilot stations (`IITM-PUNE-COSMOS` and `MPKV-RAHURI-CAAST`) covering 2,556 daily timesteps from **2017-01-01 to 2023-12-31**.
2. **Data Leakage & Integrity Audit:** 100% compliant. Prohibited reanalysis deep soil moisture (`swvl2`, `swvl3`, `swvl4`) and modelled `smap_l4` are strictly barred. Target lags are strictly excluded from ungauged feature sets.
3. **In-Situ Ground-Truth Data:** **0 records received to date**. Supervised training remains strictly gated/blocked until institutional access agreements are fulfilled.
4. **Acquisition & Ingestion Readiness:** Complete ingestion adapter supporting CSV, TSV, TXT, Excel, JSON, and Parquet, with automated receipt packages and SHA-256 manifests.

---

## 2. Multi-Modal Environmental Feature Pipeline

### 2.1 Meteorological & Atmospheric (ERA5-Land)
- **Source:** ECMWF ERA5-Land Reanalysis (surface layer only; deep soil moisture strictly removed).
- **Temporal Resolution:** Hourly aggregated to daily UTC.
- **Coverage:** 2,556 daily records (2017-01-01 to 2023-12-31).
- **Features Extracted:**
  - `temperature_2m_mean_c`, `temperature_2m_min_c`, `temperature_2m_max_c`
  - `dewpoint_2m_mean_c`, `vpd_kpa` (Vapor Pressure Deficit)
  - `precipitation_total_mm`, `solar_radiation_total_mj_m2`
  - `wind_speed_10m_ms`, `wind_u10_mean_ms`, `wind_v10_mean_ms`
  - `precip_lag_1d`, `precip_roll_sum_3d`, `precip_roll_sum_7d`, `precip_roll_sum_14d`, `precip_roll_sum_30d`
  - `days_since_rain_gt_1mm`, `temp_roll_mean_7d`, `vpd_roll_mean_7d`, `solar_roll_mean_7d`
  - `doy_sin`, `doy_cos` (cyclical day-of-year harmonic features)

### 2.2 Microwave SAR (Sentinel-1 C-Band)
- **Instrument:** Sentinel-1 C-SAR (interferometric wide swath mode, 12-day revisit nominal per satellite).
- **Features Extracted:**
  - `s1_vv_db_locf`, `s1_vh_db_locf`, `s1_vv_vh_ratio_db_locf`
  - `s1_days_since_valid_obs`, `s1_is_stale`, `s1_has_past_obs`
- **Integrity Rule:** Strictly forward-propagating Last Observation Carried Forward (LOCF) with staleness tracking to eliminate lookahead bias.

### 2.3 Optical Multispectral (Sentinel-2 MSI)
- **Instrument:** Sentinel-2 MultiSpectral Instrument (MSI, 10-20m resolution, Level-2A surface reflectance).
- **Features Extracted:**
  - `s2_ndvi_locf` (Normalized Difference Vegetation Index)
  - `s2_evi_locf` (Enhanced Vegetation Index)
  - `s2_b04_red_locf`, `s2_b08_nir_locf`, `s2_b11_swir1_locf`, `s2_b12_swir2_locf`
  - `s2_days_since_valid_obs`, `s2_is_stale`, `s2_has_past_obs`
- **Cloud Screening:** Strict scene and pixel QA mask filtering prior to feature aggregation.

### 2.4 Microwave Radiometry (SMAP L3 Enhanced)
- **Product:** SPL3SMP_E (SMAP L3 Enhanced Radiometer 9 km surface soil moisture).
- **Features Extracted:**
  - `smap_sm_daily_mean_m3_m3` (surface 0–5 cm only)
  - `smap_sm_lag_1d`, `smap_sm_roll_mean_3d`, `smap_sm_roll_mean_7d`
  - `smap_days_since_valid_retrieval`, `smap_is_stale`
- **Prohibition:** Strictly prohibits SMAP L4 modelled root-zone soil moisture (`smap_l4`).

### 2.5 Soil Pedological Properties (SoilGrids 250m v2.0)
- **Layers:** 0–5 cm, 5–15 cm, 15–30 cm, 30–60 cm.
- **Properties Extracted:**
  - Bulk density (`bdod`), Clay fraction (`clay`), Sand fraction (`sand`), Silt fraction (`silt`), Organic carbon (`ocd`)
  - Water retention at -10 kPa (`wv0010`), -33 kPa (`wv0033`, Field Capacity), -1500 kPa (`wv1500`, Wilting Point)
  - Derived Available Water Capacity (`awc`) and Drainable Porosity.

### 2.6 Digital Elevation & Terrain (Copernicus DEM GLO-30)
- **Resolution:** 30m (1 arcsecond).
- **Features Extracted:**
  - Elevation (`elevation_m`), sub-pixel bilinear elevation
  - Slope in degrees (`slope_deg`) and rise/run via Horn (1981) 3x3 finite difference
  - Aspect in degrees (`aspect_deg`), `aspect_sin`, `aspect_cos`
  - Benchmark elevation discrepancy resolution (+31.58 m documented at Pashan foothill plateau).

---

## 3. Station Inventory and Extraction Status

| Station ID | Station Name | Institution | Lat / Lon | Status | Daily Environmental Records |
|---|---|---|---|---|---|
| `IITM-PUNE-COSMOS` | Pashan COSMOS-India | IITM / MoES | 18.5372, 73.8051 | `EXTRACTION_COMPLETE` | 2,556 (2017–2023) |
| `MPKV-RAHURI-CAAST` | Rahuri CAAST-CSAWM | MPKV Rahuri | 19.3333, 74.6500 | `EXTRACTION_COMPLETE` | 2,556 (2017–2023) |
| `NIASM-BARAMATI-FLUX` | Baramati Flux & Agronomy | ICAR-NIASM | 18.1511, 74.5772 | `CANDIDATE_EXTRACTION_PENDING` | - |
| `IMD-AGRIMET-PUNE` | IMD National Data Centre | IMD | 18.5310, 73.8550 | `CANDIDATE_EXTRACTION_PENDING` | - |
| `POCRA-AURANGABAD` | PoCRA Demonstration Hub | Maha PoCRA | 19.8762, 75.3433 | `CANDIDATE_EXTRACTION_PENDING` | - |
| *11 Other Candidate Stations* | Statewide candidate network | SAUs/IMD/ICAR | Various | `CANDIDATE_EXTRACTION_PENDING` | - |

---

## 4. In-Situ Ground-Truth Campaign Status

- **Institutional Packets Prepared:** 5 formal dispatch packets (`SOILDEPTH-REQ-2026-001` through `005`).
- **Operational Status:** All 5 requests are currently `DRAFTED` (not yet formally dispatched).
- **Physical Observation Records Received:** **0 records**.
- **Ingestion Harness Readiness:** `MaharashtraGroundTruthAdapter` is operational, tested, and supports CSV, TSV, TXT, Excel, JSON, and Parquet.
- **Reporting Harness:** Produces SHA-256 manifests, receipt reports, coverage summaries, and rejected-record tracking.

---

## 5. Conclusion

The data acquisition infrastructure for Maharashtra is complete, mathematically validated, and ready for immediate deployment as soon as in-situ ground truth data is received from institutional providers.
