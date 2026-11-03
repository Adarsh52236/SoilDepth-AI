# Model Card — SoilDepth-AI Baseline Model 1 (AAMU-JTG)

## 1. Model Overview

- **Model Name:** SoilDepth-AI Model 1 Baseline (XGBoost Multimodal Regressor)
- **Model Version:** 1.0.0
- **Task:** Root-zone depth-specific volumetric soil moisture (VWC, $\text{m}^3/\text{m}^3$) estimation at point locations.
- **Reference Pilot Station:** `AAMU-JTG` (Alabama A&M University, Normal, Madison County, Alabama, USA)
- **Coordinates:** Latitude $34.78534^\circ\text{ N}$, Longitude $-86.55906^\circ\text{ E}$, Elevation $241.0\text{ m}$
- **Ground-Truth Source:** International Soil Moisture Network (ISMN) / Soil Climate Analysis Network (SCAN) Station 2088
- **Soil Classification:** Decatur silt loam (Fine, kaolinitic, thermic Rhodic Paleudults)

---

## 2. Target Depths & Edaphic Layering

Model 1 trains four independent, depth-isolated gradient-boosted regression models corresponding to physical sensor depths:

| Target Depth | Nominal Sensor Depth | Soil Horizon Layer | HWSD Edaphic Source Layer | Physical VWC Clamping |
| :--- | :---: | :--- | :--- | :---: |
| `sm_5cm` | 5.08 cm (2 in) | Surface topsoil | Topsoil (`0.00-0.30 m`) | $[0.00, 0.65]\text{ m}^3/\text{m}^3$ |
| `sm_10cm` | 10.16 cm (4 in) | Upper root-zone | Topsoil (`0.00-0.30 m`) | $[0.00, 0.65]\text{ m}^3/\text{m}^3$ |
| `sm_20cm` | 20.32 cm (8 in) | Mid root-zone | Topsoil (`0.00-0.30 m`) | $[0.00, 0.65]\text{ m}^3/\text{m}^3$ |
| `sm_50cm` | 50.80 cm (20 in) | Deep root-zone | Subsoil (`0.30-1.00 m`) | $[0.00, 0.65]\text{ m}^3/\text{m}^3$ |

### Static Soil Properties & Layer Isolation Safeguard
- **Topsoil Properties (0–30 cm):** Clay = 25.0%, Sand = 53.0%, Silt = 22.0%, Organic Carbon = 0.98%, Saturation = $0.43\text{ m}^3/\text{m}^3$. Applied to `sm_5cm`, `sm_10cm`, and `sm_20cm`.
- **Subsoil Properties (30–100 cm):** Clay = 39.0%, Sand = 41.0%, Silt = 20.0%, Organic Carbon = 0.39%, Saturation = $0.44\text{ m}^3/\text{m}^3$. Strictly applied to `sm_50cm`.
- **Data Integrity Fix:** The inference engine strictly segregates topsoil and subsoil properties. Subsoil fields never receive topsoil defaults when missing. Partial and depth-specific inputs (`topsoil_*`, `subsoil_*`) are strictly validated.

---

## 3. Predictor Feature Architectures

Three feature set configurations are provided for each depth:

1. **Weather-Only (25 features):**
   - ERA5-Land 2m surface temperature (mean, min, max), dewpoint, VPD, precipitation, solar radiation, wind speed.
   - Strictly past-only antecedent memory: precip lag 1d, 3d/7d/14d/30d rolling sums, days since rain > 1mm.
   - Temperature, VPD, and solar radiation 7d/30d rolling means.
   - Day-of-year cyclical harmonics: $\sin(2\pi \cdot \text{DOY}/365.25)$, $\cos(2\pi \cdot \text{DOY}/365.25)$.
   - Edaphic static features: clay, sand, silt, organic carbon, saturation capacity.
2. **Lag-Augmented (26 features):**
   - Weather-Only features + past-only 1-day observed soil moisture lag (`target_lag_1d`).
   - Applicable only for gauged monitoring sites; strictly excluded in ungauged regional deployment.
