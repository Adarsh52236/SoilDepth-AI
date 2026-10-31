# SoilDepth-AI — SoilGrids File Inspection Report

**Layer:** `bulk_density` (`bdod`)  
**Depth Interval:** `5–15 cm`  
**Estimator:** `mean`  
**Station:** `AAMU-JTG` (SCAN network, Alabama, USA)  
**Station Reference Coordinates:** Latitude `34.78534° N`, Longitude `-86.55906° W`, Elevation `241.0 m`  
**Inspection Date:** 2026-10-26  
**File Inspected:** `dataset/SoilGrids/raw/AAMU-JTG/bulk_density/bdod_mean_5-15cm.tif`  

---

## 1. File Integrity & Physical Metadata

- **Filename:** `bdod_mean_5-15cm.tif`
- **File Path:** `dataset/SoilGrids/raw/AAMU-JTG/bulk_density/bdod_mean_5-15cm.tif`
- **File Size:** `436,596 bytes` ($426.36\text{ KB}$)
- **SHA-256 Checksum:** `c5904ea2c8d9d659bbb96dfd1faddac6f128211dad6b10a504b911f350394566`
- **Format:** GeoTIFF (Tiled: $256 \times 256$, Deflate compression, Horizontal differencing predictor)
- **Data Type:** `Int16` (16-bit signed integer, `SampleFormat=2`, `BitsPerSample=16`)
- **Raster Dimensions:** `885 columns` $\times$ `837 rows` ($740,745$ total pixels)
- **Number of Bands:** 1 (Single channel)
- **Grid Alignment:** Exactly aligns with `bdod_mean_0-5cm.tif` (identical dimensions and pixel grid)

---

## 2. Spatial Reference System & Geographic Extent

- **Coordinate Reference System (CRS):** `EPSG:4326` (Geographic WGS84)
- **Ellipsoid:** WGS84 (Semi-major axis: $6378137.0\text{ m}$, Inverse flattening: $298.257223563$)
- **Upper-Left Origin (Tie Point):** Latitude `35.77130° N`, Longitude `-87.58210° W`
- **Pixel Resolution:**
  - $\Delta \text{Longitude} = 0.002259887^\circ$ ($\sim 206.6\text{ m}$ at $34.785^\circ\text{ N}$)
  - $\Delta \text{Latitude} = 0.002389486^\circ$ ($\sim 265.1\text{ m}$)
  - Resolution is consistent with the standard ISRIC SoilGrids 250 m product projected to WGS84 geographic coordinates.
- **Bounding Box Extent:**
  - **West (Min Longitude):** `-87.58210° W`
  - **East (Max Longitude):** `-85.58210° W` (exact $2.0^\circ$ span)
  - **South (Min Latitude):** `33.77130° N`
  - **North (Max Latitude):** `35.77130° N` (exact $2.0^\circ$ span)
- **Station Coverage Confirmation:**
  - Target Station Coordinates: `(34.78534, -86.55906)`
  - Longitudinal coverage: $-87.58210 \le -86.55906 \le -85.58210$ $\rightarrow$ **Inside extent**
  - Latitudinal coverage: $33.77130 \le 34.78534 \le 35.77130$ $\rightarrow$ **Inside extent**
  - Relative Position: Station falls near the geographic center (`col=453, row=413`).

---

## 3. Data Values & Station Pixel Sampling

- **Raw Value Range:** $[0, 174]$ (Mean across tile: $144.59\text{ cg}/\text{cm}^3$)
- **No-Data Value:** No negative NoData markers ($-9999$ or $-32768$) present in this local clip; all $740,745$ pixels contain valid predictions.
- **Physical Scale Factor:**
  $$\text{Bulk Density } [\text{g}/\text{cm}^3] = \frac{\text{Raw Value } [\text{cg}/\text{cm}^3]}{100}$$
- **Station Pixel Location:** `Column = 453`, `Row = 413`
- **Station Values:**
  - **Raw Value:** `149 cg/cm³`
  - **Scaled Value:** `1.49 g/cm³` ($1490\text{ kg}/\text{m}^3$)
- **$3 \times 3$ Local Neighborhood around Station:**
  ```text
  [1.54  1.54  1.55]
  [1.49  1.49  1.49]
  [1.44  1.45  1.39]  (all values in g/cm³)
  ```

---

## 4. Vertical Profile Comparison & Hydrological Plausibility

Comparing the two verified layers at station `AAMU-JTG`:

| Depth Interval | Soil Horizon Context | Raw Sample (`cg/cm³`) | Scaled Bulk Density (`g/cm³`) | $3 \times 3$ Local Range (`g/cm³`) |
| :--- | :--- | :---: | :---: | :---: |
| **0–5 cm** | Organic-enriched surface layer | `130` | **$1.30\text{ g}/\text{cm}^3$** | $1.21 - 1.34$ |
| **5–15 cm** | Shallow subsurface mineral horizon | `149` | **$1.49\text{ g}/\text{cm}^3$** | $1.39 - 1.55$ |

### Physical Assessment
- Bulk density increases with depth ($1.30 \rightarrow 1.49\text{ g}/\text{cm}^3$).
- This vertical trend aligns with soil pedology: organic matter content declines beneath the surface zone, while overburden pressure and agricultural tillage compaction (plow pan) typically increase bulk density in the 5–15 cm depth interval.
- The value of $1.49\text{ g}/\text{cm}^3$ is within the normal physical range for agricultural silt loam / loam subsurface horizons ($1.35 - 1.60\text{ g}/\text{cm}^3$).
- **No suspicious anomalies or out-of-bounds artifacts detected.**

---

## 5. Verification Verdict

- **File Integrity:** Verified (436,596 bytes, SHA-256 confirmed)
- **Raster Dimensions:** Verified ($885 \times 837$, 1 channel)
- **CRS & Projection:** Verified (`EPSG:4326`, WGS84)
- **Pixel Resolution:** Verified ($\sim 250\text{ m}$)
- **Station Coverage:** Verified (`col=453, row=413`)
- **Sampled Value & Scale:** Verified (`149` $\rightarrow 1.49\text{ g}/\text{cm}^3$)
- **Manifest Status:** Recorded as `downloaded` in [`dataset/SoilGrids/manifests/download_manifest.csv`](../manifests/download_manifest.csv)
