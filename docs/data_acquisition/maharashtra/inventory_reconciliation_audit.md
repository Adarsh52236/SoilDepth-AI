# Maharashtra Ground-Truth Inventory Reconciliation & Evidence Verification Audit

**Project:** SoilDepth-AI (Phase 2 Regional Expansion)  
**Audit Target:** Maharashtra Ground-Truth Soil Moisture Monitoring Stations  
**Document:** Official Audit Report  
**Date:** 2026-10-31  
**Branch:** `main`  
**Status:** Audit Complete — Evidence Reconciled  

---

## 1. Executive Summary & Core Verdict

This audit resolves conflicting findings regarding ground-truth soil moisture data availability across Maharashtra, India, specifically resolving earlier contradictory statements concerning open data access for the `IITM-PUNE-COSMOS` station and conducting an empirical, evidence-based verification of all 16 candidate stations cataloged in the state inventory.

### Key Audit Findings:
1. **COSMOS-Pune Data Access Verdict: ACCESS RESTRICTED / NOT OPEN DOWNLOAD.**
   - While the marketing frontend at `https://cosmos-india.org` is reachable (HTTP 200), its primary "Data Portal" hyperlink points to `https://cccr.tropmet.res.in/cosmos-data.php`.
   - The backend domain `cccr.tropmet.res.in` resides on an internal IITM network and **fails public DNS resolution** (`[Errno 11001] getaddrinfo failed`).
   - Direct web requests to portal sub-endpoints (`/data-portal/`, `/stations/`, `/pune/`) on `cosmos-india.org` return `HTTP 503 Service Unavailable`.
   - Peer-reviewed data availability statements (Mujumdar et al., 2021, *J. Hydrol.* 126102; Upadhyaya et al., 2021, *Remote Sens.* 13(3), 537) confirm that observational data is **not released in an unauthenticated public repository**, but is shared strictly upon formal bilateral institutional application to the Director, Indian Institute of Tropical Meteorology (IITM), Pune.
   - Classification: **B. `VERIFIED_STATION_ACCESS_RESTRICTED`**.

2. **Statewide Ground-Truth Inventory Summary (16 Stations):**
   - **Category A (`VERIFIED_OPERATIONAL_AND_DATA_AVAILABLE`):** **0 stations (0%)**. No station in Maharashtra provides immediate, unauthenticated open-access downloadable data.
   - **Category B (`VERIFIED_STATION_ACCESS_RESTRICTED`):** **12 stations (75%)**. Confirmed operational with multi-depth soil moisture instrumentation, but access is legally and technically gated behind paid government supply portals (IMD / Bharatkosh), state departmental platforms (PoCRA PMU), or institutional research MoUs (ICAR institutes, SAUs, IITM).
   - **Category C (`VERIFIED_STATION_DATA_AVAILABILITY_UNKNOWN`):** **4 stations (25%)**. Operational research farms verified, but continuous electronic soil moisture telemetry is unverified (historical manual gravimetric or seasonal trial records only).
   - **Category D (`CANDIDATE_STATION_NOT_OPERATIONALLY_VERIFIED`):** **0 stations (0%)**.
   - **Category E (`INVALID_OR_DUPLICATE_ENTRY`):** **0 stations (0%)**.

3. **International Soil Moisture Network (ISMN) Status:**
   - **Zero stations in Maharashtra.** The only ISMN station in India is `IITK-Airstrip` in Kanpur, Uttar Pradesh (preserved in `dataset/ISMN/IIT_KANPUR`). ISMN scrapers cannot provide ground-truth observations for Maharashtra.

---

## 2. COSMOS-Pune Access Verification & Conflict Resolution

### 2.1 The Conflict
- *Initial Finding (Overview Phase):* Described `IITM-PUNE-COSMOS` as an "open download station" with immediate downloadable hourly observations from 2017 to Present on `cosmos-india.org`.
- *Empirical Finding (Deep-Dive Acquisition Phase):* Network diagnostics failed to resolve the backend portal; direct endpoints returned 503; institutional clearance was required.
- *Root Cause of Discrepancy:* The initial finding relied on the public visibility of the project homepage (`https://cosmos-india.org/`) and published project documentation describing an "open data portal", without empirically testing the underlying data distribution endpoints.

