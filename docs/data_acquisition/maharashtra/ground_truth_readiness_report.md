# SoilDepth-AI — Maharashtra Ground-Truth Acquisition & Training Readiness Report

**Phase:** Phase 2D Multi-Station Expansion  
**Audit Standard:** ISO-19157 / SoilDepth-AI High-Assurance QA  
**Date:** October 31, 2026  
**Decision:** **BLOCKED_AWAITING_IN_SITU_GROUND_TRUTH (NO-GO for Supervised Model Training)**  

---

## 1. Executive Summary

This independent readiness audit evaluated the operational and physical availability of in-situ root-zone soil moisture (RZSM) ground-truth datasets across Maharashtra State, India. The audit surveyed 16 candidate observatories across five primary sensor network custodians:
1. **COSMOS-India / MoES-NERC** (Cosmic-Ray Neutron Sensors)
2. **India Meteorological Department (IMD)** (Agrimet Soil Moisture Observatories)
3. **State Agricultural Universities (SAUs: MPKV, Dr. PDKV, VNMKV, Dr. BSKKV)**
4. **ICAR Central Institutes (NIASM, CICR, NBSS&LUP, CRIDA)**
5. **Project on Climate Resilient Agriculture (PoCRA-II / World Bank)**

### Core Finding:
- **Zero in-situ ground-truth observations are currently accessible via open public download.**
- **Zero synthetic ground-truth values have been fabricated.**
- **Environmental predictor extraction has completed for the 2 configured pilot stations (IITM-PUNE and MPKV-RAHURI-CAAST)**; the remaining 14 statewide candidate stations remain in `FALSE_EXTRACTION_PENDING` status. **Supervised regional model training is strictly BLOCKED** pending the receipt and cryptographic verification of official ground-truth telemetry.

---

## 2. Station Classification & Sensor Modalities

| Category / Network | Station Count | Representative Stations | Primary Sensor Physics | Measurement Footprint | Typical Depths |
| :--- | :---: | :--- | :--- | :---: | :---: |
| **Cosmic-Ray Neutron Probes (CRNS)** | 2 | `IITM-PUNE-COSMOS`, `PDKV-AKOLA-COSMOS` | Fast neutron attenuation | $\sim 200\text{ m}$ radius | $0\text{--}30\text{ cm}$ (effective integrated) |
| **Automated In-Situ Probes (FDR / Capacitance / TDR)** | 7 | `IMD-AGRIMET-PUNE`, `MPKV-RAHURI-CAAST`, `NIASM-BARAMATI-FLUX`, `VNMKV-PARBHANI-AWS`, `POCRA-CHHATRAPATI-SAMBHAJINAGAR`, `POCRA-JALNA-CLUSTER`, `CICR-NAGPUR-EDDY` | High-frequency dielectric permittivity | Point / cylinder ($\sim 10\text{ cm}$) | 5, 10, 20, 30, 50, 60 cm |
| **Dryland / Pedon Benchmark Networks** | 3 | `AICRPDA-SOLAPUR`, `NBSS-LUP-NAGPUR`, `BSKKV-DAPOLI-AGROMET` | Gravimetric / TDR / Suction plates | Core samples | 15, 30, 60, 90, 100 cm |
| **Manual / Periodic Research Trials** | 4 | `CRIDA-KVK-BARAMATI`, `MPKV-KASBE-DIGRAJ`, `PDKV-YAVATMAL-COTTON`, `VNMKV-BADNAPUR-PULSES` | Gravimetric / Tensiometer / Neutron moisture meter | Periodic plot trials | Unscheduled |

---

## 3. Sensor Depth Compatibility Audit (vs Model 1 Architecture)

SoilDepth-AI Model 1 was trained and validated at AAMU-JTG (Alabama) on four standard ISMN profile depths:
- **5.08 cm** (2 inches)
- **10.16 cm** (4 inches)
- **20.32 cm** (8 inches)
- **50.80 cm** (20 inches)

A rigorous depth-compatibility audit of Maharashtra candidate networks reveals fundamental structural and physical distinctions:

