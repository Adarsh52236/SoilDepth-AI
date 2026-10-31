# SoilDepth-AI — ISMN and ERA5-Land Dataset Collection Audit Report

**Audit Date:** 2026-10-26 21:30:00 UTC  
**Audit Scope:** Read-only dataset collection verification for **ISMN** (in situ ground soil moisture observations) and **ERA5-Land** (reanalysis meteorological and surface forcings).  
**Repository Working Directory:** `SoilDepth-AI/dataset/`  
**Pilot Target Station:** `AAMU-JTG` (SCAN Network, Alabama, USA; Lat `34.78534° N`, Lon `-86.55906° W`, Elevation `241.0 m`)  
**Audit Purpose:** Establish what physical data files currently exist locally, verify their spatial/temporal bounds against the 2015–2023 study period, identify missing elements, and define concrete next collection steps.

---

## 1. Executive Summary Table

| Dataset | Downloaded Data Confirmed | Coverage Verified | Collection Complete | Next Action |
| :--- | :---: | :---: | :---: | :--- |
| **ISMN** | **YES** (Extracted `.stm` files confirmed; raw `.zip` unretained) | **YES** for AAMU-JTG pilot & US SCAN (2015–2023); **NO** for India/Maharashtra | **PARTIALLY COLLECTED** (Complete for US pilot benchmark; incomplete for India regional validation) | Standardize manifest under `dataset/ISMN/manifests/`; resolve Indian validation source if regional transfer is pursued. |
| **ERA5-Land** | **YES** (4 raw NetCDF files + 2 processed CSV tables confirmed) | **YES** (100% hourly coverage 2015-01-01 to 2023-12-31 at station grid point) | **COMPLETE** (for AAMU-JTG pilot station) / **PARTIALLY COLLECTED** (for regional spatial grid) | Maintain pilot archive; acquire spatial grid tiles only if multi-station or distributed spatial modelling is initiated. |

---

## 2. ISMN — Ground-Station Soil Moisture Data Audit

### 2.1 Overall Status
**`PARTIALLY COLLECTED`**  
*(Complete and fully verified for the pilot station AAMU-JTG and the 220-station US SCAN benchmark across 2015–2023; partially collected globally due to un-retained raw archive zips, absence of a top-level manifest, and zero in situ station coverage in Maharashtra, India).*

---

### 2.2 Files, Directories, and Quantities Found

ISMN data is organized under `dataset/ISMN/` into two distinct network subtrees:

```text
dataset/ISMN/
├── IIT_KANPUR/                               # Indian in situ network (1 station)
│   ├── README.md                             # Specification & metadata (3,522 bytes)
│   ├── raw/                                  # Empty (0 files)
│   ├── extracted/                            # Extracted observation files
│   │   ├── surface_0-10cm/IIT_KANPUR/IITK-Airstrip/   (1 .stm + 1 .csv)
│   │   ├── middle_10-30cm/IIT_KANPUR/IITK-Airstrip/   (2 .stm + 1 .csv)
│   │   └── deep_30-60cm/IIT_KANPUR/IITK-Airstrip/     (1 .stm + 1 .csv)
│   └── audit/                                # Audit reports (18,762 bytes)
├── SCAN/                                     # USDA-NRCS SCAN network (USA, 220 stations)
│   ├── README.md                             # Specification & metadata (1,781 bytes)
│   ├── raw/                                  # Empty (raw ZIPs unretained locally)
│   ├── extracted/                            # 2,457 files across 658 directories
│   │   ├── surface_0-10cm/SCAN/              # 456 .stm files + 218 static CSVs (10,359,229 rows)
│   │   ├── middle_10-30cm/SCAN/              # 866 .stm files + 219 static CSVs (20,650,316 rows)
│   │   └── deep_30-60cm/SCAN/                # 465 .stm files + 215 static CSVs (9,001,163 rows)
│   └── audit/                                # 22 files, including verification reports & CSVs
└── ISMN/                                     # Artifact folder from prior directory move
    └── SCAN/audit/verification/              # 3 redundant verification CSV copies
```

#### File Counts and Storage Metrics:
1. **Total Extracted `.stm` Time Series Files:**
   - `SCAN`: **1,787 files** (456 surface, 866 middle, 465 deep)
   - `IIT_KANPUR`: **4 files** (1 surface duplicate, 2 middle, 1 deep)
   - **Total:** **1,791 `.stm` files**
2. **Total Static Metadata Files:** **670 `.csv` files** in SCAN (`<Network>_<Station>_static_variables.csv`) + **3 `.csv` files** in IIT_KANPUR.
3. **Total In Situ Hourly Observations:**
   - `SCAN`: **40,010,708 hourly observations** across 2015–2023.
   - `IIT_KANPUR`: **32,737 hourly observations** across 2011–2012.