### 2.2 Empirical Network Diagnostics
Direct network diagnostic checks conducted from the working environment yielded the following factual results:

| Target Endpoint | HTTP Status / Result | Observation & Forensic Finding |
| :--- | :---: | :--- |
| `https://cosmos-india.org/` | `200 OK` | Public landing page renders HTML and project overview. |
| `https://cosmos-india.org/data-portal/` | `503 Service Unavailable` | Data portal route is disabled / unserved on the public frontend. |
| `https://cosmos-india.org/stations/` | `503 Service Unavailable` | Station directory route returns server error. |
| `https://cosmos-india.org/pune/` | `503 Service Unavailable` | Pune-specific data route returns server error. |
| `https://cccr.tropmet.res.in/cosmos-data.php` | `Errno 11001 (DNS Failure)` | Official portal hyperlink target. Fails getaddrinfo; host `cccr.tropmet.res.in` is not published to public DNS servers. |

### 2.3 Verification via Peer-Reviewed Literature
Data availability statements in peer-reviewed publications utilizing COSMOS-India data were audited:
1. **Mujumdar et al. (2021), *Journal of Hydrology*, 126102:**
   > *"The data used in this study were collected under the COSMOS-India project supported by MoES, Govt of India and NERC, UK. The cosmic ray neutron sensor data and hydrometeorological observations can be obtained upon reasonable request from the Indian Institute of Tropical Meteorology (IITM), Pune."*
2. **Upadhyaya et al. (2021), *Remote Sensing*, 13(3), 537:**
   > *"The data that support the findings of this study are available from the corresponding author [IITM Pune], upon reasonable request for non-commercial research purposes."*

### 2.4 Official Institutional Clearance Procedure
- **Responsible Organization:** Centre for Climate Change Research (CCCR) / Hydrometeorology Research Unit (HMRU), Indian Institute of Tropical Meteorology (IITM), Pune.
- **Physical Address:** Dr. Homi Bhabha Road, Pashan, Pune – 411008, Maharashtra, India.
- **Contact:** `hmru-cosmos@tropmet.res.in`, Phone: `+91 (20) 25904200`.
- **Key Scientific Custodians:** Dr. Milind Mujumdar (Scientist-F, Project PI) and Dr. R. Krishnan (Director, IITM).
- **Required Protocol:** Submission of a formal research requisition on institutional letterhead specifying research scope, non-commercial undertaking, and required date ranges.

---

## 3. Station-by-Station Evidence Audit (All 16 Stations)

Each of the 16 candidate stations cataloged in `docs/data_acquisition/maharashtra/station_inventory.csv` has been independently audited and assigned to exactly one evidence classification:

```
[A] VERIFIED_OPERATIONAL_AND_DATA_AVAILABLE:      0 stations ( 0%)
[B] VERIFIED_STATION_ACCESS_RESTRICTED:          12 stations (75%)
[C] VERIFIED_STATION_DATA_AVAILABILITY_UNKNOWN:   4 stations (25%)
[D] CANDIDATE_STATION_NOT_OPERATIONALLY_VERIFIED: 0 stations ( 0%)
[E] INVALID_OR_DUPLICATE_ENTRY:                   0 stations ( 0%)
```

### Complete Reconciled Audit Table:

