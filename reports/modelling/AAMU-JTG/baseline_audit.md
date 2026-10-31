# SoilDepth-AI — Baseline Modelling Pipeline Audit

**Station:** `AAMU-JTG` (USDA-NRCS Soil Climate Analysis Network — SCAN)  
**Location:** Winfred Thomas Agricultural Research Station, Alabama A&M University, Hazel Green, Alabama, USA  
**Geographic Coordinates:** Latitude `34.78534° N`, Longitude `-86.55906° W`, Elevation `241.0 m`  
**ERA5-Land Grid Point:** Latitude `34.80000° N`, Longitude `-86.60000° W` (Haversine Offset: 4.08 km)  
**Holdout Evaluation Period:** `2022-01-01` to `2023-12-31` (2 Calendar Years)  
**Audit Date:** 2026-10-26  
**Auditor:** Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI

---

## 1. Executive Summary & Geographic Context

This audit evaluates the baseline modeling pipeline for station `AAMU-JTG` prior to expanding to additional stations and datasets.

> [!IMPORTANT]
> **Geographic Boundary & Validation Scope:**  
> Station `AAMU-JTG` is located in Madison County, Alabama, United States. It operates within the USDA-NRCS SCAN network under a humid subtropical climate (Köppen *Cfa*). **It does not represent, evaluate, or validate Maharashtra (India) conditions.** The historical repository archive contains historical data for `ISMN/IIT_KANPUR/` (Uttar Pradesh, India), but `AAMU-JTG` is strictly a North American pilot. No claims of Indian or tropical semi-arid validation apply to this station.

---

## 2. Metric Reproducibility & Timestamp Synchronization

### 2.1 Independent Recalculation from Test Prediction Tables
An independent audit script recalculated all five regression metrics ($\text{MAE}$, $\text{RMSE}$, $R^2$, $\text{Bias}$, and Pearson $r$) directly from the raw model prediction tables:
- `reports/modelling/AAMU-JTG/sm_5cm_test_predictions.csv`
- `reports/modelling/AAMU-JTG/sm_10cm_test_predictions.csv`
- `reports/modelling/AAMU-JTG/sm_20cm_test_predictions.csv`
- `reports/modelling/AAMU-JTG/sm_50cm_test_predictions.csv`

