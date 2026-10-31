# SoilDepth-AI — Phase 2C: Maharashtra Pune Environmental Dataset Scientific & Data Integrity Audit

**Target Station:** `IITM-PUNE-COSMOS` (Indian Institute of Tropical Meteorology, Pashan, Pune)  
**Geographic Coordinates:** Latitude $18.5372^\circ\text{ N}$, Longitude $73.8051^\circ\text{ E}$  
**Audit Period:** 2017-01-01 to 2023-12-31 (2,556 daily epochs / 61,344 hourly timesteps)  
**Audit Standard:** ISO-19157 (Geographic Information — Data Quality), Open Geospatial Consortium (OGC), and SoilDepth-AI High-Assurance ML Governance  
**Auditor:** Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI  
**Branch:** `main`  
**Execution Date:** 2026-10-31  

---

## 1. Audit Methodology

This independent scientific audit evaluated the multi-modal environmental predictor datasets generated during Phase 2B for the Pune COSMOS pilot station. The audit examined raw inputs, spatial indexing, unit conversions, temporal causal alignment, missingness semantics, and cryptographic provenance across six distinct data streams:
1. **Copernicus Global 30m DEM (GLO-30):** Coordinate indexing, tile decoding, floating-point predictor inversion, subpixel interpolation, and physical elevation reconciliation against ground benchmarks and independent satellite topography.
2. **Sentinel-1 RTC (GRD):** Spatial subsetting, orbit direction, revisit periodicity, raw acquisition counts, causal LOCF forward-fill (`shift(1)`), staleness thresholds ($30\text{ days}$), and explicit observation provenance.
3. **Sentinel-2 L2A MultiSpectral:** Scene Classification Layer (SCL) cloud/shadow masking, clear observation filtering, spectral index derivations (NDVI, EVI), causal LOCF forward-fill (`shift(1)`), staleness thresholds ($45\text{ days}$), and separation of raw missingness from imputed availability.
4. **ISRIC SoilGrids v2.0 (250m):** 32 WCS GeoTIFF extractions (8 properties $\times$ 4 depths), integer DN decoding, scale factors, mass-balance texture closure ($\text{Clay} + \text{Sand} + \text{Silt} = 100\%$), suction hierarchy ($\theta_{1500\text{kPa}} < \theta_{33\text{kPa}} < \theta_{10\text{kPa}}$), and pedotransfer hydraulic derivations (AWC, Field Capacity, Wilting Point).
5. **ECMWF ERA5-Land Reanalysis:** Timestamps, UTC temporal alignment, daily aggregation rules, physical units, antecedent memory causal lags, and verification of zero deep soil moisture variable leakage.
6. **NASA SMAP Enhanced L3 (SPL3SMP_E.006):** CMR granule inventory, authentication gating, fill-value handling, and strict prevention of synthetic data fabrication.

---

## 2. Findings by Dataset

### 2.1 Digital Elevation Model (Copernicus 30m GLO-30)
- **Grid Geometry & Decoding:**
  - Product: `Copernicus_DSM_COG_10_N18_00_E073_00_DEM.tif` (Tile 6).
  - Spatial reference: EPSG:4326 (WGS84).
  - Grid cell convention: Tag 34735 `GTRasterTypeGeoKey = 2` (`RasterPixelIsPoint`).
  - Pixel scale: $\Delta x = 1/3600^\circ$, $\Delta y = 1/3600^\circ$ ($1\text{ arc-second} \approx 30.9\text{ m}$).
  - Coordinate mapping:
    $$\text{col} = \frac{73.8051 - 73.0}{1/3600} = 2898.36 \implies \text{col\_idx} = 2898$$
    $$\text{row} = \frac{19.0 - 18.5372}{1/3600} = 1666.08 \implies \text{row\_idx} = 1666$$
  - Tile index: Tile 6 ($1024 \times 1024$ tile covering row $[1024, 2047]$, col $[2048, 3071]$). Local coordinates within tile: $(\text{row}=642, \text{col}=850)$.
  - Floating-point predictor inversion (Tag 317 = 3): Adobe Deflate byte planes successfully reassembled via `cumsum(uint8)` and unpacked to big-endian IEEE-754 `float32`.
