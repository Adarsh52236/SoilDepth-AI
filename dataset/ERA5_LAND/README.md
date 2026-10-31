# SoilDepth-AI — ERA5-Land Local Storage & Pilot Ingestion Guide

This directory houses the ERA5-Land hourly meteorological reanalysis time-series data for the SoilDepth-AI project, manually downloaded via the official [Copernicus Climate Data Store (CDS)](https://cds.climate.copernicus.eu/).

---

## 1. Directory Structure

```text
ERA5_LAND/
├── README.md                          # This configuration and workflow documentation
├── raw/                               # Destination for original, unmodified CDS downloads
│   └── AAMU-JTG/
│       └── hourly/                    # Destination for AAMU-JTG NetCDF file(s)
├── manifests/
│   └── download_manifest.csv          # Audit ledger tracking request parameters and file hashes
├── audit/                             # Audit reports generated after file validation
├── processed/                         # Derived/re-gridded/feature-aligned datasets (future phase)
└── scripts/
    └── validate_era5_land.py          # Standalone verification script for downloaded NetCDF files
```

---

## 2. Pilot Request Specification: Station `AAMU-JTG`

The initial pilot time series is configured for the **AAMU-JTG** ground station (Alabama, USA), selected for its complete 2015–2023 3-layer in situ soil moisture profile in the SCAN dataset.

### Copernicus CDS Form Settings
- **Dataset:** `ERA5-Land hourly data from 1950 to present`
- **Data Type:** Hourly time series
- **Target Location:** Single point extraction
  - **Latitude:** `34.78534` (North)
  - **Longitude:** `-86.55906` (West)
- **Requested Observation Period:** `2015-01-01` through `2023-12-31` (all 9 years, all 12 months, all days, hours `00:00` to `23:00` UTC)
- **Requested Meteorological Variables:**
  1. `2m temperature` (Kelvin)
  2. `2m dewpoint temperature` (Kelvin)
  3. `Total precipitation` (meters, hourly accumulated/de-accumulated)
  4. `Surface solar radiation downwards` (J/m², accumulated/de-accumulated)
  5. `10m u-component of wind` (m/s)
  6. `10m v-component of wind` (m/s)
- **Requested Format:** NetCDF (`.nc`)
- **Suggested Expected Filename:** `ERA5Land_AAMU-JTG_2015-2023_hourly.nc`

> [!IMPORTANT]
> The parameters above represent the **requested configuration** submitted through the Copernicus CDS portal. Actual availability, dimension structure, variable naming convention (e.g., shortnames `t2m`, `d2m`, `tp`, `ssrd`, `u10`, `v10`), timestamp continuity, and physical range plausibility must be rigorously verified using the validation script once the download is placed in `raw/AAMU-JTG/hourly/`.

---

## 3. Step-by-Step Manual Workflow

### Step 1: Download from Copernicus CDS
1. Log in to the Copernicus Climate Data Store website.
2. Navigate to **ERA5-Land hourly data from 1950 to present**.
3. Select the 6 requested variables, years 2015–2023, all months, all days, all hours, sub-region coordinates (`34.78534`, `-86.55906`), and NetCDF format.
4. Submit the request and download the file once processed.

### Step 2: Copy the Downloaded File to Local Storage
Copy the downloaded NetCDF file directly into:
```text
SoilDepth-AI/ERA5_LAND/raw/AAMU-JTG/hourly/
```
*(Example: `SoilDepth-AI/ERA5_LAND/raw/AAMU-JTG/hourly/ERA5Land_AAMU-JTG_2015-2023_hourly.nc`)*

- Preserve the exact downloaded file without modification or manual renaming.
- Do not convert, compress, or unpack.

### Step 3: Install Validation Dependencies (If not already installed)
The validation script relies on `xarray` and `netCDF4` to parse NetCDF coordinates and dimensions. To install them in your local environment, run:

```bash
pip install xarray netCDF4
```

### Step 4: Run the Validation Script
Execute the validation script from the project root:

```bash
python ERA5_LAND/scripts/validate_era5_land.py
```

Or target a specific filename explicitly:

```bash
python ERA5_LAND/scripts/validate_era5_land.py --file ERA5_LAND/raw/AAMU-JTG/hourly/ERA5Land_AAMU-JTG_2015-2023_hourly.nc
```

The script will:
1. Verify SHA-256 checksum and exact byte count.
2. Parse dimensions, coordinates, and timestamps.
3. Verify that 100% of the 2015-01-01 to 2023-12-31 period is covered without missing intervals.
4. Confirm all 6 requested variables are mapped and present.
5. Generate an audit report inside `ERA5_LAND/audit/`.
6. Update `ERA5_LAND/manifests/download_manifest.csv` with status `DOWNLOADED` and `VALIDATED`.

---

## 4. Data Governance & Storage Rules

1. **No External Network Calls:** The automated pipeline will not make unauthorized network calls or scrape external portals. All raw downloads are managed manually by the user.
2. **Read-Only Raw Isolation:** Original files in `raw/` are immutable. Any unit conversions, hourly flux de-accumulations, or feature alignment will be written strictly to `processed/`.
3. **No Git Leakage:** All `.nc` and raw binary files are ignored via `.gitignore` to prevent repository bloat.
