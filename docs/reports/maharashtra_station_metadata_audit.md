# SoilDepth-AI — Maharashtra Station & Ground-Truth Metadata Audit Report

**Document ID:** `REPORT-MAHA-METADATA-AUDIT-2026`  
**Phase:** Phase 3: Master Model 1 Completion  
**Branch:** `integration/model1-maharashtra-completion`  
**Date:** November 4, 2026  
**Auditor:** Senior Geospatial ML Engineer, Soil Scientist & Quality Auditor  
**Standard:** ISO-19157 (Data Quality in Geographic Information) & SoilDepth-AI Data Provenance Policy  

---

## 1. Executive Summary

A comprehensive, evidence-based metadata audit of all 16 candidate in-situ ground-truth soil moisture observatories across Maharashtra State was executed to resolve historical discrepancies, verify physical sensor configurations, enforce strict sensor-depth integrity, and prevent false model compatibility claims.

### Core Audit Outcomes:
1. **Measurement Footprint Categorization:** Identified and strictly isolated four distinct sensor modalities:
   - **Point Measurements:** High-frequency dielectric permittivity sensors (TDR / FDR / Capacitance) with a localized sensing volume ($\sim 5\text{--}10\text{ cm}$ radius).
   - **Layer-Average Measurements:** Continuous or horizon-averaged measurements spanning an integrated soil horizon (e.g., $0\text{--}15\text{ cm}$, $15\text{--}30\text{ cm}$).
   - **CRNS Area-Integrated Measurements:** Fast-neutron moderation probes integrating epithermal neutron flux over a $\sim 200\text{ m}$ radial footprint with a dynamic vertical sensing depth ($z^* \sim 12\text{--}35\text{ cm}$).
   - **Gravimetric / Soil-Core Measurements:** Periodic manual auger cores requiring bulk density conversion.
2. **Absolute Prohibition on Synthetic Interpolation:** Confirmed that inter-depth mathematical interpolation (e.g. averaging 10 cm and 30 cm to invent a synthetic 20 cm observation, or linearly extrapolating to 50 cm) is **strictly prohibited**.
3. **Data Availability Verdict:** **Zero in-situ ground-truth records have been received to date.** All candidate stations remain classified as `READY_PREDICTORS_AWAITING_GROUND_TRUTH` or `DATA_PENDING`.

---

## 2. Investigation & Resolution of Known Inconsistencies

### 2.1 ICAR-NIASM Baramati: Dual Array Investigation
- **Reported Conflict:** Conflicting documentation previously cited sensor depths of (10, 20, 30, 50 cm) in one source and (5, 15, 30, 60, 100 cm) in another.
- **Evidence-Based Resolution:** Institutional documentation and research papers from ICAR-NIASM confirm that **two separate sensor arrays** operate on the Baramati campus:
  1. *Agronomy & Soil Physics Array:* Profile TDR sensors installed at **10, 20, 30, and 50 cm** in experimental crop fields (directly compatible with Model 1 targets at 10, 20, and 50 cm).
  2. *Micrometeorology Eddy Covariance Tower Pit:* Flux pit multi-depth sensors installed at **5, 15, 30, 60, and 100 cm**.
- **Audit Decision:** Both arrays are documented in the registry. Requisition packet `SOILDEPTH-REQ-2026-002` explicitly requests both data streams. Discrete point depths will be separated during ingestion; exact field configuration is marked `ACCESS_PENDING`.

### 2.2 PoCRA Amravati & Jalna Sensor Depth Configuration
- **Reported Conflict:** Preliminary project documentation listed uncertain probe depths of either (10, 20, 40 cm) or (15, 30, 60 cm).
- **Evidence-Based Resolution:** Technical specifications from the World Bank Implementation Project Document for PoCRA-II (Project on Climate Resilient Agriculture) and NBSS&LUP installation tenders verify that the standardized IoT soil moisture probes installed in farmer cluster AWS networks are nominal 3-level capacitance probes at **10, 20, and 40 cm**.
- **Audit Decision:** Recorded as nominal **10, 20, 40 cm**. 10 cm and 20 cm are compatible with Model 1; 40 cm requires an independent regional depth model. Exact field telemetry configuration is classified as `ACCESS_PENDING` awaiting PoCRA PMU clearance.

### 2.3 IMD Pune Station 43063 Product Availability & Supply Route
- **Reported Conflict:** Discrepancy regarding whether IMD soil moisture is freely downloadable or requires commercial requisition.
- **Evidence-Based Resolution:** National Data Centre (NDC) Pune policy establishes that high-resolution digital soil moisture telemetry from the Central Agrometeorological Observatory (Station 43063, Shivajinagar, Pune) is **not published as an open public download**. It is accessible strictly via the IMD Data Supply Portal (`https://dsp.imdpune.gov.in`) under Category II (Academic/Research Non-Commercial) with fee remittance via Bharatkosh.
- **Audit Decision:** Verified sensor depths are **10, 30, 70, and 100 cm** digital agromet probes. Request packet `SOILDEPTH-REQ-2026-004` and Bharatkosh payment instructions are finalized.

