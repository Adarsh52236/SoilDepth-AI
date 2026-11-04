# SoilDepth-AI — Phase 3 Operational Ground-Truth Acquisition Tracker

**Project:** SoilDepth-AI  
**Phase:** Phase 3: Maharashtra Ground-Truth Acquisition  
**Branch:** `feature/maharashtra-ground-truth-tracker`  
**Date:** November 4, 2026  
**Baseline Lock:** Model 1 Frozen at commit `339897e`  
**Integrity Standard:** ISO-19157 / SoilDepth-AI High-Assurance Protocol  

---

## 1. Executive Summary

Phase 3 transitions SoilDepth-AI from environmental predictor preparation to the active acquisition, tracking, and high-assurance cryptographic ingestion of verified in-situ root-zone soil moisture observations across Maharashtra State, India.

All model architectures, training workflows, and baseline weights remain **strictly frozen**. In strict accordance with SoilDepth-AI scientific integrity standards:
- **No request is marked as `SUBMITTED` without tangible archival submission evidence** (e.g., postal speed post receipt, delivery scan, or DSP portal application receipt).
- **Zero synthetic, simulated, or vertically interpolated values** are accepted as ground truth.
- Each of the five formal academic request packets possesses a dedicated evidence and dataset repository under `dataset/Maharashtra/acquisition/`.

---

## 2. Central Institutional Request Tracker

| Request ID | Target Institution | Station IDs | Contact Route | Requested Period | Requested Depths | Submission Status | Acknowledgement Status | Expected Delivery Format | Follow-up Date | Evidence Repository |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: | :---: | :--- | :---: | :--- |
| **`SOILDEPTH-REQ-2026-001`** | **IITM / MoES Pune** | `IITM-PUNE-COSMOS` | `director@tropmet.res.in`<br>`hmru-cosmos@tropmet.res.in` | 2017-01-01 to 2023-12-31 | $0\text{--}30\text{ cm}$ dynamic CRNS footprint; 5, 15, 50 cm FDR point probes | `DRAFTED` | `PENDING_SUBMISSION` | CSV / NetCDF hourly & daily | `PENDING_DISPATCH` | [`REQ-001-IITM-PUNE`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/Maharashtra/acquisition/SOILDEPTH-REQ-2026-001-IITM-PUNE/) |
| **`SOILDEPTH-REQ-2026-002`** | **ICAR-NIASM Baramati** | `NIASM-BARAMATI-FLUX` | `director.niasm@icar.gov.in` | 2017-01-01 to 2023-12-31 | 10, 20, 30, 50 cm Agronomy TDR array; 5, 15, 30, 60, 100 cm Flux Pit | `DRAFTED` | `PENDING_SUBMISSION` | CSV / Excel (.xlsx) daily/hourly | `PENDING_DISPATCH` | [`REQ-002-ICAR-NIASM`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/Maharashtra/acquisition/SOILDEPTH-REQ-2026-002-ICAR-NIASM/) |
| **`SOILDEPTH-REQ-2026-003`** | **MPKV Rahuri CAAST** | `MPKV-RAHURI-CAAST` | `dr_mpkv@rediffmail.com`<br>`caast.csawm2018@gmail.com` | 2017-01-01 to 2023-12-31 | 10, 20, 30, 60 cm PSMISS IoT capacitive array | `DRAFTED` | `PENDING_SUBMISSION` | CSV / Excel (.xlsx) hourly/daily | `PENDING_DISPATCH` | [`REQ-003-MPKV-RAHURI`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/Maharashtra/acquisition/SOILDEPTH-REQ-2026-003-MPKV-RAHURI/) |
| **`SOILDEPTH-REQ-2026-004`** | **IMD NDC Pune** | `IMD-AGRIMET-PUNE` | `https://dsp.imdpune.gov.in`<br>`ndc.pune@imd.gov.in` | 2017-01-01 to 2023-12-31 | 10, 30, 70, 100 cm Agromet digital probes (Station 43063) | `DRAFTED` | `PENDING_SUBMISSION` | Standard IMD CSV / ASCII fixed-width | `PENDING_DISPATCH` | [`REQ-004-IMD-PUNE`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/Maharashtra/acquisition/SOILDEPTH-REQ-2026-004-IMD-PUNE/) |
| **`SOILDEPTH-REQ-2026-005`** | **Maharashtra PoCRA PMU** | `POCRA-AMRAVATI-DARYAPUR`<br>`POCRA-JALNA-BADNAPUR` | `pmu.pocra@gov.in`<br>`projectdirector@mahapocra.gov.in` | 2019-01-01 to 2023-12-31 | 10, 20, 40 cm agronomic IoT capacitance probes | `DRAFTED` | `PENDING_SUBMISSION` | JSON / CSV API export | `PENDING_DISPATCH` | [`REQ-005-POCRA-PMU`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/Maharashtra/acquisition/SOILDEPTH-REQ-2026-005-POCRA-PMU/) |

