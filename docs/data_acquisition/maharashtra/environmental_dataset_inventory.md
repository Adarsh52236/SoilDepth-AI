# Maharashtra Environmental & Earth Observation Dataset Inventory

**Project:** SoilDepth-AI  
**Target Region:** Maharashtra State, India ($15.6^\circ\text{ N}$ to $22.0^\circ\text{ N}$, $72.6^\circ\text{ E}$ to $80.9^\circ\text{ E}$, Area: $307,713\text{ km}^2$)  
**Document Type:** Environmental Data Availability & Role Classification  
**Date:** 2026-10-30  
**Status:** Complete Assessment  

---

## 1. Inventory Overview & Functional Classification

To reconstruct vertical root-zone soil moisture profiles across Maharashtra, a multimodal data stack combining global satellite observations, high-resolution reanalysis, state-level automatic weather networks, and regional pedological databases is required.

Each identified dataset is categorized according to its functional role within the SoilDepth-AI architecture:

```
[SoilDepth-AI Maharashtra Architecture]
   ├── Ground-Truth Targets (In-situ stations: COSMOS, IMD, PoCRA, SAU/ICAR)
   ├── Dynamic Predictor Inputs (ERA5-Land, Sentinel-1 SAR, Sentinel-2 Optical, SMAP L3)
   ├── Static Geographical & Soil Attributes (ICAR-NBSS&LUP BHOOMI, SoilGrids 250m, ALOS/SRTM DEM)
   ├── Auxiliary Benchmarks & Intercomparisons (ISRO EOS-04, DiCRA Maharashtra)
   └── Independent Weather Reference (Mahavedh Circle-Level AWS Network)
```

---

## 2. Dataset Classification & Technical Specifications

| Dataset Name | Primary Provider | Spatial Resolution | Temporal Frequency | Historical Span | Functional Pipeline Role | Access Mode / URL |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **ERA5-Land** | ECMWF / Copernicus CDS | $0.1^\circ$ ($\sim 9\text{ km}$) | Hourly & Daily | 1950–Present | **Predictor Input** (Atmospheric forcing & antecedent memory) | Open Access (`cds.climate.copernicus.eu`) |
| **Sentinel-1 SAR** | ESA / Copernicus Data Space | $10\text{ m}$ (GRD) | 6–12 days | 2014–Present | **Predictor Input** (Roughness, moisture & vegetation dielectric) | Open Access (`dataspace.copernicus.eu`) |
| **Sentinel-2 MSI** | ESA / Copernicus Data Space | $10\text{--}20\text{ m}$ | 5 days | 2015–Present | **Predictor Input** (Canopy greenness, crop phenology & NIR/SWIR) | Open Access (`dataspace.copernicus.eu`) |
| **SMAP L3 Radiometer** | NASA / NSIDC / JPL | $9\text{ km}$ / $36\text{ km}$ | Daily (AM/PM) | 2015–Present | **Predictor Input** (Macro surface soil brightness temperature) | Open Access (`earthdata.nasa.gov`) |
| **SoilGrids 250m** | ISRIC - World Soil Info | $250\text{ m}$ | Static | 6 Standard Layers | **Static Geographical Attribute** (Baseline global hydraulics) | Open Access (`soilgrids.org` / WCS / GeoTIFF) |
| **ICAR-NBSS&LUP BHOOMI**| ICAR-NBSS&LUP Nagpur | $1:250\text{k}$ & $1:50\text{k}$ | Static | Multi-decadal surveys | **Static Geographical Attribute** (High-precision Vertisol properties) | Institutional / Geoportal (`bhoomigeoportal-nbsslup.in`)|
| **ALOS AW3D30 / SRTM DEM** | JAXA / NASA USGS | $30\text{ m}$ ($1\text{ arc-sec}$) | Static | Baseline global | **Static Geographical Attribute** (Elevation, slope, aspect, TWI) | Open Access (`eorc.jaxa.jp`, `earthexplorer.usgs.gov`) |
| **ISRO EOS-04 (RISAT-1A)** | ISRO SAC / NRSC | $500\text{ m}$ | 11–17 days | 2022–Present | **Auxiliary Benchmark** (High-res spaceborne C-band radar product) | Open Access (`bhoonidhi.nrsc.gov.in`, `mosdac.gov.in`)|
| **DiCRA Maharashtra** | UNDP / NABARD / GoM | $10\text{--}1000\text{ m}$ | Monthly / Annual | 2018–Present | **Auxiliary Benchmark** (Statewide climate vulnerability & soil indices)| Open Access DPG (`dicra.nabard.org`) |
| **Mahavedh AWS Network**| Dept of Agriculture, GoM / Skymet| Revenue Circle (~2,100 AWS) | Hourly / Daily | 2016–Present | **Weather Reference** (Hyper-local ground precipitation & validation) | Restricted / State Portal (`maharain.maharashtra.gov.in`)|

