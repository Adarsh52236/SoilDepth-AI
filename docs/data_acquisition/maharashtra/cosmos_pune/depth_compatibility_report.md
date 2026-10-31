# Depth Compatibility & Sensor Footprint Harmonization Report

**Project:** SoilDepth-AI (Maharashtra Phase 2A)  
**Station:** `IITM-PUNE-COSMOS` (Indian Institute of Tropical Meteorology, Pune)  
**Document Type:** Target Depth Alignment & Physical Sensor Harmonization  
**Date:** 2026-10-31  
**Status:** Complete Depth Compatibility Assessment  

---

## 1. SoilDepth-AI Target Architecture vs. COSMOS Available Sensors

In SoilDepth-AI Model 1 (developed and validated at AAMU-JTG, Alabama), four discrete physical point-depth targets were established based on standard agricultural impedance probe tines:

1. **`sm_5cm`:** $5.08\text{ cm}$ ($0.0508\text{ m}$ / $2\text{ inches}$) — Direct surface soil layer (evaporation & satellite penetration).
2. **`sm_10cm`:** $10.16\text{ cm}$ ($0.1016\text{ m}$ / $4\text{ inches}$) — Upper root zone (shallow seedbed & infiltration front).
3. **`sm_20cm`:** $20.32\text{ cm}$ ($0.2032\text{ m}$ / $8\text{ inches}$) — Mid root zone (primary pulse & cereal root uptake).
4. **`sm_50cm`:** $50.80\text{ cm}$ ($0.5080\text{ m}$ / $20\text{ inches}$) — Deep root zone (hydraulic buffer & subsoil storage).

### Depth Alignment Comparison Matrix:

| Target Depth Key | Metric Target Depth | Available In-Situ Sensor at IITM Pune | In-Situ Measurement Depth | Physical Depth Discrepancy ($\Delta z$) | Training Feasibility | Independent Validation Feasibility | Verdict |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **`sm_5cm`** | $5.08\text{ cm}$ ($0.0508\text{ m}$) | Stevens Hydra Probe II | $5.00\text{ cm}$ ($0.0500\text{ m}$) | $+0.08\text{ cm}$ ($0.8\text{ mm}$) | **FEASIBLE** | **VALID** | **COMPATIBLE (DIRECT MATCH)** |
| **`sm_10cm`** | $10.16\text{ cm}$ ($0.1016\text{ m}$) | *None* (Sensors at 5 cm & 15 cm) | — | N/A | **INFEASIBLE** | **INVALID** | **MISSING SENSOR TARGET** |
| **`sm_20cm`** | $20.32\text{ cm}$ ($0.2032\text{ m}$) | *None* (Sensors at 15 cm & 50 cm) | — | N/A | **INFEASIBLE** | **INVALID** | **MISSING SENSOR TARGET** |
| **`sm_50cm`** | $50.80\text{ cm}$ ($0.5080\text{ m}$) | Stevens Hydra Probe II | $50.00\text{ cm}$ ($0.5000\text{ m}$) | $+0.80\text{ cm}$ ($8.0\text{ mm}$) | **FEASIBLE** | **VALID** | **COMPATIBLE (DIRECT MATCH)** |
| *Macro Layer* | $0\text{--}30\text{ cm}$ integrated | Cosmic-Ray Sensor (CRNS) | $z^*(t) \in [12, 30]\text{ cm}$ | Variable ($\sim 200\text{ m}$ footprint) | **INFEASIBLE (Point)** | **VALID (Satellite / Macro)** | **MACRO BENCHMARK ONLY** |

---

## 2. Inadmissible Conversions & Physical Non-Equivalence

In strict adherence to project rules, two specific data conflations are explicitly barred from execution:

