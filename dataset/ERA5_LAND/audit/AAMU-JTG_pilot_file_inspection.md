# SoilDepth-AI — ERA5-Land Pilot Inspection Report: Station AAMU-JTG

**Inspection Timestamp:** 2026-10-26 07:01:37 UTC  
**Target Station:** `AAMU-JTG` (Lat: `34.78534`, Lon: `-86.55906`, Elev: `241.0 m`)  
**ERA5-Land Grid Point:** Lat: `34.8000`, Lon: `-86.6000` (Offset: dLat = 0.0147 deg, dLon = 0.0409 deg, approx 4.1 km)  
**Total NetCDF Files Inspected:** 4  
**Collective Verification Verdict:** **`COLLECTION_COMPLETE_AND_VALIDATED`**

---

## 1. Executive Summary

1. **All 4 NetCDF files open successfully** via `xarray` and `netCDF4` without error, corruption, or structural truncation.
2. **All 6 requested meteorological variables are present** across the 4 downloaded files:
   - `2m_temperature` (`t2m`)
   - `2m_dewpoint_temperature` (`d2m`)
   - `total_precipitation` (`tp`)
   - `surface_solar_radiation_downwards` (`ssrd`)
   - `10m_u_component_of_wind` (`u10`)
   - `10m_v_component_of_wind` (`v10`)
3. **Exact 100% Temporal Coincidence:** Every single file covers the exact requested study window of **2015-01-01 00:00:00 UTC to 2023-12-31 23:00:00 UTC** (all 9 calendar years, 108 months).
4. **Zero Gaps, Zero Duplicates, Zero Missing Values:** Every file contains exactly **78,888 contiguous hourly time steps** (expected: 3,287 days * 24 hrs = 78,888 hrs) with **0 NaN values**, **0 duplicate timestamps**, and a strictly uniform 1-hour interval throughout.

---

## 2. File-by-File Technical Profile

### File 1: `reanalysis-era5-land-timeseries-sfc-2m-temperaturew47vt3yx.nc`
- **File Size:** 1,282,918 bytes (1.22 MB)
- **SHA-256 Checksum:** `f19c9d5de565b048dfae4b7052a522a3c100873e08e5e450b4592670c1ff14a5`
- **Dimensions:** `{'valid_time': 78888}`
- **Coordinate Names:** `latitude, longitude, valid_time`
- **Time Range:** `2015-01-01T00:00:00` to `2023-12-31T23:00:00` UTC
- **Time Steps Count:** **78,888 steps** (Expected: 78,888)
- **Temporal Integrity:** 0 duplicates, 0 irregular gaps, 100% hourly continuity
- **Matches Requested Period (2015–2023):** **YES (100.0%)**
- **Data Variables Contained:**
  - **`d2m`** (`2 metre dewpoint temperature`):
    - Units: `K`
    - Array Shape: `(78888,)`
    - Physical Range: `[248.0758, 299.5856]` (Mean: `284.2523`)
    - Missing (NaN) Count: **0**
  - **`t2m`** (`2 metre temperature`):
    - Units: `K`
    - Array Shape: `(78888,)`
    - Physical Range: `[260.2562, 310.3333]` (Mean: `289.9039`)
    - Missing (NaN) Count: **0**

### File 2: `reanalysis-era5-land-timeseries-sfc-pressure-precipitation1imwkrl7.nc`
- **File Size:** 961,489 bytes (0.92 MB)
- **SHA-256 Checksum:** `0ab48ba9dca091cad9b6ced7967465999f4aff370701d7f017a3f80336d66762`
- **Dimensions:** `{'valid_time': 78888}`
- **Coordinate Names:** `latitude, longitude, valid_time`
- **Time Range:** `2015-01-01T00:00:00` to `2023-12-31T23:00:00` UTC
- **Time Steps Count:** **78,888 steps** (Expected: 78,888)
- **Temporal Integrity:** 0 duplicates, 0 irregular gaps, 100% hourly continuity
- **Matches Requested Period (2015–2023):** **YES (100.0%)**
- **Data Variables Contained:**
  - **`tp`** (`Total precipitation`):
    - Units: `m`
    - Array Shape: `(78888,)`
    - Physical Range: `[-0.0000, 0.0200]` (Mean: `0.0002`)
    - Missing (NaN) Count: **0**

### File 3: `reanalysis-era5-land-timeseries-sfc-radiation-heat2t08fnvs.nc`
- **File Size:** 961,422 bytes (0.92 MB)
- **SHA-256 Checksum:** `0ff3f7572776f52737d9e721f9b503b92bb8d3ae612cd419f4036413f03f5a25`
- **Dimensions:** `{'valid_time': 78888}`
- **Coordinate Names:** `latitude, longitude, valid_time`
- **Time Range:** `2015-01-01T00:00:00` to `2023-12-31T23:00:00` UTC
- **Time Steps Count:** **78,888 steps** (Expected: 78,888)
- **Temporal Integrity:** 0 duplicates, 0 irregular gaps, 100% hourly continuity
- **Matches Requested Period (2015–2023):** **YES (100.0%)**
- **Data Variables Contained:**
  - **`ssrd`** (`Surface solar radiation downwards`):
    - Units: `J m**-2`
    - Array Shape: `(78888,)`
    - Physical Range: `[-2.0000, 3721800.0000]` (Mean: `661235.7500`)
    - Missing (NaN) Count: **0**