### 3.1 Point Sensors vs Layer-Averaged CRNS
- **CRNS (`IITM-PUNE-COSMOS`, `PDKV-AKOLA-COSMOS`):** Measures moderated epithermal/fast neutron flux reflected from the surrounding $\sim 200\text{ m}$ radius. The effective sensing depth ($z^*$) is dynamic: $\sim 12\text{--}15\text{ cm}$ in wet saturated soils up to $\sim 30\text{--}35\text{ cm}$ in dry Vertisols.
  - **Verdict:** CRNS measurements represent a non-linear, vertically weighted average over $0\text{--}30\text{ cm}$. **CRNS cannot be equated to discrete point sensors at 5.08 cm or 10.16 cm without an explicit forward neutron moderation model or vertical calibration weighting.**
  - Point models trained on ISMN sensors cannot be directly evaluated against CRNS without introducing profound representativeness errors.

### 3.2 Point Sensor Depth Compatibility
- **`IMD-AGRIMET-PUNE`:** Probes at 5, 10, 20, 50, 100 cm. **Fully compatible** with Model 1 (depth error $< 0.8\text{ cm}$).
- **`MPKV-RAHURI-CAAST`:** Probes at 10, 20, 30, 60 cm. **Partially compatible** (10 cm and 20 cm match; 5 cm and 50 cm missing).
- **`NIASM-BARAMATI-FLUX`:** Probes at 10, 20, 30, 50 cm. **Partially compatible** (10, 20, 50 cm match; 5 cm missing).
- **`AICRPDA-SOLAPUR` & `CICR-NAGPUR-EDDY`:** Probes at 15, 30, 60, 90 cm. **Incompatible off-depths.**

### 3.3 Strict Sensor-Depth Integrity Rule
> [!CAUTION]
> **Strict Prohibition on Inter-Depth Interpolation:** Under SoilDepth-AI engineering standards, it is strictly forbidden to linearly interpolate or extrapolate between disparate sensor depths (e.g. averaging a 10 cm and 30 cm probe to invent a "20 cm" target, or extrapolating 20 cm to claim a "50 cm" prediction). Every ground-truth record must reflect genuine physical instrumentation at that specific horizon.

---

## 4. Institutional Access Status & Blocker Analysis

A comprehensive tracker of institutional requisitions and blockers is documented below:

