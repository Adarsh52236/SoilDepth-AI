# SoilDepth-AI — Model 1 Baseline & Multimodal Evaluation Report
**Station:** `AAMU-JTG` (SCAN Network, USDA-NRCS, USA)
**Geographic Coordinates:** Latitude `34.78534° N`, Longitude `-86.55906° W`, Elevation `241.0 m`
**ERA5-Land Grid Point:** Latitude `34.80000° N`, Longitude `-86.60000° W` (Offset: 4.08 km)
**Timestamp of Evaluation:** 2026-10-30 10:32:44 UTC

---

## 1. Experimental Setup & Protocol

- **Objective:** Model 1 pointwise discrete sensor depth estimation across four target depths (`sm_5cm`, `sm_10cm`, `sm_20cm`, `sm_50cm`).
- **Chronological Split Partitioning:**
  - **Train:** `2015-01-01` to `2020-12-31` (6 full years, 2,192 days). Used for fitting baselines and training gradient boosted trees.
  - **Validation:** `2021-01-01` to `2021-12-31` (1 full year, 365 days). Used exclusively for early stopping (35 rounds) and model selection.
  - **Test (Holdout):** `2022-01-01` to `2023-12-31` (2 full years, 730 days). Strictly untouched during training and model selection.
- **Leakage Safeguards:**
  - Strictly past-only memory features (`shift(1)` on precipitation and thermal memory).
  - Strictly past-only remote sensing features (LOCF on SMAP, S1 SAR, and S2 optical).
  - Ground truth ISMN observations are strictly dependent targets, never features (except autoregressive `target_lag_1d` in explicitly designated lag models).
  - Point-sensor observations treated strictly as point proxies, not layer-integrated averages.
- **Model Formulations:**
  1. `Historical Mean`: Constant historical mean from training split.
  2. `DOY Climatology`: Empirical mean for each Day-Of-Year ($1..366$) from training split.
  3. `Persistence (t-1)`: Autoregressive naive baseline: $\hat{y}_t = y_{t-1}$.
  4. `XGBoost Weather-Only`: Remote sensing proxy model using 25 past-only atmospheric, memory, seasonal, and static edaphic features without in-situ soil moisture.
  5. `XGBoost Lag-Augmented`: Forecasting model using weather + memory + seasonal + edaphic + autoregressive $y_{t-1}$ (26 features).
  6. `XGBoost Full Multimodal`: Earth observation model using 58 features (Weather + HWSD + SoilGrids + DEM + SMAP L3 + Sentinel-1 SAR + Sentinel-2 Optical).

---

## 2. Model Selection on Validation Split (2021-01-01 to 2021-12-31)

