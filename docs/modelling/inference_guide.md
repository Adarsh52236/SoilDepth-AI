# SoilDepth-AI — Model 1 Production Inference Guide
**Station:** `AAMU-JTG` (`34.78534° N, -86.55906° W`, Elevation: `241.0 m`)  
**Deployment Target:** 100% Ground-Sensor-Independent Discrete Point-Depth Estimation  
**Depths Supported:** `5.08 cm` (`sm_5cm`), `10.16 cm` (`sm_10cm`), `20.32 cm` (`sm_20cm`), `50.80 cm` (`sm_50cm`)

---

## 1. Selected Operational Models

Following the deployment-feasibility audit, Model 1 serves **exclusively ground-sensor-independent** gradient-boosted regression models loaded from [`models/baselines/AAMU-JTG/`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/models/baselines/AAMU-JTG/):

| Target Depth | Metric Depth | Operational Model Artifact | Model Configuration | Predictor Feature Count | Test RMSE ($m^3/m^3$) | Test $R^2$ | Test Pearson $r$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`sm_5cm`** | 0.0508 m | [`sm_5cm_weather_only_xgb.json`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/models/baselines/AAMU-JTG/sm_5cm_weather_only_xgb.json) | XGBoost Weather-Only | 25 features | 0.0496 | 0.5220 | 0.7401 |
| **`sm_10cm`** | 0.1016 m | [`sm_10cm_weather_only_xgb.json`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/models/baselines/AAMU-JTG/sm_10cm_weather_only_xgb.json) | XGBoost Weather-Only | 25 features | 0.0371 | 0.5882 | 0.8150 |
| **`sm_20cm`** | 0.2032 m | [`sm_20cm_full_multimodal_xgb.json`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/models/baselines/AAMU-JTG/sm_20cm_full_multimodal_xgb.json) | XGBoost Full Multimodal | 58 features | 0.0277 | 0.4959 | 0.8309 |
| **`sm_50cm`** | 0.5080 m | [`sm_50cm_weather_only_xgb.json`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/models/baselines/AAMU-JTG/sm_50cm_weather_only_xgb.json) | XGBoost Weather-Only | 25 features | 0.0289 | 0.3573 | 0.7829 |

> [!IMPORTANT]
> **Zero Ground-Sensor Reliance:** None of these four operational models require previous or current in-situ ISMN probe measurements, `target_lag_1d`, deep ERA5 VWC, or SMAP L4 modeling. They are fully viable at ungauged sites.

---

## 2. Required Input Features & Schemas

### A. Weather-Only Predictors (25 Features for 5 cm, 10 cm, 50 cm)
- **Base Weather (8):** `temperature_2m_mean_c`, `temperature_2m_min_c`, `temperature_2m_max_c`, `dewpoint_2m_mean_c`, `vpd_kpa`, `precipitation_total_mm`, `solar_radiation_total_mj_m2`, `wind_speed_10m_ms`
- **Past-Only Memory (10, strictly `shift(1)`):** `precip_lag_1d`, `precip_roll_sum_3d`, `precip_roll_sum_7d`, `precip_roll_sum_14d`, `precip_roll_sum_30d`, `days_since_rain_gt_1mm`, `temp_roll_mean_7d`, `temp_roll_mean_30d`, `vpd_roll_mean_7d`, `solar_roll_mean_7d`
- **Seasonality (2):** `doy_sin`, `doy_cos` (auto-computed from `date_utc` if missing)
- **HWSD Edaphics (5):** `clay_fraction_pct`, `sand_fraction_pct`, `silt_fraction_pct`, `organic_carbon_pct`, `saturation_m3_m3` (auto-filled with station physical defaults if omitted)