### 2.1 The "15 cm" Target Fallacy (Why 15 cm Cannot Map to 10 cm or 20 cm)
* **The Temptation:** Approximating the missing $10\text{ cm}$ or $20\text{ cm}$ targets using the installed $15\text{ cm}$ Stevens Hydra Probe.
* **Why This is Scientifically Inadmissible:**
  - In tropical monsoon climates under bare soil or sparse canopies, the vertical soil moisture gradient $\frac{\partial \theta}{\partial z}$ is **steeply non-linear** across the top $25\text{ cm}$ (governed by the Richards equation for 1-D vertical unsaturated flow):
    $$\frac{\partial \theta}{\partial t} = \frac{\partial}{\partial z}\left[K(\theta)\left(\frac{\partial \psi}{\partial z} + 1\right)\right] - S(z, t)$$
  - During drying phases (e.g., a 7-day monsoon break), atmospheric evaporative demand desiccates the surface. Observations at $5\text{ cm}$ drop to $0.10\text{ m}^3/\text{m}^3$, while $10\text{ cm}$ remains at $0.18\text{ m}^3/\text{m}^3$, $15\text{ cm}$ at $0.26\text{ m}^3/\text{m}^3$, and $20\text{ cm}$ at $0.32\text{ m}^3/\text{m}^3$.
  - Treating $15\text{ cm}$ as $10\text{ cm}$ introduces an artificial wet bias ($+0.08\text{ m}^3/\text{m}^3$); treating $15\text{ cm}$ as $20\text{ cm}$ introduces an artificial dry bias ($-0.06\text{ m}^3/\text{m}^3$).
  - Neither linear interpolation nor direct relabeling is permissible. Targets `sm_10cm` and `sm_20cm` **must remain un-evaluated at IITM-Pune**.

### 2.2 The "CRNS to Point Depth" Fallacy (Spatial & Vertical Conflation)
* **The Temptation:** Converting the area-integrated cosmic-ray neutron sensor (`vwc_crns`) into an individual point-depth target (e.g., calling it "surface" or "20 cm" moisture).
* **Why This is Scientifically Inadmissible:**
  1. **Spatial Footprint Scale Mismatch:** The Stevens Hydra Probe measures dielectric properties in a tiny localized cylinder of $\sim 50\text{ cm}^3$ ($0.00005\text{ m}^3$). The Cosmic-Ray Sensor measures fast neutron moderation over a circular footprint of radius $R \approx 150\text{--}200\text{ m}$, integrating an area of **$\sim 70,000\text{ to }125,000\text{ m}^2$** and a soil volume of **$>20,000\text{ m}^3$**. Local soil heterogeneity, grass tussocks, and tree root networks are spatially smoothed by the CRNS.
  2. **Dynamic Penetration Depth $z^*(t)$:** The vertical measurement depth of a point probe is physically fixed ($z = 5.08\text{ cm}$ or $50.80\text{ cm}$). In contrast, the effective measurement depth of a CRNS is an inverse function of hydrogen density:
     $$z^*(t) \approx \frac{5.8}{\rho_{bd} \cdot \theta(t) + 0.0829}$$
     When Pune's soil is wet after a $50\text{ mm}$ storm ($\theta = 0.38\text{ m}^3/\text{m}^3$), $z^* \approx 12.5\text{ cm}$. When the soil dries in March ($\theta = 0.06\text{ m}^3/\text{m}^3$), $z^* \approx 32.8\text{ cm}$. A measurement whose effective sampling depth shifts by $>20\text{ cm}$ between seasons cannot represent a fixed-depth point target.
  3. **Vegetation and Above-Ground Hydrogen:** The CRNS detector responds to all hydrogen atoms within its footprint, including grass biomass, tree foliage, and dew, requiring separate vegetation corrections.

---

## 3. Approved Role of COSMOS Data in SoilDepth-AI

Based on the physical sensor characteristics, the permissible roles for IITM-Pune data are strictly delineated:

### Approved Applications:
1. **Direct Validation of Surface Point Target (`sm_5cm`):**
   - The $5\text{ cm}$ Stevens Hydra Probe can be used to validate SoilDepth-AI’s Model 1 surface prediction (`sm_5cm_weather_only_xgb.json`) or train regional Model 2 surface models.
2. **Direct Validation of Deep Subsoil Target (`sm_50cm`):**
   - The $50\text{ cm}$ Stevens Hydra Probe can be used to validate SoilDepth-AI’s Model 1 deep prediction (`sm_50cm_weather_only_xgb.json`) or train regional Model 2 deep models.
3. **Spaceborne Macro Benchmark (`vwc_crns`):**
   - The $0\text{--}30\text{ cm}$ area-integrated CRNS measurement is ideally scaled ($\sim 200\text{ m}$) to validate satellite soil moisture products (NASA SMAP L3 $9\text{ km}$, ISRO EOS-04 $500\text{ m}$, and Sentinel-1 SAR aggregations) and regional hydrological water balance models.

### Prohibited Applications:
1. **NO Training or Validation of `sm_10cm`:** The station possesses no sensor at $10\text{ cm}$.
2. **NO Training or Validation of `sm_20cm`:** The station possesses no sensor at $20\text{ cm}$.
3. **NO Point-Depth Substitution with CRNS:** `vwc_crns` cannot be used as target $y$ in gradient boosting point-depth regressions.