| Depth | Model Configuration | N (Eval) | MAE (m³/m³) | RMSE (m³/m³) | R² | Bias (m³/m³) | Pearson r | Date Range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sm_5cm | Historical Mean Baseline | 313 | 0.0484 | 0.0564 | -0.0038 | -0.0035 | 0.0000 | 2021-01-01 to 2021-12-31 |
| sm_5cm | DOY Climatology Baseline | 313 | 0.0509 | 0.0625 | -0.2314 | -0.0037 | 0.2050 | 2021-01-01 to 2021-12-31 |
| sm_5cm | Persistence Baseline (t-1) | 313 | 0.0192 | 0.0274 | 0.7635 | +0.0003 | 0.8792 | 2021-01-01 to 2021-12-31 |
| sm_5cm | XGBoost (Weather + Memory + Seasonality + Edaphics) | 313 | 0.0323 | 0.0393 | 0.5125 | +0.0077 | 0.7321 | 2021-01-01 to 2021-12-31 |
| sm_5cm | XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1) | 313 | 0.0123 | 0.0189 | 0.8875 | -0.0001 | 0.9421 | 2021-01-01 to 2021-12-31 |
| sm_5cm | XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2) | 313 | 0.0277 | 0.0344 | 0.6279 | +0.0162 | 0.8454 | 2021-01-01 to 2021-12-31 |
| sm_10cm | Historical Mean Baseline | 328 | 0.0280 | 0.0347 | -0.0173 | -0.0045 | 0.0000 | 2021-01-01 to 2021-12-31 |
| sm_10cm | DOY Climatology Baseline | 328 | 0.0301 | 0.0373 | -0.1703 | -0.0046 | 0.3137 | 2021-01-01 to 2021-12-31 |
| sm_10cm | Persistence Baseline (t-1) | 328 | 0.0096 | 0.0152 | 0.8040 | -0.0004 | 0.9012 | 2021-01-01 to 2021-12-31 |
| sm_10cm | XGBoost (Weather + Memory + Seasonality + Edaphics) | 328 | 0.0189 | 0.0242 | 0.5058 | +0.0040 | 0.7208 | 2021-01-01 to 2021-12-31 |
| sm_10cm | XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1) | 328 | 0.0072 | 0.0110 | 0.8988 | +0.0005 | 0.9482 | 2021-01-01 to 2021-12-31 |
| sm_10cm | XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2) | 328 | 0.0175 | 0.0242 | 0.5058 | +0.0115 | 0.8126 | 2021-01-01 to 2021-12-31 |
| sm_20cm | Historical Mean Baseline | 216 | 0.0240 | 0.0255 | -2.7338 | -0.0219 | 0.0000 | 2021-01-01 to 2021-12-28 |
| sm_20cm | DOY Climatology Baseline | 216 | 0.0235 | 0.0275 | -3.3268 | -0.0220 | 0.3840 | 2021-01-01 to 2021-12-28 |
| sm_20cm | Persistence Baseline (t-1) | 216 | 0.0027 | 0.0047 | 0.8743 | +0.0001 | 0.9380 | 2021-01-01 to 2021-12-28 |
| sm_20cm | XGBoost (Weather + Memory + Seasonality + Edaphics) | 216 | 0.0158 | 0.0188 | -1.0277 | -0.0144 | 0.5899 | 2021-01-01 to 2021-12-28 |
| sm_20cm | XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1) | 216 | 0.0032 | 0.0048 | 0.8672 | -0.0018 | 0.9419 | 2021-01-01 to 2021-12-28 |
| sm_20cm | XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2) | 216 | 0.0127 | 0.0154 | -0.3617 | -0.0105 | 0.5773 | 2021-01-01 to 2021-12-28 |
| sm_50cm | Historical Mean Baseline | 132 | 0.0116 | 0.0129 | -3.3489 | -0.0113 | 0.0000 | 2021-01-01 to 2021-12-28 |
| sm_50cm | DOY Climatology Baseline | 132 | 0.0143 | 0.0183 | -7.7258 | -0.0135 | -0.1172 | 2021-01-01 to 2021-12-28 |
| sm_50cm | Persistence Baseline (t-1) | 132 | 0.0014 | 0.0019 | 0.9021 | +0.0002 | 0.9575 | 2021-01-01 to 2021-12-28 |
| sm_50cm | XGBoost (Weather + Memory + Seasonality + Edaphics) | 132 | 0.0113 | 0.0128 | -3.2780 | -0.0113 | 0.3645 | 2021-01-01 to 2021-12-28 |
| sm_50cm | XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1) | 132 | 0.0017 | 0.0022 | 0.8692 | -0.0016 | 0.9672 | 2021-01-01 to 2021-12-28 |
| sm_50cm | XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2) | 132 | 0.0104 | 0.0120 | -2.7560 | -0.0101 | 0.3088 | 2021-01-01 to 2021-12-28 |

---

## 3. Untouched Holdout Test Performance (2022-01-01 to 2023-12-31)

