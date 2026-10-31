# Environmental Data Alignment & Extraction Plan: IITM-Pune COSMOS

**Project:** SoilDepth-AI (Maharashtra Phase 2A)  
**Station:** `IITM-PUNE-COSMOS` (Indian Institute of Tropical Meteorology, Pune)  
**Coordinates:** Latitude: $18.5372^\circ\text{ N}$, Longitude: $73.8051^\circ\text{ E}$, Elevation: $560.0\text{ m}$ AMSL  
**Observation Window:** 2017-01-01 to 2023-12-31 (7 calendar years / 2,556 daily epochs)  
**Document Type:** Environmental Extraction Protocols & Alignment Architecture  
**Date:** 2026-10-31  
**Status:** Approved Technical Plan (Zero Large Downloads Initiated)  

---

## 1. Objective & Extraction Bounds

This technical plan defines the exact spatial bounding boxes, temporal windows, query parameters, and feature engineering transformations required to extract multimodal environmental predictors for the `IITM-PUNE-COSMOS` site without downloading superfluous statewide rasters.

```
[Target Point: 18.5372° N, 73.8051° E (Pune, Maharashtra)]
   ├── Spatial Bounding Box (3 km x 3 km Buffer):
   │     • North: 18.5522° N
   │     • South: 18.5222° N
   │     • East:  73.8201° E
   │     • West:  73.7901° E
   └── Temporal Coverage: 2017-01-01 to 2023-12-31 (Daily Monotonic UTC)
```

---

## 2. Dataset Extraction Parameters

### 2.1 ERA5-Land Reanalysis (ECMWF Copernicus CDS)
* **API Service:** Copernicus Climate Data Store (`cdsapi`)
* **Dataset Identifier:** `reanalysis-era5-land`
* **Grid Selection:** Nearest grid centroid at **Latitude: $18.50^\circ\text{ N}$, Longitude: $73.80^\circ\text{ E}$** (Distance from station $\approx 4.1\text{ km}$).
* **Variables Requested:**
  1. `2m_temperature` ($K \rightarrow ^\circ\text{C}$)
  2. `2m_dewpoint_temperature` ($K \rightarrow ^\circ\text{C}$)
  3. `total_precipitation` ($m \rightarrow \text{mm}$)
  4. `surface_solar_radiation_downwards` ($J/\text{m}^2 \rightarrow MJ/\text{m}^2$)
  5. `10m_u_component_of_wind` ($\text{m/s}$)
  6. `10m_v_component_of_wind` ($\text{m/s}$)
* **Temporal Aggregation (Hourly $\rightarrow$ Daily):**
  - Mean temperature: `temperature_2m_mean_c`
  - Min/Max temperature: `temperature_2m_min_c`, `temperature_2m_max_c`
  - Mean dewpoint: `dewpoint_2m_mean_c`
  - Daily cumulative precipitation: `precipitation_total_mm`
  - Cumulative solar radiation: `solar_radiation_total_mj_m2`
  - Scalar wind speed: `wind_speed_10m_ms = sqrt(u^2 + v^2)`
  - Vapor pressure deficit: `vpd_kpa = e_s - e_a`
* **Antecedent Memory Transformations (Strictly `shift(1)` Past-Only):**
  - `precip_lag_1d`
  - `precip_roll_sum_3d`, `precip_roll_sum_7d`, `precip_roll_sum_14d`, `precip_roll_sum_30d`
  - `days_since_rain_gt_1mm`
  - `temp_roll_mean_7d`, `temp_roll_mean_30d`
  - `vpd_roll_mean_7d`, `solar_roll_mean_7d`
  - `doy_sin`, `doy_cos`

---

### 2.2 Sentinel-1 SAR (ESA Copernicus Data Space)
* **Access Mode:** STAC API (`dataspace.copernicus.eu` / `earth-search.aws.element84.com`)
* **Collection:** `sentinel-1-grd`
* **Platform / Sensor:** Sentinel-1A & Sentinel-1B, C-band SAR ($5.405\text{ GHz}$)
* **Sensor Mode:** Interferometric Wide Swath (IW), Ground Range Detected (GRD)
* **Polarizations:** Dual-polarization $\text{VV}$ and $\text{VH}$
* **Orbit Characteristics for Pune:**
  - Relative Orbit / Track: 70 (Ascending, evening pass $\sim 18{:}30\text{ IST}$) and Track 143 (Descending, morning pass $\sim 06{:}15\text{ IST}$).
  - Revisit cycle: 6 to 12 days.
* **Spatial Extraction:** $3\text{ km} \times 3\text{ km}$ bounding box around $(18.5372, 73.8051)$.
* **Preprocessing Pipeline:**
  1. Radiometric calibration to gamma-nought ($\gamma^0$) or sigma-nought ($\sigma^0$).
  2. Range-Doppler terrain correction using ALOS 30m DEM.
  3. Conversion to decibels: $\sigma^0_{\text{dB}} = 10 \cdot \log_{10}(\sigma^0_{\text{linear}})$.
  4. Cross-polarization ratio: $\text{VV}/\text{VH}_{\text{dB}} = \sigma^0_{\text{VV, dB}} - \sigma^0_{\text{VH, dB}}$.
  5. Causal temporal alignment via LOCF (Last Observation Carried Forward): `s1_vv_db_locf`, `s1_vh_db_locf`, `s1_days_since_valid_obs`, `s1_is_stale`.

---

