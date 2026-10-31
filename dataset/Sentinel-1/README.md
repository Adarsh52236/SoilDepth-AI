# SoilDepth-AI — Sentinel-1 SAR Dataset Guide

This directory houses Sentinel-1 C-band Synthetic Aperture Radar (SAR) observations for the **SoilDepth-AI** project. SAR microwave backscatter ($\lambda \approx 5.6\text{ cm}$) provides all-weather sensitivity to surface roughness, geometric crop structure, and soil dielectric properties (moisture dynamics).

---

## 1. Directory Structure

```text
dataset/Sentinel-1/
├── README.md                          # Configuration, specifications, and acquisition guide
├── raw/
│   └── AAMU-JTG/                      # Authoritative STAC catalog JSON and sample raw COG tiles
├── manifests/
│   ├── download_manifest.csv          # Audit ledger tracking sources, CRS, resolution, and SHA256 hashes
│   └── sentinel1_manifest.json        # Machine-readable provenance and inventory
├── audit/
│   └── AAMU-JTG/
│       └── sentinel1_quality_report.json # Quality metrics, observation counts, and statistics
├── processed/
│   └── AAMU-JTG/
│       ├── sentinel1_acquisitions.csv    # Observation-level backscatter (VV, VH, ratio)
│       └── sentinel1_daily_features.csv  # Full-calendar 2015-2023 aligned daily feature series
└── scripts/
    └── process_sentinel1.py           # Automated cloud-native ingestion & extraction pipeline
```

---

## 2. Product Specifications & Preprocessing

- **Mission:** Sentinel-1A & Sentinel-1B
- **Instrument:** C-band Synthetic Aperture Radar (C-SAR)
- **Product:** Level-1 Ground Range Detected (GRD) Radiometrically Terrain Corrected (RTC)
- **Polarizations:** Dual-polarization (VV, VH)
- **Radiometric Normalization:** Gamma0 ($\gamma^0$) terrain-flattened backscatter using high-resolution DEM
- **Spatial Resolution:** $10\text{ m} \times 10\text{ m}$
- **Coordinate Reference System:** Universal Transverse Mercator (UTM Zone 16N, `EPSG:32616`)
- **Distribution:** Microsoft Planetary Computer STAC & Azure Blob Storage Cloud-Optimized GeoTIFFs (COGs)

---

## 3. Extracted Features

1. `vv_linear`, `vh_linear`: Radiometrically terrain-corrected backscatter in linear power units ($\text{m}^2/\text{m}^2$).
2. `vv_db`, `vh_db`: Logarithmic backscatter in decibels:
   $$\sigma^0_{\text{dB}} = 10 \log_{10}(\gamma^0_{\text{linear}})$$
3. `vv_vh_ratio_db`: Polarization ratio ($\text{vv}_{\text{dB}} - \text{vh}_{\text{dB}}$), sensitive to vegetation canopy volume vs bare soil scattering.
4. `vv_3x3_mean_db`: $3 \times 3$ pixel spatial neighborhood mean ($30\text{ m} \times 30\text{ m}$ filter for speckle attenuation).
5. `orbit_direction`: Orbital flight geometry (`ascending` evening pass or `descending` morning pass).

