# SoilDepth-AI — ISMN In Situ Data Audit & Model-Readiness Report

**Audit Date:** 2026-10-25  
**Audit Scope:** Full structural, physical, and temporal audit of all files in `ISMN/ISMN_surface_0-10`, `ISMN/ISMN_middle_10-30`, and `ISMN/ISMN_deep_30-60`.  
**Execution Mode:** Audit-Only (Original files, directories, and Git working state preserved 100% untouched).

---

## Executive Summary & Core Findings

1. **Actual Data Downloaded:**
   - Across the three directories, a total of **28 files** were inventoried, containing **4 data time-series files** in ISMN native Header+values (`.stm`) format alongside 24 accompanying metadata, schema, and documentation files.
   - **Crucial Redundancy Discovery:** Only **3 unique sensor time series** exist. The 10 cm sensor file (`sm_0.100000_0.100000`) is **100% byte-for-byte identical** between `ISMN_surface_0-10` and `ISMN_middle_10-30` (SHA-256: `91448b111db096414cefa05252b4eaee06024467ecbc7664687071dbff5aa1eb`, size: 304,200 bytes).
2. **Network, Station & Geographic Coverage:**
   - **Contributing Networks:** Exactly **1 network** (`IIT_KANPUR`).
   - **Contributing Stations:** Exactly **1 station** (`IITK_Airstrip` / `IITK-Airstrip`).
   - **Geographic Coordinates:** Latitude **26.51881°N**, Longitude **80.23303°E**, Elevation **123.44 m** (Kanpur, Uttar Pradesh, Indo-Gangetic Plain, North-Central India).
   - **Maharashtra Coverage:** **0 stations, 0 files, 0 rows.** No data exist for the primary study region of Maharashtra.
3. **Observation Volume & Deduplication:**
   - **Total Raw Observation Rows:** **44,017 rows** across the 3 folders.
   - **Unique Physical Observations:** **32,737 unique hourly observations**.
   - **Cross-Folder Duplicated Rows:** Exactly **11,280 redundant rows** (the duplicated 10 cm sensor).
4. **Sensor Depths & Target Alignment:**
   - **Surface Folder (`ISMN_surface_0-10`):** Contains a sensor at **0.10 m (10 cm)** depth. **Zero 5 cm point-sensor proxy observations exist.** A 10 cm sensor sits at the bottom boundary of the 0–10 cm layer and cannot serve as a surface 5 cm proxy.
   - **Middle Folder (`ISMN_middle_10-30`):** Contains sensors at **0.10 m (10 cm)** and **0.25 m (25 cm)** depth.
   - **Deep Folder (`ISMN_deep_30-60`):** Contains a sensor at **0.50 m (50 cm)** depth.
5. **Temporal Window & Satellite Feature Blocker:**
   - **Observation Time Range:** Strictly **2011-06-16 13:00:00 UTC to 2012-11-22 05:00:00 UTC** (~17 months).
   - **Temporal Mismatch:** This period **completely precedes** the planned 2015–2023 satellite reanalysis window. Overlap with Sentinel-1 (launched 2014), Sentinel-2 (launched 2015), and NASA SMAP (launched 2015) is **0.0% (0 days)**.
   - ERA5-Land weather reanalysis is available historically for 2011–2012, but satellite multi-sensor feature alignment is impossible without temporal overlap.

---

## Detailed Data Inventory Across Depth Groups

### Table 1: Comprehensive Comparison of the Three ISMN Depth Groups

