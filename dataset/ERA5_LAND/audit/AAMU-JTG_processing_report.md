# SoilDepth-AI — ERA5-Land Weather Processing Report: Station AAMU-JTG

**Processing Timestamp:** 2026-10-26 07:28:50 UTC  
**Target Station:** `AAMU-JTG`  
**Station In Situ Location:** Lat `34.78534`, Lon `-86.55906` (Elevation: `241.0 m`)  
**ERA5-Land Grid Point:** Lat `34.8000`, Lon `-86.6000` (Offset: `4.08 km`)  
**Processing Status:** **`PROCESSING_PASSED_AND_VERIFIED`**

---

## 1. Input Source NetCDF Files

| Source Filename | Variables Contained | File Size | SHA-256 Checksum | Time Steps |
| :--- | :--- | :--- | :--- | :---: |
| `reanalysis-era5-land-timeseries-sfc-2m-temperaturew47vt3yx.nc` | `d2m; t2m` | 1,282,918 bytes (1.22 MB) | `f19c9d5de565b048dfae4b7052a522a3c100873e08e5e450b4592670c1ff14a5` | 78,888 |
| `reanalysis-era5-land-timeseries-sfc-pressure-precipitation1imwkrl7.nc` | `tp` | 961,489 bytes (0.92 MB) | `0ab48ba9dca091cad9b6ced7967465999f4aff370701d7f017a3f80336d66762` | 78,888 |
| `reanalysis-era5-land-timeseries-sfc-radiation-heat2t08fnvs.nc` | `ssrd` | 961,422 bytes (0.92 MB) | `0ff3f7572776f52737d9e721f9b503b92bb8d3ae612cd419f4036413f03f5a25` | 78,888 |
| `reanalysis-era5-land-timeseries-sfc-wind4ewbndqw.nc` | `u10; v10` | 1,282,908 bytes (1.22 MB) | `2c54d2fd01107085de8b119e9bcdc8a17f987a7f875c25f52a27963d007c1585` | 78,888 |

---

## 2. Verification of Accumulation Semantics

In ECMWF ERA5-Land hourly time series:
1. **Total Precipitation (`tp`):**
   - The variable `tp` represents total accumulated liquid and frozen water in meters over the **preceding 1-hour interval** ($t-1$ to $t$).
   - Verification across multiple rain events confirmed that values non-monotonically peak and decrease hour-by-hour (e.g. rising to 6.75 mm/h during a storm and dropping to 1.15 mm/h), confirming it is an incremental 1-hour sum, **not a cumulative 24-hour run**.
   - **Transformation Applied:**
     `precipitation_mm = max(0.0, tp * 1000.0)  [mm/hr]`
     *(Small negative values from spectral truncation e.g. -1.65e-8 m were clipped to 0.0.)*

2. **Surface Solar Radiation Downwards (`ssrd`):**
   - The variable `ssrd` is accumulated downwelling shortwave solar radiation in J/m² over the **preceding 1-hour interval** (t-1 to t).
   - Diurnal verification confirmed that values rise from 0 at sunrise, peak at solar noon, and drop back to 0 at sunset each calendar day without multi-day carryover.
   - **Transformation Applied for Hourly Dataset:**
     `solar_radiation = max(0.0, ssrd / 3600.0)  [W/m²]`
     *Each hourly value represents the mean downward shortwave flux density in Watts per square meter over the hour.*
   - **Transformation Applied for Daily Dataset:**
     `solar_radiation_total_mj_m2 = sum(ssrd_hourly) / 1,000,000.0  [MJ/m²]`
     *Represents the standard FAO-56 daily solar radiation energy integral.*

---

## 3. Variable Range and Transformation Summary

| Feature Column | Raw Name & Units | Processed Units | Raw Min | Raw Max | Raw Mean | Converted Min | Converted Max | Converted Mean | Missing (NaN) Count |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `temperature_2m_c` | `t2m` (K) | °C | 260.26 K | 310.33 K | 289.90 K | -12.89 °C | 37.18 °C | 16.75 °C | **0** |
| `dewpoint_2m_c` | `d2m` (K) | °C | 248.08 K | 299.59 K | 284.25 K | -25.07 °C | 26.44 °C | 11.10 °C | **0** |
| `precipitation_mm` | `tp` (m) | mm/hr | -0.000000 m | 0.0200 m | 0.000168 m | 0.00 mm | 20.03 mm | 0.1681 mm | **0** |
| `solar_radiation` | `ssrd` (J/m²) | W/m² | -2.0 | 3721800.0 | 661235.8 | 0.00 W/m² | 1033.83 W/m² | 183.68 W/m² | **0** |
| `wind_u10_ms` | `u10` (m/s) | m/s | -6.996 | 6.511 | 0.014 | -6.996 m/s | 6.511 m/s | 0.014 m/s | **0** |
| `wind_v10_ms` | `v10` (m/s) | m/s | -6.049 | 8.389 | 0.286 | -6.049 m/s | 8.389 m/s | 0.286 m/s | **0** |

---

## 4. Output Datasets Generated

1. **Hourly Processed Table:**
   - **Path:** [`ERA5_LAND/processed/AAMU-JTG/ERA5Land_AAMU-JTG_2015-2023_hourly.csv`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ERA5_LAND/processed/AAMU-JTG/ERA5Land_AAMU-JTG_2015-2023_hourly.csv)
   - **Row Count:** **78,888 rows** (100.0% complete for 2015-01-01 00:00:00 to 2023-12-31 23:00:00 UTC)
   - **Duplicate Timestamps:** 0
   - **Missing Timestamps:** 0
   - **Columns:** `timestamp_utc, station_id, latitude_station, longitude_station, latitude_era5_grid, longitude_era5_grid, temperature_2m_c, dewpoint_2m_c, precipitation_mm, solar_radiation, wind_u10_ms, wind_v10_ms`

2. **Daily Aggregated Table:**
   - **Path:** [`ERA5_LAND/processed/AAMU-JTG/ERA5Land_AAMU-JTG_2015-2023_daily.csv`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ERA5_LAND/processed/AAMU-JTG/ERA5Land_AAMU-JTG_2015-2023_daily.csv)
   - **Row Count:** **3,287 days** (100.0% of calendar days)
   - **Incomplete Days:** **0** (All 3,287 days have `hourly_obs_count == 24` and `is_complete == True`)
   - **Columns:** `date_utc, station_id, latitude_station, longitude_station, latitude_era5_grid, longitude_era5_grid, hourly_obs_count, is_complete, temperature_2m_mean_c, temperature_2m_min_c, temperature_2m_max_c, dewpoint_2m_mean_c, precipitation_total_mm, solar_radiation_total_mj_m2, solar_radiation_mean_w_m2, wind_u10_mean_ms, wind_v10_mean_ms`

---

## 5. Manifest Ledger Status

The manifest [`ERA5_LAND/manifests/download_manifest.csv`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/ERA5_LAND/manifests/download_manifest.csv) was updated to reflect `PROCESSED` status for the AAMU-JTG pilot suite.
