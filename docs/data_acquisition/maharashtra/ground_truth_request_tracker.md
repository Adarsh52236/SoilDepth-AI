# SoilDepth-AI — Maharashtra Ground-Truth Data Request Tracker

**Document ID:** `DOC-MAHA-GT-TRACKER-2026`  
**Phase:** Phase 2F (Institutional Request Dispatch Readiness)  
**Standard:** SoilDepth-AI Project Governance & Data Provenance Policy  
**Branch:** `main`  
**Last Updated:** November 3, 2026  

---

## 1. Ground-Truth Requisition Summary

| Tracked Stations | Total Candidate Stations | Formal Requests Submitted | Requests Ready for Submission | Requests Drafted (Incomplete) | Merely Identified as Necessary | Data Received | Data Verified | Model Training Approved |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16** | **16** | **0** | **5 Packets (6 Stations)** | **0** | **10** | **0** | **0** | **0 (BLOCKED)** |

> [!IMPORTANT]
> **Phase 2F Milestone Status:** All five formal institutional request packets (`IITM`, `NIASM`, `MPKV`, `IMD`, `PoCRA`) have completed Phase 2F review, contact verification, and attachment specification. Their status is promoted to **`READY_FOR_SUBMISSION`**. In strict accordance with SoilDepth-AI high-assurance anti-fabrication rules, **no request is marked as `REQUEST_SUBMITTED` until official submission receipts, portal application numbers, or stamped delivery slips are archived in the repository**.

---

## 2. Standard Nine-State Status Taxonomy

Every candidate station and institutional requisition strictly adheres to this 9-state state machine:

1. **`MERELY_IDENTIFIED`:** Identified in research literature or institutional registries; no requisition documents prepared.
2. **`DRAFTED_NOT_SENT`:** Request letter drafted but awaiting formal attachments, contact verification, or review.
3. **`READY_FOR_SUBMISSION`:** Request packet finalized, contacts verified, attachments specified, awaiting academic supervisor physical signature and dispatch.
4. **`REQUEST_SUBMITTED`:** Formally submitted via official portal, institutional email, or speed post, backed by archival submission evidence.
5. **`ACKNOWLEDGED`:** Target institution issues formal receipt, ticket number, or proforma invoice.
6. **`APPROVED`:** Data access formally approved by competent authority; payment cleared or bilateral MOU executed.
7. **`DATA_RECEIVED`:** Raw observational files and metadata physically received or downloaded into `dataset/Maharashtra/raw/`.
8. **`DATA_VERIFIED`:** Dataset successfully evaluated and passed all 10 gates of the SoilDepth-AI Ingestion Protocol.
9. **`DATA_REJECTED`:** Requisition formally rejected, or data permanently unavailable / incompatible.

---

## 3. Formal Institutional Request Log

### Request 01: `IITM-PUNE-COSMOS`
- **Custodian Institution:** Centre for Climate Change Research (CCCR) / Indian Institute of Tropical Meteorology (IITM), Pune
- **Recipient Authority:** Director, IITM Pune & Scientist-in-Charge, COSMOS-India Network
- **Contact Channels (Verified):** `hmru-cosmos@tropmet.res.in` / `director@tropmet.res.in`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/iitm_cosmos_pune_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/iitm_cosmos_pune_request.md)
- **Requested Dataset:** Hourly CRNS neutron counts ($N, N_{\text{corr}}$), Stevens Hydra Probe FDR soil moisture at 5, 15, and 50 cm, soil temperature, precipitation, and calibration metadata for 2017-01-01 to 2023-12-31.
- **Evidence Audit:** Requisition letter, contact routes, and Annexures A–D finalized.
- **Status:** **`READY_FOR_SUBMISSION`**
- **Action Required for Dispatch:** Institutional endorsement on university letterhead, supervisor signature, dual dispatch (Speed Post + Official Email).

---

### Request 02: `IMD-AGRIMET-PUNE`
- **Custodian Institution:** National Data Centre (NDC), India Meteorological Department, Pune
- **Recipient Authority:** Head, Agrimet Division / National Data Centre (NDC)
- **Portal URL (Verified):** `https://dsp.imdpune.gov.in` (Payment: `https://bharatkosh.gov.in`, Ministry 081 - Earth Sciences)
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/imd_national_data_centre_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/imd_national_data_centre_request.md)
- **Requisition Mode:** Paid Data Supply via Government of India Non-Tax Receipt Portal (Bharatkosh, Category II Academic).
- **Requested Dataset:** Digital capacitive probe hourly/daily soil moisture observations at 10, 30, 70, 100 cm (2015–2023).
- **Evidence Audit:** DSP portal requisition form, Annexures A–D, and Bharatkosh payment instructions prepared.
- **Status:** **`READY_FOR_SUBMISSION`**
- **Action Required for Dispatch:** Online application submission via DSP portal, upload of university undertaking, and Bharatkosh payment remittance upon proforma generation.