---

## 3. Strict Six-State Status Taxonomy & Transition Machine

The status of each request strictly progresses through the following sequential states:

```
 [ DRAFTED ] ──(PI Endorsement)──> [ APPROVED ] ──(Physical Dispatch & Receipt)──> [ SUBMITTED ]
                                                                                           │
                                                                                 (Institutional Ack)
                                                                                           ▼
 [ DATA_VERIFIED ] <──(Protocol Gates & Checklists)── [ DATA_RECEIVED ] <──(File Delivery)── [ ACKNOWLEDGED ]
```

### Definitions & Gate Requirements:
1. **`DRAFTED`**:
   - Request letter, annexures, and data specifications fully compiled and verified.
   - Pending physical signature and official university seal.
2. **`APPROVED`**:
   - Academic Principal Investigator (PI) or Department Head has formally endorsed the packet.
   - Signed PDF copy archived in `dataset/Maharashtra/acquisition/<REQUEST_DIR>/signed_letters/`.
3. **`SUBMITTED`**:
   - Packet formally dispatched via India Post Registered Speed Post, official institutional email, or Government Data Portal.
   - **Mandatory Prerequisite:** Postal receipt scan with tracking barcode, official mail server delivery confirmation (`.eml`), or portal submission receipt PDF must be deposited in `dataset/Maharashtra/acquisition/<REQUEST_DIR>/receipts/` or `email_evidence/`.
   - `submission_date` and `follow_up_date` (submission + 10 to 14 business days) recorded in the tracker.
4. **`ACKNOWLEDGED`**:
   - Target institution issues an official acknowledgement, registration ticket number, DSP portal application number, or proforma invoice.
   - Confirmation archived in `receipts/` or `email_evidence/`.
5. **`DATA_RECEIVED`**:
   - Raw observational data files and metadata delivered via portal download, email attachment, or secure transfer.
   - Raw unmodified files placed in `dataset/Maharashtra/acquisition/<REQUEST_DIR>/received_datasets/`.
   - Initial SHA-256 manifest generated.
6. **`DATA_VERIFIED`**:
   - Dataset passes all 7 validation gates of the Data-Receipt Checklist and `MaharashtraGroundTruthAdapter.ingest_file(..., strict=True)`.
   - Target depths authenticated against physical station records.
   - Data promoted to `dataset/Maharashtra/ground_truth/verified/` to unblock regional model training.

> [!CAUTION]
> **Anti-Fabrication Enforcement:** Any change of status to `SUBMITTED`, `ACKNOWLEDGED`, `DATA_RECEIVED`, or `DATA_VERIFIED` that lacks corresponding documentary evidence in the designated folder is invalid and constitutes a protocol violation.

---

## 4. Evidence & Dataset Repository Structure

Dedicated repositories are initialized for every request under `dataset/Maharashtra/acquisition/`:

```
dataset/Maharashtra/acquisition/
├── SOILDEPTH-REQ-2026-001-IITM-PUNE/
│   ├── signed_letters/       <- Scanned PDF of PI-signed university request letter
│   ├── email_evidence/       <- .eml exports or delivery confirmation logs
│   ├── receipts/             <- Speed post barcode slips or portal receipts
│   ├── received_datasets/    <- Raw incoming in-situ datasets (unmodified)
│   └── README.md
├── SOILDEPTH-REQ-2026-002-ICAR-NIASM/
│   ├── signed_letters/
│   ├── email_evidence/
│   ├── receipts/
│   ├── received_datasets/
│   └── README.md
├── SOILDEPTH-REQ-2026-003-MPKV-RAHURI/
│   ├── signed_letters/
│   ├── email_evidence/
│   ├── receipts/
│   ├── received_datasets/
│   └── README.md
├── SOILDEPTH-REQ-2026-004-IMD-PUNE/
│   ├── signed_letters/
│   ├── email_evidence/
│   ├── receipts/             <- DSP application acknowledgment & Bharatkosh challan
│   ├── received_datasets/
│   └── README.md
└── SOILDEPTH-REQ-2026-005-POCRA-PMU/
    ├── signed_letters/
    ├── email_evidence/
    ├── receipts/
    ├── received_datasets/
    └── README.md
```

---

## 5. Institutional Requisition Profiles

### 5.1 Request 001 — IITM / MoES COSMOS Pune
- **Request ID:** `SOILDEPTH-REQ-2026-001`
- **Target Station:** `IITM-PUNE-COSMOS` ($18.5372^\circ\text{ N}, 73.8051^\circ\text{ E}$, Elevation $560.0\text{ m}$)
- **Authority:** Director, IITM Pune & Scientist-in-Charge, COSMOS-India Network
- **Official Address:** Indian Institute of Tropical Meteorology, Dr. Homi Bhabha Road, Pashan, Pune – 411008, Maharashtra
- **Contact Channels:** `director@tropmet.res.in`, `hmru-cosmos@tropmet.res.in`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/iitm_cosmos_pune_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/iitm_cosmos_pune_request.md)
- **Requested Parameters:** Hourly corrected fast neutron counts ($N_{\text{corr}}$), calibrated volumetric water content (effective $0\text{--}30\text{ cm}$), point FDR probes (5, 15, 50 cm), precipitation, and soil temperature for 2017-01-01 to 2023-12-31.
- **Dispatch Route:** Dual dispatch (Registered Speed Post to Pashan Campus + Direct Institutional Email).
- **Follow-up SLA:** 12 business days post-dispatch.

### 5.2 Request 002 — ICAR-NIASM Baramati
- **Request ID:** `SOILDEPTH-REQ-2026-002`
- **Target Station:** `NIASM-BARAMATI-FLUX` ($18.1522^\circ\text{ N}, 74.5028^\circ\text{ E}$, Elevation $570.0\text{ m}$)
- **Authority:** Director, ICAR - National Institute of Abiotic Stress Management
- **Official Address:** ICAR-NIASM, Malegaon Khurd, Baramati, Pune District – 413115, Maharashtra
- **Contact Channels:** `director.niasm@icar.gov.in`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/icar_niasm_baramati_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/icar_niasm_baramati_request.md)
- **Requested Parameters:** Multi-depth TDR profile measurements (10, 20, 30, 50 cm) and eddy covariance soil flux logs (2017-01-01 to 2023-12-31).
- **Dispatch Route:** Registered Speed Post + Official Email to Institute Director.
- **Follow-up SLA:** 14 business days post-dispatch.

