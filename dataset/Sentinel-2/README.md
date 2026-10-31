# SoilDepth-AI — Sentinel-2 Optical Dataset Guide

This directory houses Sentinel-2 MultiSpectral Instrument (MSI) optical observations for the **SoilDepth-AI** project. Multispectral surface reflectance governs vegetation greenness, canopy transpiration, and bare surface albedo across the soil-vegetation-atmosphere interface.

---

## 1. Directory Structure

```text
dataset/Sentinel-2/
├── README.md                          # Configuration, specifications, and acquisition guide
├── raw/
│   └── AAMU-JTG/                      # Authoritative STAC catalog JSON and sample raw COG tiles
├── manifests/
│   ├── download_manifest.csv          # Audit ledger tracking sources, CRS, resolution, and SHA256 hashes
│   └── sentinel2_manifest.json        # Machine-readable provenance and inventory
├── audit/
│   └── AAMU-JTG/
│       └── sentinel2_quality_report.json # Quality metrics, cloud masking rates, and statistics
├── processed/
│   └── AAMU-JTG/
│       ├── sentinel2_acquisitions.csv    # Observation-level reflectance, SCL, and vegetation indices
│       └── sentinel2_daily_features.csv  # Full-calendar 2015-2023 aligned daily feature series
└── scripts/
    └── process_sentinel2.py           # Automated cloud-native ingestion & extraction pipeline
```

---

## 2. Product Specifications & Cloud Masking

- **Mission:** Sentinel-2A & Sentinel-2B
- **Instrument:** MultiSpectral Instrument (MSI)
- **Product:** Level-2A Bottom-Of-Atmosphere (BOA) Surface Reflectance (Sen2Cor atmospheric correction)
- **Spectral Bands:**
  - `B02` (Blue, 490 nm, 10m)
  - `B03` (Green, 560 nm, 10m)
  - `B04` (Red, 665 nm, 10m)
  - `B08` (NIR, 842 nm, 10m)
  - `B11` (SWIR1, 1610 nm, 20m)
  - `B12` (SWIR2, 2190 nm, 20m)
- **Digital Scale Factor:** $10,000.0$ (Digital Number to physical surface reflectance $[0.0, 1.0]$)
- **Cloud & Shadow Masking:**
  - Evaluated via native Scene Classification Layer (`SCL`, 20m).
  - Masked classes (reflectance set to `NaN`, never 0):
    - `0`: No Data
    - `3`: Cloud Shadows
    - `8`: Cloud Medium Probability
    - `9`: Cloud High Probability
    - `10`: Thin Cirrus
- **Derived Vegetation Indices:**
  - **NDVI:** Normalized Difference Vegetation Index:
    $$\text{NDVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04}}$$
  - **EVI:** Enhanced Vegetation Index (improved canopy sensitivity):
    $$\text{EVI} = 2.5 \times \frac{\text{B08} - \text{B04}}{\text{B08} + 6.0 \times \text{B04} - 7.5 \times \text{B02} + 1.0}$$