| Metric | Surface: `ISMN_surface_0-10` | Middle: `ISMN_middle_10-30` | Deep: `ISMN_deep_30-60` | Full Dataset Total (Unique) |
| :--- | :--- | :--- | :--- | :--- |
| **Total Files in Folder** | 9 files | 10 files | 9 files | **28 files** (21 unique files) |
| **Data Files (`.stm`)** | 1 file | 2 files | 1 file | **4 files** (3 unique files) |
| **Networks Represented** | 1 (`IIT_KANPUR`) | 1 (`IIT_KANPUR`) | 1 (`IIT_KANPUR`) | **1 network** |
| **Unique Stations** | 1 (`IITK_Airstrip`) | 1 (`IITK_Airstrip`) | 1 (`IITK_Airstrip`) | **1 station** |
| **Unique Sensor Time Series** | 1 series (10 cm) | 2 series (10 cm, 25 cm) | 1 series (50 cm) | **3 unique sensor series** |
| **Actual Sensor Depths** | **0.10 m (10 cm)** | **0.10 m & 0.25 m** | **0.50 m (50 cm)** | **10 cm, 25 cm, 50 cm** |
| **Nominal 5 cm Surface Probes** | **0 (None)** | 0 | 0 | **0** |
| **Raw Observation Rows** | 11,280 | 22,562 | 10,175 | **44,017 rows** |
| **Unique Observations** | 11,280 | 22,562 | 10,175 | **32,737 unique rows** |
| **Cross-Folder Duplicates** | 11,280 (100%) | 11,280 (50%) | 0 (0%) | **11,280 redundant rows** |
| **Missing Soil Moisture Values** | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | **0 (0.0%)** |
| **Quality Flags Breakdown** | 100% Flag `G` (Good) | 100% Flag `G` (Good) | 100% Flag `G` (Good) | **100% Flag `G` (Good)** |
| **Provider Flags Breakdown** | 100% Flag `M` | 100% Flag `M` | 100% Flag `M` | **100% Flag `M`** |
| **Earliest Observation** | 2011-06-16 13:00:00 | 2011-06-16 13:00:00 | 2011-06-16 13:00:00 | **2011-06-16 13:00:00** |
| **Latest Observation** | 2012-11-22 05:00:00 | 2012-11-22 05:00:00 | 2012-11-22 05:00:00 | **2012-11-22 05:00:00** |
| **Temporal Span (days)** | 524.7 days | 524.7 days | 524.7 days | **524.7 days (~17 months)** |
| **Sensor Hardware Model** | Spectrum WaterScout SM100 | Spectrum WaterScout SM100 | Spectrum WaterScout SM100 | Spectrum WaterScout SM100 |
| **Measurement Support** | `point_sensor` | `point_sensor` | `point_sensor` | `point_sensor` |
| **Volumetric Water Content Range** | $0.052 - 0.420\text{ m}^3/\text{m}^3$ | $0.052 - 0.420\text{ m}^3/\text{m}^3$ | $0.003 - 0.414\text{ m}^3/\text{m}^3$ | $0.003 - 0.420\text{ m}^3/\text{m}^3$ |
| **VWC Mean $\pm$ Std** | $0.190 \pm 0.108$ | $0.192 \pm 0.099$ | $0.220 \pm 0.092$ | $0.201 \pm 0.098$ |
| **Extended Gaps (>24h)** | 6 gaps (1,128 hrs) | 6 gaps (1,128 hrs) | 7 gaps (2,233 hrs) | 7 unique gap events |
| **Overlap with Sentinel-1/2, SMAP** | **0.0% (0 days)** | **0.0% (0 days)** | **0.0% (0 days)** | **0.0% (0 days)** |
| **Target Readiness Classification** | **Insufficient for Target** | **Requires Investigation** | **Requires Investigation** | **Blocked for Production** |

---

## Observation Statistics by Sensor Depth and Year

### Table 2: Hourly Observations by Depth and Year

| Sensor Depth | 2011 Observations | 2012 Observations | Total Observations | % of Unique Data | Sensor Model |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0.10 m (10 cm)** | 3,684 | 7,596 | **11,280** | 34.46% | Spectrum WaterScout SM100 |
| **0.25 m (25 cm)** | 3,684 | 7,598 | **11,282** | 34.46% | Spectrum WaterScout SM100 |
| **0.50 m (50 cm)** | 3,665 | 6,510 | **10,175** | 31.08% | Spectrum WaterScout SM100 |
| **Total (Unique)** | **11,033** | **21,704** | **32,737** | **100.00%** | Capacitance Point Sensors |

*Note: In `ISMN_middle_10-30`, the 25 cm sensor recorded 2 additional valid readings on 2012-01-20 compared to the 10 cm sensor.*

---

## File Format, Schema and Metadata Audit

Every downloaded folder follows the official ISMN "Separate files (Header+values)" standard:

### 1. Header Structure (`.stm`)
The first line of each `.stm` file defines the station and sensor metadata tokens:
```text
IIT_KANPUR IIT_KANPUR IITK_Airstrip 26.51881 80.23303 123.444 0.1000 0.1000 'Spectrum-WaterScoutSM100'
```
- **Field 1 (CSE):** `IIT_KANPUR` (Continental Scale Experiment acronym / Network).
- **Field 2 (Network):** `IIT_KANPUR`.
- **Field 3 (Station Name):** `IITK_Airstrip` (Airfield campus of IIT Kanpur).
- **Field 4 (Latitude):** `26.51881` decimal degrees North (WGS 84).
- **Field 5 (Longitude):** `80.23303` decimal degrees East (WGS 84).
- **Field 6 (Elevation):** `123.444` metres above sea level.
- **Field 7 (Depth From):** Upper boundary in metres (`0.1000`, `0.2500`, or `0.5000`).
- **Field 8 (Depth To):** Lower boundary in metres (`0.1000`, `0.2500`, or `0.5000`).
- **Field 9 (Sensor Description):** `'Spectrum-WaterScoutSM100'`.

### 2. Record Structure (`.stm`)
Subsequent lines record individual hourly observations:
```text
2011/06/16 13:00 0.201 G M
```
- **Token 1 & 2:** UTC Date (`YYYY/MM/DD`) and Time (`HH:MM`).
- **Token 3:** Volumetric Soil Moisture value in $\text{m}^3/\text{m}^3$ ($0.0$ to $1.0$).
- **Token 4:** ISMN Automated Quality Flag (`G` = Good).
- **Token 5:** Provider Quality Flag (`M` = Missing / Not supplied by provider).

### 3. Static Soil & Environmental Metadata (`static_variables.csv`)
Derived from the Harmonized World Soil Database (HWSD v1.1) and ESA CCI Land Cover:
- **Soil Texture (0–30 cm):** Sand = 42.0%, Silt = 36.0%, Clay = 22.0% (Loam soil class).
- **Soil Texture (30–100 cm):** Sand = 40.0%, Silt = 35.0%, Clay = 25.0% (Loam to Clay Loam).
- **Organic Carbon:** 1.0% (topsoil) to 0.4% (subsoil).
- **Soil Saturation Water Content ($VWC_{\text{sat}}$):** $0.44\text{ m}^3/\text{m}^3$ (0–30 cm) and $0.42\text{ m}^3/\text{m}^3$ (30–100 cm).
- **In Situ Land Cover:** Grassland / Rainfed Cropland.
- **Climate Classification:** Köppen-Geiger `Cwa` (Temperate, Dry Winter, Hot Summer) and `BSh` (Arid, Steppe, Hot).

---

## Data Quality, Integrity & Anomaly Assessment

### 1. Timestamps and Sampling Regularity
- **Timezone:** Standard UTC.
- **Sampling Interval:** Regular 1-hour interval during active operational periods.
- **Timestamp Duplicates:** **0 duplicate timestamps** within any individual file.
- **Conflicting Values:** **0 conflicting duplicates** for any timestamp within a file.

### 2. Major Observation Dropouts (Gaps > 24 Hours)
Both shallow sensors (10 cm and 25 cm) exhibit 6 identical extended data dropouts:
1. **2011-08-11 09:00 to 2011-08-20 12:00:** 219 hours (9.1 days) during active monsoon.
2. **2011-08-20 12:00 to 2011-08-24 06:00:** 90 hours (3.75 days).
3. **2011-10-23 05:00 to 2011-11-13 05:00:** **504 hours (21.0 days / 3 full weeks)** during the post-monsoon drying phase.
4. **2011-12-02 13:00 to 2011-12-13 06:00:** 257 hours (10.7 days) during winter.
5. **2012-01-19 08:00 to 2012-01-20 11:00:** 27 hours (1.1 days).
6. **2012-01-20 11:00 to 2012-01-21 12:00:** 25 hours (1.0 day).

At 50 cm depth, an additional extended failure occurred between September and November 2012, resulting in **1,105 missing hours** relative to the 10 cm and 25 cm records.

