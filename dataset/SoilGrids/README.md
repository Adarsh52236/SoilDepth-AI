# SoilDepth-AI — SoilGrids Dataset Guide & Storage Architecture

This directory houses static soil physical, chemical, and hydraulic property estimates from **SoilGrids** (ISRIC — World Soil Information) for the **SoilDepth-AI** project.

---

## 1. Directory Structure

Following the established repository architecture:

```text
dataset/SoilGrids/
├── README.md                          # Configuration, specifications, and acquisition guide
├── raw/                               # Destination for original, unmodified SoilGrids manual downloads
│   └── AAMU-JTG/                      # Pilot station raw downloads organized by property
│       ├── bulk_density/              # Fine earth bulk density (bdod)
│       ├── clay/                      # Clay fraction (< 2 µm)
│       ├── sand/                      # Sand fraction (50–2000 µm)
│       ├── silt/                      # Silt fraction (2–50 µm)
│       ├── water_content_10kPa/       # Volumetric water content at -10 kPa (wv0010)
│       ├── water_content_33kPa/       # Volumetric water content at -33 kPa / field capacity (wv0033)
│       ├── water_content_1500kPa/     # Volumetric water content at -1500 kPa / wilting point (wv1500)
│       └── organic_carbon_density/    # Organic carbon density (ocd)
├── manifests/
│   └── download_manifest.csv          # Audit ledger tracking properties, depths, and download states
├── audit/                             # Audit reports generated after raster and tabular verification
└── processed/                         # Harmonized, scaled, and station-extracted static tables
    └── AAMU-JTG/                      # Model-ready edaphic feature tables for AAMU-JTG
```

---

## 2. Dataset Purpose & Role in SoilDepth-AI

SoilDepth-AI combines atmospheric forcing with soil hydraulic characteristics to predict moisture variation throughout the soil profile. 

Soil properties dictate the water retention curve (soil water retention characteristics), hydraulic conductivity, and infiltration capacity:
- **Soil Texture (Clay, Sand, Silt):** Governs pore-size distribution, capillary suction, and permeability.
- **Bulk Density:** Reflects soil compaction, total porosity ($\phi \approx 1 - \rho_b / \rho_s$), and root penetration resistance.
- **Volumetric Water Content at Suction Tensions:**
  - **$-10\text{ kPa}$ (`wv0010`):** Rapid gravitational drainage boundary; field capacity proxy for coarse-textured soils.
  - **$-33\text{ kPa}$ (`wv0033`):** Standard agricultural field capacity ($\theta_{\text{fc}}$); upper limit of plant-available water.
  - **$-1500\text{ kPa}$ (`wv1500`):** Permanent wilting point ($\theta_{\text{pwp}}$); lower boundary of plant-accessible moisture.
  - **Plant-Available Water Capacity (AWC):** $\text{AWC} = \theta_{\text{fc}} - \theta_{\text{pwp}}$.
- **Organic Carbon Density:** Governs soil structure, aggregate stability, and organic matter water retention.

> [!IMPORTANT]
> **Static Property Estimates vs Time-Varying Observations:**  
> SoilGrids values are **static, spatially mapped edaphic estimates** produced by machine learning ensembles from legacy soil profiles and environmental covariates. They **do not vary over time** and are **not dynamic soil-moisture observations**. Dynamic time-varying ground truth is provided exclusively by the ISMN SCAN point-sensor observations.

---

## 3. Pilot Station Reference Context: `AAMU-JTG`

All initial downloads are centered on pilot station **AAMU-JTG**:

- **Station ID:** `AAMU-JTG` (USDA-NRCS SCAN network)
- **Location:** Winfred Thomas Agricultural Research Station, Hazel Green, Madison County, Alabama, USA
- **Target Coordinates:** Latitude `34.78534° N`, Longitude `-86.55906° W`
- **Coordinate Reference System:** WGS84 (`EPSG:4326`)
- **Benchmark Elevation:** `241.0 m` above sea level
- **Dominant Soil Class (HWSD baseline):** Silt Loam / Sandy Clay Loam

---

## 4. Planned Properties & Depth Intervals

### 4.1 Target Soil Properties