4. **Raw Archive Files (`raw/`):**
   - Both `dataset/ISMN/SCAN/raw/` and `dataset/ISMN/IIT_KANPUR/raw/` are currently **empty** (0 bytes). Original downloaded `.zip` packages were unpacked directly into `extracted/` during initial acquisition and were not retained locally.

---

### 2.3 Verification of Previously Tested Stations: Narbonne & ARM-1

A specific search was performed across all directories, filenames, git logs, and past session transcripts:

| Station Name | Network | Country | Claimed Observations | Current File Status | Origin & Historical Role |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Narbonne** | `SMOSMANIA` | France | 741 rows (2007) | **DOES NOT EXIST** | Disposable reader smoke-test sample created in `tmp/real_data/` during early development. Intentionally removed during pipeline cleanup. Never part of the intended final collection. |
| **ARM-1** | `COSMOS` | USA (Oklahoma) | 6,865 rows (2017–2018) | **DOES NOT EXIST** | Disposable reader smoke-test sample created in `tmp/real_data/` to test Cosmic-Ray probe headers. Intentionally removed during pipeline cleanup. Never part of the intended final collection. |

**Verdict:** Narbonne and ARM-1 were **purely diagnostic smoke-test samples** used to validate ASCII parser robustness. Their absence from `dataset/ISMN/` is intentional and correct.

---

### 2.4 Verification of Pilot Station AAMU-JTG

Station `AAMU-JTG` is confirmed present with 4 verified `.stm` files and 3 metadata CSVs:

| Target Layer | Sensor Hardware | Depth ($m$) | Rows / Obs | Temporal Range (UTC) | Quality Flags | Provider Flags | Mean SM ($\text{m}^3/\text{m}^3$) | File Path |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Surface** | Stevens-Hydraprobe-Analog | 0.0508 (5 cm) | 70,251 | 2015-01-01 00:00 to 2023-11-19 04:00 | 100% `G` (Good) | 70,246 `V`, 5 `E` | 0.2776 | [dataset/ISMN/SCAN/extracted/surface_0-10cm/SCAN/AAMU-JTG/](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/ISMN/SCAN/extracted/surface_0-10cm/SCAN/AAMU-JTG) |
| **Middle** | Stevens-Hydraprobe-Analog | 0.1016 (10 cm) | 73,546 | 2015-01-01 00:00 to 2023-12-31 00:00 | 100% `G` (Good) | 73,544 `V`, 2 `E` | 0.3365 | [dataset/ISMN/SCAN/extracted/middle_10-30cm/SCAN/AAMU-JTG/](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/ISMN/SCAN/extracted/middle_10-30cm/SCAN/AAMU-JTG) |
| **Middle** | Stevens-Hydraprobe-Analog | 0.2032 (20 cm) | 63,248 | 2015-01-01 00:00 to 2023-12-31 00:00 | 100% `G` (Good) | 63,244 `V`, 4 `E` | 0.3771 | [dataset/ISMN/SCAN/extracted/middle_10-30cm/SCAN/AAMU-JTG/](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/ISMN/SCAN/extracted/middle_10-30cm/SCAN/AAMU-JTG) |
| **Deep** | Stevens-Hydraprobe-Analog | 0.5080 (50 cm) | 56,854 | 2015-01-01 00:00 to 2023-12-31 00:00 | 100% `G` (Good) | 56,847 `V`, 7 `E` | 0.4163 | [dataset/ISMN/SCAN/extracted/deep_30-60cm/SCAN/AAMU-JTG/](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/ISMN/SCAN/extracted/deep_30-60cm/SCAN/AAMU-JTG) |

**Total Observations for AAMU-JTG:** **263,899 hourly records** (100% flagged `G` - Good, with zero corrupted lines).

---

### 2.5 Actual Spatial & Temporal Coverage

1. **Spatial Coverage:**
   - **United States (SCAN):** 220 stations distributed across 40 US states (108 East of $-100^\circ\text{ W}$, 112 West of $-100^\circ\text{ W}$). 213 stations possess simultaneous surface, middle, and deep sensors.
   - **India (IIT_KANPUR):** Exactly 1 station (`IITK-Airstrip`, Kanpur, Uttar Pradesh; Lat `26.5188° N`, Lon `80.2330° E`). **Zero stations exist in Maharashtra, India.**
2. **Temporal Coverage:**
   - **SCAN:** Continuous 9 calendar years (2015-01-01 to 2023-12-31; 108 months), perfectly synchronized with Sentinel-1 / SMAP / ERA5-Land satellite records.
   - **IIT_KANPUR:** 2011-06-16 to 2012-11-22 (17 months). Completely disjoint from the 2015–2023 satellite and meteorological study window.

---

### 2.6 Missing Requirements, Deficiencies, and Unresolved Issues

