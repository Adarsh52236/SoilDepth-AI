# Maharashtra Ground-Truth Soil Moisture Station Inventory

**Project:** SoilDepth-AI (Phase 2 Regional Expansion)  
**Target Region:** Maharashtra State, India  
**Document Type:** Ground-Truth Station Assessment & Reconciled Audit  
**Date:** 2026-10-31 (Reconciled Post-Empirical Access Audit)  
**Status:** Complete Reconciled Assessment  

---

## 1. Executive Ground-Truth Summary

To support regional calibration and validation of root-zone soil moisture models across Maharashtra's contrasting agro-climatic zones (Western Maharashtra, Vidarbha, Marathwada, Khandesh, and Konkan), an exhaustive audit and evidence reconciliation of in-situ soil moisture monitoring stations was conducted.

### Core Inventory Findings & Reconciled Evidence Classifications:
- **Total Candidate Stations Cataloged:** 16 stations across 5 geographical divisions and 11 agro-climatic clusters.
- **Category A (VERIFIED_OPERATIONAL_AND_DATA_AVAILABLE):** **0 stations**.
  - No station in Maharashtra offers immediate, unauthenticated public open-download data access.
- **Category B (VERIFIED_STATION_ACCESS_RESTRICTED):** **12 stations**.
  - Deployed, active multi-depth stations requiring institutional agreements, formal research requests, government project clearances, or paid supply pipelines:
    - `IITM-PUNE-COSMOS` (Institutional access via Director IITM Pune / MoES; backend portal unresolvable publicly)
    - `IMD-AGRIMET-PUNE` (Paid Government Supply via IMD National Data Centre / Bharatkosh Portal)
    - `MPKV-RAHURI-CAAST` (Academic MoU / CAAST-CSAWM project clearance)
    - `NIASM-BARAMATI-FLUX` (Formal ICAR Research Requisition)
    - `AICRPDA-SOLAPUR` (AICRPDA / ICAR-CRIDA / MPKV institutional request)
    - `NBSSLUP-NAGPUR-HQ` (ICAR-NBSS&LUP Bhoomi Geoportal / formal request)
    - `PDKV-AKOLA-CRS` (Dr. PDKV Central Research Station research request)
    - `POCRA-AMRAVATI-DARYAPUR` (Govt of Maharashtra Department of Agriculture / PoCRA PMU clearance)
    - `CICR-NAGPUR-FARM` (Formal ICAR Research Request to Director, CICR)
    - `VNMKV-PARBHANI-CRS` (VNMKV Parbhani university research permission)
    - `POCRA-JALNA-BADNAPUR` (Govt of Maharashtra PoCRA PMU clearance)
    - `NHP-CWC-PUNE` (Central Water Commission / India-WRIS portal user approval)
- **Category C (VERIFIED_STATION_DATA_AVAILABILITY_UNKNOWN):** **4 stations**.
  - Operational agricultural research stations verified, but continuous digital soil moisture time series telemetry is unconfirmed (intermittent agronomic trial cores / manual gravimetric records only):
    - `MPKV-JALGAON-ORS`
    - `MPKV-DHULE-ARS`
    - `BSKKV-DAPOLI-CENTRAL`
    - `BSKKV-KARJAT-ARS`
- **Category D (CANDIDATE_STATION_NOT_OPERATIONALLY_VERIFIED):** **0 stations**.
- **Category E (INVALID_OR_DUPLICATE_ENTRY):** **0 stations**.
- **International Soil Moisture Network (ISMN) Coverage in Maharashtra:** **0 stations**.
  - An exhaustive query of `https://ismn.earth` confirms that while India is represented by the `IIT_KANPUR` network (`IITK-Airstrip` in Uttar Pradesh), no participating network or station has ever been integrated from Maharashtra.
- **Multi-Depth Sensor Stations ($\ge 3$ depths):** **14 stations** (supporting surface to root-zone down to 60–120 cm).

---

## 2. Institutional Network Evaluations & Access Evidence