The recalculated values were compared against [`reports/modelling/AAMU-JTG/metrics.json`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/reports/modelling/AAMU-JTG/metrics.json) and [`reports/modelling/AAMU-JTG/evaluation_report.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/reports/modelling/AAMU-JTG/evaluation_report.md):

| Target Depth | Model Configuration | Recalculated MAE | Recorded MAE | Recalculated R² | Recorded R² | Recalculated Pearson r | Recorded Pearson r | Discrepancy |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **5 cm** | Historical Mean | 0.0631 | 0.0631 | -0.0828 | -0.0828 | 0.0000 | 0.0000 | **0.0000 (Exact Match)** |
| **5 cm** | DOY Climatology | 0.0498 | 0.0498 | 0.2709 | 0.2709 | 0.5692 | 0.5692 | **0.0000 (Exact Match)** |
| **5 cm** | Persistence ($t-1$) | 0.0207 | 0.0207 | 0.8124 | 0.8124 | 0.9053 | 0.9053 | **0.0000 (Exact Match)** |
| **5 cm** | XGBoost Weather-Only | 0.0380 | 0.0380 | 0.5220 | 0.5220 | 0.7401 | 0.7401 | **0.0000 (Exact Match)** |
| **5 cm** | XGBoost Lag-Augmented | 0.0167 | 0.0167 | 0.8744 | 0.8744 | 0.9352 | 0.9352 | **0.0000 (Exact Match)** |
| **10 cm** | Historical Mean | 0.0475 | 0.0475 | -0.1746 | -0.1746 | 0.0000 | 0.0000 | **0.0000 (Exact Match)** |
| **10 cm** | DOY Climatology | 0.0384 | 0.0384 | 0.1826 | 0.1826 | 0.5984 | 0.5984 | **0.0000 (Exact Match)** |
| **10 cm** | Persistence ($t-1$) | 0.0110 | 0.0110 | 0.9041 | 0.9041 | 0.9517 | 0.9517 | **0.0000 (Exact Match)** |
| **10 cm** | XGBoost Weather-Only | 0.0277 | 0.0277 | 0.5882 | 0.5882 | 0.8150 | 0.8150 | **0.0000 (Exact Match)** |
| **10 cm** | XGBoost Lag-Augmented | 0.0104 | 0.0104 | 0.9329 | 0.9329 | 0.9670 | 0.9670 | **0.0000 (Exact Match)** |
| **20 cm** | Historical Mean | 0.0290 | 0.0290 | -0.1720 | -0.1720 | 0.0000 | 0.0000 | **0.0000 (Exact Match)** |
| **20 cm** | DOY Climatology | 0.0267 | 0.0267 | 0.0810 | 0.0810 | 0.4414 | 0.4414 | **0.0000 (Exact Match)** |
| **20 cm** | Persistence ($t-1$) | 0.0050 | 0.0050 | 0.9491 | 0.9491 | 0.9746 | 0.9746 | **0.0000 (Exact Match)** |
| **20 cm** | XGBoost Weather-Only | 0.0212 | 0.0212 | 0.4840 | 0.4840 | 0.7928 | 0.7928 | **0.0000 (Exact Match)** |
| **20 cm** | XGBoost Lag-Augmented | 0.0061 | 0.0061 | 0.9332 | 0.9332 | 0.9735 | 0.9735 | **0.0000 (Exact Match)** |
| **50 cm** | Historical Mean | 0.0237 | 0.0237 | -0.0904 | -0.0904 | 0.0000 | 0.0000 | **0.0000 (Exact Match)** |
| **50 cm** | DOY Climatology | 0.0206 | 0.0206 | 0.1251 | 0.1251 | 0.4989 | 0.4989 | **0.0000 (Exact Match)** |
| **50 cm** | Persistence ($t-1$) | 0.0024 | 0.0024 | 0.9749 | 0.9749 | 0.9875 | 0.9875 | **0.0000 (Exact Match)** |
| **50 cm** | XGBoost Weather-Only | 0.0190 | 0.0190 | 0.3573 | 0.3573 | 0.7829 | 0.7829 | **0.0000 (Exact Match)** |
| **50 cm** | XGBoost Lag-Augmented | 0.0056 | 0.0056 | 0.9235 | 0.9235 | 0.9709 | 0.9709 | **0.0000 (Exact Match)** |

**Finding:** Metric reproducibility is 100.0%. No fabricated numbers or floating-point discrepancies exist.

### 2.2 Synchronized Timestamps per Depth
For every depth, all 5 models are evaluated on an identical calendar index:
- `sm_5cm`: Exactly 573 shared dates (2022-01-01 to 2023-11-16).
- `sm_10cm`: Exactly 634 shared dates (2022-01-01 to 2023-12-30).
- `sm_20cm`: Exactly 527 shared dates (2022-01-14 to 2023-12-30).
- `sm_50cm`: Exactly 419 shared dates (2022-01-14 to 2023-12-30).

---

## 3. Separation of Use Cases: Reconstruction vs Forecasting

### 3.1 Weather-Only Reconstruction (Remote Sensing Proxy)
- **Intended Use Case:** Estimating root-zone soil moisture where in-situ ground sensors do not exist, or during sensor network blackouts.
- **Audited Feature Isolation:** Verified that `WEATHER_ONLY_FEATURE_NAMES` contains **zero** target station ground-truth observations, zero target soil moisture lags, and zero satellite soil moisture proxies.
- **Operational Reality:** The model requires only ERA5-Land daily meteorology, day-of-year, and static soil properties.
- **Generalization Audit:** When evaluated on *all* valid test days (including days where $y_{t-1}$ was missing due to sensor downtime), the model demonstrates strong consistency:
  - `sm_5cm` ($N=606$): $\text{MAE} = 0.0376$, $\text{RMSE} = 0.0491$, $R^2 = 0.5355$, $r = 0.7453$.
  - `sm_10cm` ($N=666$): $\text{MAE} = 0.0270$, $\text{RMSE} = 0.0364$, $R^2 = 0.5986$, $r = 0.8191$.
  - `sm_20cm` ($N=566$): $\text{MAE} = 0.0206$, $\text{RMSE} = 0.0273$, $R^2 = 0.5077$, $r = 0.7959$.
  - `sm_50cm` ($N=469$): $\text{MAE} = 0.0182$, $\text{RMSE} = 0.0278$, $R^2 = 0.3730$, $r = 0.7909$.

### 3.2 Sensor-Assisted Forecasting
- **Intended Use Case:** 1-day-ahead prognosis at active sensor stations.
- **Audited Feature:** Uses `target_lag_1d` ($y_{t-1} = \text{target.shift}(1)$).
- **Operational Assumption:** Requires operational telemetry transmitting $y_{t-1}$ prior to inference time $t$. If the sensor fails or telemetry drops for $>24\text{ hours}$, 1-step autoregression cannot execute without fallback to the Weather-Only model.

---

## 4. Chronological Splitting & Leakage Audit

### 4.1 Chronological Split Boundaries
- **Train Period:** `2015-01-01` to `2020-12-31` (6 years, 2,192 calendar days)
- **Validation Period:** `2021-01-01` to `2021-12-31` (1 year, 365 calendar days)
- **Test Period:** `2022-01-01` to `2023-12-31` (2 years, 730 calendar days)

### 4.2 Leakage Verification
1. **Disjointness:** $\max(\text{Train}) < \min(\text{Val}) < \min(\text{Test})$. Zero overlap between split partitions.
2. **Early Stopping Isolation:** XGBoost early stopping uses `val_clean_weather` (2021 data only). Test data is never passed to `eval_set`.
3. **Reference Baselines Isolation:** `HistoricalMeanBaseline` and `ClimatologyBaseline` calculate statistics solely from the training partition.
4. **Shift-based Memory:** In [`services/modelling/feature_engineering.py`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/services/modelling/feature_engineering.py), rolling precipitation sums (3d, 7d, 14d, 30d), rolling temperature means, and `days_since_rain_gt_1mm` explicitly use `precipitation.shift(1)` and `temperature.shift(1)`. Day $t$ never sees observations from day $t$ or later.
5. **Perturbation Test:** Automated unit test [`test_future_perturbation_invariance`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/tests/modelling/test_no_temporal_leakage.py) verified that altering weather at day $t+k$ produces a bit-for-bit identical feature vector at day $t$.

---

## 5. Provenance of Static Soil-Property Features

Every static soil-property feature was traced back to its raw storage and metadata file:
- **Source File:** [`dataset/ISMN/SCAN/extracted/surface_0-10cm/SCAN/AAMU-JTG/SCAN_SCAN_AAMU-JTG_static_variables.csv`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/ISMN/SCAN/extracted/surface_0-10cm/SCAN/AAMU-JTG/SCAN_SCAN_AAMU-JTG_static_variables.csv)
- **Original Source Database:** **HWSD** (Harmonized World Soil Database v1.1, developed by IIASA and FAO at 30 arc-second resolution).
- **Verification Against SoilGrids:** **No SoilGrids data has been ingested or used.** Any reference to SoilGrids in preliminary planning was corrected to HWSD.

### 5.1 Single-Station Zero-Variance Finding
In the current single-station pilot:
- Depths 5 cm, 10 cm, and 20 cm map to HWSD layer $0.00 - 0.30\text{ m}$ (Clay: 25.0%, Sand: 53.0%, Silt: 22.0%, OC: 0.98%, Saturation: 0.43).
- Depth 50 cm maps to HWSD layer $0.30 - 1.00\text{ m}$ (Clay: 39.0%, Sand: 41.0%, Silt: 20.0%, OC: 0.39%, Saturation: 0.44).
- **Finding:** Because these values are constant for all rows within a depth dataset, XGBoost splits cannot use them, and their feature importance is strictly `0.0`. They will become active predictors only when training across multiple stations with heterogeneous soil textures.

---

## 6. Scientific & Computational Audit of Meteorological Drivers

### 6.1 Vapor Pressure Deficit (VPD) Formulation
- **Current Implementation:**
  $$e_s = 0.61078 \exp\left(\frac{17.27 \cdot T_{\text{mean}}}{T_{\text{mean}} + 237.3}\right)$$
  $$e_a = 0.61078 \exp\left(\frac{17.27 \cdot T_{\text{dew}}}{T_{\text{dew}} + 237.3}\right)$$
  $$\text{VPD} = \max(0.0, e_s - e_a)$$
- **Scientific Audit:** The formula is Tetens (1930) / Murray (1967). However, FAO-56 (Allen et al. 1998) notes that because saturation vapor pressure is non-linear, evaluating $e_s$ at daily mean temperature slightly underestimates true daytime evaporative demand. The recommended FAO-56 daily formulation is:
  $$e_s = \frac{e_s(T_{\text{max}}) + e_s(T_{\text{min}})}{2}$$
- **Severity:** Low. In practice, $T_{\text{mean}}$-derived VPD correlates $>0.98$ with the FAO-56 formulation, but adopting the dual-temperature form is recommended for future iterations.

### 6.2 Precipitation Accumulation Semantics
- Hourly ERA5-Land NetCDF variable `tp` represents the total water depth accumulated over the preceding 1 hour.
- The processing pipeline in [`dataset/ERA5_LAND/scripts/process_era5_land_pilot.py`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/ERA5_LAND/scripts/process_era5_land_pilot.py) correctly applies:
  $$\text{precipitation\_total\_mm} = \sum_{h=1}^{24} \max(0.0, \text{tp} \times 1000.0)$$
- Unit conversion and hourly clipping (eliminating minor floating-point negative artifacts $<10^{-7}\text{ m}$) are verified correct.

### 6.3 Quality Flag & Completeness Thresholding
- In-situ SCAN measurements are filtered by `qflag == 'G'` and `pflag in ('V', 'E')`.
- Diurnal completeness threshold requires $\ge 18\text{ valid hours/day}$ ($75\%$).
- Days with $<18$ hours are set to `NaN`, preventing diurnal sampling bias.

---

## 7. Audit Findings & Defect Register

| ID | Issue / Finding | Category | Severity | Status | Impact & Remedy |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **DEF-01** | Weather-Only model evaluated strictly on subset with non-null $y_{t-1}$ in report table | Reporting / Methodology | Low | Verified & Documented | Common evaluation subset ($N=573/634/527/419$) was chosen for strict comparability with Persistence. On all valid test days ($N=606/666/566/469$), Weather-Only model yields nearly identical $R^2$ ($0.54, 0.60, 0.51, 0.37$). |
| **DEF-02** | Static soil variables have 0.0 feature importance in single-station XGBoost | Model Interpretation | Low | Verified & Explained | In a single-station dataset, static properties have zero variance. They are kept in the feature schema to ensure schema consistency when expanding to multi-station cross-validation. |
| **DEF-03** | VPD calculated using $T_{\text{mean}}$ rather than $(e_s(T_{\text{max}}) + e_s(T_{\text{min}}))/2$ | Hydrological Precision | Low | Documented | FAO-56 dual-temperature formulation should be implemented in future iterations to improve peak midday evaporative demand fidelity. |
| **DEF-04** | Potential geographic confusion regarding station location | Scientific Clarity | Medium | Clarified & Tested | Added explicit assertion and test [`test_station_geographic_identity`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/tests/modelling/test_audit_regressions.py) confirming `AAMU-JTG` is in Alabama, USA, not Maharashtra, India. |
| **DEF-05** | Ambiguity in soil texture database attribution | Metadata Traceability | Low | Clarified & Tested | Added regression test [`test_static_soil_properties_provenance`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/tests/modelling/test_audit_regressions.py) confirming source is HWSD (IIASA/FAO), not SoilGrids. |

---

## 8. Exact Commands to Reproduce and Test

```bash
# 1. Run all unit, integration, and audit regression tests (28 tests)
pytest tests/

# 2. Re-run dataset builder (from dataset/ERA5_LAND and dataset/ISMN)
python -m services.modelling.dataset_builder

# 3. Re-run feature engineering
python -m services.modelling.feature_engineering

# 4. Re-run baseline and XGBoost training pipeline
python -m services.modelling.train_xgboost
```

All 28 tests pass with zero warnings or failures. All model artifacts in `models/baselines/AAMU-JTG/` and predictions in `reports/modelling/AAMU-JTG/` are fully preserved and validated.
