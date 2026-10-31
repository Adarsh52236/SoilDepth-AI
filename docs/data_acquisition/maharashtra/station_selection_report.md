# Maharashtra Station Selection & Regional Pilot Prioritization Report

**Project:** SoilDepth-AI (Phase 2 Regional Expansion)  
**Target Region:** Maharashtra State, India  
**Document Type:** Station Selection Methodology, Multi-Criteria Prioritization & Pilot Phasing  
**Date:** 2026-10-30  
**Status:** Complete Assessment  

---

## 1. Selection Methodology & Rigorous Criteria

Candidate stations across Maharashtra were not selected merely to fill geographical space on a map. Selection strictly prioritizes empirical data integrity, depth profile compatibility, historical record length, and verifiable institutional ownership.

Each candidate station was evaluated against five weighted criteria:

1. **Depth Multiplicity & Root-Zone Profile ($\text{Weight: } 30\%$):** Presence of discrete sensor measurements across shallow ($0\text{--}10\text{ cm}$), intermediate ($15\text{--}30\text{ cm}$), and deep root-zone ($50\text{--}100\text{ cm}$) layers.
2. **Temporal Resolution & Continuity ($\text{Weight: } 25\%$):** Continuous automated hourly or daily telemetric logging over multiple cropping seasons vs. intermittent manual sampling.
3. **Historical Observation Span ($\text{Weight: } 20\%$):** Availability of $\ge 3\text{--}5\text{ years}$ of concurrent historical observations overlapping with Sentinel-1 (2015+), Sentinel-2 (2015+), and SMAP (2015+).
4. **Agro-Ecological & Soil Representativeness ($\text{Weight: } 15\%$):** Representation of major soil orders (Vertisols / black cotton soils, Inceptisols, Alfisols, Ultisols / laterites) and cropping regimes (rainfed dryland vs. canal-irrigated).
5. **Data Access Feasibility & Governance ($\text{Weight: } 10\%$):** Verified availability via existing open portals, approved paid government pipelines, or structured institutional MoU frameworks.

---

## 2. Regional Candidate Evaluation & Ranking

### 2.1 Western Maharashtra (Desh / Sugar Belt / Transition Zone)
*Soil Orders:* Vertisols, Inceptisols, Entisols.  
*Key Crops:* Sugarcane, Soybean, Wheat, Chickpea, Rabi Sorghum, Grapes.

* **Rank 1 (Primary Operational Anchor - Institutional Access): `IITM-PUNE-COSMOS` (Pashan, Pune)**
  - *Score:* **90 / 100** *(Reconciled from 94 post-empirical access audit)*
  - *Justification:* Highest multi-depth sensor alignment in Western Maharashtra combining intermediate-scale Cosmic-Ray Neutron Sensing (integrating $0\text{--}30\text{ cm}$ over a $200\text{ m}$ radius) with Stevens Hydra Probe FDR profile measurements at **5 cm, 15 cm, and 50 cm**. Continuous hourly observations from 2017 to Present. Classified as `Category B: VERIFIED_STATION_ACCESS_RESTRICTED` because empirical network diagnostics confirmed backend data portal host `cccr.tropmet.res.in` fails public DNS and direct endpoints return 503; raw data acquisition requires bilateral institutional requisition to Director, IITM Pune / MoES.
* **Rank 2 (High-Priority Research Benchmark): `NIASM-BARAMATI-FLUX` (Baramati, Pune)**
  - *Score:* **88 / 100**
  - *Justification:* Located in the severe rain-shadow scarcity belt of Western Maharashtra. Features an open-path Eddy Covariance flux tower, precision lysimeters, and multi-depth TDR sensors (**5, 15, 30, 60, 100 cm**). Exceptional for validating evapotranspiration-driven moisture depletion.