---

### Request 03: `MPKV-RAHURI-CAAST`
- **Custodian Institution:** Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri / ICAR-NAHEP CAAST-CSAWM
- **Recipient Authority:** Director of Research & Principal Investigator, CAAST-CSAWM, MPKV Rahuri
- **Contact Channels (Verified):** `caast.csawm2018@gmail.com` / `dr_mpkv@rediffmail.com`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/mpkv_rahuri_caast_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/mpkv_rahuri_caast_request.md)
- **Requisition Mode:** Academic Research Collaboration MoU under ICAR-NAHEP
- **Requested Dataset:** PSMISS IoT station capacitive soil moisture observations at 10, 20, 30, 60 cm across Rahuri central research campus (2018–2023).
- **Evidence Audit:** Formal academic proposal, Annexures A–E, and draft bilateral academic MOU prepared.
- **Status:** **`READY_FOR_SUBMISSION`**
- **Action Required for Dispatch:** PI signature, university letterhead dispatch to Director of Research, MPKV Rahuri.

---

### Request 04: `NIASM-BARAMATI-FLUX`
- **Custodian Institution:** ICAR - National Institute of Abiotic Stress Management (NIASM), Baramati
- **Recipient Authority:** Director, ICAR-NIASM, Baramati, Pune District
- **Contact Channels (Verified):** `director.niasm@icar.gov.in`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/icar_niasm_baramati_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/icar_niasm_baramati_request.md)
- **Requisition Mode:** ICAR Institutional Data Exchange Requisition / Bilateral MOU
- **Requested Dataset:** Multi-depth TDR soil moisture profile observations (10, 20, 30, 50 cm) and eddy covariance soil heat/moisture flux data (2016–2023).
- **Evidence Audit:** Requisition packet, contact verified from ICAR directory, Annexures A–E compiled.
- **Status:** **`READY_FOR_SUBMISSION`**
- **Action Required for Dispatch:** University letterhead printing, PI signature, dispatch to Director, NIASM.

---

### Request 05: `POCRA-AMRAVATI-DARYAPUR` & `POCRA-JALNA-BADNAPUR`
- **Custodian Institution:** Project on Climate Resilient Agriculture (PoCRA), Department of Agriculture, Government of Maharashtra
- **Recipient Authority:** State Project Director, PoCRA PMU Mumbai
- **Contact Channels (Verified):** `pmu.pocra@gov.in`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/maharashtra_pocra_pmu_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/maharashtra_pocra_pmu_request.md)
- **Requisition Mode:** Government Academic Collaboration / Data Access Agreement
- **Requested Dataset:** Micro-watershed IoT capacitive soil moisture observations at 10, 20, 40 cm across Amravati and Jalna clusters (2019–2023).
- **Evidence Audit:** Requisition letter, contact verified from Maharashtra Government portal, Annexures A–E compiled.
- **Status:** **`READY_FOR_SUBMISSION`**
- **Action Required for Dispatch:** University letterhead printing, PI signature, dispatch to State Project Director, Dadar PMU.

---

### Requests 06 to 16: Additional Candidate Stations (Deferred Tier 3)
- **`AICRPDA-SOLAPUR` (MPKV / ICAR-CRIDA):** Dryland Vertisol gravimetric profile auger data. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`NBSSLUP-NAGPUR-HQ` (ICAR-NBSS&LUP):** Benchmark pedon monitoring TDR series. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`PDKV-AKOLA-CRS` (Dr. PDKV Akola):** Central Research Station agronomy farm gravimetric and probe logs. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`CICR-NAGPUR-FARM` (ICAR-CICR):** Research farm cotton Vertisol capacitance probe observations. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`VNMKV-PARBHANI-CRS` (VNMKV Parbhani):** Agrometeorological research farm multi-depth probe logs. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`NHP-CWC-PUNE` (Central Water Commission):** National Hydrology Project telemetry station logs. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`MPKV-JALGAON-ORS` (MPKV Rahuri):** Oilseeds research station periodic gravimetric core logs. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`MPKV-DHULE-ARS` (MPKV Rahuri):** Scarcity zone agricultural research station periodic soil moisture logs. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`BSKKV-DAPOLI-CENTRAL` (Dr. BSKKV Dapoli):** Coastal agrometeorological observatory continuous capacitive probes. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
- **`BSKKV-KARJAT-ARS` (Dr. BSKKV Dapoli):** Lowland rice experimental farm hydrological water table dipwell logs. Status: **`MERELY_IDENTIFIED`** (Contact: `CONTACT_VERIFICATION_REQUIRED`).