### File 4: `reanalysis-era5-land-timeseries-sfc-wind4ewbndqw.nc`
- **File Size:** 1,282,908 bytes (1.22 MB)
- **SHA-256 Checksum:** `2c54d2fd01107085de8b119e9bcdc8a17f987a7f875c25f52a27963d007c1585`
- **Dimensions:** `{'valid_time': 78888}`
- **Coordinate Names:** `latitude, longitude, valid_time`
- **Time Range:** `2015-01-01T00:00:00` to `2023-12-31T23:00:00` UTC
- **Time Steps Count:** **78,888 steps** (Expected: 78,888)
- **Temporal Integrity:** 0 duplicates, 0 irregular gaps, 100% hourly continuity
- **Matches Requested Period (2015–2023):** **YES (100.0%)**
- **Data Variables Contained:**
  - **`u10`** (`10 metre U wind component`):
    - Units: `m s**-1`
    - Array Shape: `(78888,)`
    - Physical Range: `[-6.9964, 6.5106]` (Mean: `0.0141`)
    - Missing (NaN) Count: **0**
  - **`v10`** (`10 metre V wind component`):
    - Units: `m s**-1`
    - Array Shape: `(78888,)`
    - Physical Range: `[-6.0487, 8.3895]` (Mean: `0.2856`)
    - Missing (NaN) Count: **0**

---

## 3. Collective Six-Variable Coverage Matrix

| Requested Variable | ERA5-Land Shortname | Source NetCDF File | Units | Physical Plausibility & Range | Missing (NaN) Count | Status |
| :--- | :---: | :--- | :---: | :--- | :---: | :---: |
| **2m_temperature** | `t2m` | `reanalysis-era5-land-timeseries-sfc-2m-temperaturew47vt3yx.nc` | `K` | `[260.26, 310.33]` (Mean: `289.90`) | **0** | **`PRESENT`** |
| **2m_dewpoint_temperature** | `d2m` | `reanalysis-era5-land-timeseries-sfc-2m-temperaturew47vt3yx.nc` | `K` | `[248.08, 299.59]` (Mean: `284.25`) | **0** | **`PRESENT`** |
| **total_precipitation** | `tp` | `reanalysis-era5-land-timeseries-sfc-pressure-precipitation1imwkrl7.nc` | `m` | `[-0.00, 0.02]` (Mean: `0.00`) | **0** | **`PRESENT`** |
| **surface_solar_radiation_downwards** | `ssrd` | `reanalysis-era5-land-timeseries-sfc-radiation-heat2t08fnvs.nc` | `J m**-2` | `[-2.00, 3721800.00]` (Mean: `661235.75`) | **0** | **`PRESENT`** |
| **10m_u_component_of_wind** | `u10` | `reanalysis-era5-land-timeseries-sfc-wind4ewbndqw.nc` | `m s**-1` | `[-7.00, 6.51]` (Mean: `0.01`) | **0** | **`PRESENT`** |
| **10m_v_component_of_wind** | `v10` | `reanalysis-era5-land-timeseries-sfc-wind4ewbndqw.nc` | `m s**-1` | `[-6.05, 8.39]` (Mean: `0.29`) | **0** | **`PRESENT`** |

---

## 4. Modeling & Feature Extraction Recommendations

1. **Precipitation Flux De-accumulation:**
   - In ERA5-Land hourly reanalysis, `tp` represents total accumulated liquid and frozen water in meters over the hourly forecast interval. In time-series extractions, each hour represents the incremental accumulation since the previous step. For ML features, convert `tp` from meters to millimeters per hour:
     $$\text{Precipitation (mm/h)} = \text{tp (m)} \times 1000.0$$
2. **Solar Radiation Flux Conversion:**
   - `ssrd` is accumulated surface solar radiation downwards in $\text{J}/\text{m}^2$. To convert hourly accumulated Joules to mean flux density in Watts per square meter ($\text{W}/\text{m}^2$):
     $$\text{Solar Flux (W/m}^2) = \frac{\text{ssrd (J/m}^2)}{3600.0\text{ s}}$$
3. **Wind Speed & Direction Calculation:**
   - Calculate total 10m wind speed ($W_{10}$) from orthogonal vectors:
     $$W_{10} = \sqrt{u_{10}^2 + v_{10}^2}$$
4. **Vapor Pressure Deficit (VPD):**
   - Combine $t_{2m}$ and $d_{2m}$ to compute actual vapor pressure ($e_a$) and saturation vapor pressure ($e_s$) via the Tetens formula, generating the atmospheric demand feature (VPD) critical for soil-water balance modeling.

---
*Report generated automatically by `ERA5_LAND/scripts/validate_era5_land.py`. All original files in `raw/` remain pristine and immutable.*
