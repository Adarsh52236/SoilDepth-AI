# SoilDepth-AI — SoilGrids Batch Dataset Audit & Verification Report

**Station:** `AAMU-JTG` (SCAN network, Madison County, Alabama, USA)  
**Coordinates:** Latitude `34.78534° N`, Longitude `-86.55906° W`, Elevation `241.0 m`  
**Dataset Provider:** ISRIC — World Soil Information ([SoilGrids250m v2.0](https://soilgrids.org/))  
**Audit Date:** 2026-10-26  
**Auditor:** Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI  

---

## 1. Executive Summary & Verification Scope

All planned SoilGrids layers for the `AAMU-JTG` pilot station have been downloaded manually via the official ISRIC portal and subjected to a comprehensive batch audit.

### Layer Accounting Summary
- **Expected Combinations:** **32** (8 physical/hydraulic properties $\times$ 4 standardized GlobalSoilMap depth intervals)
- **Discovered GeoTIFF Rasters:** **32** ($100\%$)
- **Verified Valid Layers:** **32** ($100\%$)
- **Missing Layers:** **0**
- **Ambiguous / Unidentified Files:** **0**
- **Corrupt or Unreadable Rasters:** **0**
- **Grid Alignment Consistency:** **100%** (All 32 layers share an identical $885 \times 837$ grid, identical bounding box, and identical station pixel coordinate `col=453, row=413`).

---

## 2. Master Verification Ledger (All 32 Expected Layers)

| Property | Depth (cm) | Value Type | Filename | Size (B) | SHA-256 Checksum | Station Raw | Scale Factor | Station Scaled Physical Value | Verification Status |
| :--- | :---: | :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| `bulk_density` | `0-5` | `mean` | `bdod_mean_0-5cm.tif` | 398,685 | `1ced2f6b561e618596c9adf0d809a0c5d8ad4d6e49a500b885c3caab7aa24d09` | 130 | $\div 100$ | **$1.30\text{ g}/\text{cm}^3$** | **VERIFIED** |
| `bulk_density` | `5-15` | `mean` | `bdod_mean_5-15cm.tif` | 436,596 | `c5904ea2c8d9d659bbb96dfd1faddac6f128211dad6b10a504b911f350394566` | 149 | $\div 100$ | **$1.49\text{ g}/\text{cm}^3$** | **VERIFIED** |
| `bulk_density` | `15-30` | `mean` | `bdod_mean_15-30cm.tif` | 376,400 | `61df05c9ffd2a94f0d2853f64c8a01bc3c4709bf1ed490eb83b51e3554057a5c` | 155 | $\div 100$ | **$1.55\text{ g}/\text{cm}^3$** | **VERIFIED** |
| `bulk_density` | `30-60` | `mean` | `bdod_mean_30-60cm.tif` | 328,536 | `e10835dcdf1953e67ef3f57155923d5efc291a60e323a79645827c8c2ea5ad3e` | 158 | $\div 100$ | **$1.58\text{ g}/\text{cm}^3$** | **VERIFIED** |
| `clay` | `0-5` | `mean` | `clay_mean_0-5cm.tif` | 655,456 | `910e0dcac69195e79310c59e61f7db73b0cd943d1bfcd16b1d1ae02e7aa8963c` | 247 | $\div 10$ | **$24.70\%$** | **VERIFIED** |
| `clay` | `5-15` | `mean` | `clay_mean_5-15cm.tif` | 659,193 | `9be70d2a69291fcf563ab3e17a2c99eb07751b1ca0e32abb3e8739fa70dc3359` | 273 | $\div 10$ | **$27.30\%$** | **VERIFIED** |
| `clay` | `15-30` | `mean` | `clay_mean_15-30cm.tif` | 677,960 | `cb83bd12a79b5448706de22e762632fb06235ad924060b08244d3de2bcb17396` | 328 | $\div 10$ | **$32.80\%$** | **VERIFIED** |
| `clay` | `30-60` | `mean` | `clay_mean_30-60cm.tif` | 702,354 | `cf4398bd2da10df5f01094c5bc80ca09706693601d9e06dabbacecac88a3d66f` | 339 | $\div 10$ | **$33.90\%$** | **VERIFIED** |
| `sand` | `0-5` | `mean` | `sand_mean_0-5cm.tif` | 658,251 | `7b40c08fbf464e6361f7c8919da731753603a27337362f8a8ec83fec04ed2dee` | 174 | $\div 10$ | **$17.40\%$** | **VERIFIED** |
| `sand` | `5-15` | `mean` | `sand_mean_5-15cm.tif` | 655,823 | `96b1a0143acc4557d6b541244bc831ef81d0d44759d9a38fdf45b915db2c14a8` | 164 | $\div 10$ | **$16.40\%$** | **VERIFIED** |
| `sand` | `15-30` | `mean` | `sand_mean_15-30cm.tif` | 643,350 | `410b117c4c9a85ecf0ee02bf8a5f78520240d4ffcde5f1a063364e7c2d08fe1f` | 149 | $\div 10$ | **$14.90\%$** | **VERIFIED** |
| `sand` | `30-60` | `mean` | `sand_mean_30-60cm.tif` | 643,812 | `05d1e74191606fd766428607e5125ce6f27defa9e4f31b2828a42613df4b1ca1` | 151 | $\div 10$ | **$15.10\%$** | **VERIFIED** |
| `silt` | `0-5` | `mean` | `silt_mean_0-5cm.tif` | 707,105 | `baf3ca7857a918a50adba25690bbf10f1b381d8d801f5d497b25317ff750adad` | 579 | $\div 10$ | **$57.90\%$** | **VERIFIED** |
| `silt` | `5-15` | `mean` | `silt_mean_5-15cm.tif` | 706,043 | `683a1ade983a9abeaca2f8cec2f12a128afae429afeafac4240cdd19911a403c` | 563 | $\div 10$ | **$56.30\%$** | **VERIFIED** |
| `silt` | `15-30` | `mean` | `silt_mean_15-30cm.tif` | 707,165 | `602d1844b2c1474ec491763138b30f81d1e434f073fa8ff112cf2ca8bb90ea88` | 523 | $\div 10$ | **$52.30\%$** | **VERIFIED** |
| `silt` | `30-60` | `mean` | `silt_mean_30-60cm.tif` | 710,381 | `15fae0051184ff1656ca89e246fc1d51a6697b0559eb4ee82811a2f073b64b18` | 510 | $\div 10$ | **$51.00\%$** | **VERIFIED** |
| `organic_carbon_density` | `0-5` | `mean` | `ocd_mean_0-5cm.tif` | 665,310 | `47d2ce87e0743b177d636dbd0879664b971a805f1593c66f779774619da0cbe1` | 382 | $\div 10$ | **$38.20\text{ kg}/\text{m}^3$** | **VERIFIED** |
| `organic_carbon_density` | `5-15` | `mean` | `ocd_mean_5-15cm.tif` | 643,684 | `25bc16e911277a83d726b0144f8087799d1fa98d89cb801ef462705cc865aa4e` | 211 | $\div 10$ | **$21.10\text{ kg}/\text{m}^3$** | **VERIFIED** |
| `organic_carbon_density` | `15-30` | `mean` | `ocd_mean_15-30cm.tif` | 600,030 | `f287a998bb3628e9324b17f541e21b71177ae8eb71d22e033e0310214c7760eb` | 132 | $\div 10$ | **$13.20\text{ kg}/\text{m}^3$** | **VERIFIED** |
| `organic_carbon_density` | `30-60` | `mean` | `ocd_mean_30-60cm.tif` | 523,214 | `f10d9313ea99d0e14a1a069ba5f0612c6a469956f4d3c90731fa6bfe90e7939c` | 73 | $\div 10$ | **$7.30\text{ kg}/\text{m}^3$** | **VERIFIED** |
| `water_content_10kPa` | `0-5` | `mean` | `wv0010_mean_0-5cm.tif` | 489,522 | `b99d5ca4ba16e1e779a1d1246db2bf1973ffb6170624d775e533e46c7d2427a7` | 390 | $\div 10$ | **$39.00\text{ vol}\%$** ($0.390\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_10kPa` | `5-15` | `mean` | `wv0010_mean_5-15cm.tif` | 488,888 | `1321ee7998bc43db8eb697072ebf4a66a3d6f1a8c3d9b4db74c7e6e5ddae4068` | 384 | $\div 10$ | **$38.40\text{ vol}\%$** ($0.384\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_10kPa` | `15-30` | `mean` | `wv0010_mean_15-30cm.tif` | 491,553 | `810484e555989104c952003c4013143c16260e1d5113d5084920275c911d0442` | 380 | $\div 10$ | **$38.00\text{ vol}\%$** ($0.380\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_10kPa` | `30-60` | `mean` | `wv0010_mean_30-60cm.tif` | 504,885 | `2f9f1225574ccfcdd1d9045bdf44cf12fe85e86d75c5e854fa16b17a12b3ce62` | 383 | $\div 10$ | **$38.30\text{ vol}\%$** ($0.383\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_33kPa` | `0-5` | `mean` | `wv0033_mean_0-5cm.tif` | 535,243 | `7a13d7195a6fc5b75fcfa17eb527df474bdf7fa15f7956ff7a03006cb524f0c4` | 337 | $\div 10$ | **$33.70\text{ vol}\%$** ($0.337\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_33kPa` | `5-15` | `mean` | `wv0033_mean_5-15cm.tif` | 530,282 | `e4fc108d3ff96d65377f0951c3d1f1484ff3526aa87d609ee59e2170ccf0be52` | 338 | $\div 10$ | **$33.80\text{ vol}\%$** ($0.338\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_33kPa` | `15-30` | `mean` | `wv0033_mean_15-30cm.tif` | 531,293 | `1b138fe97df058b7625cb27bc9eb8d58a58a74ec4e3d3dd547161e1b1233d45e` | 338 | $\div 10$ | **$33.80\text{ vol}\%$** ($0.338\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_33kPa` | `30-60` | `mean` | `wv0033_mean_30-60cm.tif` | 521,518 | `13247c4583b4b88fc7c0aa782725fa82496d0da300cf9d75b31df6e1076f6a73` | 344 | $\div 10$ | **$34.40\text{ vol}\%$** ($0.344\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_1500kPa` | `0-5` | `mean` | `wv1500_mean_0-5cm.tif` | 527,057 | `ae0656157077aee21e05d0cbcc5f3b730fdf1d2e1bb4930b80897f1f728fae92` | 126 | $\div 10$ | **$12.60\text{ vol}\%$** ($0.126\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_1500kPa` | `5-15` | `mean` | `wv1500_mean_5-15cm.tif` | 528,270 | `a4e98f73a3c9e6d091e9f1a26027a412c98d63351ec3aa488ff96180370d0a7a` | 126 | $\div 10$ | **$12.60\text{ vol}\%$** ($0.126\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_1500kPa` | `15-30` | `mean` | `wv1500_mean_15-30cm.tif` | 531,511 | `16ee179f8ea75c40134440fa619d0092fae20e3d64284b3ca660e504c57c4c37` | 154 | $\div 10$ | **$15.40\text{ vol}\%$** ($0.154\text{ m}^3/\text{m}^3$) | **VERIFIED** |
| `water_content_1500kPa` | `30-60` | `mean` | `wv1500_mean_30-60cm.tif` | 552,620 | `74a7ca33bf13df13ca01f40954b43c44566c3ae06d1dbb8feaa1a851d9d95f84` | 200 | $\div 10$ | **$20.00\text{ vol}\%$** ($0.200\text{ m}^3/\text{m}^3$) | **VERIFIED** |

---

## 3. Spatial Reference, Grid Alignment & Coverage Verification

All 32 GeoTIFF files were inspected tag-by-tag. The geospatial metadata is strictly consistent across every single layer:

- **Dimensions:** Width = `885 columns`, Height = `837 rows` ($740,745$ total pixels), `1 band`
- **Data Type:** `Int16` (16-bit signed integer, `SampleFormat=2`, `BitsPerSample=16`)
- **Tiling & Compression:** Tiled $256 \times 256$, Deflate compression (`Compression=8`)
- **Coordinate Reference System:** `EPSG:4326` (Geographic WGS84)
  - `GeoKeyDirectoryTag`: ModelTypeGeographic (2), RasterPixelIsArea (1), GeographicTypeGeoKey (4326)
  - `GeoAsciiParamsTag`: `WGS 84|`
- **Geographic Extent:**
  - **West:** `-87.58210° W`
  - **East:** `-85.58210° W` (exact $2.0^\circ$ span)
  - **South:** `33.77130° N`
  - **North:** `35.77130° N` (exact $2.0^\circ$ span)
- **Pixel Resolution:**
  - $\Delta \text{Longitude} = 0.002259887^\circ$ ($\sim 206.6\text{ m}$ at $34.785^\circ\text{ N}$)
  - $\Delta \text{Latitude} = 0.002389486^\circ$ ($\sim 265.1\text{ m}$)
  - Consistent with the native SoilGrids 250 m product projected to geographic WGS84.
- **Station Coverage:**
  - Station Coordinates: Latitude `34.78534° N`, Longitude `-86.55906° W`
  - Falls inside extent: $-87.58210 \le -86.55906 \le -85.58210$ and $33.77130 \le 34.78534 \le 35.77130$.
  - Exact Station Pixel: **`Column = 453`, `Row = 413`** across all 32 rasters.

---

## 4. Physical Plausibility & Hydrological Consistency

### 4.1 Soil Texture Mass Balance ($\text{Clay} + \text{Sand} + \text{Silt}$)
Authoritative soil physics requires that the textural components sum to $100\%$:

| Depth Interval | Clay ($\%$) | Sand ($\%$) | Silt ($\%$) | Sum ($\%$) | USDA Textural Class |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **0–5 cm** | $24.70\%$ | $17.40\%$ | $57.90\%$ | **$100.00\%$** | **Silt Loam** |
| **5–15 cm** | $27.30\%$ | $16.40\%$ | $56.30\%$ | **$100.00\%$** | **Silty Clay Loam** |
| **15–30 cm** | $32.80\%$ | $14.90\%$ | $52.30\%$ | **$100.00\%$** | **Silty Clay Loam** |
| **30–60 cm** | $33.90\%$ | $15.10\%$ | $51.00\%$ | **$100.00\%$** | **Silty Clay Loam** |

**Finding:** The textural mass balance is mathematically exact ($100.00\%$) across all four depth intervals at the station. The texture transitions smoothly from silt loam in the topsoil to silty clay loam in the subsoil, matching the USDA Soil Survey for the Decatur and Cumberland silt loam series in Madison County, Alabama.

### 4.2 Vertical Compaction & Organic Carbon Decay
- **Bulk Density:** Monotonically increases with depth:
  $$1.30\text{ g}/\text{cm}^3 \longrightarrow 1.49\text{ g}/\text{cm}^3 \longrightarrow 1.55\text{ g}/\text{cm}^3 \longrightarrow 1.58\text{ g}/\text{cm}^3$$
- **Organic Carbon Density:** Monotonically decays with depth:
  $$38.20\text{ kg}/\text{m}^3 \longrightarrow 21.10\text{ kg}/\text{m}^3 \longrightarrow 13.20\text{ kg}/\text{m}^3 \longrightarrow 7.30\text{ kg}/\text{m}^3$$
- **Plausibility:** The reduction in organic matter and increase in overburden compaction creates a realistic physical vertical profile.

### 4.3 Water Retention Characteristic Hierarchy
Water retention theory requires that volumetric water content decreases monotonically as suction tension increases ($\theta_{-1500\text{ kPa}} < \theta_{-33\text{ kPa}} < \theta_{-10\text{ kPa}}$):

| Depth Interval | $\theta_{-1500\text{ kPa}}$ (Wilting Point) | $\theta_{-33\text{ kPa}}$ (Field Capacity) | $\theta_{-10\text{ kPa}}$ (Rapid Drainage) | Available Water Capacity ($\text{AWC}$) | Suction Hierarchy Satisfied? |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **0–5 cm** | $12.60\text{ vol}\%$ ($0.126\text{ m}^3/\text{m}^3$) | $33.70\text{ vol}\%$ ($0.337\text{ m}^3/\text{m}^3$) | $39.00\text{ vol}\%$ ($0.390\text{ m}^3/\text{m}^3$) | **$21.10\text{ vol}\%$** ($0.211\text{ m}^3/\text{m}^3$) | **YES ($\theta_{1500} < \theta_{33} < \theta_{10}$)** |
| **5–15 cm** | $12.60\text{ vol}\%$ ($0.126\text{ m}^3/\text{m}^3$) | $33.80\text{ vol}\%$ ($0.338\text{ m}^3/\text{m}^3$) | $38.40\text{ vol}\%$ ($0.384\text{ m}^3/\text{m}^3$) | **$21.20\text{ vol}\%$** ($0.212\text{ m}^3/\text{m}^3$) | **YES ($\theta_{1500} < \theta_{33} < \theta_{10}$)** |
| **15–30 cm** | $15.40\text{ vol}\%$ ($0.154\text{ m}^3/\text{m}^3$) | $33.80\text{ vol}\%$ ($0.338\text{ m}^3/\text{m}^3$) | $38.00\text{ vol}\%$ ($0.380\text{ m}^3/\text{m}^3$) | **$18.40\text{ vol}\%$** ($0.184\text{ m}^3/\text{m}^3$) | **YES ($\theta_{1500} < \theta_{33} < \theta_{10}$)** |
| **30–60 cm** | $20.00\text{ vol}\%$ ($0.200\text{ m}^3/\text{m}^3$) | $34.40\text{ vol}\%$ ($0.344\text{ m}^3/\text{m}^3$) | $38.30\text{ vol}\%$ ($0.383\text{ m}^3/\text{m}^3$) | **$14.40\text{ vol}\%$** ($0.144\text{ m}^3/\text{m}^3$) | **YES ($\theta_{1500} < \theta_{33} < \theta_{10}$)** |

**Finding:** The physical suction hierarchy holds strictly at all four depth intervals without any inversion. As subsoil clay content increases, the permanent wilting point $\theta_{-1500\text{ kPa}}$ rises from $12.60\%$ to $20.00\%$, which reduces available water capacity from $21.10\%$ to $14.40\%$, exactly as expected in clay-enriched subsoils.

---

## 5. Discrepancies & Downstream Preprocessing Considerations

| Finding ID | Observation | Scope | Impact | Recommended Handling in Preprocessor |
| :---: | :--- | :---: | :---: | :--- |
| **DISC-01** | Water body NoData encoding discrepancy | Tile-wide (28,766 pixels / $3.88\%$) | None at station (`col 453, row 413` is terrestrial) | In 31 of 32 rasters, open water bodies (e.g. Tennessee River) are masked as `0`. In `wv0010_mean_5-15cm.tif`, the water mask is encoded as `-32768`. Preprocessing adapters must filter `pixel <= 0 or pixel == -32768` when extracting spatial windows. |
| **DISC-02** | Static property representation | Scientific Methodology | Educational | SoilGrids properties are stationary spatial predictors. They provide baseline pedological boundary conditions but do not substitute for dynamic soil moisture observations. |
| **DISC-03** | Layer-average vs point-sensor proxy | Architectural | Pipeline Design | SoilGrids depth intervals (`0-5`, `5-15`, `15-30`, `30-60 cm`) represent integrated horizon averages, whereas SCAN sensors are point sensors at $5.08$, $10.16$, $20.32$, and $50.80\text{ cm}$. In preprocessing, preserve them as distinct features rather than assuming direct equivalence. |

---

## 6. Readiness Recommendation

> [!NOTE]
> **READINESS DECISION: READY FOR PREPROCESSING**  
> All 32 planned SoilGrids rasters are verified, cryptographically cataloged, physically sound, and spatially aligned. No missing, corrupted, or ambiguous layers remain. The dataset is approved for adapter and feature extraction development.