- **Elevation Values:**
  - Nearest-pixel extracted elevation: **$591.58\text{ m}$ AMSL**.
  - Sub-pixel bilinear interpolated elevation at $(1666.08, 2898.36)$: **$590.64\text{ m}$ AMSL**.
  - Independent benchmark: Independent SRTM 90m / Copernicus 90m via Open-Meteo elevation service: **$590.0\text{ m}$ AMSL** (residual: $+1.58\text{ m}$ / $+0.64\text{ m}$).
  - Surrounding $5 \times 5$ window ($150\text{ m} \times 150\text{ m}$): values range from $585.37\text{ m}$ to $593.97\text{ m}$ AMSL.
- **Topographic Terrain Derivatives:**
  - Slope: $2.0369^\circ$ (rise/run: $0.035565$, Horn 1981 $3 \times 3$ finite difference).
  - Aspect: $330.13^\circ$ (North-Northwest facing slope, $\sin = -0.498$, $\cos = 0.8672$).
- **Discrepancy Investigation:**
  - Discrepancy against station nominal benchmark ($560.0\text{ m}$): $+31.58\text{ m}$.
  - Root cause: The nominal $560.0\text{ m}$ value cited in general COSMOS-India station tables corresponds to central Pune city (Shivajinagar IMD observatory is $559.0\text{ m}$ AMSL). However, the physical station is situated at the IITM campus in **Pashan**, located in the western outskirts of Pune along the foothill plateau of Vetal Hill / ARAI Ridge, where physical ground elevations are confirmed by both Copernicus 30m ($591.58\text{ m}$) and SRTM 90m ($590.0\text{ m}$).
  - Action taken: In compliance with scientific directives ("Do not force the DEM value to 560 m"), the true Copernicus DEM elevation ($591.58\text{ m}$) is preserved as `elevation_m`, and `benchmark_elevation_m` ($560.0\text{ m}$), `elevation_diff_benchmark_m` ($+31.58\text{ m}$), `subpixel_bilinear_elevation_m` ($590.64\text{ m}$), and `independent_srtm_elevation_m` ($590.0\text{ m}$) are explicitly documented.

---

### 2.2 Sentinel-1 SAR Backscatter
- **Raw Observations:**
  - Total cataloged acquisitions: 175 distinct dates (2017-01-08 to 2023-12-27).
  - Average revisit periodicity: $14.5\text{ days}$ (intermittent 6-day, 12-day, and occasional 24-day intervals).
  - Raw observation coverage: **$6.85\%$** ($175 / 2,556\text{ days}$).
  - Raw missingness: **$93.15\%$** ($2,381 / 2,556\text{ days}$).
- **LOCF Feature Imputation & Provenance:**
  - Strictly past-only LOCF forward-fill: applied via `shift(1).ffill()`. An observation on day $D$ is never available for inference on day $D$; it only becomes available on day $D+1$.
  - LOCF feature availability: **$99.69\%$** ($2,548 / 2,556\text{ days}$); the initial 7 days (2017-01-01 to 2017-01-07) precede the first S1 overpass and correctly remain unpopulated (NaN).
  - Staleness tracking: $164\text{ days}$ ($6.42\%$) exceed the $30\text{ day}$ staleness threshold (`s1_is_stale = True`), caused primarily by satellite constellation orbit maintenance and the Sentinel-1B anomaly in December 2021.
  - New provenance fields: `s1_raw_observation_available`, `s1_observation_source_date`, `s1_days_since_last_valid_observation`, and `s1_is_stale`.

---

### 2.3 Sentinel-2 Optical MultiSpectral
- **Raw Observations & Cloud Filtering:**
  - Total cataloged overpasses: 540 scenes.
  - Distinct calendar dates: 455 dates.
  - Scene Classification Layer (SCL) filtering: 156 dates excluded due to severe cloud cover ($> 60\%$) or cloud shadow.
  - Clear, valid observation dates retained: **299 dates** (2017-02-09 to 2023-12-30).
  - Raw clear observation coverage: **$11.70\%$** ($299 / 2,556\text{ days}$).
  - Raw missingness / cloud-masked rate: **$88.30\%$** ($2,257 / 2,556\text{ days}$).