### B. Full Multimodal Predictors (58 Features for 20 cm)
- All 25 Weather-Only features above, plus:
- **SoilGrids 250m Hydraulics (8):** `soilgrids_clay_pct`, `soilgrids_sand_pct`, `soilgrids_silt_pct`, `soilgrids_bdod_g_cm3`, `soilgrids_ocd_kg_m3`, `soilgrids_wv0010_m3_m3`, `soilgrids_wv0033_m3_m3`, `soilgrids_wv1500_m3_m3` (auto-filled if omitted)
- **USGS 3DEP DEM Terrain (4):** `dem_elevation_m`, `dem_slope_deg`, `dem_aspect_sin`, `dem_aspect_cos` (auto-filled if omitted)
- **SMAP L3 9km Radiometer (6):** `smap_sm_daily_mean_m3_m3`, `smap_sm_lag_1d`, `smap_sm_roll_mean_3d`, `smap_sm_roll_mean_7d`, `smap_has_valid_retrieval`, `smap_days_since_valid_retrieval`
- **Sentinel-1 SAR C-Band (6):** `s1_vv_db_locf`, `s1_vh_db_locf`, `s1_vv_vh_ratio_db_locf`, `s1_days_since_valid_obs`, `s1_is_stale`, `s1_has_past_obs`
- **Sentinel-2 Optical BOA Reflectance (9):** `s2_ndvi_locf`, `s2_evi_locf`, `s2_b04_red_locf`, `s2_b08_nir_locf`, `s2_b11_swir1_locf`, `s2_b12_swir2_locf`, `s2_days_since_valid_obs`, `s2_is_stale`, `s2_has_past_obs`

---

## 3. How to Run Inference

### A. Python API
```python
from services.inference.predictor import Model1Predictor

predictor = Model1Predictor()

# 1. Single-day prediction
daily_features = {
    "date_utc": "2023-06-15",
    "temperature_2m_mean_c": 24.5,
    "temperature_2m_min_c": 19.2,
    "temperature_2m_max_c": 30.1,
    "dewpoint_2m_mean_c": 18.0,
    "vpd_kpa": 1.12,
    "precipitation_total_mm": 0.0,
    "solar_radiation_total_mj_m2": 24.8,
    "wind_speed_10m_ms": 1.8,
    # (Memory and satellite features, or let defaults apply)
}

response = predictor.predict_single(daily_features)
print(f"5cm Prediction:  {response.predictions['sm_5cm'].volumetric_soil_moisture} m³/m³")
print(f"20cm Prediction: {response.predictions['sm_20cm'].volumetric_soil_moisture} m³/m³")

# 2. Batch DataFrame prediction
import pandas as pd
df = pd.read_csv("data/modelling/processed/AAMU-JTG_all_depths_features_daily.csv")
batch_resp = predictor.predict_dataframe(df.tail(10))
print(f"Batch processed: {batch_resp.batch_size} days")
```

### B. Command-Line Interface (CLI)
```powershell
# 1. Print model catalog and active feature requirements
python services/inference/cli.py --catalog

# 2. Run inference on a 5-day demonstration sample
python services/inference/cli.py --sample

# 3. Run inference on an input CSV and export JSON
python services/inference/cli.py --input path/to/input.csv --output reports/predictions.json

# 4. Run inference for a specific date and export flat CSV
python services/inference/cli.py --input path/to/input.csv --date 2023-06-01 --csv-out predictions.csv
```

### C. FastAPI HTTP REST Service
```powershell
# Start local API server on port 8000
uvicorn services.inference.api:app --host 0.0.0.0 --port 8000
```
Endpoints:
- `GET /health`: Model loading readiness check.
- `GET /catalog`: Feature schemas and benchmark metrics.
- `POST /predict`: Single-day JSON inference.
- `POST /predict/batch`: Multi-day batch inference.
- `GET /docs`: Interactive Swagger UI.

---

## 4. Standardized Prediction JSON Response

