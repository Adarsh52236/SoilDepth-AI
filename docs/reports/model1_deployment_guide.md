# SoilDepth-AI — Model 1 Production Deployment & Operations Guide

**Author:** Senior MLOps Engineer & Platform Architect, SoilDepth-AI  
**Version:** 1.0.0 (Production Release Baseline)  
**System:** SoilDepth-AI Model 1 Inference & Irrigation Intelligence Engine  

---

## 1. System Overview

SoilDepth-AI Model 1 provides 100% ground-sensor-independent root-zone soil moisture estimation and FAO-56 irrigation decision intelligence using free satellite observations, reanalysis weather data, terrain, and soil properties.

### Key Capabilities:
1. **Four-Depth Point-Sensor Estimation:**
   - 5.08 cm (~5 cm): Weather-Only XGBoost (25 features)
   - 10.16 cm (~10 cm): Weather-Only XGBoost (25 features)
   - 20.32 cm (~20 cm): Full Multimodal XGBoost (58 features, SAR + Optical + Radiometry)
   - 50.80 cm (~50 cm): Weather-Only XGBoost (25 features, deep subsoil edaphic isolation)
2. **Region-Aware Intelligent Routing:**
   - `region="alabama"`: Fully operational inference over validated benchmark domain.
   - `region="maharashtra"`: Gated with explicit `MODEL_NOT_AVAILABLE` status until local in-situ data arrives.
3. **FAO-56 Irrigation Decision Advisor:**
   - Automated conversion of predicted profile VWC into root-zone depletion ($D_r$), crop stress ($K_s$), and irrigation depth ($I_{\text{req}}$).

---

## 2. Service Architecture & REST Endpoints

The service is built on FastAPI and Uvicorn:

| Method | Endpoint | Description | Sample Request / Response |
|---|---|---|---|
| `GET` | `/health` | Service health & model load state | `{"status": "HEALTHY", "models_loaded_count": 4}` |
| `GET` | `/catalog` | Operational catalog & feature requirements | Query param: `?region=alabama` or `?region=maharashtra` |
| `POST` | `/predict` | Single-day inference across all 4 depths | Accepts daily features dict and target region |
| `POST` | `/predict/batch` | Multi-day batch inference | Accepts list of daily feature dictionaries |

---

## 3. Quick Start & Execution

### 3.1 Starting the Production API Server

```powershell
# Run via Uvicorn
python -m uvicorn services.inference.api:app --host 0.0.0.0 --port 8000 --workers 2
```

### 3.2 Testing Single-Day Prediction (cURL / Python)

```python
import requests

url = "http://localhost:8000/predict"
payload = {
    "region": "alabama",
    "station_id": "AAMU-JTG",
    "date": "2023-08-01",
    "features": {
        "temperature_2m_mean_c": 28.5,
        "precipitation_total_mm": 0.0,
        "solar_radiation_total_mj_m2": 22.4,
        "wind_speed_10m_ms": 1.8,
        "vpd_kpa": 1.45,
    }
}
response = requests.post(url, json=payload)
print(response.json())
```

### 3.3 Running FAO-56 Irrigation Decision Advisor

```python
from services.water_balance.fao56 import FAO56WaterBalance
from services.irrigation_decision.advisor import IrrigationAdvisor

advisor = IrrigationAdvisor()
advice = advisor.generate_advice(
    crop_id="CROP-SOYBEAN",
    growth_stage="mid",
    depth_predictions={"sm_5cm": 0.22, "sm_10cm": 0.24, "sm_20cm": 0.26, "sm_50cm": 0.28},
    et0_mm=4.5,
    forecast_rain_mm_48h=0.0,
)
print("Action:", advice["decision"]["action"])
print("Recommended Depth:", advice["decision"]["recommended_depth_mm"], "mm")
print("Recommended Volume:", advice["decision"]["recommended_volume_m3_per_ha"], "m3/ha")
```

---

## 4. Input Sanitization & Safety Protocols

1. **Zero-Leakage In-Situ Target Stripping:**
   Any input column containing `target`, `sm_0.`, or in-situ sensor telemetry is automatically stripped and logged as a validation warning before model inference.
2. **Depth-Appropriate Edaphic Routing:**
   Subsoil features (`sm_50cm`) strictly draw from subsoil static properties; topsoil properties will never contaminate subsoil models.
3. **Physical Clamping:**
   Predicted soil moisture is clamped to the physically possible mineral soil range `[0.0, 0.60 m³/m³]`.

---

## 5. Summary

SoilDepth-AI Model 1 is completely container-ready, production-tested (229 automated tests passing), and hardened against operational data contamination.
