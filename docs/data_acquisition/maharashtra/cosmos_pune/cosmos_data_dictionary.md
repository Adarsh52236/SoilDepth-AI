# COSMOS-India Pune Station Data Dictionary & Schema Specification

**Project:** SoilDepth-AI (Maharashtra Phase 2A)  
**Station:** `IITM-PUNE-COSMOS` (Indian Institute of Tropical Meteorology, Pune)  
**Document Type:** Technical Data Dictionary & Variable Schema  
**Date:** 2026-10-31  
**Status:** Approved Reference Standard  

---

## 1. Primary Variable Schema

The data schema for the IITM-Pune COSMOS-India station integrates three distinct observational layers:
1. **Cosmic-Ray Area-Integrated Soil Moisture (CRNS)**
2. **Point-Scale Multi-Depth In-Situ Dielectric Probes (Stevens Hydra Probe II)**
3. **Ancillary Atmospheric & Soil Temperatures**

| Variable Name | Data Type | Physical Units | Sensor / Hardware | Measurement Scale | Valid Physical Range | Missing Value Representation | Description / Physical Semantics |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| `date_utc` | String | `YYYY-MM-DD` | Master System Clock | Point | Calendar date | `None` | Coordinated Universal Time (UTC) observation date. |
| `time_utc` | String | `HH:MM:SS` | Master System Clock | Point | `00:00:00`–`23:00:00`| `None` | Coordinated Universal Time (UTC) timestamp. |
| `timestamp_ist` | String | ISO 8601 | Calculated ($\text{UTC}+05{:}30$) | Point | Datetime string | `None` | Indian Standard Time localized timestamp. |
| `neutron_count_raw` | Integer | $\text{cph}$ (counts/hr)| Hydroinnova CRS-2000/B | $\sim 200\text{ m}$ radius | $500\text{--}3,500$ | `-9999` / `NaN` | Raw unmoderated and moderated epithermal neutron counts. |
| `neutron_count_corr`| Float | $\text{cph}$ (counts/hr)| Corrected CRNS | $\sim 200\text{ m}$ radius | $500\text{--}3,500$ | `-9999` / `NaN` | Neutron count rate corrected for pressure, vapor, and solar flux. |
| `vwc_crns` | Float | $\text{m}^3/\text{m}^3$ | CRNS moderated flux | $\sim 200\text{ m}$ radius ($z^* \sim 12\text{--}30\text{ cm}$)| $0.02\text{--}0.50$ | `-9999` / `NaN` | Area-integrated volumetric water content across CRNS footprint. |
| `crns_sensing_depth_m`| Float | $\text{m}$ | Calculated ($z^*$) | $\sim 200\text{ m}$ radius | $0.10\text{--}0.35$ | `-9999` / `NaN` | Effective depth of penetration ($z^*$) based on moisture state. |
| `sm_point_5cm` | Float | $\text{m}^3/\text{m}^3$ | Stevens Hydra Probe II | Point ($\sim 50\text{ cm}^3$) at $0.05\text{ m}$ | $0.02\text{--}0.45$ | `-9999` / `NaN` | Point-scale volumetric soil moisture at $5\text{ cm}$ depth. |
| `sm_point_15cm` | Float | $\text{m}^3/\text{m}^3$ | Stevens Hydra Probe II | Point ($\sim 50\text{ cm}^3$) at $0.15\text{ m}$ | $0.02\text{--}0.45$ | `-9999` / `NaN` | Point-scale volumetric soil moisture at $15\text{ cm}$ depth. |
| `sm_point_50cm` | Float | $\text{m}^3/\text{m}^3$ | Stevens Hydra Probe II | Point ($\sim 50\text{ cm}^3$) at $0.50\text{ m}$ | $0.05\text{--}0.45$ | `-9999` / `NaN` | Point-scale volumetric soil moisture at $50\text{ cm}$ depth. |
| `soil_temp_5cm` | Float | $^\circ\text{C}$ | Thermistor (Hydra Probe) | Point at $0.05\text{ m}$ | $10.0\text{--}50.0$ | `-9999` / `NaN` | Subsurface soil temperature at $5\text{ cm}$ depth. |
| `soil_temp_15cm` | Float | $^\circ\text{C}$ | Thermistor (Hydra Probe) | Point at $0.15\text{ m}$ | $12.0\text{--}45.0$ | `-9999` / `NaN` | Subsurface soil temperature at $15\text{ cm}$ depth. |
| `soil_temp_50cm` | Float | $^\circ\text{C}$ | Thermistor (Hydra Probe) | Point at $0.50\text{ m}$ | $15.0\text{--}38.0$ | `-9999` / `NaN` | Subsurface soil temperature at $50\text{ cm}$ depth. |
| `precip_total_mm` | Float | $\text{mm}$ | Tipping Bucket Rain Gauge| Point | $0.0\text{--}150.0$ | `-9999` / `NaN` | Total hourly precipitation. |
| `air_temp_c` | Float | $^\circ\text{C}$ | Vaisala WXT520 | Point ($2\text{ m}$ height) | $5.0\text{--}45.0$ | `-9999` / `NaN` | Ambient air temperature at $2\text{ m}$. |
| `rel_humidity_pct` | Float | $\%$ | Vaisala WXT520 | Point ($2\text{ m}$ height) | $10.0\text{--}100.0$ | `-9999` / `NaN` | Relative humidity of air. |
| `barom_press_hpa` | Float | $\text{hPa}$ | Vaisala WXT520 | Point | $920.0\text{--}980.0$ | `-9999` / `NaN` | Atmospheric surface barometric pressure. |
| `battery_volts` | Float | $\text{V}$ | System Datalogger | System | $11.0\text{--}14.5$ | `-9999` / `NaN` | Datalogger supply voltage (warning flag if $<11.8\text{ V}$). |
| `qc_flag_crns` | Integer | Categorical | Automated QC Algorithm | Footprint | `0`, `1`, `2` | `2` | Quality flag for CRNS soil moisture retrieval. |
| `qc_flag_profile` | Integer | Categorical | Automated QC Algorithm | Profile | `0`, `1`, `2` | `2` | Quality flag for Stevens Hydra Probe profile array. |