- **LOCF Feature Imputation & Provenance:**
  - Strictly past-only LOCF forward-fill: applied via `shift(1).ffill()`.
  - LOCF feature availability: **$98.44\%$** ($2,516 / 2,556\text{ days}$); the initial 39 days (2017-01-01 to 2017-02-08) precede the first clear pass and correctly remain unpopulated (NaN).
  - Staleness tracking: $315\text{ days}$ ($12.32\%$) exceed the $45\text{ day}$ staleness threshold (`s2_is_stale = True`), primarily during the persistent cloud-cover monsoon months (June–September) when cloud masking excludes optical observations.
  - New provenance fields: `s2_raw_observation_available`, `s2_observation_source_date`, `s2_days_since_last_valid_observation`, and `s2_is_stale`.

---

### 2.4 ISRIC SoilGrids v2.0
- **Acquisitions:**
  - 32 GeoTIFF rasters covering all 8 properties across 4 depth intervals ($0–5\text{ cm}$, $5–15\text{ cm}$, $15–30\text{ cm}$, $30–60\text{ cm}$) acquired via OGC WCS 2.0.1.
- **Physical Scale Factor Conversions:**
  - `bdod` (Bulk density): Raw DN in $\text{cg/cm}^3$ divided by $100 \implies \text{g/cm}^3$ ($1.490$ to $1.550\text{ g/cm}^3$).
  - `clay`, `sand`, `silt`: Raw DN in $\text{g/kg}$ divided by $10 \implies \%$ ($37.5\%$ to $43.0\%$ clay, $32.8\%$ to $35.9\%$ sand, $24.2\%$ to $26.6\%$ silt).
  - `ocd` (Organic carbon density): Raw DN in $\text{hg/m}^3$ divided by $10 \implies \text{kg/m}^3$ ($21.7\text{ kg/m}^3$ at surface, decreasing pedologically to $8.7\text{ kg/m}^3$ at depth).
  - `wv0010`, `wv0033`, `wv1500`: Raw DN in $10 \times \text{cm}^3/\text{dm}^3$ divided by $1,000 \implies \text{m}^3/\text{m}^3$ volumetric water content ($0.177$ to $0.358\text{ m}^3/\text{m}^3$).
- **Mass Balance Texture Closure:**
  - $0–5\text{ cm}$: $37.5\% + 35.9\% + 26.6\% = \mathbf{100.00\%}$
  - $5–15\text{ cm}$: $39.6\% + 34.3\% + 26.1\% = \mathbf{100.00\%}$
  - $15–30\text{ cm}$: $43.0\% + 32.8\% + 24.2\% = \mathbf{100.00\%}$
  - $30–60\text{ cm}$: $38.8\% + 34.7\% + 26.5\% = \mathbf{100.00\%}$
  - Closure error is exactly $0.00\%$ across all 4 depth intervals.
- **Suction Hierarchy & Derived Pedotransfer Features:**
  - Strict suction hierarchy holds across all layers: $\theta_{1500\text{kPa}} < \theta_{33\text{kPa}} < \theta_{10\text{kPa}}$.
  - Derived pedotransfer hydraulic properties explicitly constructed and distinguished:
    - Field Capacity: $\theta_{FC} = \theta_{33\text{kPa}}$ ($0.301$ to $0.314\text{ m}^3/\text{m}^3$).
    - Permanent Wilting Point: $\theta_{PWP} = \theta_{1500\text{kPa}}$ ($0.177$ to $0.208\text{ m}^3/\text{m}^3$).
    - Available Water Capacity: $AWC = \theta_{FC} - \theta_{PWP}$ ($0.1060$ to $0.1300\text{ m}^3/\text{m}^3$, characteristic of vertic clay-loam soils).
    - Rapid Gravitational Drainage Pore Volume: $\Delta\theta_{drain} = \theta_{10\text{kPa}} - \theta_{33\text{kPa}}$ ($0.0420$ to $0.0550\text{ m}^3/\text{m}^3$).

---

### 2.5 ECMWF ERA5-Land Reanalysis
- **Completeness & Timestamps:**
  - 7 calendar years (2017 to 2023), including 2020 leap year ($366\text{ days}$).
  - Exactly 2,556 daily epochs.
  - Exactly 61,344 hourly timesteps ($2,556 \times 24$). Zero missing hours, zero duplicate timestamps, zero irregular intervals.