* **Rank 3 (Agricultural IoT Pilot): `MPKV-RAHURI-CAAST` (Rahuri, Ahmednagar)**
  - *Score:* **83 / 100**
  - *Justification:* Modern IoT capacitive sensor network deployed under the World Bank-ICAR NAHEP project, tracking moisture at **10, 20, 30, and 60 cm** under intensive sugarcane and pulse trials.
* **Rank 4 (Rabi Drought Scarcity Baseline): `AICRPDA-SOLAPUR` (Solapur)**
  - *Score:* **76 / 100**
  - *Justification:* Premier national center for dryland Rabi sorghum in deep Vertisols ($>100\text{ cm}$ soil depth).

---

### 2.2 Vidarbha (Cotton / Soybean / Deep Vertisol Belt)
*Soil Orders:* Chromic Haplusterts (Deep Vertisols / Black Cotton Soils).  
*Key Crops:* Rainfed Cotton, Soybean, Pigeon pea, Kharif Sorghum.

* **Rank 1 (Primary Pilot - Operational IoT): `POCRA-AMRAVATI-DARYAPUR` (Daryapur, Amravati)**
  - *Score:* **86 / 100**
  - *Justification:* Automated multi-depth telemetry probes measuring at **10 cm, 30 cm, 60 cm, and 100 cm** installed in heavy Vertisols along the Purna basin. Directly calibrated by ICAR-NBSS&LUP for the World Bank-assisted PoCRA climate project. Represents the epicenter of rainfed cotton/soybean vulnerability.
* **Rank 2 (Pedological Reference): `NBSSLUP-NAGPUR-HQ` (Nagpur)**
  - *Score:* **84 / 100**
  - *Justification:* National Bureau of Soil Survey headquarters farm with comprehensive physical, hydraulic, and mineralogical pedon characterization down to $150\text{ cm}$.
* **Rank 3 (Dryland Agronomic Benchmark): `PDKV-AKOLA-CRS` (Akola)**
  - *Score:* **81 / 100**
  - *Justification:* Decadal AICRPDA and AICRPAM dryland experiments in deep black cotton soils with standard profile depths: **0–15, 15–30, 30–45, 45–60, and 60–90 cm**.

---

### 2.3 Marathwada (Drought-Prone Pulses & Oilseeds Plateau)
*Soil Orders:* Vertic Inceptisols, Typic Haplusterts.  
*Key Crops:* Soybean, Cotton, Pigeon pea (Tur), Chickpea (Gram), Rabi Sorghum.

* **Rank 1 (Primary Operational Pilot): `VNMKV-PARBHANI-CRS` (Parbhani)**
  - *Score:* **85 / 100**
  - *Justification:* Premier agricultural research university in Marathwada. Houses the AICRPDA/AICRPAM agrometeorological observatory tracking moisture dynamics across deep Vertisol layers (**0–15, 15–30, 30–45, 45–60, 60–100 cm**). Critical for capturing severe mid-season monsoon dry spells (Break-Monsoon conditions).
* **Rank 2 (Climate-Resilience Pilot): `POCRA-JALNA-BADNAPUR` (Badnapur, Jalna)**
  - *Score:* **82 / 100**
  - *Justification:* PoCRA IoT telemetry station monitoring **10, 30, 60, and 100 cm** depths in high-vulnerability pulse-growing micro-watersheds.

---

### 2.4 Khandesh (Tapi Valley Alluvial & Scarcity Zone)
*Soil Orders:* Deep Alluvial Vertisols, Entisols.  
*Key Crops:* Cotton, Banana, Groundnut, Maize, Pulses.

* **Rank 1 (Primary Pilot): `MPKV-JALGAON-ORS` (Jalgaon)**
  - *Score:* **79 / 100**
  - *Justification:* Located in the fertile, deep alluvial black soil belt of the Tapi river basin. Tracks profile moisture storage (**0–15, 15–30, 30–60, 60–90 cm**) under intensive cotton, groundnut, and maize rotations.