### 2.1 COSMOS-India / COSMOS-IITM Pune
* **Managing Entity:** Indian Institute of Tropical Meteorology (IITM), Pune, under the Ministry of Earth Sciences (MoES), in partnership with the UK Centre for Ecology & Hydrology (UKCEH).
* **Operational Mechanism:** Deploys a stationary Cosmic-Ray Neutron Sensor (CRNS) providing non-invasive, intermediate footprint-scale ($\sim 200\text{ m}$ radius) volumetric soil water content, complemented by a profile network of Stevens Hydra Probe FDR sensors.
* **Depths:** 5 cm, 15 cm, and 50 cm point probes; CRNS provides integrated moisture over the top 0–30 cm with dynamic penetration depth $z^*(t)$.
* **Temporal Resolution:** Hourly continuous observations from 2017 to Present.
* **Reconciled Access Classification:** **Category B: VERIFIED_STATION_ACCESS_RESTRICTED**.
* **Empirical Diagnostics:**
  - Initial reports indicated that `https://cosmos-india.org` was an open download portal. Empirical network testing revealed that while the landing frontend returns `200 OK`, the "Data Portal" redirection target `https://cccr.tropmet.res.in/cosmos-data.php` fails public DNS resolution (`[Errno 11001] getaddrinfo failed`).
  - Direct HTTP requests to portal endpoints (`/data-portal/`, `/stations/`, `/pune/`) on `cosmos-india.org` return `HTTP 503 Service Unavailable`.
  - Peer-reviewed data availability statements (Mujumdar et al., 2021, *J. Hydrol.* 126102; Upadhyaya et al., 2021, *Remote Sens.* 13(3), 537) confirm: observational series are not hosted in an open public archive, but are released upon formal bilateral institutional request to the Director, IITM Pune / MoES.

### 2.2 International Soil Moisture Network (ISMN)
* **Audited Status:** **ZERO STATIONS IN MAHARASHTRA**.
* **Verification Detail:** A full spatial query of `https://ismn.earth` confirms that while India is represented by the `IIT_KANPUR` network (`IITK-Airstrip` in Uttar Pradesh, preserved in `dataset/ISMN/IIT_KANPUR`), no participating network or station has ever been integrated from Maharashtra.
* **Operational Implication:** SoilDepth-AI cannot rely on automated ISMN scrapers for Maharashtra ground truth.

### 2.3 IMD Agro-Meteorological Observatories (Agrimet Division)
* **Managing Entity:** India Meteorological Department (IMD), Agricultural Meteorology Division, Shivajinagar, Pune.
* **Operational Setup:** Standard Agro-AWS stations record soil moisture alongside soil temperature at four standardized subsurface depths: **10 cm, 30 cm, 70 cm, and 100 cm (1 meter)**. Probes utilize SDI-12 digital capacitive/impedance sensors (Water Fraction by Volume).
* **Temporal Resolution:** Hourly telemetric transmission to the National Data Centre (NDC), Pune.
* **Reconciled Access Classification:** **Category B: VERIFIED_STATION_ACCESS_RESTRICTED**.
* **Procurement Protocol:**
  - Governed by the IMD Data Supply Portal (`https://dsp.imdpune.gov.in`).
  - Requires user enrollment, an official institutional undertaking letter, calculation of official data charges + 18% GST, and non-tax receipt payment via the Government of India **Bharatkosh** portal (`https://bharatkosh.gov.in`, Ministry: `081 - EARTH SCIENCES`).
  - Upon payment verification, datasets are released for download.

### 2.4 PoCRA / PoCRA-II Soil Moisture Network
* **Managing Entity:** Project on Climate Resilient Agriculture (Nanaji Deshmukh Krishi Sanjivani Prakalp), Department of Agriculture, Govt. of Maharashtra, with World Bank assistance.
* **Technical Anchor:** ICAR-National Bureau of Soil Survey and Land Use Planning (NBSS&LUP), Nagpur.
* **Operational Scope:** Implemented across 15 climate-vulnerable districts in Marathwada (8 districts), Vidarbha (6 districts), and Khandesh (Jalgaon). Deploys multi-depth automated soil moisture stations measuring down to 1-meter depth to feed village-level water budgets.
* **Depths:** 10 cm, 30 cm, 60 cm, and 100 cm.
* **Temporal Resolution:** Hourly and daily telemetry.
* **Reconciled Access Classification:** **Category B: VERIFIED_STATION_ACCESS_RESTRICTED**.
* **Procurement Protocol:**
  - The live GIS platform (`https://mahapocra.gov.in`) displays dashboard analytics and advisories, but raw tabular time series downloads are restricted to authorized government project personnel and NBSS&LUP researchers.
  - Procurement requires a formal institutional request to the Project Director, PoCRA PMU, Mumbai.