1. **Absence of Ground Truth in India / Maharashtra:**
   - The primary project vision includes independent regional transfer to Maharashtra, India.
   - ISMN has **zero ground stations in Maharashtra**. The only Indian station present (`IITK-Airstrip`) is in Uttar Pradesh and ceased reporting in November 2012.
2. **Unretained Raw ZIP Archives:**
   - `dataset/ISMN/SCAN/raw/` and `dataset/ISMN/IIT_KANPUR/raw/` contain no archive files. While extracted files are verified, end-to-end byte-level reproducibility from raw source archives is unretained.
3. **No Central Manifest Schema:**
   - Unlike `ERA5_LAND` and `SoilGrids`, ISMN lacks a standardized `dataset/ISMN/manifests/download_manifest.csv`. Its verification records currently reside in `dataset/ISMN/SCAN/audit/verification/`.
4. **Nested Redundant Directory:**
   - `dataset/ISMN/ISMN/` exists as a duplicate nested path with 3 orphaned verification CSV copies, created during earlier file reorganizations.

---

### 2.7 Exact Next Action Required for ISMN

1. **Create Standardized Manifest:** Consolidate station records into `dataset/ISMN/manifests/download_manifest.csv` adhering to the repository manifest standard.
2. **Remove Redundant Directory:** Remove the empty nested artifact directory `dataset/ISMN/ISMN/`.
3. **Document Regional Boundary:** Explicitly maintain in project documentation that the ISMN dataset supports the US SCAN benchmark and pilot station AAMU-JTG, but does not provide ground truth for Maharashtra.

---

## 3. ERA5-Land — Weather and Land Variables Audit

### 3.1 Overall Status
**`COMPLETE` (for Pilot Station AAMU-JTG)** / **`PARTIALLY COLLECTED` (for Full Spatial Grids)**  
*(100% of required meteorological variables for AAMU-JTG over the complete 2015–2023 study window are downloaded, verified, and preprocessed into hourly and daily tables).*

---

### 3.2 Files, Directories, and Quantities Found

ERA5-Land data is fully cataloged under `dataset/ERA5_LAND/`:

```text
dataset/ERA5_LAND/
├── README.md                                 # Architecture and pipeline documentation (4,953 bytes)
├── raw/AAMU-JTG/hourly/                      # 4 raw downloaded NetCDF files (4,488,737 bytes total)
│   ├── reanalysis-era5-land-timeseries-sfc-2m-temperaturew47vt3yx.nc          (1,282,918 bytes)
│   ├── reanalysis-era5-land-timeseries-sfc-pressure-precipitation1imwkrl7.nc   (961,489 bytes)
│   ├── reanalysis-era5-land-timeseries-sfc-radiation-heat2t08fnvs.nc          (961,422 bytes)
│   └── reanalysis-era5-land-timeseries-sfc-wind4ewbndqw.nc                    (1,282,908 bytes)
├── processed/AAMU-JTG/                       # 2 verified tabular outputs (8,012,818 bytes total)
│   ├── ERA5Land_AAMU-JTG_2015-2023_hourly.csv                                (7,622,638 bytes, 78,888 rows)
│   └── ERA5Land_AAMU-JTG_2015-2023_daily.csv                                 (390,180 bytes, 3,287 rows)
├── manifests/                                # Official manifest
│   └── download_manifest.csv                 # 6 verified records with SHA-256 (2,355 bytes)
├── audit/                                    # Detailed technical inspection logs
│   ├── AAMU-JTG_pilot_file_inspection.md     (7,810 bytes)
│   └── AAMU-JTG_processing_report.md         (5,576 bytes)
└── scripts/                                  # Processing and verification code
    ├── process_era5_land_pilot.py            (19,043 bytes)
    └── validate_era5_land.py                 (15,333 bytes)
```

---

### 3.3 Actual Spatial and Temporal Coverage

1. **Spatial Coverage:**
   - **Target In Situ Station:** `AAMU-JTG` (Latitude `34.78534° N`, Longitude `-86.55906° W`, Elevation `241.0 m`).
   - **ERA5-Land Grid Point:** Extracted at grid center `34.80000° N, -86.60000° E` (offset: $\Delta\text{Lat} = +0.0147^\circ$, $\Delta\text{Lon} = -0.0409^\circ$, approximately $4.08\text{ km}$).
   - **Coverage Classification:** Single-point time series extraction covering the pilot station. (Does not contain a wide spatial grid or multi-station ERA5-Land extractions).
2. **Temporal Coverage:**
   - **Start:** `2015-01-01 00:00:00 UTC`
   - **End:** `2023-12-31 23:00:00 UTC`
   - **Total Hourly Steps:** Exactly **78,888 contiguous hourly steps** ($3,287\text{ days} \times 24\text{ hours}$).
   - **Gaps & Missing Data:** **0 irregular gaps, 0 duplicates, 0 missing (NaN) values**.