```json
{
  "station_id": "AAMU-JTG",
  "date": "2023-06-01",
  "model_version": "1.0.0",
  "inference_timestamp_utc": "2026-10-30T12:52:40.126454+00:00",
  "status": "SUCCESS",
  "disclaimer": "Point-sensor depth estimates (~5 cm, ~10 cm, ~20 cm, ~50 cm) derived via remote sensing and meteorological proxies. These values are point-scale proxy estimates, NOT direct physical measurements or validated vertical layer averages.",
  "units": "m³/m³",
  "predictions": {
    "sm_5cm": {
      "nominal_depth_cm": 5.08,
      "depth_m": 0.0508,
      "volumetric_soil_moisture": 0.22406,
      "units": "m³/m³",
      "model_id": "sm_5cm_sm_5cm_weather_only_xgb",
      "model_file": "sm_5cm_weather_only_xgb.json",
      "model_configuration": "XGBoost Weather-Only",
      "feature_count": 25,
      "sensor_proxy_description": "Point-sensor depth proxy; NOT a direct physical measurement or layer-integrated average."
    },
    "sm_10cm": {
      "nominal_depth_cm": 10.16,
      "depth_m": 0.1016,
      "volumetric_soil_moisture": 0.30182,
      "units": "m³/m³",
      "model_id": "sm_10cm_sm_10cm_weather_only_xgb",
      "model_file": "sm_10cm_weather_only_xgb.json",
      "model_configuration": "XGBoost Weather-Only",
      "feature_count": 25,
      "sensor_proxy_description": "Point-sensor depth proxy; NOT a direct physical measurement or layer-integrated average."
    },
    "sm_20cm": {
      "nominal_depth_cm": 20.32,
      "depth_m": 0.2032,
      "volumetric_soil_moisture": 0.38957,
      "units": "m³/m³",
      "model_id": "sm_20cm_sm_20cm_full_multimodal_xgb",
      "model_file": "sm_20cm_full_multimodal_xgb.json",
      "model_configuration": "XGBoost Full Multimodal",
      "feature_count": 58,
      "sensor_proxy_description": "Point-sensor depth proxy; NOT a direct physical measurement or layer-integrated average."
    },
    "sm_50cm": {
      "nominal_depth_cm": 50.8,
      "depth_m": 0.508,
      "volumetric_soil_moisture": 0.41779,
      "units": "m³/m³",
      "model_id": "sm_50cm_sm_50cm_weather_only_xgb",
      "model_file": "sm_50cm_weather_only_xgb.json",
      "model_configuration": "XGBoost Weather-Only",
      "feature_count": 25,
      "sensor_proxy_description": "Point-sensor depth proxy; NOT a direct physical measurement or layer-integrated average."
    }
  },
  "validation_info": {
    "is_valid": true,
    "missing_features_filled_with_default": [],
    "clamped_predictions": [],
    "warnings": []
  }
}
```

---

## 5. Operational Limitations & Edge Cases

1. **Proxy Semantics:** Predictions are proxies for discrete point sensor tines (at 5.08, 10.16, 20.32, 50.80 cm depth in Decatur silt loam). They must not be misconstrued as integrated soil layer volumetric totals without depth-weighted numerical trapezoidal integration.
2. **Missing Satellite Observations:** SMAP, Sentinel-1, and Sentinel-2 features naturally exhibit revisit gaps. XGBoost handles NaNs natively along learned optimal default branches.
3. **Physical Clamping:** All predictions are constrained to $[0.0, 0.60\text{ m}^3/\text{m}^3]$ (physical limits for mineral soils). Any raw model output outside this range is clamped and flagged in `validation_info.clamped_predictions`.
4. **Spatial Specificity:** Model 1 weights are calibrated on pilot station `AAMU-JTG`. Static soil properties are constant during single-station calibration; spatial transfer to different soil textures requires Model 2 multi-station training.

---

## 6. Reproducing Inference Tests

Run the full pytest suite (88 passing tests):
```powershell
python -c "import pytest, sys; sys.exit(pytest.main(['-s', 'tests']))"
```
Or execute the inference test module specifically:
```powershell
python -c "import pytest, sys; sys.exit(pytest.main(['-s', 'tests/test_model1_inference.py']))"
```