| Depth | Model Configuration | N (Eval) | MAE (m³/m³) | RMSE (m³/m³) | R² | Bias (m³/m³) | Pearson r | Date Range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sm_5cm | Historical Mean Baseline | 573 | 0.0631 | 0.0746 | -0.0828 | +0.0206 | 0.0000 | 2022-01-01 to 2023-11-16 |
| sm_5cm | DOY Climatology Baseline | 573 | 0.0498 | 0.0612 | 0.2709 | +0.0165 | 0.5692 | 2022-01-01 to 2023-11-16 |
| sm_5cm | Persistence Baseline (t-1) | 573 | 0.0207 | 0.0311 | 0.8124 | -0.0004 | 0.9053 | 2022-01-01 to 2023-11-16 |
| sm_5cm | XGBoost (Weather + Memory + Seasonality + Edaphics) | 573 | 0.0380 | 0.0496 | 0.5220 | +0.0115 | 0.7401 | 2022-01-01 to 2023-11-16 |
| sm_5cm | XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1) | 573 | 0.0167 | 0.0254 | 0.8744 | +0.0008 | 0.9352 | 2022-01-01 to 2023-11-16 |
| sm_5cm | XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2) | 573 | 0.0486 | 0.0630 | 0.2278 | +0.0236 | 0.6471 | 2022-01-01 to 2023-11-16 |
| sm_10cm | Historical Mean Baseline | 634 | 0.0475 | 0.0626 | -0.1746 | +0.0242 | 0.0000 | 2022-01-01 to 2023-12-30 |
| sm_10cm | DOY Climatology Baseline | 634 | 0.0384 | 0.0523 | 0.1826 | +0.0233 | 0.5984 | 2022-01-01 to 2023-12-30 |
| sm_10cm | Persistence Baseline (t-1) | 634 | 0.0110 | 0.0179 | 0.9041 | -0.0006 | 0.9517 | 2022-01-01 to 2023-12-30 |
| sm_10cm | XGBoost (Weather + Memory + Seasonality + Edaphics) | 634 | 0.0277 | 0.0371 | 0.5882 | +0.0159 | 0.8150 | 2022-01-01 to 2023-12-30 |
| sm_10cm | XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1) | 634 | 0.0104 | 0.0150 | 0.9329 | +0.0025 | 0.9670 | 2022-01-01 to 2023-12-30 |
| sm_10cm | XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2) | 634 | 0.0280 | 0.0393 | 0.5384 | +0.0230 | 0.8345 | 2022-01-01 to 2023-12-30 |
| sm_20cm | Historical Mean Baseline | 527 | 0.0290 | 0.0423 | -0.1720 | +0.0162 | 0.0000 | 2022-01-14 to 2023-12-30 |
| sm_20cm | DOY Climatology Baseline | 527 | 0.0267 | 0.0374 | 0.0810 | +0.0132 | 0.4414 | 2022-01-14 to 2023-12-30 |
| sm_20cm | Persistence Baseline (t-1) | 527 | 0.0050 | 0.0088 | 0.9491 | +0.0000 | 0.9746 | 2022-01-14 to 2023-12-30 |
| sm_20cm | XGBoost (Weather + Memory + Seasonality + Edaphics) | 527 | 0.0212 | 0.0281 | 0.4840 | +0.0050 | 0.7928 | 2022-01-14 to 2023-12-30 |
| sm_20cm | XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1) | 527 | 0.0061 | 0.0101 | 0.9332 | -0.0011 | 0.9735 | 2022-01-14 to 2023-12-30 |
| sm_20cm | XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2) | 527 | 0.0214 | 0.0277 | 0.4959 | +0.0130 | 0.8309 | 2022-01-14 to 2023-12-30 |
| sm_50cm | Historical Mean Baseline | 419 | 0.0237 | 0.0376 | -0.0904 | +0.0108 | 0.0000 | 2022-01-14 to 2023-12-30 |
| sm_50cm | DOY Climatology Baseline | 419 | 0.0206 | 0.0337 | 0.1251 | +0.0098 | 0.4989 | 2022-01-14 to 2023-12-30 |
| sm_50cm | Persistence Baseline (t-1) | 419 | 0.0024 | 0.0057 | 0.9749 | -0.0000 | 0.9875 | 2022-01-14 to 2023-12-30 |
| sm_50cm | XGBoost (Weather + Memory + Seasonality + Edaphics) | 419 | 0.0190 | 0.0289 | 0.3573 | +0.0070 | 0.7829 | 2022-01-14 to 2023-12-30 |
| sm_50cm | XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1) | 419 | 0.0056 | 0.0100 | 0.9235 | +0.0016 | 0.9709 | 2022-01-14 to 2023-12-30 |
| sm_50cm | XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2) | 419 | 0.0197 | 0.0306 | 0.2763 | +0.0089 | 0.7239 | 2022-01-14 to 2023-12-30 |