### 2.5 National Hydrology Project (NHP / India-WRIS)
* **Managing Entity:** Ministry of Jal Shakti, Central Water Commission (CWC), in collaboration with NRSC/ISRO.
* **Operational Setup:** Automated hydro-meteorological stations and dedicated soil moisture probe sites deployed for calibrating the national Variable Infiltration Capacity (VIC) hydrological model (5.5 km grid).
* **Depths:** Surface layer (0–10 cm) and root zone.
* **Temporal Resolution:** Daily.
* **Reconciled Access Classification:** **Category B: VERIFIED_STATION_ACCESS_RESTRICTED**.
* **Procurement Protocol:**
  - Drought indicators like the Soil Moisture Availability Index (SMAI) are visualized on Bhuvan NHP (`https://bhuvan.nrsc.gov.in/nhp/`).
  - Raw time series from permanent in-situ probes require user account approval on `https://indiawris.gov.in`.

### 2.6 ICAR & State Agricultural University (SAU) Research Stations
Maharashtra hosts four major agricultural universities and multiple premier ICAR institutes that maintain long-term experimental soil moisture plots under the All India Coordinated Research Project for Dryland Agriculture (AICRPDA) and Agrometeorology (AICRPAM):
1. **MPKV Rahuri (Western Maharashtra):** CAAST-CSAWM IoT sensor stations (PSMISS system; 10, 20, 30, 60 cm) and Solapur dryland station (Category B).
2. **ICAR-NIASM Baramati (Pune district):** Eddy Covariance flux towers, multi-depth soil moisture sensor profiles (5, 15, 30, 60, 100 cm), and precision lysimeter facilities (Category B).
3. **Dr. PDKV Akola (Vidarbha):** Central Research Station long-term AICRPDA Vertisol profile trials (0–15, 15–30, 30–45, 45–60, 60–90 cm) (Category B).
4. **VNMKV Parbhani (Marathwada):** AICRPDA/AICRPAM central dryland station monitoring deep black cotton soils down to 100 cm (Category B).
5. **ICAR-NBSS&LUP (Nagpur):** Benchmark Vertisol pedon monitoring (Category B).
6. **ICAR-CICR (Nagpur):** Rainfed cotton root-zone dynamics (Category B).
7. **Khandesh & Konkan ARS Stations (`MPKV-JALGAON-ORS`, `MPKV-DHULE-ARS`, `BSKKV-DAPOLI-CENTRAL`, `BSKKV-KARJAT-ARS`):** Operational research farms, but ongoing continuous electronic time series are unverified (Category C: Unknown Data Availability).

---

## 3. Station Directory & Reconciled Evidence Classification