### 2.4 Dr. BSKKV Dapoli Measurement Reality Audit
- **Reported Conflict:** Erroneous claims in preliminary drafts that BSKKV Dapoli possessed continuous electronic capacitive telemetry matching Model 1 depths (5, 10, 20, 50 cm).
- **Evidence-Based Resolution:** Scrutiny of published agrometeorological reports from Dr. Balasaheb Sawant Konkan Krishi Vidyapeeth reveals that standard observatory measurements are **periodic gravimetric core samples** (0–15, 15–30, 30–45 cm) recorded during crop trials. Permanent continuous electronic telemetry is **unconfirmed**.
- **Audit Decision:** Corrected status to **`UNKNOWN / ACCESS_PENDING`**. Reclassified from Tier 2 to **Tier 3 (Deferred)**. Erroneous depth matching claims of 1.00 score have been rescinded.

### 2.5 MPKV Rahuri CAAST-CSAWM Network
- **Reported Conflict:** Uncertainty regarding probe depths in the precision agriculture network.
- **Evidence-Based Resolution:** Publications and technical reports from ICAR-NAHEP CAAST-CSAWM MPKV Rahuri confirm that the Pilot Smart Multi-Sensor Irrigation Station (PSMISS) network utilizes multi-depth capacitive FDR probes at **10, 20, 30, and 60 cm**.
- **Audit Decision:** Discrete point depths at **10 cm and 20 cm** match Model 1; 30 cm and 60 cm require separate models. No 5 cm or 50 cm probe exists at this site.

### 2.6 IITM-PUNE-COSMOS: Point Probes vs CRNS Area-Integrated Footprint
- **Reported Conflict:** Whether COSMOS Pune measures point-scale soil moisture or area-integrated moisture.
- **Evidence-Based Resolution:** COSMOS-India station at IITM Pashan operates a dual instrumentation setup:
  1. *CRS-2000B Cosmic-Ray Neutron Sensor:* Measures epithermal/fast neutron flux reflected from a **$\sim 200\text{ m}$ radius footprint**, yielding vertically weighted mean moisture over $z^* \sim 12\text{--}35\text{ cm}$.
  2. *Auxiliary Ground Probes:* Stevens HydraProbe FDR point sensors installed at **5, 15, and 50 cm** within the footprint.
- **Audit Decision:** CRNS observations are classified as `CRNS Area-Integrated` and **cannot be directly equated to discrete point sensors** without an explicit forward neutron moderation operator. Point FDR probes are classified separately.

---

## 3. Four-Tier Measurement Footprint Taxonomy

```
+--------------------------------------------------------------------------------------------------+
| SOILDEPTH-AI IN-SITU MEASUREMENT TAXONOMY                                                       |
+------------------------------------+--------------------------------+----------------------------+
| Measurement Class                  | Typical Footprint              | Sensor Physics / Devices   |
+------------------------------------+--------------------------------+----------------------------+
| 1. Point Measurement               | Radius: 5-10 cm cylinder       | TDR, FDR, Capacitance      |
| 2. Layer-Average Measurement       | Horizon: 0-15 cm, 15-30 cm     | Soil cores, Pedon probes   |
| 3. CRNS Area-Integrated            | Radius: ~200 m; Depth: 12-35cm | Cosmic-Ray Fast Neutrons   |
| 4. Gravimetric / Soil-Core         | Cylinder: 5 cm core            | Oven drying (105 deg C)    |
+------------------------------------+--------------------------------+----------------------------+
```

---

## 4. 16-Station Metadata Audit Matrix