- **Physical Aggregation & Units:**
  - 2m Air Temperature: ${}^\circ\text{C}$ (Daily mean, min, max; mean range $[15.8, 36.4]{}^\circ\text{C}$).
  - 2m Dewpoint: ${}^\circ\text{C}$ (Daily mean range $[-2.1, 24.3]{}^\circ\text{C}$).
  - Vapor Pressure Deficit (VPD): $\text{kPa}$ (Tetens formulation; range $[0.08, 4.21]\text{ kPa}$).
  - Precipitation: $\text{mm}$ (Hourly sum; max daily rainfall $125.8\text{ mm}$).
  - Shortwave Solar Radiation: $\text{MJ/m}^2$ ($\sum W/m^2 \times 3600 / 10^6$; range $[4.12, 29.85]\text{ MJ/m}^2$).
  - 10m Wind: $\text{m/s}$ (Vector components $u_{10}, v_{10}$ and scalar speed).
- **Strict Leakage Prevention & Deep Soil Moisture Verification:**
  - Every antecedent feature (`precip_lag_1d`, `precip_roll_sum_*`, `temp_roll_mean_*`, `vpd_roll_mean_*`, `solar_roll_mean_*`) uses `shift(1)`.
  - **Zero ERA5-Land deep soil moisture variables (`swvl1`, `swvl2`, `swvl3`, `swvl4`) are present in the feature matrix.**

---

### 2.6 NASA SMAP Enhanced L3
- **CMR Inventory & Authentication Status:**
  - Granule search on NASA Earthdata CMR (`SPL3SMP_E.006`) confirmed granule availability over Pune coordinates.
  - Raw HDF5/AppEEARS access requires authenticated NASA Earthdata credentials (`.netrc`).
  - Current status: **`AWAITING_AUTH`**.
- **Data Integrity Preservation:**
  - In compliance with project guidelines ("Do not create synthetic SMAP observations or replace them with SMAP L4"):
    - `smap_raw_observation_available = False` across all 2,556 rows.
    - `smap_has_valid_retrieval = False` across all 2,556 rows.
    - `smap_is_stale = True` across all 2,556 rows.
    - All feature columns (`smap_sm_daily_mean_m3_m3`, lags, rolls) are strictly preserved as unpopulated `NaN`.

---

## 3. Issues Discovered During Audit

1. **Elevation Merge Overwrite in Static Feature Table:**
   - *Discovery:* When `pipeline.py` merged SoilGrids features (`df_sg`) with DEM features (`df_dem`), `df_sg` had a hardcoded default field `elevation_m = 560.0`, while `df_dem`'s measured Copernicus DEM elevation (`591.58 m`) was dropped via `df_dem.drop(columns=[..., 'elevation_m'])`.
   - *Consequence:* The static feature CSV recorded $560.0\text{ m}$ in `elevation_m` instead of the extracted Copernicus DEM measurement, masking the true physical terrain elevation.
   - *Severity:* High (data integrity bug violating the rule: "Do not force the DEM value to 560 m").

2. **Absence of Standard Observation Provenance Columns:**
   - *Discovery:* The Phase 2B dataset tracked staleness boolean flags, but lacked standard provenance timestamps (`observation_source_date`), standard raw observation flags (`raw_observation_available`), and standardized staleness distance columns (`days_since_last_valid_observation`).
   - *Consequence:* Downstream consumers could not trace which historical satellite pass generated any forward-filled LOCF observation.
   - *Severity:* Medium (provenance and reproducibility limitation).

3. **Ambiguity Between Downloaded SoilGrids Attributes and Derived Hydraulics:**
   - *Discovery:* While water retention values at $-10\text{ kPa}$, $-33\text{ kPa}$, and $-1500\text{ kPa}$ were extracted, key agronomic parameters (Field Capacity, Wilting Point, Available Water Capacity) were not explicitly distinguished as derived pedotransfer features.
   - *Severity:* Low (clarity and agronomic interpretability).

4. **Manifest Schema Gaps:**
   - *Discovery:* The Phase 2B manifest recorded file size, SHA-256 hash, and CRS, but omitted standard collection identifiers, temporal coverage bounds, and download query URLs.
   - *Severity:* Low (metadata completeness).