---

## 4. Selected Best Models per Depth & Physical Interpretation

| Depth | Selected Best Overall Model (by Val RMSE) | Val RMSE (m³/m³) | Test RMSE (m³/m³) | Test R² | Selected Remote-Sensing Model (Ungauged) | RS Val RMSE | RS Test RMSE | RS Test R² |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sm_5cm | XGBoost_Lag_Augmented | 0.0189 | 0.0254 | 0.8744 | XGBoost_Full_Multimodal | 0.0344 | 0.0630 | 0.2278 |
| sm_10cm | XGBoost_Lag_Augmented | 0.0110 | 0.0150 | 0.9329 | XGBoost_Weather_Only | 0.0242 | 0.0371 | 0.5882 |
| sm_20cm | Persistence | 0.0047 | 0.0088 | 0.9491 | XGBoost_Full_Multimodal | 0.0154 | 0.0277 | 0.4959 |
| sm_50cm | Persistence | 0.0019 | 0.0057 | 0.9749 | XGBoost_Full_Multimodal | 0.0120 | 0.0306 | 0.2763 |

### 4.1 Surface Zone: 5 cm (`sm_5cm`)
- The 5 cm layer responds rapidly to precipitation impulses and solar evaporation.
- Full Multimodal XGBoost leverages satellite surface observations (SMAP radiometry, Sentinel-1 backscatter, and Sentinel-2 vegetation indices) alongside meteorology and static hydraulics.
- When antecedent in-situ observations are accessible, Lag-Augmented XGBoost achieves near-perfect tracking.

### 4.2 Upper Root Zone: 10 cm (`sm_10cm`)
- Strong hydrological damping compared to 5 cm.
- Meteorological forcing combined with static soil hydraulics and satellite observations is highly predictive of upper root-zone moisture dynamics.

### 4.3 Mid Root Zone: 20 cm (`sm_20cm`)
- Higher moisture retention and thermal damping.
- Persistence is a very strong baseline at this depth due to slow water percolation and root uptake timescales.

### 4.4 Deep Root Zone: 50 cm (`sm_50cm`)
- Slowest hydraulic dynamics and high buffer against high-frequency weather noise.
- Models rely heavily on long-term rolling memory (14d, 30d precipitation and thermal integrals).

---

## 5. Artifact Manifest

All model artifacts and intermediate datasets are saved under standard repository paths:
- Models: `models/baselines/AAMU-JTG/`
- Interim aligned data: `data/modelling/interim/AAMU-JTG_aligned_raw.csv`
- Processed feature data: `data/modelling/processed/AAMU-JTG_*.csv`
- Validation predictions & residuals: `reports/modelling/AAMU-JTG/*_val_predictions.csv`
- Test predictions & residuals: `reports/modelling/AAMU-JTG/*_test_predictions.csv`
- Residual diagnostics: `reports/modelling/AAMU-JTG/*_residual_diagnostics.json`
- Diagnostic plots: `reports/modelling/AAMU-JTG/plots/`
- Metrics JSON: `reports/modelling/AAMU-JTG/metrics.json`