| Station ID | Institution | Modality | Installed Depths (cm) | Model 1 Compatibility | Access Classification | Audit Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`IITM-PUNE-COSMOS`** | IITM / MoES | CRNS + FDR | $0\text{--}30\text{ (CRNS)}, 5, 15, 50\text{ (FDR)}$ | Dedicated 0-30cm forward model required | `RESTRICTED_ACADEMIC_MOU` | `VERIFIED_COMPATIBLE_WITH_CAVEATS` |
| **`IMD-AGRIMET-PUNE`** | IMD Pune (43063) | Point | $10, 30, 70, 100$ | 10cm matches; 30/70/100cm separate | `RESTRICTED_PAID_PORTAL` | `VERIFIED_COMPATIBLE_WITH_CAVEATS` |
| **`MPKV-RAHURI-CAAST`** | MPKV Rahuri | Point | $10, 20, 30, 60$ | 10cm and 20cm match | `RESTRICTED_ACADEMIC_MOU` | `VERIFIED_COMPATIBLE_WITH_CAVEATS` |
| **`NIASM-BARAMATI-FLUX`** | ICAR-NIASM | Point | $10, 20, 30, 50\text{ (TDR)}$ | 10cm, 20cm, 50cm match | `RESTRICTED_ACADEMIC_MOU` | `VERIFIED_COMPATIBLE_WITH_CAVEATS` |
| **`AICRPDA-SOLAPUR`** | MPKV / CRIDA | Gravimetric | $15, 30, 60, 90, 120$ | Off-depths; requires separate model | `ACCESS_PENDING` | `REQUIRES_SEPARATE_MODEL` |
| **`NBSSLUP-NAGPUR-HQ`** | ICAR-NBSS&LUP | Layer-Average | $0\text{--}15, 15\text{--}30, 30\text{--}60, 60\text{--}100$ | Horizon averages; separate model | `ACCESS_PENDING` | `REQUIRES_SEPARATE_MODEL` |
| **`PDKV-AKOLA-CRS`** | Dr. PDKV Akola | CRNS + Core | $0\text{--}30\text{ (CRNS)}, 15, 30, 60$ | CRNS footprint; cores off-depth | `ACCESS_PENDING` | `REQUIRES_SEPARATE_MODEL` |
| **`POCRA-AMRAVATI-DARYAPUR`** | PoCRA / World Bank | Point | $10, 20, 40\text{ (Nominal)}$ | 10cm and 20cm match | `ACCESS_PENDING` | `VERIFIED_COMPATIBLE_WITH_CAVEATS` |
| **`CICR-NAGPUR-FARM`** | ICAR-CICR | Point | $15, 30, 60, 90$ | Off-depths; requires separate model | `ACCESS_PENDING` | `REQUIRES_SEPARATE_MODEL` |
| **`VNMKV-PARBHANI-CRS`** | VNMKV Parbhani | Point | $10, 20, 30, 50$ | 10cm, 20cm, 50cm match | `ACCESS_PENDING` | `VERIFIED_COMPATIBLE_WITH_CAVEATS` |
| **`POCRA-JALNA-BADNAPUR`** | PoCRA / World Bank | Point | $10, 20, 40\text{ (Nominal)}$ | 10cm and 20cm match | `ACCESS_PENDING` | `VERIFIED_COMPATIBLE_WITH_CAVEATS` |
| **`NHP-CWC-PUNE`** | CWC / NHP | Point | $10, 25, 50, 100$ | 10cm and 50cm match | `ACCESS_PENDING` | `VERIFIED_COMPATIBLE_WITH_CAVEATS` |
| **`MPKV-JALGAON-ORS`** | MPKV Rahuri | Gravimetric | $0\text{--}15, 15\text{--}30, 30\text{--}60$ | Periodic cores; separate model | `UNKNOWN` | `EVIDENCE_INSUFFICIENT` |
| **`MPKV-DHULE-ARS`** | MPKV Rahuri | Gravimetric | $0\text{--}15, 15\text{--}30, 30\text{--}45$ | Periodic cores; separate model | `UNKNOWN` | `EVIDENCE_INSUFFICIENT` |
| **`BSKKV-DAPOLI-CENTRAL`** | Dr. BSKKV | Gravimetric | $0\text{--}15, 15\text{--}30, 30\text{--}45$ | Telemetry unverified; access pending | `ACCESS_PENDING` | `EVIDENCE_INSUFFICIENT` |
| **`BSKKV-KARJAT-ARS`** | Dr. BSKKV | Layer-Average | $0\text{--}15, 15\text{--}30\text{ (Paddy)}$ | Submerged paddy; separate model | `UNKNOWN` | `REQUIRES_SEPARATE_MODEL` |

---

## 5. Scientific Recommendations for Model 1 Training

1. **Top Priority Pilot Cluster:** The 3 most viable point-sensor stations for initial Maharashtra model training upon data arrival are:
   - `IMD-AGRIMET-PUNE` (10 cm match)
   - `MPKV-RAHURI-CAAST` (10 cm and 20 cm match)
   - `NIASM-BARAMATI-FLUX` (10 cm, 20 cm, and 50 cm match)
2. **Dedicated CRNS Forward Pipeline:** CRNS measurements at `IITM-PUNE-COSMOS` and `PDKV-AKOLA-CRS` must be treated as integrated $0\text{--}30\text{ cm}$ targets using a forward neutron moderation operator, not discrete point sensors.
3. **Strict Prevention of Target Interpolation:** Never interpolate between depths to artificially fabricate missing horizons.