### 2.3 Sentinel-2 MSI (ESA Copernicus Data Space)
* **Access Mode:** STAC API (`dataspace.copernicus.eu`)
* **Collection:** `sentinel-2-l2a` (Bottom-Of-Atmosphere / BOA Surface Reflectance)
* **MGRS Tile:** `43QDA`
* **Spatial Extraction:** $500\text{ m} \times 500\text{ m}$ buffer over the IITM campus meteorological field ($18.5372, 73.8051$).
* **Cloud Masking Strategy:**
  - Strict Scene Classification Layer (SCL) filtering.
  - Exclude pixels with $\text{SCL} \in \{3\text{ (cloud shadow)}, 7\text{ (unclassified)}, 8\text{ (medium cloud)}, 9\text{ (high cloud)}, 10\text{ (cirrus)}, 11\text{ (snow/ice)}\}$.
* **Bands & Vegetation Indices:**
  - $B_4$ (Red, $665\text{ nm}$), $B_8$ (NIR, $842\text{ nm}$), $B_{11}$ (SWIR-1, $1610\text{ nm}$), $B_{12}$ (SWIR-2, $2190\text{ nm}$).
  - $\text{NDVI} = \frac{B_8 - B_4}{B_8 + B_4}$
  - $\text{EVI} = 2.5 \cdot \frac{B_8 - B_4}{B_8 + 6 \cdot B_4 - 7.5 \cdot B_2 + 1}$
  - $\text{NDWI} = \frac{B_8 - B_{11}}{B_8 + B_{11}}$
  - Causal forward-fill alignment (LOCF): `s2_ndvi_locf`, `s2_evi_locf`, `s2_b04_red_locf`, `s2_b08_nir_locf`, `s2_b11_swir1_locf`, `s2_days_since_valid_obs`, `s2_is_stale`.

---

### 2.4 NASA SMAP L3 Radiometer Soil Moisture (L-Band)
* **Product:** `SPL3SMP_E.005` (SMAP Enhanced L3 Radiometer Daily 9 km EASE-Grid 2.0 Soil Moisture)
* **Provider:** NASA National Snow and Ice Data Center (NSIDC) DAAC / Earthdata
* **Grid Cell:** EASE-Grid row/col intersecting Latitude: $18.5372^\circ\text{ N}$, Longitude: $73.8051^\circ\text{ E}$.
* **Variables:**
  - `soil_moisture_am`: Morning pass ($06{:}00\text{ local}$, optimal due to minimized vertical temperature gradient).
  - `soil_moisture_pm`: Evening pass ($18{:}00\text{ local}$).
  - `retrieval_qual_flag`: Quality flag (retain only `quality == 0`).
  - Derived features: `smap_sm_daily_mean_m3_m3`, `smap_sm_lag_1d`, `smap_sm_roll_mean_3d`, `smap_sm_roll_mean_7d`, `smap_days_since_valid_retrieval`.

---

### 2.5 SoilGrids 250m (ISRIC World Soil Information)
* **Access Mode:** ISRIC Web Coverage Service (WCS) query at point $(18.5372, 73.8051)$.
* **Vertical Layers:** 6 standard depth slices:
  1. $0\text{--}5\text{ cm}$
  2. $5\text{--}15\text{ cm}$
  3. $15\text{--}30\text{ cm}$
  4. $30\text{--}60\text{ cm}$
  5. $60\text{--}100\text{ cm}$
  6. $100\text{--}200\text{ cm}$
* **Attributes Extracted:**
  - `soilgrids_clay_pct`, `soilgrids_sand_pct`, `soilgrids_silt_pct`
  - `soilgrids_bdod_g_cm3` (Bulk density)
  - `soilgrids_ocd_kg_m3` (Organic carbon density)
  - `soilgrids_wv0010_m3_m3` (Water content at $-10\text{ kPa}$)
  - `soilgrids_wv0033_m3_m3` (Water content at field capacity, $-33\text{ kPa}$)
  - `soilgrids_wv1500_m3_m3` (Water content at wilting point, $-1500\text{ kPa}$)

---

### 2.6 ALOS World 3D (AW3D30) & SRTM 30m DEM
* **Provider:** Japan Aerospace Exploration Agency (JAXA) / USGS
* **Resolution:** $30\text{ m}$ ($1\text{ arc-second}$)
* **Attributes Extracted for $(18.5372, 73.8051)$:**
  - `dem_elevation_m`: $560.0\text{ m}$
  - `dem_slope_deg`: Surface slope computed from $3 \times 3$ Sobel filter.
  - `dem_aspect_sin`, `dem_aspect_cos`: Terrain aspect trigonometric transformations.
  - `dem_twi`: Topographic Wetness Index.

---

## 3. Multimodal Table Alignment Schema

When Phase 2A data extraction is executed, all daily predictor records will be aligned into a single chronological matrix:

```
data/Maharashtra/interim/IITM-PUNE_aligned_raw.csv (2,556 rows, 2017-01-01 to 2023-12-31)
   ├── Column 1: date_utc (YYYY-MM-DD, monotonic increasing)
   ├── Columns 2–26: 25 Weather-Only Predictors (ERA5-Land daily, memory, cyclical DOY, static edaphics)
   ├── Columns 27–42: Satellite Predictors (SMAP L3, Sentinel-1 SAR LOCF, Sentinel-2 LOCF)
   ├── Columns 43–58: Static Hydraulics & Terrain (SoilGrids 250m, DEM elevation, slope, aspect)
   └── Validated Targets:
         • target_sm_5cm  (From 5 cm Stevens Hydra Probe, when acquired)
         • target_sm_50cm (From 50 cm Stevens Hydra Probe, when acquired)
         • benchmark_crns (From 0–30 cm CRNS, for satellite benchmark comparisons)
         [TARGETS sm_10cm and sm_20cm REMAIN EMPTY / NaN]
```

This strict schema guarantees zero leakage, complete backward compatibility with SoilDepth-AI engineering standards, and scientific target integrity.