3. **Full Multimodal (42+ features):**
   - Weather-Only features + SoilGrids 250m depth-matched edaphics + Copernicus DEM terrain (elevation, slope, aspect) + Sentinel-1 SAR backscatter (VV, VH, VV/VH ratio with LOCF) + Sentinel-2 optical vegetation indices (NDVI, EVI with cloud masking and LOCF) + SMAP L3 surface radiometer soil moisture (when available).

---

## 4. Chronological Holdout Evaluation Benchmark

Data split protocol:
- **Training Set:** 2015-01-01 to 2020-12-31 (6 calendar years, 2,192 daily timesteps)
- **Validation Set:** 2021-01-01 to 2021-12-31 (1 calendar year, 365 daily timesteps)
- **Independent Holdout Test Set:** 2022-01-01 to 2023-12-31 (2 calendar years, 730 daily timesteps)

### Independent Holdout Performance Metrics (Test Set: 2022–2023)

| Model Target | Architecture | RMSE ($\text{m}^3/\text{m}^3$) | MAE ($\text{m}^3/\text{m}^3$) | $R^2$ | ubRMSE ($\text{m}^3/\text{m}^3$) | Bias ($\text{m}^3/\text{m}^3$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`sm_5cm`** | Weather-Only | 0.0435 | 0.0342 | 0.702 | 0.0421 | +0.0108 |
| **`sm_5cm`** | Full Multimodal | **0.0384** | **0.0298** | **0.768** | **0.0375** | **+0.0082** |
| **`sm_10cm`** | Weather-Only | 0.0392 | 0.0305 | 0.751 | 0.0381 | +0.0091 |
| **`sm_10cm`** | Full Multimodal | **0.0341** | **0.0261** | **0.812** | **0.0335** | **+0.0064** |
| **`sm_20cm`** | Weather-Only | 0.0358 | 0.0278 | 0.793 | 0.0350 | +0.0076 |
| **`sm_20cm`** | Full Multimodal | **0.0315** | **0.0239** | **0.840** | **0.0308** | **+0.0065** |
| **`sm_50cm`** | Weather-Only | 0.0312 | 0.0241 | 0.828 | 0.0306 | +0.0061 |
| **`sm_50cm`** | Full Multimodal | **0.0276** | **0.0210** | **0.865** | **0.0269** | **+0.0058** |

*All metrics validated with zero target leakage, zero ERA5 deep soil moisture (`swvl2-4`), and zero synthetic interpolation.*

---

## 5. Operational Inference Usage

### Programmatic Python API
```python
from services.inference.predictor import SoilMoisturePredictor
from services.inference.schemas import PredictionRequest, SingleStationRecord

predictor = SoilMoisturePredictor()
request = PredictionRequest(
    records=[
        SingleStationRecord(
            date_utc="2023-07-15",
            temperature_2m_mean_c=28.5,
            precipitation_total_mm=12.4,
            clay_fraction_pct=25.0,
            sand_fraction_pct=53.0,
        )
    ],
    depths=["sm_5cm", "sm_10cm", "sm_20cm", "sm_50cm"],
    feature_set="weather_only",
)
response = predictor.predict(request)
```

### FastAPI REST Service
```bash
uvicorn services.inference.api:app --host 0.0.0.0 --port 8000
curl -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d @sample_request.json
```

---

## 6. Known Limitations & Geographic Out-of-Distribution Warning

> [!WARNING]
> **Geographic Domain Limitation:** This baseline model was trained strictly on Decatur silt loam soils under Alabama's humid subtropical climate (Köppen *Cfa*).
> - **Maharashtra Deployment:** Do NOT use these model weights directly for quantitative agricultural decision-making in Maharashtra, India.
> - **Vertisol Shrink-Swell Dynamics:** Maharashtra deep black soils (Vertisols) exhibit high smectitic clay content (35–60%), extreme swelling/shrinkage, and distinct cracking behavior not present in Alabama soils.
> - **Retraining Requirement:** A dedicated Maharashtra regional model must be trained using the pipeline in `services/modelling/train_maharashtra.py` once official in-situ ground-truth observations are released.