### 3. Physical Range Validation & Suspicious Outliers
- **Upper Limit:** The maximum observed VWC is $0.420\text{ m}^3/\text{m}^3$ (at 10 cm) and $0.414\text{ m}^3/\text{m}^3$ (at 50 cm). Neither exceeds the HWSD soil saturation threshold ($0.44\text{ m}^3/\text{m}^3$). No saturation breach flags were triggered.
- **Lower Limit (Suspicious Subsoil Outlier):**
  - At 10 cm: minimum VWC is $0.052\text{ m}^3/\text{m}^3$ (plausible dry surface soil).
  - At 25 cm: minimum VWC is $0.071\text{ m}^3/\text{m}^3$ (plausible mid-layer dry soil).
  - **At 50 cm:** minimum VWC reaches **$0.003\text{ m}^3/\text{m}^3$ (0.3% VWC)**, with 46 consecutive hourly observations recording VWC $< 0.010\text{ m}^3/\text{m}^3$ during June 2012. In a deep loam subsoil (clay fraction 25%), natural soil moisture rarely drops below the hygroscopic water limit (~$0.03 - 0.05\text{ m}^3/\text{m}^3$). This points to a temporary probe decoupling, air gap around the probe prongs, or capacitance calibration drift.

---

## Target-Depth Evaluation & Model-Readiness Verdict

### A. Surface Layer (0–10 cm): `ISMN_surface_0-10`
- **Audit Finding:** The folder contains ONLY the 10 cm sensor (`sm_0.100000_0.100000`). It contains **zero 5 cm sensors**.
- **Scientific Assessment:** Project requirements strictly mandate that the 0–10 cm surface layer must be supervised by an eligible point-sensor proxy installed around 5 cm (0.00 to 0.06 m). A sensor at 10 cm measures water content at the bottom boundary of the 0–10 cm zone, where evaporation dynamics are heavily decoupled from the soil skin layer observed by satellite optical (NDVI/NDMI) and C-band SAR radar ($VV/VH$).
- **Classification:** **Insufficient for the Target.**
- **Action:** **REJECT** from serving as a 0–10 cm surface proxy label. Reassign this file exclusively to the middle layer (10–30 cm).

### B. Middle Layer (10–30 cm): `ISMN_middle_10-30`
- **Audit Finding:** Contains two discrete point sensors: 10 cm (11,280 rows) and 25 cm (11,282 rows).
- **Scientific Assessment:** Both installation depths fall squarely within the 10–30 cm layer interval. Observations are continuous and physically consistent. However, the two sensors must **not** be averaged into an unweighted scalar without a documented vertical weighting function.
- **Classification:** **Requires Investigation / Satellite Temporal Mismatch.**
- **Action:** Suitable as ground truth for reanalysis-only historical experiments (ERA5-Land weather), but **blocked from satellite feature alignment** due to zero temporal overlap with Sentinel-1/2 and SMAP.

### C. Deep Layer (30–60 cm): `ISMN_deep_30-60`
- **Audit Finding:** Contains one discrete point sensor at 50 cm (10,175 rows).
- **Scientific Assessment:** The 50 cm installation depth accurately represents the 30–60 cm root zone. However, the 46 extreme dry readings ($<0.01\text{ m}^3/\text{m}^3$) in June 2012 require investigation, and the 1,105-hour outage in late 2012 reduces deep-layer training volume.
- **Classification:** **Requires Investigation / Satellite Temporal Mismatch.**
- **Action:** Suitable as an auxiliary deep-layer ground truth against ERA5-Land historical soil water balance simulations; **blocked from satellite feature alignment**.

---

## Readiness for Feature Alignment with the Other Datasets

| Feature Source | Status with Current ISMN Data | Reason & Impact |
| :--- | :--- | :--- |
| **ERA5-Land Weather** | **Ready for Historical Alignment** | ERA5-Land reanalysis covers 1950 to present. Weather variables (precipitation, temperature, VPD, solar radiation) can be aligned to IITK_Airstrip coordinates ($26.5188^\circ\text{N}, 80.2330^\circ\text{E}$) for 2011–2012. |
| **Sentinel-1 SAR Radar** | **BLOCKED (0.0% Overlap)** | Sentinel-1 launched April 2014. IITK_Airstrip ISMN series ended November 2012. Zero radar backscatter acquisitions exist during the observation window. |
| **Sentinel-2 Optical** | **BLOCKED (0.0% Overlap)** | Sentinel-2 launched June 2015. Zero NDVI, NDMI, or surface reflectance scenes exist during 2011–2012. |
| **NASA SMAP** | **BLOCKED (0.0% Overlap)** | SMAP launched January 2015. Zero radiometer soil moisture retrievals exist for 2011–2012. |
| **ISRIC SoilGrids 250m** | **Ready for Alignment** | Static soil properties (sand, clay, silt, bulk density, organic carbon, pH) can be extracted at IITK_Airstrip coordinates for all 4 depth intervals. |
| **Copernicus DEM (GLO-30)** | **Ready for Alignment** | Static topographic features (elevation 123.4 m, slope, aspect, TWI) can be extracted at the station coordinates. |