| Station ID | Station Name | Network / Institution | Coordinates | District & Region | Active Period | Measurement Method | Available Depths (cm) | Resolution | Evidence Classification | Reconciled Access Procedure |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- | :--- | :---: | :---: | :--- |
| **`IITM-PUNE-COSMOS`** | IITM Pune Campus | COSMOS-India / MoES | $18.5372^\circ\text{ N}, 73.8051^\circ\text{ E}$ | Pune, Western Maharashtra | 2017–Pres. | CRNS + Stevens Hydra Probe FDR | 5, 15, 50 (CRNS integrates 0–30) | Hourly | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Formal institutional request to Director, IITM Pune |
| **`IMD-AGRIMET-PUNE`** | Central Agromet Observatory | IMD Agrimet / NDC | $18.5308^\circ\text{ N}, 73.8507^\circ\text{ E}$ | Pune, Western Maharashtra | 2013–Pres. | Digital Capacitive SDI-12 + Gravimetric Core | 10, 30, 70, 100 | Hourly / Daily | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Paid order via Bharatkosh; request via `dsp.imdpune.gov.in` |
| **`MPKV-RAHURI-CAAST`** | MPKV Central Farm | CAAST-CSAWM / MPKV | $19.3932^\circ\text{ N}, 74.6475^\circ\text{ E}$ | Ahmednagar, Western Maharashtra | 2018–Pres. | IoT Multi-Depth Capacitive / FDR (PSMISS) | 10, 20, 30, 60 | 15-min / Hourly | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Institutional research collaboration MoU with MPKV Rahuri |
| **`NIASM-BARAMATI-FLUX`**| NIASM Research Farm | ICAR-NIASM Baramati | $18.1519^\circ\text{ N}, 74.5828^\circ\text{ E}$ | Pune, Western Maharashtra | 2014–Pres. | Campbell TDR Probes + Eddy Covariance + Lysimeter | 5, 15, 30, 60, 100 | 30-min / Daily | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Formal request to Director, ICAR-NIASM, Baramati |
| **`AICRPDA-SOLAPUR`** | ZARS Solapur Farm | MPKV / AICRPDA | $17.6621^\circ\text{ N}, 75.9103^\circ\text{ E}$ | Solapur, Western Maharashtra | 2015–Pres. | Gravimetric core auger + Neutron Probe / FDR | 0–15, 15–30, 30–60, 60–90, 90–120 | Weekly / Seasonal | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Permission from Director of Research, MPKV / CRIDA |
| **`NBSSLUP-NAGPUR-HQ`** | NBSS&LUP Experimental Farm| ICAR-NBSS&LUP Nagpur | $21.1332^\circ\text{ N}, 79.0305^\circ\text{ E}$ | Nagpur, Vidarbha | 2012–Pres. | TDR Probes + Benchmark Pedon Analysis | 0–15, 15–30, 30–60, 60–100 | Daily / Campaign | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Official request to Director, ICAR-NBSS&LUP Nagpur |
| **`PDKV-AKOLA-CRS`** | PDKV Central Research Station| Dr. PDKV / AICRPDA | $20.7025^\circ\text{ N}, 77.0315^\circ\text{ E}$ | Akola, Vidarbha | 2015–Pres. | Gravimetric core sampling + TDR sensors | 0–15, 15–30, 30–45, 45–60, 60–90 | Weekly / Campaign | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Written request to Director of Research, Dr. PDKV Akola |
| **`POCRA-AMRAVATI-DARYAPUR`**| Daryapur Cluster Station | PoCRA / NBSS&LUP | $20.9284^\circ\text{ N}, 77.3182^\circ\text{ E}$ | Amravati, Vidarbha | 2019–Pres. | Automated IoT multi-depth probes (1 m) | 10, 30, 60, 100 | Hourly / Daily | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | State Department clearance via Project Director, PoCRA |
| **`CICR-NAGPUR-FARM`** | CICR Panjri Farm | ICAR-CICR Nagpur | $21.0617^\circ\text{ N}, 79.0614^\circ\text{ E}$ | Nagpur, Vidarbha | 2015–Pres. | Capacitive FDR sensors + Neutron probe | 15, 30, 60, 90, 120 | Weekly (Kharif-Rabi) | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Formal request to Director, ICAR-CICR, Nagpur |
| **`VNMKV-PARBHANI-CRS`** | VNMKV Central Dryland Farm | VNMKV / AICRPDA | $19.2638^\circ\text{ N}, 76.7824^\circ\text{ E}$ | Parbhani, Marathwada | 2015–Pres. | Gravimetric core + Capacitive FDR probes | 0–15, 15–30, 30–45, 45–60, 60–100 | Weekly / Seasonal | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Written request to Director of Research, VNMKV Parbhani |
| **`POCRA-JALNA-BADNAPUR`** | Badnapur Cluster Station | PoCRA / NBSS&LUP | $19.8692^\circ\text{ N}, 75.7258^\circ\text{ E}$ | Jalna, Marathwada | 2020–Pres. | Automated IoT multi-depth probes | 10, 30, 60, 100 | Hourly / Daily | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | State Department clearance via Project Director, PoCRA |
| **`NHP-CWC-PUNE`** | CWC Hydro-Met Station | CWC / NHP | $18.5204^\circ\text{ N}, 73.8567^\circ\text{ E}$ | Pune, Western Maharashtra | 2018–Pres. | Telemetric in-situ probe + AWS | 0–10, Root-zone | Daily | **B. VERIFIED_STATION_ACCESS_RESTRICTED** | Account registration & permission on `indiawris.gov.in` |
| **`MPKV-JALGAON-ORS`** | Oilseeds Research Station | MPKV Rahuri | $21.0116^\circ\text{ N}, 75.5678^\circ\text{ E}$ | Jalgaon, Khandesh | 2016–Pres. | Gravimetric sampling + FDR sensors | 0–15, 15–30, 30–60, 60–90 | Weekly (Kharif-Rabi) | **C. VERIFIED_STATION_DATA_AVAILABILITY_UNKNOWN** | Research permission via Associate Director, MPKV Jalgaon |
| **`MPKV-DHULE-ARS`** | Scarcity Zone Research Farm | MPKV Rahuri | $20.9042^\circ\text{ N}, 74.7749^\circ\text{ E}$ | Dhule, Khandesh | 2016–Pres. | Gravimetric profile sampling | 0–15, 15–30, 30–45, 45–60 | Weekly (Seasonal) | **C. VERIFIED_STATION_DATA_AVAILABILITY_UNKNOWN** | Written request via Head, ARS Dhule / MPKV Rahuri |
| **`BSKKV-DAPOLI-CENTRAL`**| Dapoli Central Farm | Dr. BSKKV Dapoli | $17.7594^\circ\text{ N}, 73.1906^\circ\text{ E}$ | Ratnagiri, Konkan | 2016–Pres. | Automated FDR sensors + Gravimetric core | 0–15, 15–30, 30–45 | Weekly / Campaign | **C. VERIFIED_STATION_DATA_AVAILABILITY_UNKNOWN** | Written request to Director of Research, BSKKV Dapoli |
| **`BSKKV-KARJAT-ARS`** | Rice Research Station | Dr. BSKKV Dapoli | $18.9103^\circ\text{ N}, 73.3282^\circ\text{ E}$ | Raigad, Konkan | 2016–Pres. | Hydrological root-zone sampling | 0–15, 15–30 | Weekly (Kharif) | **C. VERIFIED_STATION_DATA_AVAILABILITY_UNKNOWN** | Research permission via Officer In-charge, ARS Karjat |