---

## 4. Corrections Made

1. **Fixed DEM Elevation Retention in Static Feature Pipeline:**
   - Removed `elevation_m = BENCHMARK_ELEVATION_M` from `SoilGridsAdapter`.
   - Updated `MaharashtraEnvironmentalPipeline` to preserve the extracted Copernicus DEM measurement ($591.58\text{ m}$) as `elevation_m`.
   - Added `benchmark_elevation_m` ($560.0\text{ m}$), `elevation_diff_benchmark_m` ($+31.58\text{ m}$), `subpixel_bilinear_elevation_m` ($590.64\text{ m}$), and `independent_srtm_elevation_m` ($590.0\text{ m}$) to the static feature table.
   - Added geodetic metadata: `dem_pixel_type = "RasterPixelIsPoint"` (Tag 34735 GeoKey 1025).

2. **Added Complete Satellite Provenance Fields:**
   - Implemented `s1_raw_observation_available` and `s2_raw_observation_available` (boolean).
   - Implemented `s1_observation_source_date` and `s2_observation_source_date` (ISO `YYYY-MM-DD` date string tracing the origin observation).
   - Implemented `s1_days_since_last_valid_observation` and `s2_days_since_last_valid_observation` (exact elapsed calendar days).
   - Implemented matching unpopulated schema for SMAP (`smap_raw_observation_available`, `smap_observation_source_date`, etc.).
   - Preserved backwards-compatible column names (`s1_has_valid_observation`, `s1_days_since_valid_obs`).

3. **Constructed Explicit Derived Hydraulic Features:**
   - Added `derived_field_capacity_{depth}` ($\theta_{33\text{kPa}}$ in $\text{m}^3/\text{m}^3$).
   - Added `derived_wilting_point_{depth}` ($\theta_{1500\text{kPa}}$ in $\text{m}^3/\text{m}^3$).
   - Added `derived_awc_{depth}` ($\theta_{33\text{kPa}} - \theta_{1500\text{kPa}}$ in $\text{m}^3/\text{m}^3$).
   - Added `derived_drainable_porosity_{depth}` ($\theta_{10\text{kPa}} - \theta_{33\text{kPa}}$ in $\text{m}^3/\text{m}^3$).
   - Added `soilgrids_texture_sum_{depth}` mass-balance check ($100.00\%$).

4. **Hardened Acquisition Manifest:**
   - Updated `BaseEnvironmentalAdapter.create_manifest_record` to include:
     - `collection_identifier`
     - `temporal_coverage`
     - `download_url_or_id`
     - `processing_version` (`Phase 2C (Data Integrity Audited)`)
   - Regenerated all 43 manifest records with cryptographic SHA-256 hashes.

5. **Created Independent Phase 2C Regression Test Suite:**
   - Authored `tests/test_maharashtra_phase2c_integrity.py` with 9 dedicated test cases.
   - Verified that all 105 tests across the entire repository pass with zero errors.

---

## 5. Before-and-After Metrics

