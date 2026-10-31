# SoilDepth-AI — Baseline Modelling Pipeline Documentation

**Author:** Senior Data Engineer & Geospatial Soil-Moisture ML Researcher, SoilDepth-AI  
**Pilot Station:** `AAMU-JTG` (Alabama A&M University - Winfred Thomas Agricultural Research Station, USA)  
**Evaluation Holdout Period:** `2022-01-01` to `2023-12-31` (Chronological Unseen Test Split)  
**Status:** Validated, Tested, and Fully Reproducible

---

## 1. Executive Summary

This document details the first baseline machine learning pipeline for **SoilDepth-AI**, establishing reproducible benchmarks for estimating volumetric soil moisture ($\text{m}^3/\text{m}^3$) across discrete soil depths. 

Using validated daily meteorological forcing from **ERA5-Land** and in-situ ground truth observations from the **ISMN SCAN** network at pilot station `AAMU-JTG`, this pipeline:
1. Enforces **station metadata verification** (latitude, longitude, elevation, sensor depth).
2. Treats observations at $\sim 5\text{ cm}$, $\sim 10\text{ cm}$, $\sim 20\text{ cm}$, and $\sim 50\text{ cm}$ as **independent point-sensor proxies** rather than assuming layer-average moisture or arbitrarily fusing sensors.
3. Implements **strict chronological data splitting** (Train: 2015–2020, Val: 2021, Test: 2022–2023) and **shift-based memory features** (`shift(1)`) to guarantee complete absence of temporal leakage.
4. Benchmarks five distinct model configurations per depth:
   - **Historical Mean Baseline**
   - **Day-of-Year Climatology Baseline**
   - **Persistence Baseline** ($\hat{y}_t = y_{t-1}$)
   - **Weather-Only XGBoost** (Remote Sensing / Meteorological Proxy)
   - **Lag-Augmented XGBoost** (Forecasting Model)

---

## 2. Station Verification & Sensor Depth Provenance

### 2.1 Station Identity & Coordinates
The pilot station was verified across both ISMN STM headers and ERA5-Land grid metadata:
- **Station ID:** `AAMU-JTG`
- **Network:** ISMN SCAN (United States USDA-NRCS)
- **Station Location:** Latitude `34.78534° N`, Longitude `-86.55906° W`, Elevation `241.0 m`
- **ERA5-Land Grid Point:** Latitude `34.80000° N`, Longitude `-86.60000° W` (Haversine offset: 4.08 km)
- **Soil Class (HWSD):** Silt Loam / Sandy Clay Loam (Grassland vegetation)

### 2.2 Discrete Point-Sensor Mappings
Ground-truth observations are recorded using calibrated `Stevens-Hydraprobe-Analog` point sensors. In accordance with physical soil measurement principles, these are **point proxies** and must never be merged into synthetic depth ranges:

| Target Key | Nominal Depth | Metric Depth | ISMN Archive Path | HWSD Edaphic Layer | Role in Hydrological Column |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sm_5cm` | $5.08\text{ cm}$ | $0.0508\text{ m}$ | `surface_0-10cm/` | $0.00 - 0.30\text{ m}$ | Surface boundary zone (rapid weather response) |
| `sm_10cm` | $10.16\text{ cm}$ | $0.1016\text{ m}$ | `middle_10-30cm/` | $0.00 - 0.30\text{ m}$ | Upper root zone (strong evaporation sensitivity) |
| `sm_20cm` | $20.32\text{ cm}$ | $0.2032\text{ m}$ | `middle_10-30cm/` | $0.00 - 0.30\text{ m}$ | Mid root zone (transpiration and percolation) |
| `sm_50cm` | $50.80\text{ cm}$ | $0.5080\text{ m}$ | `deep_30-60cm/` | $0.30 - 1.00\text{ m}$ | Deep root zone / subsoil buffer |

---

## 3. Data Processing & Quality Filtering

### 3.1 ERA5-Land Weather Ingestion
Daily weather drivers are aggregated from hourly ERA5-Land NetCDF data (`ERA5_LAND/processed/AAMU-JTG/ERA5Land_AAMU-JTG_2015-2023_daily.csv`):
- `temperature_2m_mean_c`, `temperature_2m_min_c`, `temperature_2m_max_c`: Daily 2m air temperatures (°C).
- `dewpoint_2m_mean_c`: Mean 2m dewpoint temperature (°C).
- `precipitation_total_mm`: Cumulative daily precipitation ($\text{tp} \times 1000\text{ mm}$).
- `solar_radiation_total_mj_m2`: Daily downward solar radiation integral ($\sum \text{ssrd} / 10^6\text{ MJ}/\text{m}^2$).
- `wind_u10_mean_ms`, `wind_v10_mean_ms`: Mean 10m zonal and meridional wind components.

### 3.2 ISMN Quality Control & Diurnal Completeness
Hourly SCAN records are filtered with strict quality criteria:
- **Quality flag (`qflag`):** Must be `'G'` (Good).
- **Provider flag (`pflag`):** Must be `'V'` (Validated) or `'E'` (Estimated).
- **Physical bounds:** $0.00 \le \theta \le 0.60\text{ m}^3/\text{m}^3$.
- **Diurnal Completeness Rule:** A day is considered valid if and only if it contains $\ge 18$ valid hourly readings ($75\%$ threshold). Days with $< 18$ hours are set to `NaN` to prevent diurnal sampling bias.

---

## 4. Feature Engineering Architecture

All features are designed to avoid look-ahead bias and capture physical hydrological memory:

### 4.1 Atmospheric Diagnostic Features
- **Vapor Pressure Deficit (VPD in kPa):**
  $$e_s(T) = 0.61078 \exp\left(\frac{17.27 \cdot T}{T + 237.3}\right)$$
  $$e_a(T_d) = 0.61078 \exp\left(\frac{17.27 \cdot T_d}{T_d + 237.3}\right)$$
  $$\text{VPD} = \max(0.0, e_s - e_a)$$
- **Horizontal Wind Speed:** $\sqrt{u_{10}^2 + v_{10}^2}$ [m/s].

### 4.2 Shift-Based Weather Memory Features
To guarantee zero intra-day or future leakage, all rolling features are calculated on `precipitation.shift(1)` and `temperature.shift(1)`:
- `precip_lag_1d`: $P_{t-1}$ (yesterday's precipitation).
- `precip_roll_sum_3d`: $\sum_{k=1}^3 P_{t-k}$ (past 3-day rainfall integral).
- `precip_roll_sum_7d`: $\sum_{k=1}^7 P_{t-k}$ (past 7-day rainfall integral).
- `precip_roll_sum_14d`: $\sum_{k=1}^{14} P_{t-k}$ (past 14-day rainfall integral).
- `precip_roll_sum_30d`: $\sum_{k=1}^{30} P_{t-k}$ (past 30-day rainfall integral).
- `days_since_rain_gt_1mm`: Number of days elapsed since the most recent rainfall event exceeding $1.0\text{ mm}$ prior to day $t$.
- `temp_roll_mean_7d`, `temp_roll_mean_30d`: Antecedent thermal regimes.
- `vpd_roll_mean_7d`, `solar_roll_mean_7d`: Antecedent evaporative demand.

### 4.3 Cyclical Seasonality
- Day-of-year circular projection: $\sin(2\pi \cdot \text{DOY} / 365.25)$ and $\cos(2\pi \cdot \text{DOY} / 365.25)$.

### 4.4 Static Soil Edaphics (HWSD)
Ingested from `SCAN_SCAN_AAMU-JTG_static_variables.csv`:
- `clay_fraction_pct`, `sand_fraction_pct`, `silt_fraction_pct`, `organic_carbon_pct`, `saturation_m3_m3`.

---

## 5. Temporal Leakage Safeguards

1. **Chronological Splitting:**
   - **Training:** `2015-01-01` to `2020-12-31` (6 years, 2,192 days)
   - **Validation:** `2021-01-01` to `2021-12-31` (1 year, 365 days; early stopping only)
   - **Testing:** `2022-01-01` to `2023-12-31` (2 years, 730 days; holdout evaluation)
   - Random shuffling is strictly prohibited.
2. **Perturbation Invariance Tested:** Verified via automated unit tests that altering weather at day $t+k$ produces zero change in any feature at day $t$.
3. **No Target Leakage:** Future soil moisture values are strictly excluded. For the Lag-Augmented model, only $y_{t-1}$ is permitted.

---

## 6. Empirical Results & Benchmark Comparison

Models evaluated chronologically on the unseen test period (`2022-01-01` to `2023-12-31`):

| Depth | Model Configuration | N (Eval) | MAE ($\text{m}^3/\text{m}^3$) | RMSE ($\text{m}^3/\text{m}^3$) | $R^2$ | Bias ($\text{m}^3/\text{m}^3$) | Pearson $r$ | Evaluation Date Range |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **5 cm** | Historical Mean Baseline | 573 | 0.0631 | 0.0746 | -0.0828 | +0.0206 | 0.0000 | 2022-01-01 to 2023-11-16 |
| **5 cm** | DOY Climatology Baseline | 573 | 0.0498 | 0.0612 | 0.2709 | +0.0165 | 0.5692 | 2022-01-01 to 2023-11-16 |
| **5 cm** | Persistence Baseline ($t-1$) | 573 | 0.0207 | 0.0311 | 0.8124 | -0.0004 | 0.9053 | 2022-01-01 to 2023-11-16 |
| **5 cm** | **XGBoost (Weather-Only)** | 573 | **0.0380** | **0.0496** | **0.5220** | **+0.0116** | **0.7401** | 2022-01-01 to 2023-11-16 |
| **5 cm** | **XGBoost (Lag-Augmented)** | 573 | **0.0167** | **0.0254** | **0.8744** | **+0.0008** | **0.9352** | 2022-01-01 to 2023-11-16 |
| **10 cm** | Historical Mean Baseline | 634 | 0.0475 | 0.0626 | -0.1746 | +0.0242 | 0.0000 | 2022-01-01 to 2023-12-30 |
| **10 cm** | DOY Climatology Baseline | 634 | 0.0384 | 0.0523 | 0.1826 | +0.0233 | 0.5984 | 2022-01-01 to 2023-12-30 |
| **10 cm** | Persistence Baseline ($t-1$) | 634 | 0.0110 | 0.0179 | 0.9041 | -0.0006 | 0.9517 | 2022-01-01 to 2023-12-30 |
| **10 cm** | **XGBoost (Weather-Only)** | 634 | **0.0277** | **0.0371** | **0.5882** | **+0.0159** | **0.8150** | 2022-01-01 to 2023-12-30 |
| **10 cm** | **XGBoost (Lag-Augmented)** | 634 | **0.0104** | **0.0150** | **0.9329** | **+0.0025** | **0.9670** | 2022-01-01 to 2023-12-30 |
| **20 cm** | Historical Mean Baseline | 527 | 0.0290 | 0.0423 | -0.1720 | +0.0162 | 0.0000 | 2022-01-14 to 2023-12-30 |
| **20 cm** | DOY Climatology Baseline | 527 | 0.0267 | 0.0374 | 0.0810 | +0.0132 | 0.4414 | 2022-01-14 to 2023-12-30 |
| **20 cm** | Persistence Baseline ($t-1$) | 527 | 0.0050 | 0.0088 | 0.9491 | +0.0000 | 0.9746 | 2022-01-14 to 2023-12-30 |
| **20 cm** | **XGBoost (Weather-Only)** | 527 | **0.0212** | **0.0281** | **0.4840** | **+0.0050** | **0.7928** | 2022-01-14 to 2023-12-30 |
| **20 cm** | **XGBoost (Lag-Augmented)** | 527 | **0.0061** | **0.0101** | **0.9332** | **-0.0011** | **0.9735** | 2022-01-14 to 2023-12-30 |
| **50 cm** | Historical Mean Baseline | 419 | 0.0237 | 0.0376 | -0.0904 | +0.0108 | 0.0000 | 2022-01-14 to 2023-12-30 |
| **50 cm** | DOY Climatology Baseline | 419 | 0.0206 | 0.0337 | 0.1251 | +0.0098 | 0.4989 | 2022-01-14 to 2023-12-30 |
| **50 cm** | Persistence Baseline ($t-1$) | 419 | 0.0024 | 0.0057 | 0.9749 | -0.0000 | 0.9875 | 2022-01-14 to 2023-12-30 |
| **50 cm** | **XGBoost (Weather-Only)** | 419 | **0.0190** | **0.0289** | **0.3573** | **+0.0070** | **0.7829** | 2022-01-14 to 2023-12-30 |
| **50 cm** | **XGBoost (Lag-Augmented)** | 419 | **0.0056** | **0.0100** | **0.9235** | **+0.0016** | **0.9709** | 2022-01-14 to 2023-12-30 |

### 6.1 Scientific Insights
1. **Weather-Only Reconstruction Performance:**
   - At 10 cm, pure atmospheric forcing drives an $R^2$ of **0.588** and Pearson $r$ of **0.815**, proving that surface weather features effectively estimate root-zone dynamics even without satellite or in-situ ground sensors.
   - At 5 cm, $R^2$ is **0.522** with Pearson $r$ of **0.740**.
2. **Persistence Strength at Depth:**
   - At 50 cm, soil moisture changes very slowly due to deep hydraulic damping. Persistence achieves $R^2 = 0.975$ and $\text{MAE} = 0.0024\text{ m}^3/\text{m}^3$. Any deep soil moisture forecasting model must beat persistence to demonstrate genuine prognostic value.
3. **Lag-Augmentation Synergy:**
   - In dynamic upper layers (5 cm and 10 cm), adding atmospheric drivers to persistence significantly outperforms pure persistence:
     - At 5 cm: MAE drops from **0.0207** (persistence) to **0.0167** (XGBoost), with $R^2$ increasing from **0.812** to **0.874**.
     - At 10 cm: MAE drops from **0.0110** to **0.0104**, with $R^2$ increasing from **0.904** to **0.933**.

---

## 7. Artifact Manifest & Directory Structure

```text
SoilDepth-AI/
├── dataset/
│   ├── ERA5_LAND/                     # Meteorological archives and processed tables
│   │   ├── raw/
│   │   ├── processed/
│   │   ├── audit/
│   │   └── scripts/
│   └── ISMN/                          # In-situ ground truth networks
│       ├── SCAN/                      # Soil Climate Analysis Network
│       └── IIT_KANPUR/                # Reference historical network
├── services/
│   └── modelling/
│       ├── __init__.py
│       ├── config.py
│       ├── dataset_builder.py
│       ├── feature_engineering.py
│       ├── baselines.py
│       ├── evaluate.py
│       └── train_xgboost.py
├── data/
│   └── modelling/
│       ├── interim/
│       │   ├── AAMU-JTG_aligned_raw.csv
│       │   └── AAMU-JTG_alignment_audit.json
│       └── processed/
│           ├── AAMU-JTG_all_depths_features_daily.csv
│           ├── AAMU-JTG_sm_5cm_daily.csv
│           ├── AAMU-JTG_sm_10cm_daily.csv
│           ├── AAMU-JTG_sm_20cm_daily.csv
│           └── AAMU-JTG_sm_50cm_daily.csv
├── models/
│   └── baselines/
│       └── AAMU-JTG/
│           ├── sm_5cm_weather_only_xgb.json
│           ├── sm_5cm_lag_augmented_xgb.json
│           ├── sm_10cm_weather_only_xgb.json
│           ├── sm_10cm_lag_augmented_xgb.json
│           ├── sm_20cm_weather_only_xgb.json
│           ├── sm_20cm_lag_augmented_xgb.json
│           ├── sm_50cm_weather_only_xgb.json
│           ├── sm_50cm_lag_augmented_xgb.json
│           ├── *_feature_importances.csv
│           └── training_metadata.json
├── reports/
│   └── modelling/
│       └── AAMU-JTG/
│           ├── evaluation_report.md
│           ├── metrics.json
│           └── *_test_predictions.csv
├── tests/
│   ├── conftest.py
│   ├── test_era5_land_processing.py
│   └── modelling/
│       ├── test_dataset_builder.py
│       ├── test_feature_engineering.py
│       ├── test_no_temporal_leakage.py
│       └── test_evaluation.py
└── docs/
    └── modelling/
        └── baseline_pipeline.md
```

---

## 8. Execution Commands

To reproduce the full pipeline end-to-end:

```bash
# 1. Run unit test suite
pytest tests/

# 2. Build aligned interim dataset
python -m services.modelling.dataset_builder

# 3. Derive past-only features
python -m services.modelling.feature_engineering

# 4. Train baselines and XGBoost models
python -m services.modelling.train_xgboost
```