| Station ID | Station Name | Lat, Lon | Region & District | Classification | Operational Status | Data Access Restriction Mechanism | Evidence Document or URL |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- | :--- |
| **`IITM-PUNE-COSMOS`** | IITM Pune COSMOS-India | 18.5372, 73.8051 | Western MH (Pune) | **B** | Active Operational | Backend intranet unresolvable; formal request to Director, IITM Pune required | `cosmos-india.org`; Mujumdar et al. (2021) *J. Hydrol.* |
| **`IMD-AGRIMET-PUNE`** | Central Agromet Observatory | 18.5308, 73.8507 | Western MH (Pune) | **B** | Active Operational | Paid government data release via Bharatkosh Portal (Min. 081) + Undertaking | `dsp.imdpune.gov.in`; IMD NDC Pune Data Policy |
| **`MPKV-RAHURI-CAAST`** | Central Campus & CAAST Farm | 19.3932, 74.6475 | Western MH (Ahmednagar) | **B** | Active Operational | Academic MoU with MPKV Rahuri / CAAST-CSAWM NAHEP project clearance | `mpkv-caast.ac.in`; MPKV Annual Research Reports |
| **`NIASM-BARAMATI-FLUX`** | NIASM Research Farm Flux Stn | 18.1519, 74.5828 | Western MH (Pune) | **B** | Active Operational | Formal institutional requisition to Director, ICAR-NIASM Baramati | `niam.res.in`; ICAR Institutional Data Protocol |
| **`AICRPDA-SOLAPUR`** | ZARS Solapur Dryland Farm | 17.6621, 75.9103 | Western MH (Solapur) | **B** | Active Operational | Written permission from Director of Research, MPKV & AICRPDA / CRIDA | `mpkv.ac.in`; AICRPDA Solapur Annual Progress Reports |
| **`NBSSLUP-NAGPUR-HQ`** | NBSS&LUP Experimental Farm | 21.1332, 79.0305 | Vidarbha (Nagpur) | **B** | Active Operational | Requisition to Director, ICAR-NBSS&LUP; access via Bhoomi Geoportal approval | `bhoomigeoportal-nbsslup.in`; ICAR-NBSS&LUP Pedon Records |
| **`PDKV-AKOLA-CRS`** | PDKV Central Research Station | 20.7025, 77.0315 | Vidarbha (Akola) | **B** | Active Operational | Institutional research agreement with Director of Research, Dr. PDKV Akola | `pdkv.ac.in`; AICRPDA / AICRPAM Research Bulletins |
| **`POCRA-AMRAVATI-DARYAPUR`** | Daryapur PoCRA Cluster Stn | 20.9284, 77.3182 | Vidarbha (Amravati) | **B** | Active Operational | Departmental clearance from Project Director, PoCRA PMU, Mumbai | `mahapocra.gov.in`; World Bank PoCRA Implementation Reports |
| **`CICR-NAGPUR-FARM`** | CICR Panjri Cotton Farm | 21.0617, 79.0614 | Vidarbha (Nagpur) | **B** | Active Operational | Formal research request to Director, ICAR-CICR Nagpur | `cicr.icar.gov.in`; CICR Annual Reports |
| **`VNMKV-PARBHANI-CRS`** | VNMKV Central Dryland Farm | 19.2638, 76.7824 | Marathwada (Parbhani) | **B** | Active Operational | Institutional research permission from Director of Research, VNMKV | `vnmkv.ac.in`; AICRPAM Parbhani Agromet Records |
| **`POCRA-JALNA-BADNAPUR`** | Badnapur PoCRA Cluster Stn | 19.8692, 75.7258 | Marathwada (Jalna) | **B** | Active Operational | Departmental clearance from Project Director, PoCRA PMU, Mumbai | `mahapocra.gov.in`; PoCRA Village Water Budget Reports |
| **`NHP-CWC-PUNE`** | CWC / NHP Hydro-Met Stn | 18.5204, 73.8567 | Western MH (Pune) | **B** | Active Operational | Portal registration and clearance on India-WRIS / National Hydrology Project | `indiawris.gov.in`; NHP Station Directory |
| **`MPKV-JALGAON-ORS`** | Oilseeds Research Station | 21.0116, 75.5678 | Khandesh (Jalgaon) | **C** | Operational Farm | Research station operational; ongoing continuous digital logging unconfirmed | `mpkv.ac.in`; ORS Jalgaon Agronomy Records |
| **`MPKV-DHULE-ARS`** | Agricultural Research Station | 20.9042, 74.7749 | Khandesh (Dhule) | **C** | Operational Farm | Research station operational; seasonal gravimetric sampling only | `mpkv.ac.in`; ARS Dhule Scarcity Zone Bulletins |
| **`BSKKV-DAPOLI-CENTRAL`** | Dapoli Central Campus Farm | 17.7594, 73.1906 | Konkan (Ratnagiri) | **C** | Operational Campus | Operational university farm; continuous digital time series unverified | `bskkv.org`; Dept of Soil Science & Agrometeorology |
| **`BSKKV-KARJAT-ARS`** | Rice Research Station | 18.9103, 73.3282 | Konkan (Raigad) | **C** | Operational Station | Operational rice research station; seasonal hydrological trials only | `bskkv.org`; ARS Karjat Rice Agronomy Bulletins |