| Metric / Dimension | Phase 2B (Before Audit) | Phase 2C (After Audit) | Audit Status |
| :--- | :---: | :---: | :---: |
| **Static Features Column Count** | 83 columns | **110 columns** | Enhanced with derived hydraulics & DEM audit fields |
| **Daily Features Column Count** | 62 columns | **71 columns** | Enhanced with observation source dates & standard flags |
| **Recorded Static Elevation (`elevation_m`)** | $560.0\text{ m}$ (Benchmark overwrite) | **$591.58\text{ m}$ (True Copernicus DEM)** | Corrected |
| **Subpixel Bilinear Elevation** | Not recorded | **$590.64\text{ m}$ AMSL** | Added |
| **Independent SRTM Elevation** | Not recorded | **$590.0\text{ m}$ AMSL** | Added |
| **DEM Discrepancy Documentation** | Not documented in schema | **Explicitly documented in schema** | Corrected |
| **S1 Raw Observation Coverage** | Reported as 175 obs | **$6.85\%$ ($93.15\%$ raw missingness)** | Explicitly separated from LOCF |
| **S1 Imputed LOCF Coverage** | Conflated with obs | **$99.69\%$ ($164\text{ days}$ stale)** | Causal provenance verified |
| **S1 Observation Source Date** | Missing | **`s1_observation_source_date`** | Traceability established |
| **S2 Raw Clear Coverage** | Reported as 299 obs | **$11.70\%$ ($88.30\%$ raw missingness)** | Explicitly separated from LOCF |
| **S2 Imputed LOCF Coverage** | Conflated with obs | **$98.44\%$ ($315\text{ days}$ stale)** | Causal provenance verified |
| **S2 Observation Source Date** | Missing | **`s2_observation_source_date`** | Traceability established |
| **SoilGrids Mass Balance Check** | Checked in tests only | **Explicit column `soilgrids_texture_sum_*` ($100.00\%$)** | Verified |
| **Derived Hydraulic Properties** | Not computed | **`derived_awc_*`, `derived_field_capacity_*`, etc.** | Added |
| **ERA5-Land Hourly Completeness** | $61,344 / 61,344$ ($100\%$) | **$61,344 / 61,344$ ($100\%$, 0 gaps, 0 dups)** | Verified |
| **ERA5 Deep Soil Moisture Ingestion** | 0 columns | **0 columns (Strictly verified)** | Confirmed clean |
| **SMAP Status** | Awaiting credentials | **`AWAITING_AUTH` (0 synthetic data, 0 SMAP L4)** | Confirmed clean |
| **Manifest Audit Metadata** | Basic 12 fields | **Full collection ID, URL, temporal coverage, SHA-256** | Hardened |
| **Repository Test Suite** | 96 tests passing | **105 tests passing** (9 new regression tests) | 100% Green |

---

## 6. Remaining Limitations

1. **COSMOS-Pune In-Situ Target Observations Remain Unavailable:**
   - Ground-truth soil moisture measurements from the IITM-Pune COSMOS cosmic-ray neutron probe remain locked behind institutional access controls.
   - Environmental predictors are fully assembled and audited, but model training for Maharashtra remains strictly blocked pending in-situ data receipt.
2. **Single-Station Pilot Limitation:**
   - The Pune dataset represents a single geographic point ($18.5372^\circ\text{ N}, 73.8051^\circ\text{ E}$).
   - In compliance with strict project rules, **this dataset must never be claimed as representing Maharashtra-wide coverage**.
   - Spatial expansion across Maharashtra will require executing the adapter pipeline across the distributed network of agro-climatic stations once ground-truth targets are secured.
3. **Monsoon Optical Satellite Attenuation:**
   - Persistent heavy cloud cover during the Southwest Monsoon (June–September) causes Sentinel-2 optical data gaps up to 60–90 days.
   - The $45\text{ day}$ staleness flag (`s2_is_stale`) correctly identifies these periods, requiring downstream models to rely on microwave radar (Sentinel-1 SAR) and antecedent weather memory during peak monsoon.
4. **SMAP L3 Awaiting Authentication:**
   - SMAP radiometer observations remain in an `AWAITING_AUTH` state pending provision of NASA Earthdata credentials (`.netrc`).

---

## 7. Final Decision: CONDITIONAL GO

### Verdict: **CONDITIONAL GO**

#### Rationale:
1. **Scientific Integrity Verified:** All environmental data extraction bugs (including the DEM elevation merge overwrite) have been corrected and verified against independent datasets.
2. **Strict Provenance & Temporal Safety:** Zero future observation leakage exists; all memory features use past-only `shift(1)`; raw satellite missingness is rigorously distinguished from imputed LOCF features; and observation source dates are recorded.
3. **Zero Contamination:** No ground-sensor targets were fabricated, no SMAP L4 or ERA5-Land deep soil moisture variables were ingested, and Alabama Model 1 models, artifacts, and evaluation baselines remain completely untouched.
4. **105/105 Passing Tests:** The full test suite confirms compliance with all architectural and scientific constraints.

#### Condition for Proceeding to Model 2 Training:
- **Condition:** Environmental feature tables (`daily_environmental_features.csv` and `static_environmental_features.csv`) are approved for inference and predictor preparation. However, **Model training for Maharashtra cannot begin until official COSMOS-India ground-truth observations are acquired and cryptographically verified.**