### 5.3 Request 003 — MPKV Rahuri CAAST-CSAWM
- **Request ID:** `SOILDEPTH-REQ-2026-003`
- **Target Station:** `MPKV-RAHURI-CAAST` ($19.3932^\circ\text{ N}, 74.6475^\circ\text{ E}$, Elevation $512.0\text{ m}$)
- **Authority:** Director of Research, MPKV Rahuri / PI, CAAST-CSAWM
- **Official Address:** Directorate of Research, MPKV Rahuri, Ahmednagar District – 413722, Maharashtra
- **Contact Channels:** `dr_mpkv@rediffmail.com`, `caast.csawm2018@gmail.com`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/mpkv_rahuri_caast_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/mpkv_rahuri_caast_request.md)
- **Requested Parameters:** PSMISS IoT station capacitive soil moisture telemetry at 10, 20, 30, 60 cm across Rahuri central research farm (2017-01-01 to 2023-12-31).
- **Dispatch Route:** Academic research collaboration proposal with draft SAU MOU.
- **Follow-up SLA:** 14 business days post-dispatch.

### 5.4 Request 004 — IMD National Data Centre Pune
- **Request ID:** `SOILDEPTH-REQ-2026-004`
- **Target Station:** `IMD-AGRIMET-PUNE` ($18.5312^\circ\text{ N}, 73.8553^\circ\text{ E}$, Elevation $559.0\text{ m}$, WMO 43063)
- **Authority:** Head, Climate Research and Services (CRS) / National Data Centre (NDC)
- **Official Address:** National Data Centre, India Meteorological Department, Shivaji Nagar, Pune – 411005, Maharashtra
- **Contact Channels:** `https://dsp.imdpune.gov.in`, `ndc.pune@imd.gov.in`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/imd_national_data_centre_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/imd_national_data_centre_request.md)
- **Requested Parameters:** Digital agromet capacitive/TDR probe soil moisture observations at 10, 30, 70, 100 cm (2017-01-01 to 2023-12-31).
- **Dispatch Route:** Web portal registration via IMD DSP (`https://dsp.imdpune.gov.in`), university non-commercial undertaking upload, and non-commercial fee remittance via Bharatkosh (`https://bharatkosh.gov.in`).
- **Follow-up SLA:** 10 business days post-payment confirmation.

### 5.5 Request 005 — Maharashtra PoCRA PMU Mumbai
- **Request ID:** `SOILDEPTH-REQ-2026-005`
- **Target Stations:** `POCRA-AMRAVATI-DARYAPUR` ($20.9250^\circ\text{ N}, 77.3150^\circ\text{ E}$) & `POCRA-JALNA-BADNAPUR` ($19.8700^\circ\text{ N}, 75.9500^\circ\text{ E}$)
- **Authority:** State Project Director, Project on Climate Resilient Agriculture (PoCRA)
- **Official Address:** PoCRA Project Management Unit, 30 Arcade, World Trade Centre, Cuffe Parade, Mumbai – 400005, Maharashtra
- **Contact Channels:** `projectdirector@mahapocra.gov.in`, `pmu.pocra@gov.in`
- **Dispatch Document:** [`docs/data_acquisition/maharashtra/dispatch/maharashtra_pocra_pmu_request.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/dispatch/maharashtra_pocra_pmu_request.md)
- **Requested Parameters:** Agronomic IoT capacitance soil moisture profile readings (10, 20, 40 cm) across climate-vulnerable village clusters (2019-01-01 to 2023-12-31).
- **Dispatch Route:** Academic research request to State Project Director, Dadar PMU.
- **Follow-up SLA:** 14 business days post-dispatch.

---

## 6. Real-World Action Logging Protocol

Whenever an action occurs in the physical world (letter signing, dispatch, email response, portal receipt, file download), follow the step-by-step procedure detailed in:
[`docs/data_acquisition/maharashtra/tracker_operational_guide.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/tracker_operational_guide.md).

All received datasets must be verified against:
[`docs/data_acquisition/maharashtra/data_receipt_checklist.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/data_receipt_checklist.md).
