# SCAN In Situ Dataset (`SCAN`)

This directory is designated for in situ soil moisture observational data from the **Soil Climate Analysis Network (SCAN)** (USDA-NRCS) accessed via the International Soil Moisture Network (ISMN).

---

## 1. Directory Structure

```text
SCAN/
├── README.md                          # Dataset specification & user instructions
├── raw/                               # Reserved for user-downloaded ZIP archives
├── extracted/                         # Extracted station time series by depth layer
│   ├── surface_0-10cm/                # For 5 cm surface point-sensor proxy files
│   ├── middle_20-30cm/                # For middle layer sensors (nominal 20 cm / 25 cm)
│   └── deep_30-60cm/                  # For deep root-zone sensors (nominal 50 cm)
└── audit/                             # Audit reports, inventories, and quality logs for SCAN
```

---

## 2. Ingestion & Placement Instructions

1. **Raw Archives (`raw/`):**
   - Place downloaded ISMN `.zip` archive packages directly into `ISMN/SCAN/raw/`.
2. **Extracted Data (`extracted/`):**
   - Extract the depth-stratified observation time series (`.stm` files and metadata) into the respective subdirectories:
     - `surface_0-10cm/`: Stations with active sensors at ~5 cm (0.00–0.05 m or 0.05–0.05 m).
     - `middle_20-30cm/`: Stations with active sensors around 20 cm or 25 cm.
     - `deep_30-60cm/`: Stations with active deep sensors around 50 cm (0.50 m).
3. **Audit Execution (`audit/`):**
   - Once files are placed, the audit suite will catalog sensor models, station coordinates, quality flags, temporal continuity (specifically verifying coverage across the 2015–2023 satellite window), and generate dataset manifests.