---

## 3. In-Depth Environmental Dataset Profiles

### 3.1 ERA5-Land Reanalysis
* **Pipeline Role:** **Predictor Input** (Core continuous meteorological driver).
* **Parameters Utilized:** 2m Air Temperature (mean, min, max), 2m Dewpoint Temperature, Total Precipitation, Surface Solar Radiation Downwards, 10m Wind Speed ($u_{10}, v_{10}$), Vapor Pressure Deficit (VPD).
* **Coverage in Maharashtra:** Continuous statewide coverage across $\sim 3,800$ grid points ($0.1^\circ \times 0.1^\circ$).
* **Role in Preprocessing:** Identical to the Model 1 feature engineering pipeline: computes antecedent memory features (`precip_roll_sum_3d`, `precip_roll_sum_7d`, `precip_roll_sum_14d`, `precip_roll_sum_30d`, `days_since_rain_gt_1mm`, `temp_roll_mean_7d`, `temp_roll_mean_30d`).
* **Known Limitations:** In regions with intense convective monsoon rainfall (Western Ghats crest, e.g., Mahabaleshwar $>5,000\text{ mm}$), ERA5-Land grid resolution ($9\text{ km}$) smooths extreme topographic orographic precipitation peaks. Pairing with circle-level Mahavedh rain gauges is highly recommended.

### 3.2 Sentinel-1 C-Band Synthetic Aperture Radar (SAR)
* **Pipeline Role:** **Predictor Input** (Surface roughness, soil dielectric permittivity, canopy penetration).
* **Parameters Utilized:** Dual-polarization $\gamma^0$ or $\sigma^0$ backscatter: $\text{VV}$ (sensitive to soil moisture and roughness) and $\text{VH}$ (sensitive to volume scattering in vegetation canopy), alongside the cross-ratio $\text{VV}/\text{VH}$.
* **Revisit Characteristics in Maharashtra:** Revisit interval is 6 to 12 days (Ascending and Descending orbits).
* **Advantage:** Microwave C-band ($5.405\text{ GHz}$) penetrates monsoon cloud cover completely, providing uninterrupted observation throughout the critical Kharif cropping season (June–October) when optical satellites are cloud-obscured.
* **Processing Requirement:** Border noise removal, thermal noise removal, radiometric calibration, and terrain correction using ALOS 30m DEM. Forward-fill LOCF (Last Observation Carried Forward) ensures zero future leakage.

### 3.3 Sentinel-2 Multi-Spectral Instrument (MSI)
* **Pipeline Role:** **Predictor Input** (Crop canopy growth, leaf area index, surface transpiration, moisture stress).
* **Parameters Utilized:** Surface reflectance in Red ($B_4$), NIR ($B_8$), SWIR-1 ($B_{11}$), SWIR-2 ($B_{12}$); derived Normalized Difference Vegetation Index (NDVI), Enhanced Vegetation Index (EVI), and Normalized Difference Water Index (NDWI).
* **Cloud Masking Strategy:** Maharashtra experiences cloud cover on $>80\%$ of days between June and August. Strict Scene Classification Layer (SCL) masking is mandatory (excluding classes 3, 7, 8, 9, 10, 11).

### 3.4 SMAP L3 Radiometer Soil Moisture (L-band)
* **Pipeline Role:** **Predictor Input** (Direct physical microwave emission from top $0\text{--}5\text{ cm}$).
* **Parameters Utilized:** Daily mean volumetric soil moisture, retrieval quality flags, AM pass ($06{:}00\text{ local}$, optimal due to thermal equilibrium) and PM pass ($18{:}00\text{ local}$).
* **Revisit & Resolution:** Daily global coverage on a $9\text{ km}$ Equal-Area Scalable Earth (EASE-2) grid. Provides an indispensable coarse-scale wetness anchor during periods between high-resolution SAR revisits.