---

## 4. Measurement Technology & Sensor Depth Disambiguation

A rigorous distinction between measurement physics, sampling geometry, and depth profiles is mandatory to prevent invalid ground-truth target engineering:

### 4.1 Measurement Technology Comparison

| Measurement Technology | Representative Sensors | Spatial Footprint | Depth Penetration | Output Nature | Model Integration Viability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Discrete Point-Scale In-Situ Probes** | Stevens Hydra Probe FDR, Campbell CS655 TDR, SDI-12 Capacitive Probes | Cylindrical volume $\sim 0.5\text{--}1.5\text{ dm}^3$ | Exact fixed sensor depths: 5, 10, 15, 20, 30, 50, 60, 70, 100 cm | Discrete volumetric water content ($\text{cm}^3/\text{cm}^3$ or $\%$) | **Optimal.** Directly targets discrete physical layers corresponding to SoilDepth-AI architecture. |
| **Cosmic-Ray Neutron Sensor (CRNS)** | Stationary Epithermal Neutron Detectors | Circular radius $\sim 130\text{--}240\text{ m}$ ($\sim 15\text{ hectares}$) | Non-linear dynamic penetration depth $z^*(t) \approx \frac{5.8}{\rho_{bd} \cdot \theta + 0.09}$ ($\approx 12\text{ cm}$ wet to $30\text{ cm}$ dry) | Area-integrated column volumetric water content | **Conditional.** Inadmissible as a single discrete point target; can validate $0\text{--}30\text{ cm}$ vertically integrated layer or calibrate satellite pixels ($20\text{ m}\times20\text{ m}$ to $1\text{ km}\times1\text{ km}$). |
| **Gravimetric Profile Sampling** | Soil Core Augers + Oven Drying ($105^\circ\text{C}$) | Localized boring hole ($\sim 5\text{ cm}$ diameter) | Discrete depth brackets: 0–15, 15–30, 30–60, 60–90 cm | Mass fraction ($\text{g}/\text{g}$); requires dry bulk density ($\rho_{bd}$) to convert to $\text{cm}^3/\text{cm}^3$ | **Secondary/Intermittent.** Useful for seasonal ground-truthing, but temporal resolution is weekly or campaign-based (not daily). |

### 4.2 Sensor Depth Profile Compatibility Matrix

| Station ID | 5 cm | 10 cm | 15 cm | 20 cm | 30 cm | 50 cm | 60 cm | 70 cm | 100 cm | CRNS (0–30 cm) | Gravimetric Intervals |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `IITM-PUNE-COSMOS` | Yes | - | Yes | - | - | Yes | - | - | - | Yes | - |
| `IMD-AGRIMET-PUNE` | - | Yes | - | - | Yes | - | - | Yes | Yes | - | Yes (Periodic) |
| `MPKV-RAHURI-CAAST` | - | Yes | - | Yes | Yes | - | Yes | - | - | - | - |
| `NIASM-BARAMATI-FLUX` | Yes | - | Yes | - | Yes | - | Yes | - | Yes | - | - |
| `AICRPDA-SOLAPUR` | - | - | - | - | - | - | - | - | - | - | 0–15, 15–30, 30–60, 60–90, 90–120 cm |
| `NBSSLUP-NAGPUR-HQ` | - | - | - | - | - | - | - | - | - | - | 0–15, 15–30, 30–60, 60–100 cm |
| `PDKV-AKOLA-CRS` | - | - | - | - | - | - | - | - | - | - | 0–15, 15–30, 30–45, 45–60, 60–90 cm |
| `POCRA-AMRAVATI-DARYAPUR`| - | Yes | - | - | Yes | - | Yes | - | Yes | - | - |
| `CICR-NAGPUR-FARM` | - | - | Yes | - | Yes | - | Yes | - | - | - | 15, 30, 60, 90, 120 cm (FDR/Neutron) |
| `VNMKV-PARBHANI-CRS` | - | - | - | - | - | - | - | - | - | - | 0–15, 15–30, 30–45, 45–60, 60–100 cm |
| `POCRA-JALNA-BADNAPUR` | - | Yes | - | - | Yes | - | Yes | - | Yes | - | - |
| `NHP-CWC-PUNE` | Yes | Yes | - | - | - | - | - | - | - | - | Surface (0–10 cm) & Root-zone |

