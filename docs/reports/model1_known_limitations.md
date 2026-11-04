# SoilDepth-AI — Model 1 Known Scientific & Operational Limitations

**Author:** Chief Scientist & Hydrological Modeling Lead, SoilDepth-AI  
**Document Version:** 1.0.0  
**Status:** FORMAL SCIENTIFIC TRANSPARENCY DISCLOSURE  

---

## 1. Purpose & Guiding Ethos

A foundational tenet of SoilDepth-AI is uncompromising scientific honesty. This document details the verified physical, spatial, temporal, and algorithmic limitations of Model 1.

Every AI model is an approximation of complex multi-scale hydrological systems. Recognizing where the model excels and where its boundaries lie is essential for safe agricultural decision support.

---

## 2. Scientific & Operational Limitations

### 2.1 Geographic Transferability & Regional Boundaries
- **Benchmark Limitation:** Model 1 weights are calibrated exclusively on historical observations from SCAN station AAMU-JTG in Alabama, USA (humid subtropical climate, silt loam soil under mixed forest/grassland).
- **Prohibition:** These model weights **must not be deployed as operational decision-makers in Maharashtra, India** without recalibration. Maharashtra soils are dominated by smectitic cracking Vertisols (black cotton soils) experiencing severe semi-arid and monsoonal climatic extremes.
- **Enforcement:** The inference engine enforces regional routing (`region="maharashtra"` returns `MODEL_NOT_AVAILABLE`).

### 2.2 Point-Sensor Proxies vs. Layer-Average Measurements
- **Discretization Limitation:** In-situ SCAN sensors (and candidate Maharashtra probes) measure permittivity at specific point depths (~5 cm, ~10 cm, ~20 cm, ~50 cm).
- **Caveat:** Predictions represent point-sensor depth proxies. They must not be equated to layer-integrated volumetric averages or depth-integrated neutron counts (CRNS) without documented calibration curves.

### 2.3 Remote Sensing Temporal Gaps & Monsoonal Cloud Obscuration
- **Optical Limitations:** Sentinel-2 MSI provides high-resolution (10–20m) vegetation indices (NDVI, EVI, SWIR), but observations are severely obscured by dense cloud cover during the peak Maharashtra monsoon (July–August).
- **LOCF Staleness:** SoilDepth-AI strictly forbids lookahead interpolation, utilizing forward-only Last Observation Carried Forward (LOCF). During persistent overcast spells, optical features may remain static for 15–40 days, causing the model to lean more heavily on real-time weather features.
- **SAR Revisit:** Sentinel-1 C-SAR has a nominal 12-day orbital repeat cycle over central India, creating 6-to-12 day gaps between radar backscatter updates.

### 2.4 Multi-Scale Spatial Resolution Disparities
- **Input Scales:**
  - ERA5-Land: $\sim 9 \text{ km}$ grid spacing.
  - SMAP L3 Enhanced: $\sim 9 \text{ km}$ grid spacing.
  - SoilGrids v2.0: $250 \text{ m}$ pixel resolution.
  - Copernicus DEM: $30 \text{ m}$ pixel resolution.
  - Agricultural Fields: $0.1 \text{ to } 2.0 \text{ hectares}$ typical plot size in Maharashtra.
- **Sub-Pixel Heterogeneity:** Macro-meteorological forcing (rainfall, solar radiation, temperature) from 9 km reanalysis does not capture micro-scale convective showers, localized furrow irrigation, or sub-kilometer drainage variations.

### 2.5 Vertisol Pedo-Hydrological Complexity
- **Shrink-Swell Cracking:** Smectite clay minerals in Maharashtra Vertisols expand upon wetting and contract upon drying, creating macro-cracks up to 5–10 cm wide and 1 m deep.
- **Preferential Flow:** Rapid bypass flow occurs through surface cracks during initial monsoon rains before soil swelling closes the fissures. Standard 1D infiltration equations and empirical ML regressors do not explicitly simulate 3D preferential macropore flow.

### 2.6 In-Situ Ground-Truth Institutional Dependencies
- **Status:** Field validation across Maharashtra is currently pending institutional data transfer from IITM, ICAR-NIASM, MPKV Rahuri, IMD NDC, and PoCRA PMU.
- **Integrity Rule:** Until genuine institutional data is delivered, the Maharashtra models will not be fitted or validated on synthetic substitutes.

---

## 3. Operational Risk Mitigation Recommendations

1. **Combine Model Predictions with Local Field Checks:** Farm managers should pair Model 1 root-zone advisories with physical soil feel-and-appearance inspections or local tensiometers.
2. **Apply Drainage Buffers in Vertisols:** In heavy clay soils, avoid irrigating immediately before forecast rain events to prevent root asphyxiation and damping-off diseases.
3. **Update Regional Weights Promptly:** As institutional datasets are acquired through the Phase 3 campaign, retrain and validate depth regressors according to the `maharashtra_validation_protocol.md`.