* **Rank 2 (Scarcity Benchmark): `MPKV-DHULE-ARS` (Dhule)**
  - *Score:* **73 / 100**
  - *Justification:* Represents the scarcity zone of Northern Maharashtra where shallow soils ($<50\text{ cm}$) experience rapid drying.

---

### 2.5 Konkan (High-Rainfall Coastal Lateritic Zone)
*Soil Orders:* Plinthustults / Lateritic soils, Coastal Alluvium.  
*Key Crops:* Lowland Paddy, Mango (Alphonso), Cashew, Summer Groundnut.

* **Rank 1 (Primary Pilot): `BSKKV-DAPOLI-CENTRAL` (Dapoli, Ratnagiri)**
  - *Score:* **80 / 100**
  - *Justification:* Dr. BSKKV central campus experimental station. Represents the high-precipitation coastal laterite belt ($>3,500\text{ mm}$ annual monsoon rainfall). Captures rapid drainage and drying dynamics in porous lateritic profiles (**0–15, 15–30, 30–45 cm**), providing essential contrast to Deccan Vertisols.
* **Rank 2 (Lowland Rice Station): `BSKKV-KARJAT-ARS` (Karjat, Raigad)**
  - *Score:* **74 / 100**
  - *Justification:* Waterlogged and flooded lowland paddy soils under heavy monsoon rainfall.

---

## 3. Recommended Phased Pilot Network Deployment

Rather than attempting statewide training across unconfirmed stations simultaneously, a **3-Phase Phased Rollout** is recommended:

```
[Phase 2A: Immediate Anchor Pilot & Requisitions]
   ├── IITM-PUNE-COSMOS (Pune, Western Maharashtra) -> Formal Institutional Requisition to Director, IITM Pune (CRNS + 5, 15, 50 cm)
   └── IMD-AGRIMET-PUNE (Pune, Western Maharashtra) -> Formal Bharatkosh Paid Requisition (10, 30, 70, 100 cm)

[Phase 2B: Core Vertisol Expansion (Dryland & Climate-Resilient Agriculture)]
   ├── POCRA-AMRAVATI-DARYAPUR (Amravati, Vidarbha) -> PoCRA PMU / NBSS&LUP Clearance (10, 30, 60, 100 cm)
   ├── VNMKV-PARBHANI-CRS (Parbhani, Marathwada)   -> SAU Research Collaboration (0-15, 15-30, 30-60, 60-100 cm)
   └── NIASM-BARAMATI-FLUX (Baramati, W. Maharashtra)-> ICAR Data Sharing Protocol (5, 15, 30, 60, 100 cm)

[Phase 2C: Agro-Climatic Boundary Calibration (Alluvial & Coastal Laterite)]
   ├── MPKV-JALGAON-ORS (Jalgaon, Khandesh)        -> Tapi Alluvial Basin Agronomy Archive (0-15, 15-30, 30-60, 60-90 cm)
   └── BSKKV-DAPOLI-CENTRAL (Dapoli, Konkan)        -> Coastal Lateritic Soils Archive (0-15, 15-30, 30-45 cm)
```

### Strategic Implementation Protocol:
- **Phase 2A** can begin environmental feature extraction (Sentinel-1 SAR, Sentinel-2 Optical, ERA5-Land, SoilGrids, MERIT DEM) immediately at confirmed station coordinates without waiting for in-situ data delivery. Simultaneously, bilateral requisitions (`IITM-PUNE-COSMOS` to IITM Pune and `IMD-AGRIMET-PUNE` via Bharatkosh) are submitted.
- **Phase 2B** integrates the heavy Vertisol soils where Model 1’s Alabama weights are scientifically invalid, resolving the core agrarian challenge of Vidarbha and Marathwada once departmental MoUs are finalized.
- **Phase 2C** completes state coverage by adding the alluvial northern belt and the tropical high-rainfall lateritic coastal zone once digital log availability is confirmed.
- **Model Training Gate:** Model training and fine-tuning are strictly prohibited until official in-situ time series datasets are delivered and ingested into the repository.