| Property Directory | SoilGrids Identifier | Description | Native Raw Unit | Integer Scale Factor | Standard Physical Unit |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `bulk_density/` | `bdod` | Bulk density of fine earth fraction ($< 2\text{ mm}$) | $\text{cg}/\text{cm}^3$ | $100$ | $\text{g}/\text{cm}^3$ or $\text{kg}/\text{m}^3$ |
| `clay/` | `clay` | Clay fraction (particles $< 2\text{ \mu m}$) | $\text{g}/\text{kg}$ | $10$ | $\%$ (percentage by weight) |
| `sand/` | `sand` | Sand fraction (particles $50 - 2000\text{ \mu m}$) | $\text{g}/\text{kg}$ | $10$ | $\%$ (percentage by weight) |
| `silt/` | `silt` | Silt fraction (particles $2 - 50\text{ \mu m}$) | $\text{g}/\text{kg}$ | $10$ | $\%$ (percentage by weight) |
| `water_content_10kPa/` | `wv0010` | Volumetric water content at $-10\text{ kPa}$ suction | $10 \times \text{cm}^3/\text{dm}^3$ | $10$ | $\text{vol}\%$ (or $\times 0.001$ for $\text{m}^3/\text{m}^3$) |
| `water_content_33kPa/` | `wv0033` | Volumetric water content at $-33\text{ kPa}$ suction (field capacity) | $10 \times \text{cm}^3/\text{dm}^3$ | $10$ | $\text{vol}\%$ (or $\times 0.001$ for $\text{m}^3/\text{m}^3$) |
| `water_content_1500kPa/` | `wv1500` | Volumetric water content at $-1500\text{ kPa}$ suction (wilting point) | $10 \times \text{cm}^3/\text{dm}^3$ | $10$ | $\text{vol}\%$ (or $\times 0.001$ for $\text{m}^3/\text{m}^3$) |
| `organic_carbon_density/` | `ocd` | Organic carbon density | $\text{hg}/\text{m}^3$ | $10$ | $\text{kg}/\text{m}^3$ |

### 4.2 Standard SoilGrids Depth Intervals
SoilGrids provides predictions standardized to six GlobalSoilMap depth intervals:
1. `0-5 cm` — Surface layer *(Prioritized)*
2. `5-15 cm` — Shallow subsurface *(Prioritized)*
3. `15-30 cm` — Upper subsoil *(Prioritized)*
4. `30-60 cm` — Mid subsoil *(Prioritized)*
5. `60-100 cm` — Deep subsoil *(Secondary phase)*
6. `100-200 cm` — Substratum *(Secondary phase)*

> [!WARNING]
> **Depth Interval Preservation:**  
> These intervals are preserved strictly as separate layers. Do not combine, merge, or imply that SoilGrids depth intervals directly represent point-sensor observations at $5.08\text{ cm}$, $10.16\text{ cm}$, $20.32\text{ cm}$, or $50.80\text{ cm}$.

---

## 5. Raw vs Processed Separation

- **`raw/AAMU-JTG/<property>/`:**  
  Contains original, unmodified downloads from the SoilGrids web interface (e.g., GeoTIFF rasters or GeoTIFF point/window clips). Files remain pristine and are tracked by cryptographic hashes.
- **`processed/AAMU-JTG/`:**  
  Contains aligned tabular extractions where:
  1. The integer scale factors are applied (e.g., raw clay $250 \rightarrow 25.0\%$).
  2. Textural consistency checks are verified ($\text{clay} + \text{sand} + \text{silt} \approx 100\%$).
  3. Physical water content units are converted to $\text{m}^3/\text{m}^3$.
  4. Features are formatted for integration into the SoilDepth-AI modeling pipeline.

---

## 6. Manifest & Ledger Protocol

All manual downloads are tracked in [`manifests/download_manifest.csv`](manifests/download_manifest.csv).

Columns:
- `property`: Property directory name (e.g., `clay`, `water_content_33kPa`).
- `depth_cm`: Standard interval (`0-5`, `5-15`, `15-30`, `30-60`).
- `value_type`: Statistical estimator selected on SoilGrids portal (e.g., `mean`, `uncertainty`, `Q0.5`).
- `filename`: Downloaded file name.
- `source`: Source provider attribution (`ISRIC SoilGrids 250m`).
- `download_date`: ISO date of manual retrieval (`YYYY-MM-DD`).
- `status`: Acquisition lifecycle state (`pending`, `verified`, `failed`).
- `notes`: Specific notes on units, scale factors, and verification results.

---

## 7. Quality Checks & Verification Workflow

Upon downloading each raster or tabular extract:
1. **Coordinate Verification:** Confirm the tile or window covers latitude `34.78534° N`, longitude `-86.55906° W`.
2. **Physical Boundary Checks:**
   - Texture: $0 \le \text{clay}, \text{sand}, \text{silt} \le 100\%$, with sum $\approx 100\%$.
   - Bulk density: $0.8 \le \rho_b \le 1.9\text{ g}/\text{cm}^3$.
   - Water content: $0.01 \le \theta_{1500} < \theta_{33} < \theta_{10} \le 0.60\text{ m}^3/\text{m}^3$.
3. **Ledger Update:** Update [`manifests/download_manifest.csv`](manifests/download_manifest.csv) with the actual verified filename and change status from `pending` to `verified`.

---

## 8. Current Dataset Status

> [!NOTE]
> **No data has been downloaded yet.** This directory structure is ready for manual downloads via [https://soilgrids.org/](https://soilgrids.org/).