---

## 4. Measurement Method Differentiation & Depth Compatibility

### 4.1 Measurement Technology Distinction
1. **Discrete Point-Scale Probes (Stevens Hydra Probe FDR, Campbell TDR, SDI-12 Capacitive):**
   - Measure localized dielectric permittivity within a cylindrical sensitivity volume of $\sim 0.5\text{--}1.5\text{ dm}^3$.
   - Directly aligned with SoilDepth-AI's physical target architecture at discrete depths (5, 10, 15, 20, 30, 50, 60, 70, 100 cm).
2. **Cosmic-Ray Neutron Sensors (CRNS):**
   - Non-invasive intermediate footprint ($\sim 200\text{ m}$ radius).
   - Measures an area-integrated volumetric soil moisture over a dynamically fluctuating effective penetration depth $z^*(t) \approx \frac{5.8}{\rho_{bd} \cdot \theta + 0.09}$, ranging from $\sim 12\text{ cm}$ in wet saturated soils to $\sim 30\text{ cm}$ in bone-dry soils.
   - **Crucial Rule:** Cannot be treated as a fixed-depth point probe without calibration against in-situ FDR/TDR profiles.
3. **Gravimetric Profile Sampling (Core Augers):**
   - Manual, destructive sampling providing mass-based moisture ($\text{g/g}$), requiring bulk density ($\rho_{bd}$) correction to convert to volumetric water content ($\text{cm}^3/\text{cm}^3$).
   - Represent integrated soil layers (e.g., 0–15 cm, 15–30 cm).

### 4.2 Alignment with SoilDepth-AI Depth Architecture
- **Depth 1 (~5 cm):** `IITM-PUNE-COSMOS` (5 cm FDR), `NIASM-BARAMATI-FLUX` (5 cm TDR).
- **Depth 2 (~10 cm):** `IMD-AGRIMET-PUNE` (10 cm SDI-12), `MPKV-RAHURI-CAAST` (10 cm), `POCRA-*` (10 cm).
- **Depth 3 (~20 cm):** `MPKV-RAHURI-CAAST` (20 cm), `IITM-PUNE-COSMOS` (15 cm FDR), `NIASM-BARAMATI-FLUX` (15 & 30 cm TDR).
- **Depth 4 (~50 cm):** `IITM-PUNE-COSMOS` (50 cm FDR), `MPKV-RAHURI-CAAST` (60 cm), `NIASM-BARAMATI-FLUX` (60 cm), `POCRA-*` (60 cm), `IMD-AGRIMET-PUNE` (70 cm).