#### Alignment with Planned Modelling Periods:
- **Training Period (2015–2020):** 52,608 hourly steps (2,192 days) $\rightarrow$ **100.0% Complete**
- **Validation Period (2021):** 8,760 hourly steps (365 days) $\rightarrow$ **100.0% Complete**
- **Testing Period (2022–2023):** 17,520 hourly steps (730 days) $\rightarrow$ **100.0% Complete**
- **Total Period:** **100.0% aligned with all study phases**.

---

### 3.4 Variables Collected, Units, and Accumulation Semantics

All 6 primary meteorological variables are present in raw NetCDF-4 format and correctly standardized in the processed tables:

| Variable Name | NetCDF Symbol | Raw Units | Processed Column | Processed Units | Semantics & Transformation |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **2m Air Temperature** | `t2m` | $\text{K}$ | `temperature_2m_c` | $^\circ\text{C}$ | Instantaneous: $T(^\circ\text{C}) = T(\text{K}) - 273.15$ |
| **2m Dewpoint Temperature** | `d2m` | $\text{K}$ | `dewpoint_2m_c` | $^\circ\text{C}$ | Instantaneous: $T_d(^\circ\text{C}) = T_d(\text{K}) - 273.15$ |
| **Total Precipitation** | `tp` | $\text{m}$ | `precipitation_mm` | $\text{mm}/\text{hr}$ | 1-hour backward accumulation ($t-1$ to $t$): $P(\text{mm}) = \max(0, \text{tp} \times 1000)$ |
| **Surface Solar Radiation** | `ssrd` | $\text{J}/\text{m}^2$ | `solar_radiation` | $\text{W}/\text{m}^2$ | 1-hour backward accumulation ($t-1$ to $t$): $R_s(\text{W}/\text{m}^2) = \max(0, \text{ssrd} / 3600)$ |
| **10m U-Wind Component** | `u10` | $\text{m}/\text{s}$ | `wind_u10_ms` | $\text{m}/\text{s}$ | Instantaneous eastward wind |
| **10m V-Wind Component** | `v10` | $\text{m}/\text{s}$ | `wind_v10_ms` | $\text{m}/\text{s}$ | Instantaneous northward wind |

**Daily Aggregations (`ERA5Land_AAMU-JTG_2015-2023_daily.csv`):**
- Daily temperature mean, min, max ($^\circ\text{C}$).
- Daily dewpoint mean ($^\circ\text{C}$).
- Daily precipitation total ($\text{mm}/\text{day}$, sum of 24 hourly values).
- Daily solar radiation total ($\text{MJ}/\text{m}^2/\text{day}$) and mean flux ($\text{W}/\text{m}^2$).
- Daily U-wind and V-wind vector means ($\text{m}/\text{s}$).
- All 3,287 days have `is_complete == True` (24/24 hourly observations).

---

### 3.5 Actual Downloaded Data vs. Mere Configurations

- **Actual Downloaded Data:** Confirmed. The 4 raw `.nc` files are physically present on disk, totaling $4.49\text{ MB}$. All files have been SHA-256 verified and parsed at the binary array level.
- **Processed Tables:** Confirmed. Both hourly and daily CSV tables exist physically in `processed/AAMU-JTG/`.
- **Manifest:** Confirmed. `dataset/ERA5_LAND/manifests/download_manifest.csv` records all 6 raw and processed artifacts with exact SHA-256 hashes.

---

### 3.6 Missing Requirements and Unresolved Issues

1. **Single-Station Scope:**
   - Current ERA5-Land collection covers only station `AAMU-JTG` (point grid cell).
   - If the study expands to other SCAN stations (e.g. 220 stations) or regional 2D spatial modeling, corresponding ERA5-Land grid cells or NetCDF raster tiles will need to be acquired.
2. **Additional Atmospheric Variables:**
   - Surface pressure (`sp`) and potential evaporation (`pev`) are not included in the current 4 NetCDF files. However, the existing 6 variables fully satisfy all baseline feature engineering and Penman-Monteith / FAO-56 radiation approximations.

---

### 3.7 Exact Next Action Required for ERA5-Land

- **For AAMU-JTG Pilot:** **No further collection action required.** The dataset is 100% complete, verified, and preprocessed.
- **For Multi-Station / Regional Scaling:** Define CDS API request scripts for batch extraction across additional target SCAN stations once the pilot pipeline is finalized.

---

## 4. Verification and Safety Confirmation

- **No external downloads were performed.**
- **No raw data files or pipeline files were modified, moved, renamed, or deleted.**
- **Repository test suite status:** 28 / 28 unit and regression tests passing (`pytest tests/`).