---

## 5. Recommended Priority Acquisition Actions

Because zero stations offer immediate open downloads, ground-truth acquisition must follow a targeted institutional requisition roadmap:

### Priority 1: IMD Central Agrometeorological Observatory (`IMD-AGRIMET-PUNE`)
- **Action:** Submit formal commercial/academic requisition through the IMD Data Supply Portal (`https://dsp.imdpune.gov.in`).
- **Advantage:** Predictable statutory process. Upon payment via Bharatkosh and standard non-commercial undertaking, IMD provides clean, quality-controlled hourly SDI-12 telemetry at 10, 30, 70, and 100 cm.
- **Estimated Timeline:** 1–3 weeks for fulfillment.

### Priority 2: COSMOS-India Pune Station (`IITM-PUNE-COSMOS`)
- **Action:** Submit an official research application letter to Dr. Milind Mujumdar (Scientist-F) and the Director, IITM Pune.
- **Advantage:** Provides continuous hourly Stevens Hydra Probe FDR data (5, 15, 50 cm) and CRNS area data from 2017 to Present.
- **Estimated Timeline:** 2–4 weeks for institutional clearance.

### Priority 3: PoCRA Amravati & Jalna Networks (`POCRA-AMRAVATI-DARYAPUR`, `POCRA-JALNA-BADNAPUR`)
- **Action:** Submit data requisition through the Project Director, PoCRA PMU, Department of Agriculture, Govt. of Maharashtra, Mumbai.
- **Advantage:** Directly targets deep Vertisols under rainfed cotton/soybean where transfer from Alabama Model 1 is most urgently required.
- **Estimated Timeline:** 3–6 weeks.

### Priority 4: State Agricultural Universities (`MPKV-RAHURI-CAAST`, `VNMKV-PARBHANI-CRS`)
- **Action:** Execute Academic Research Collaboration MoUs with the Director of Research, MPKV Rahuri and VNMKV Parbhani.
- **Advantage:** High density of agrometeorological and agronomic trial records.
- **Estimated Timeline:** 4–8 weeks.

---

## 6. Impact on Environmental Extraction & Model Training

### 6.1 Environmental Predictor Extraction: READY TO PROCEED
- Satellite data (Sentinel-1 SAR VV/VH, Sentinel-2 Optical MSI), atmospheric reanalysis (ERA5-Land hourly), static soil properties (SoilGrids 250m, HWSD v2.0), and topographic covariates (MERIT DEM) are completely independent of ground-truth probe telemetry.
- Coordinates for all 16 candidate stations are fully verified and ground-truthed.
- Preprocessing and feature engineering pipelines can extract complete 2015–2023 environmental time series at all station coordinates immediately.

### 6.2 Model Training & Calibration: STRICTLY GATED
- Model training, transfer fine-tuning, and evaluation require verified in-situ volumetric soil water content targets ($\theta$).
- **No model training can occur** until raw ground-truth datasets are legally delivered and integrated into the repository.
- Alabama Model 1 artifacts and inference pipelines must remain unmodified.

---

## 7. Formal Audit Verdict: GO / NO-GO Decision

| Activity | Decision | Justification |
| :--- | :---: | :--- |
| **Environmental Predictor Data Extraction** | **GO (Approved)** | Station coordinates and environmental data access (Copernicus, ECMWF, ISRIC) are open and verified. Extraction pipelines can proceed without ground targets. |
| **Ground-Truth Target Ingestion** | **WAIT / PROCEED WITH REQUISITION** | Formal institutional requisitions must be submitted to IITM Pune, IMD Pune (Bharatkosh), and PoCRA PMU. |
| **Model 2 Architecture & Maharashtra Training** | **NO-GO (Strictly Gated)** | Ground-truth observations are currently unavailable in the local environment. Training models prior to official dataset receipt violates project integrity rules. |