---

## 2. Fundamental Physics: Point Probes vs. Cosmic-Ray Neutron Sensing

A rigorous architectural distinction is required between the two sensing technologies co-located at the Pune station:

```
[Stevens Hydra Probes (Point Scales)]               [Cosmic-Ray Sensor (Field Scale)]
   - Depth 1: 5 cm                                     - Integrates 0 to z* (~12 to 30 cm)
   - Depth 2: 15 cm                                    - Horizontal Radius: ~150 to 200 m
   - Depth 3: 50 cm                                    - Footprint Area: ~70,000 to 125,000 m²
   - Sensing Volume: ~50 cm³                           - Measures: Epithermal Neutron Flux
   - Measures: High-frequency Dielectric Impedance     - Sensitive to: All Environmental Hydrogen
```

### 2.1 Stevens Hydra Probe II (Point-Scale Soil Moisture)
* **Measurement Principle:** High-frequency ($50\text{ MHz}$) coaxial impedance dielectric reflectometry. The probe measures the complex dielectric permittivity ($\kappa = \epsilon_r + i\epsilon_i$), from which volumetric water content is calculated using calibrations for mineral soils.
* **Sensing Geometry:** Tines enclose a cylindrical volume of approximately $50\text{ cm}^3$ ($3\text{ cm}$ diameter $\times 5\text{ cm}$ length).
* **Role in SoilDepth-AI:** Genuinely represents a **discrete point-sensor tine** analogous to the USDA SCAN Hydra Probes deployed at AAMU-JTG, Alabama.

### 2.2 Cosmic-Ray Neutron Sensor (Field-Scale Intermediate Soil Moisture)
* **Measurement Principle:** Cosmic-ray primary particles collide with nuclei in the upper atmosphere, generating a cascade of secondary fast neutrons. These fast neutrons penetrate the soil where they are moderated (slowed down to epithermal energy levels) predominantly by hydrogen atoms ($^1\text{H}$), whose mass closely matches a neutron.
* **Inverse Relationship:** A higher concentration of environmental water (soil moisture, plant biomass, atmospheric vapor) moderates more neutrons, resulting in **lower epithermal neutron counts** detected above ground.
* **Desilets Calibration Formulation:**
  $$\theta(N) = \frac{a_0}{\frac{N}{N_0} - a_1} - a_2 - \theta_{\text{lw}} - \theta_{\text{soc}}$$
  Where:
  - $N$ is the corrected neutron count rate ($\text{cph}$).
  - $N_0$ is the site-specific calibration constant (neutron count over dry soil, determined for Pune $\approx 2,150\text{ cph}$).
  - $a_0 = 0.0808$, $a_1 = 0.372$, $a_2 = 0.115$ are universal physics constants.
  - $\theta_{\text{lw}}$ is lattice water fraction (bound water in basaltic clay minerals).
  - $\theta_{\text{soc}}$ is soil organic carbon equivalent water.
* **Effective Measurement Depth ($z^*$):**
  $$z^* \approx \frac{5.8}{\rho_{bd} \cdot \theta + 0.0829}$$
  The vertical measurement depth is **not constant**: during the dry pre-monsoon (April–May, $\theta \approx 0.05\text{ m}^3/\text{m}^3$), neutrons sample down to **$\sim 30\text{ cm}$**; during peak monsoon saturation (July–August, $\theta \approx 0.35\text{ m}^3/\text{m}^3$), the effective penetration depth collapses to **$\sim 12\text{ cm}$**.

---

## 3. Strict Target Alignment Rules

To prevent algorithmic distortion and physical corruption during model evaluation:

> [!WARNING]
> **No Variable Conflation:**
> 1. `vwc_crns` **must NEVER be substituted** for a discrete point-depth target (`sm_5cm`, `sm_10cm`, `sm_20cm`, or `sm_50cm`).
> 2. `sm_point_15cm` **must NEVER be relabeled or mapped** to `sm_10cm` or `sm_20cm`. In Decatur silt loam and Deccan sandy clay loams, vertical hydraulic gradients are steepest between 5 cm and 20 cm; interpolating 15 cm into 10 cm or 20 cm introduces significant bias.
> 3. Only `sm_point_5cm` directly aligns with SoilDepth-AI's surface target ($5.08\text{ cm}$).
> 4. Only `sm_point_50cm` directly aligns with SoilDepth-AI's deep target ($50.80\text{ cm}$).

