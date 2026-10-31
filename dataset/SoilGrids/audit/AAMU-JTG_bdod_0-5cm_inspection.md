# SoilDepth-AI — SoilGrids File Inspection Report

**Layer:** `bulk_density` (`bdod`)  
**Depth Interval:** `0–5 cm`  
**Estimator:** `mean`  
**Station:** `AAMU-JTG` (SCAN network, Alabama, USA)  
**Station Reference Coordinates:** Latitude `34.78534° N`, Longitude `-86.55906° W`, Elevation `241.0 m`  
**Inspection Date:** 2026-10-26  
**File Inspected:** `dataset/SoilGrids/raw/AAMU-JTG/bulk_density/bdod_mean_0-5cm.tif`  

---

## 1. File Integrity & Physical Metadata

- **Filename:** `bdod_mean_0-5cm.tif`
- **File Path:** `dataset/SoilGrids/raw/AAMU-JTG/bulk_density/bdod_mean_0-5cm.tif`
- **File Size:** `398,685 bytes` ($389.34\text{ KB}$)
- **SHA-256 Checksum:** `1ced2f6b561e618596c9adf0d809a0c5d8ad4d6e49a500b885c3caab7aa24d09`
- **Format:** GeoTIFF (Tiled: $256 \times 256$, Deflate compression, Horizontal differencing predictor)
- **Data Type:** `Int16` (16-bit signed integer, `SampleFormat=2`, `BitsPerSample=16`)
- **Raster Dimensions:** `885 columns` $\times$ `837 rows` ($740,745$ total pixels)
- **Number of Bands:** 1 (Single channel)

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
  - Relative Position: Station falls at approximately the geographic center ($44.6\%$ from south, $51.2\%$ from west).

---

## 3. Data Values & Station Pixel Sampling

- **Raw Value Range:** $[0, 148]$
- **No-Data Value:** No negative NoData markers ($-9999$ or $-32768$) present in this local clip; all $740,745$ pixels contain valid values.
- **Physical Scale Factor:**
  $$\text{Bulk Density } [\text{g}/\text{cm}^3] = \frac{\text{Raw Value } [\text{cg}/\text{cm}^3]}{100}$$
- **Station Pixel Location:** `Column = 453`, `Row = 413`
- **Station Values:**
  - **Raw Value:** `130 cg/cm³`
  - **Scaled Value:** `1.30 g/cm³` ($1300\text{ kg}/\text{m}^3$)
- **$3 \times 3$ Local Neighborhood around Station:**
  ```text
  [1.34  1.34  1.34]
  [1.31  1.30  1.31]
  [1.29  1.26  1.21]  (all values in g/cm³)
  ```
- **Physical Plausibility Check:**
  - Topsoil ($0-5\text{ cm}$) bulk density for agricultural silt loam / grassland is typically $1.15 - 1.45\text{ g}/\text{cm}^3$.
  - The sampled estimate of $1.30\text{ g}/\text{cm}^3$ is completely consistent with realistic soil physical boundaries.

---

## 4. Verification Verdict

- **File Opens Correctly:** Yes
- **Valid Dimensions:** Yes ($885 \times 837$)
- **CRS Verified:** Yes (`EPSG:4326`, WGS 84)
- **Pixel Resolution Verified:** Yes ($\sim 250\text{ m}$)
- **Station Coverage Verified:** Yes (`col=453, row=413`)
- **Data Type & Value Verified:** Yes (`Int16`, raw `130` $\rightarrow 1.30\text{ g}/\text{cm}^3$)
- **Manifest Status:** Updated to `downloaded` in [`dataset/SoilGrids/manifests/download_manifest.csv`](../manifests/download_manifest.csv)
