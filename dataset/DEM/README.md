# SoilDepth-AI — Digital Elevation Model (DEM) Dataset Guide

This directory houses Digital Elevation Model (DEM) and topographic datasets for the **SoilDepth-AI** project. Topographic variables (elevation, slope, aspect, curvature, and Topographic Wetness Index) govern surface runoff, infiltration, and subsurface hydraulic accumulation across the soil profile.

---

## 1. Directory Structure

Following the established repository architecture:

```text
dataset/DEM/
├── README.md                          # Configuration, specifications, and acquisition guide
├── raw/                               # Destination for original, unmodified DEM manual downloads
│   └── AAMU-JTG/                      # Pilot station raw raster tiles
├── manifests/
│   └── download_manifest.csv          # Audit ledger tracking sources, CRS, resolution, and SHA256 hashes
├── audit/                             # Audit reports generated after raster integrity verification
├── processed/                         # Processed, cropped, re-projected rasters and terrain derivatives
│   └── AAMU-JTG/                      # Aligned features (slope, aspect, TWI) for AAMU-JTG
└── scripts/
    └── validate_dem.py                # Standalone verification script for downloaded DEM rasters
```

---

## 2. Pilot Station Topographic Profile: `AAMU-JTG`

The first elevation extraction is configured for pilot station **AAMU-JTG** (SCAN network):

- **Station ID:** `AAMU-JTG`
- **Location:** Winfred Thomas Agricultural Research Station, Hazel Green, Madison County, Alabama, USA
- **Station Coordinates:** Latitude `34.78534° N`, Longitude `-86.55906° W`
- **Station Benchmark Elevation:** `241.0 m` above sea level
- **Terrain Setting:** Low-relief agricultural plain / undulating plateau (Cumberland Plateau fringe)

### Recommended Minimum Spatial Bounding Box
To calculate accurate spatial terrain derivatives (e.g., slope, flow accumulation, Topographic Wetness Index), do not download a single pixel. Acquire at least a **$0.2^\circ \times 0.2^\circ$ window ($\sim 20\text{ km} \times 20\text{ km}$)** or a standard **$1^\circ \times 1^\circ$ tile**:

| Boundary | Coordinate | Context |
| :--- | :--- | :--- |
| **North (Max Latitude)** | `34.88° N` | $\sim 10.5\text{ km}$ north of station |
| **South (Min Latitude)** | `34.68° N` | $\sim 11.5\text{ km}$ south of station |
| **East (Max Longitude)** | `-86.46° W` | $\sim 9.0\text{ km}$ east of station |
| **West (Min Longitude)** | `-86.66° W` | $\sim 9.0\text{ km}$ west of station |
| **Standard $1^\circ \times 1^\circ$ Tile** | `34°N–35°N, 87°W–86°W` | Tile designation: `N34W087` or `n34_w087` |

---

## 3. Recommended Sources and Specifications

Three high-fidelity open-access DEM sources are recommended for this station:

### Option A: USGS 3D Elevation Program (3DEP) — *(Recommended for CONUS Pilot)*
- **Provider:** United States Geological Survey (USGS)
- **Portal:** [The National Map (TNM) Downloader](https://apps.nationalmap.gov/downloader/) or USGS EarthExplorer
- **Product:** 1/3 arc-second ($\sim 10\text{ m}$) or 1 arc-second ($\sim 30\text{ m}$) National Elevation Dataset (NED)
- **Horizontal CRS:** NAD83 (`EPSG:4269`) or Geographic WGS84 (`EPSG:4326`)
- **Vertical Datum:** NAVD88 (orthometric elevation in meters)
- **Format:** Cloud-Optimized GeoTIFF (COG) or standard GeoTIFF (`.tif`)
- **Advantage:** Highest spatial resolution and accuracy available for US SCAN stations.

### Option B: Copernicus DEM GLO-30 — *(Recommended for Global Standard)*
- **Provider:** European Space Agency (ESA) / Copernicus
- **Portal:** Copernicus Open Access Hub or AWS Registry of Open Data (`copernicus-dem-30m`)
- **Product:** Copernicus GLO-30 Public (1 arc-second, $\sim 30\text{ m}$)
- **Horizontal CRS:** WGS84 (`EPSG:4326`)
- **Vertical Datum:** EGM2008 geoid (elevation in meters)
- **Format:** GeoTIFF (`.tif`)
- **Advantage:** Globally consistent specification directly compatible with international ISMN stations.

### Option C: NASA NASADEM / SRTMGL1
- **Provider:** NASA JPL / USGS
- **Portal:** [NASA Earthdata Search](https://search.earthdata.nasa.gov/)
- **Product:** NASADEM Merged DEM (1 arc-second, $\sim 30\text{ m}$)
- **Tile ID:** `NASADEM_HGT_n34w087.zip`
- **Horizontal CRS:** WGS84 (`EPSG:4326`)
- **Vertical Datum:** EGM96 geoid
- **Format:** GeoTIFF or raw `.hgt`

---

## 4. Provenance Fields in Tracking Manifest

All manual downloads must be recorded in [`manifests/download_manifest.csv`](manifests/download_manifest.csv) with the following provenance fields:

1. `dataset`: Dataset identifier (`DEM`).
2. `station_id`: Ground station code (`AAMU-JTG`).
3. `latitude`, `longitude`: Station point coordinates (`34.78534`, `-86.55906`).
4. `bounding_box`: Comma-separated spatial extent (`min_lat,min_lon,max_lat,max_lon`).
5. `source_agency`: Data provider (e.g., `USGS`, `ESA-Copernicus`, `NASA-JPL`).
6. `product_name`: Official product name (e.g., `USGS_3DEP_1_arcsec`, `Copernicus_GLO-30`).
7. `resolution_m`: Spatial resolution in meters ($\sim 10\text{ m}$ or $\sim 30\text{ m}$).
8. `vertical_datum`: Height datum (e.g., `NAVD88`, `EGM2008`, `EGM96`).
9. `crs`: Coordinate Reference System (e.g., `EPSG:4326`, `EPSG:4269`, `EPSG:26916`).
10. `format`: File format (e.g., `GeoTIFF`, `COG`).
11. `expected_filename`: Target normalized filename (e.g., `DEM_AAMU-JTG_raw.tif`).
12. `actual_filename`: Name of file downloaded from portal.
13. `status`: Current lifecycle state (`PENDING`, `RAW_DOWNLOAD`, `VALIDATED`, `PROCESSED`).
14. `download_date`: ISO date of manual retrieval (`YYYY-MM-DD`).
15. `file_size_bytes`: Exact byte count.
16. `sha256`: SHA-256 cryptographic checksum for immutable provenance.
17. `validation_status`: Output of validation audit (`VALIDATED` or `REJECTED`).
18. `notes`: Key audit comments (elevation at station pixel, bounds, NoData value).

---

## 5. Manual Download Workflow

1. **Acquisition:**
   - Select either **USGS 3DEP (10m or 30m)** or **Copernicus GLO-30**.
   - Define the bounding box covering $34.68^\circ\text{N} - 34.88^\circ\text{N}$, $86.66^\circ\text{W} - 86.46^\circ\text{W}$ (or tile `n34w087`).
   - Download the raster tile in **GeoTIFF (`.tif`)** format.
2. **Placement:**
   - Place the unmodified downloaded raster into:
     ```text
     dataset/DEM/raw/AAMU-JTG/
     ```
3. **Ledger Update:**
   - Update [`manifests/download_manifest.csv`](manifests/download_manifest.csv) with actual filename, size, and source metadata.
4. **Validation:**
   - Execute the validation script:
     ```bash
     python dataset/DEM/scripts/validate_dem.py --station AAMU-JTG
     ```
   - Confirm that:
     - The raster opens and contains valid elevation values (no corrupt blocks).
     - The station coordinates fall completely within the raster extent.
     - The sampled pixel elevation at `(34.78534, -86.55906)` is physically consistent with the ground-truth benchmark ($241.0\text{ m} \pm 15\text{ m}$).

---

## 6. Derived Topographic Predictors (Upcoming Processing)

Once validated, the raw DEM will be processed into local topographic predictors:
1. `elevation_m`: Elevation at station pixel (m).
2. `slope_deg`: Local surface slope gradient (degrees).
3. `aspect_sin`, `aspect_cos`: Decomposed slope direction.
4. `topographic_wetness_index` (TWI): $\ln(a / \tan \beta)$, indicating groundwater convergence and drainage potential.
5. `elevation_diff_local_mean_m`: Elevation relative to local 1 km neighborhood mean (ridge vs valley position).