### 3.5 ICAR-NBSS&LUP BHOOMI Geoportal Soil Datasets
* **Pipeline Role:** **Static Geographical Attribute** (High-precision edaphic properties for Deccan Vertisols).
* **Significance for Maharashtra:**
  - Standard global databases like SoilGrids or HWSD often underestimate the unique shrink-swell clay mineralogy of Maharashtra's black cotton soils (Deccan trap basalt regolith).
  - NBSS&LUP provides detailed pedon characterization at $1:250,000$ and $1:50,000$ scales across all 36 districts:
    - **Physical Attributes:** Soil depth classes ($<25\text{ cm}$ very shallow, $25\text{--}50\text{ cm}$ shallow, $50\text{--}100\text{ cm}$ moderately deep, $>100\text{ cm}$ deep Vertisols), clay/sand/silt percentages, bulk density, available water capacity (AWC, $\text{mm/m}$).
    - **Mineralogical Attributes:** Smectite-rich clay content ($>50\text{--}65\%$), cracking depth, and soil reaction ($\text{pH} > 8.0$, calcareous nodules $\text{CaCO}_3$).
* **Access Protocol:** Online visualization available at `https://bhoomigeoportal-nbsslup.in/`. Digital spatial shapefiles/grids are obtained via formal institutional requisition to ICAR-NBSS&LUP, Amravati Road, Nagpur.

### 3.6 SoilGrids 250m Global Hydraulics
* **Pipeline Role:** **Static Geographical Attribute** (Standardized global vertical baseline).
* **Depths Available:** 6 standardized depth intervals ($0\text{--}5\text{ cm}$, $5\text{--}15\text{ cm}$, $15\text{--}30\text{ cm}$, $30\text{--}60\text{ cm}$, $60\text{--}100\text{ cm}$, $100\text{--}200\text{ cm}$).
* **Variables:** Clay, silt, sand, bulk density ($\text{bdod}$), organic carbon density ($\text{ocd}$), and volumetric water content at field capacity ($-33\text{ kPa}$, $\text{wv0033}$) and wilting point ($-1500\text{ kPa}$, $\text{wv1500}$).
* **Utility:** Provides an immediate, globally consistent static baseline while NBSS&LUP high-resolution vectors are being requisitioned.

### 3.7 ALOS World 3D (AW3D30) & SRTM 30m Digital Elevation Models
* **Pipeline Role:** **Static Geographical Attribute** (Topographic drainage and moisture redistribution).
* **Derived Topographic Indices:**
  - Elevation ($m$), Slope ($\text{degrees}$), Aspect ($\sin$, $\cos$).
  - Topographic Wetness Index ($\text{TWI} = \ln(a / \tan \beta)$), characterizing overland water accumulation in valley bottoms and low-lying alluvial floodplains (e.g., Godavari, Krishna, Bhima, Tapi basins).

### 3.8 ISRO EOS-04 (RISAT-1A) Operational Soil Moisture Product
* **Pipeline Role:** **Auxiliary Benchmark** (Satellite-to-satellite intercomparison).
* **Specifications:** Space Applications Centre (SAC / ISRO) produces operational surface soil moisture at **500-meter spatial resolution** using C-band SAR data from EOS-04, achieving $\sim 92\%$ retrieval accuracy over Indian croplands.
* **Access:** Accessible via ISRO's **Bhoonidhi** portal (`bhoonidhi.nrsc.gov.in`) and **VEDAS / MOSDAC** (`mosdac.gov.in`).
* **Application in SoilDepth-AI:** Serves as an independent spaceborne benchmark against which SoilDepth-AI's surface estimates ($5\text{ cm}$ and $10\text{ cm}$) can be validated statewide, without contaminating the model training loop.

### 3.9 DiCRA Maharashtra Platform (UNDP / NABARD / GoM)
* **Pipeline Role:** **Auxiliary Benchmark & Regional Validation**.
* **Specifications:** Certified Digital Public Good (DPG) hosted by NABARD (`dicra.nabard.org`), integrating multi-year spatio-temporal asset catalogs (STAC) of soil moisture anomalies, drought vulnerability indices, and crop resilience classifications across Marathwada and Vidarbha.
* **Application:** Provides macroscopic validation across agricultural clusters to verify that model-predicted moisture deficits align with observed drought alerts.

### 3.10 Mahavedh Circle-Level Automatic Weather Stations (AWS)
* **Pipeline Role:** **Weather Reference & Local Validation**.
* **Specifications:** High-density ground network developed under Public-Private Partnership between Maharashtra Agriculture Department and Skymet Weather Services.
* **Density:** Over **2,100 to 2,300 AWS units**, providing ground observations down to the revenue circle level (each covering $\sim 10\text{--}15\text{ villages}$).
* **Parameters:** Hourly rainfall, temperature, relative humidity, wind speed, wind direction, and solar radiation.
* **Application:** Used to cross-validate ERA5-Land precipitation grids and adjust localized storm rainfall amounts, particularly in convective squalls common during the pre-monsoon and retreating monsoon.