| Station ID | Institutional Authority | Access Classification | Requisition Status | Specific Blocker / Prerequisite |
| :--- | :--- | :--- | :--- | :--- |
| `IITM-PUNE-COSMOS` | Indian Institute of Tropical Meteorology (MoES) | `VERIFIED_RESTRICTED_ACCESS` | `READY_FOR_SUBMISSION` | Official institutional dispatch packet finalized (`SOILDEPTH-REQ-2026-001`); awaiting user dispatch. |
| `IMD-AGRIMET-PUNE` | India Meteorological Department (IMD) Pune | `VERIFIED_RESTRICTED_ACCESS` | `READY_FOR_SUBMISSION` | Formal academic data supply packet finalized (`SOILDEPTH-REQ-2026-004`); pending NDC portal submission & Bharatkosh payment. |
| `MPKV-RAHURI-CAAST` | MPKV Rahuri / ICAR-NAHEP CAAST | `VERIFIED_RESTRICTED_ACCESS` | `READY_FOR_SUBMISSION` | Academic bilateral data-sharing packet finalized (`SOILDEPTH-REQ-2026-003`); addressed to Director of Research. |
| `NIASM-BARAMATI-FLUX` | ICAR National Institute of Abiotic Stress Management | `VERIFIED_RESTRICTED_ACCESS` | `READY_FOR_SUBMISSION` | Academic collaborative research packet finalized (`SOILDEPTH-REQ-2026-002`); addressed to Director, ICAR-NIASM. |
| `POCRA-CHHATRAPATI-SAMBHAJINAGAR` | PoCRA / Govt of Maharashtra / World Bank | `VERIFIED_RESTRICTED_ACCESS` | `READY_FOR_SUBMISSION` | Formal academic request packet finalized (`SOILDEPTH-REQ-2026-005`); addressed to Project Director, PoCRA PMU. |
| `POCRA-JALNA-CLUSTER` | PoCRA / Govt of Maharashtra / World Bank | `VERIFIED_RESTRICTED_ACCESS` | `READY_FOR_SUBMISSION` | Covered under PoCRA PMU Mumbai dispatch packet (`SOILDEPTH-REQ-2026-005`). |
| `AICRPDA-SOLAPUR` | All India Coordinated Research Project for Dryland Agriculture | `VERIFIED_RESTRICTED_ACCESS` | `DRAFTED_NOT_SENT` | Daily digital telemetry unreleased; archived in printed annual progress reports. |
| `PDKV-AKOLA-COSMOS` | Dr. PDKV Akola / UKCEH COSMOS-India | `VERIFIED_RESTRICTED_ACCESS` | `DRAFTED_NOT_SENT` | Campaign-based calibration data held under restricted NERC-MoES research agreement. |
| `VNMKV-PARBHANI-AWS` | Vasantrao Naik Marathwada Krishi Vidyapeeth | `VERIFIED_RESTRICTED_ACCESS` | `DRAFTED_NOT_SENT` | Requires academic data agreement with Department of Agricultural Meteorology. |
| `CICR-NAGPUR-EDDY` | ICAR Central Institute for Cotton Research | `VERIFIED_RESTRICTED_ACCESS` | `DRAFTED_NOT_SENT` | Research farm profile probes gated by Division of Crop Production clearance. |
| `NBSS-LUP-NAGPUR` | ICAR National Bureau of Soil Survey & Land Use Planning | `VERIFIED_RESTRICTED_ACCESS` | `DRAFTED_NOT_SENT` | Benchmark pedon database requires institutional authorization. |
| `BSKKV-DAPOLI-AGROMET` | Dr. Balasaheb Sawant Konkan Krishi Vidyapeeth | `VERIFIED_RESTRICTED_ACCESS` | `DRAFTED_NOT_SENT` | Operational observatory records archived in manual paper registers; continuous digital telemetry unverified. |
| `CRIDA-KVK-BARAMATI` | ICAR-CRIDA NICRA Project / KVK Baramati | `ACCESS_STATUS_UNKNOWN` | `MERELY_IDENTIFIED` | Continuous digital logging unverified; station existence confirmed. |
| `MPKV-KASBE-DIGRAJ` | MPKV Regional Sugarcane Research Station | `ACCESS_STATUS_UNKNOWN` | `MERELY_IDENTIFIED` | Field trials active; permanent digital logging unconfirmed. |
| `PDKV-YAVATMAL-COTTON` | Dr. PDKV Cotton Research Station Yavatmal | `ACCESS_STATUS_UNKNOWN` | `MERELY_IDENTIFIED` | Historical neutron probe records in paper archives; continuous digital sensors unverified. |
| `VNMKV-BADNAPUR-PULSES` | VNMKV ARS Badnapur | `ACCESS_STATUS_UNKNOWN` | `MERELY_IDENTIFIED` | Periodic trial measurements during drydown; no continuous digital telemetry. |

---

## 5. Training Readiness Decision & Next Steps

### Official Audit Verdict:
```
================================================================================
MAHARASHTRA SUPERVISED MODEL TRAINING READINESS:
STATUS: BLOCKED_AWAITING_IN_SITU_GROUND_TRUTH
DECISION: NO-GO FOR MODEL 2 / REGIONAL TRAINING
================================================================================
```

### Mandatory Prerequisites to Unblock Training:
1. **At least one official in-situ ground-truth time series must be received and authenticated.**
2. **The dataset must pass all 6 validations in `MaharashtraGroundTruthAdapter`**:
   - Timestamp chronology and duplicate elimination
   - Coordinate consistency ($\le 0.05^\circ$ error)
   - Sensor depth integrity (positive physical depth $\le 200\text{ cm}$; zero inter-depth interpolation)
   - Physical VWC range checks ($0.00 \le \theta \le 0.65\text{ m}^3/\text{m}^3$)
   - Timezone alignment to UTC
   - Cryptographic SHA-256 manifest registration
3. **If CRNS data (`IITM-PUNE-COSMOS`) arrives first:** A dedicated layer-averaged calibration model or neutron moderation forward operator must be developed. CRNS cannot be mixed with discrete point-sensor depth targets.
4. **If IMD or MPKV point probes arrive first:** Multi-depth point models can be trained strictly on verified instrumented depths (e.g. 5, 10, 20, 50 cm for IMD; 10, 20, 30, 60 cm for MPKV).

