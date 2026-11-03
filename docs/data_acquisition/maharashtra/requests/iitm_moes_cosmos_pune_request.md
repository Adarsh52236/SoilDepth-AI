# Formal Academic Data Requisition: COSMOS-India Pune Station

**Document Reference:** `SOILDEPTH-REQ-2026-001`  
**Date of Drafting:** November 3, 2026  
**Status:** `DRAFTED_NOT_SENT` (Pending Institutional Submission)  
**Target Institution:**  
Centre for Climate Change Research (CCCR) / Hydrometeorology & Climate Studies  
Indian Institute of Tropical Meteorology (IITM)  
(Ministry of Earth Sciences, Government of India)  
Dr. Homi Bhabha Road, Pashan, Pune – 411008, Maharashtra, India  

**Recipient Designation:**  
Director, Indian Institute of Tropical Meteorology (IITM), Pune  
*Attention:* Scientist-in-Charge, COSMOS-India Network  

---

### Subject: Request for Historical Cosmic-Ray Neutron Sensing (CRNS) and Profile In-Situ Soil Moisture Observations for Scientific Academic Research (SoilDepth-AI Project)

Respected Sir/Madam,

We write to formally request access to historical observational data from the Cosmic-Ray Neutron Sensor (CRNS) and auxiliary in-situ hydrometeorological sensor network operated by IITM at the Pashan campus, Pune (`IITM-PUNE-COSMOS`), under the COSMOS-India / MoES-NERC research initiative.

#### 1. Research Project Context & Academic Objective
The **SoilDepth-AI** project is an open, non-commercial academic research initiative developing physics-informed machine learning architectures to reconstruct root-zone soil moisture ($0\text{--}60\text{ cm}$) across agricultural regions of Maharashtra. The project utilizes multimodal remote sensing (Sentinel-1 SAR, Sentinel-2 optical MSI, NASA SMAP L3) and ECMWF ERA5-Land reanalysis. 

To rigorously validate satellite downscaling and surface-to-depth propagation models, high-quality, continuous, independent ground-truth measurements are indispensable. The IITM Pune COSMOS station represents a unique, nationally vital hydrometeorological benchmark situated on the transition fringe between the Western Ghats and the Deccan Plateau Vertisol tract.

#### 2. Requested Station Metadata
- **Station Identifier:** `IITM-PUNE-COSMOS`
- **Location:** IITM Pashan Campus, Pune, Maharashtra
- **Geographic Coordinates:** Latitude $18.5372^\circ\text{ N}$, Longitude $73.8051^\circ\text{ E}$
- **Benchmark Elevation:** $560.0\text{ m}$ AMSL (Measured DEM plateau elevation: $591.58\text{ m}$ AMSL)

#### 3. Requested Historical Observation Period
- **Start Date:** January 1, 2017 (`2017-01-01T00:00:00Z`)
- **End Date:** December 31, 2023 (`2023-12-31T23:59:59Z`)
- **Temporal Window:** 7 continuous calendar years (2,556 daily cycles)

#### 4. Specific Parameters and Sensor Modalities Requested
We specifically request the following raw and processed parameters:
1. **Cosmic-Ray Neutron Probe (CRNS) Observations:**
   - Raw hourly neutron counts (epithermal/fast neutron counts per hour).
   - Corrected neutron counts ($N_{\text{corr}}$) incorporating barometric pressure, atmospheric water vapor, and solar incoming cosmic neutron intensity corrections.
   - Daily and hourly area-integrated volumetric soil moisture ($\text{m}^3/\text{m}^3$ or $\text{cm}^3/\text{cm}^3$) across the $\sim 200\text{ m}$ radial footprint.
   - Estimated effective measurement depth ($z^*$, cm) time series.
2. **Auxiliary Profile Point Sensors (Stevens Hydra Probe / TDR / FDR):**
   - Discrete in-situ volumetric soil moisture at instrumented depths: $5\text{ cm}$, $15\text{ cm}$, and $50\text{ cm}$ (or actual installed depths).
   - Soil temperature profile ($^\circ\text{C}$) at corresponding sensor depths.
3. **Meteorological & Environmental Auxiliaries:**
   - On-site automatic weather station (AWS) rainfall (mm), air temperature ($^\circ\text{C}$), atmospheric pressure (hPa), and relative humidity (%).
4. **Site Calibration and Edaphic Metadata:**
   - Calibration parameter $N_0$ (neutron count rate over dry silica).
   - Soil bulk density ($\rho_{bd}$, $\text{g}/\text{cm}^3$), lattice/bound water fraction ($w_{\text{lat}}$, $\text{g}/\text{g}$), and soil organic carbon weight fraction ($w_{\text{soc}}$, $\text{g}/\text{g}$) determined from calibration soil core sampling campaigns.
   - Instrument quality control and maintenance flags.

#### 5. Preferred Data Formats & Delivery
- **Formats:** Standard CSV, NetCDF-4 (`.nc`), HDF5, or native COSMOS-India ASCII text formats.
- **Timestamps:** ISO 8601 UTC or Indian Standard Time (IST) with explicit timezone annotation.
- **Delivery:** Secure FTP, institutional cloud download link, or direct email transmission.

#### 6. Academic Undertaking, Licensing & Attribution
We formally affirm that:
1. The requested data will be utilized **strictly for non-commercial academic research and algorithmic verification**.
2. The data will not be redistributed, sold, or shared with third parties without express written authorization from IITM / MoES.
3. The contribution of IITM, the Centre for Climate Change Research, and the COSMOS-India project will be **prominently cited and credited** in all resulting peer-reviewed scientific publications, conference proceedings, and open-source documentation.
4. If required by IITM institutional policy, we are fully prepared to enter into a formal **Bilateral Academic Data-Sharing Agreement / Memorandum of Understanding (MOU)** and welcome scientific collaboration with IITM scientists.

We would be deeply grateful for your favorable consideration of this academic requisition.

Sincerely,

**SoilDepth-AI Research Team**  
*Project Lead & Senior Geospatial ML Engineering Group*  
Academic Machine Learning & Hydrological Remote Sensing Initiative  
Contact: `project@soildepth-ai.org`