---

## Generated Audit Artifacts

All required audit deliverables have been created in `ISMN/audit/`:

1. [ismn_audit_report.md](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ISMN/audit/ismn_audit_report.md) — Comprehensive audit document and methodology.
2. [file_inventory.csv](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ISMN/audit/file_inventory.csv) — 28 files cataloged with formats, sizes, SHA-256 checksums, and roles.
3. [station_inventory.csv](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ISMN/audit/station_inventory.csv) — Station geographical metadata, coordinates, elevation, and sensor profiles.
4. [sensor_depth_coverage.csv](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ISMN/audit/sensor_depth_coverage.csv) — Exact sensor depths, target suitability classifications, and observation counts.
5. [temporal_coverage.csv](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ISMN/audit/temporal_coverage.csv) — Monthly observation slices cross-referenced against satellite mission timelines.
6. [quality_flag_summary.csv](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ISMN/audit/quality_flag_summary.csv) — Distribution of automated quality flags and provider flags.
7. [duplicate_and_missingness_report.csv](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ISMN/audit/duplicate_and_missingness_report.csv) — Cross-folder redundancy, duplicate counts, missing values, and physical range checks.
8. [depth_readiness_summary.json](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ISMN/audit/depth_readiness_summary.json) — Machine-readable readiness classifications and blocker registries.

---

## Answers to Specific User Questions

1. **What data have we actually downloaded?**  
   We have downloaded ISMN Header+values data for a single ground station (`IITK_Airstrip`) operated by IIT Kanpur, India, spanning June 2011 to November 2012. No data for Maharashtra was downloaded or exists in ISMN.
2. **How many stations, sensors, time series, and observations do we have?**  
   1 station, 3 physical sensor time series (10 cm, 25 cm, 50 cm), 44,017 raw rows across 3 folders, and 32,737 unique hourly observations.
3. **What are the actual sensor depths and measurement characteristics?**  
   Depths are 10 cm, 25 cm, and 50 cm using capacitance point probes (`Spectrum WaterScout SM100`). There is no 5 cm surface probe.
4. **Are the observations sufficiently complete and reliable?**  
   Within its 2011–2012 window, data quality is high (100% flag `G`, no NaN values), but there are 6 multi-day to multi-week gaps (including a 21-day gap in post-monsoon 2011).
5. **Are there duplicate records, missing values, invalid measurements, or timestamp issues?**  
   There are zero missing values, zero within-file duplicate timestamps, and zero invalid coordinates. However, the entire 10 cm sensor file (11,280 rows) is duplicated across `ISMN_surface_0-10` and `ISMN_middle_10-30`.
6. **Which observations are suitable for each intended target depth?**  
   - Surface 0–10 cm: **None.** (10 cm is not an eligible 5 cm proxy).
   - Middle 10–30 cm: Both 10 cm and 25 cm sensors are suitable.
   - Deep 30–60 cm: The 50 cm sensor is suitable.
7. **Are the datasets ready for feature alignment and model preparation?**  
   They are **NOT ready** for multi-sensor satellite feature alignment because they pre-date Sentinel-1, Sentinel-2, and SMAP by over two years. They are ready for historical ERA5-Land weather-only baseline modeling once deduplication is resolved.
8. **What information or data do we still need before acquiring ERA5-Land and other datasets?**  
   We need a strategic decision on ground truth acquisition:
   - For Maharashtra: In-situ stations must be sourced from Indian agencies (e.g., IMD, ISRO/SAC, or ICON cosmic-ray probe network), as ISMN contains zero stations in Maharashtra.
   - For satellite model development (2015–2023): Supplementary international ISMN stations with 5 cm surface probes (e.g., `REMEDHUS` Canizal in Spain or `USCRN` in the USA) must be downloaded to cover the common satellite window.
   - For the existing IIT Kanpur data: We can proceed with an ERA5-Land historical weather-only reanalysis experiment (2011–2012) if desired.
