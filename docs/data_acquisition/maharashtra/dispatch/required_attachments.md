# SoilDepth-AI — Dispatch Requisition Required Attachments Specification

**Document Reference:** `DOC-MAHA-DISPATCH-ATTACHMENTS-2026`  
**Phase:** Phase 2F (Institutional Request Dispatch Readiness)  
**Standard:** SoilDepth-AI Data Requisition Governance Protocol  
**Date:** November 3, 2026  
**Status:** `MANDATORY_DISPATCH_SPECIFICATION`  

---

## 1. Overview & Attachment Architecture

Every formal academic data requisition submitted to government ministries, research councils, or agricultural universities must be accompanied by mandatory supporting documentation. Incomplete submission packets lead to administrative rejection, prolonged committee reviews, or classification under commercial tariff categories.

To ensure frictionless institutional acceptance, every dispatch packet must assemble the following standard annexure package:

```
DISPATCH SUBMISSION PACKET
├── Primary Requisition Letter (Printed on University Letterhead, Signed & Sealed)
├── Annexure A: Institutional Endorsement Letter (Signed by Guide / HoD / Dean)
├── Annexure B: Non-Commercial Academic Research Undertaking
├── Annexure C: SoilDepth-AI Technical Research Summary & Methodology Brief
├── Annexure D: Station Coordinates, Depths & Spatial Bounding Box Specification
└── Annexure E: Institution-Specific Instrument (Bharatkosh Challan / Draft MOU)
```

---

## 2. Standard Annexure Specifications

### Annexure A: Institutional Endorsement Letter
- **Purpose:** Certifies that the applicant is a bona fide academic researcher / research group at an accredited institution and that the requisition is conducted under institutional academic auspices.
- **Issuing Authority:** Head of Department (HoD), Dean of Research, or Registrar of the sponsoring academic institution.
- **Mandatory Elements:**
  - Official university/institute letterhead with official seal.
  - Names, academic roll numbers / employee codes of the investigating team.
  - Confirmation that the project is strictly non-commercial and academic.
  - Explicit endorsement of the data requisition from the target institution.

---

### Annexure B: Non-Commercial Academic Research Undertaking
- **Purpose:** Legally binding undertaking guaranteeing data protection, non-redistribution, and adherence to intellectual property terms.
- **Signatories:** Research Supervisor / Principal Investigator and Lead Student / ML Engineer.
- **Standard Text Template:**
  > *"We, the undersigned research team, hereby solemnly declare and undertake that:  
  > 1. All meteorological, hydrological, and soil moisture data provided by [Target Institution] shall be utilized exclusively for non-commercial academic research under the SoilDepth-AI initiative.  
  > 2. The dataset will remain securely stored on encrypted academic storage servers and will not be transferred, published in raw bulk form, leased, or sub-licensed to any commercial organization or third party.  
  > 3. Due scientific attribution, citation of datasets, and acknowledgment of [Target Institution] and contributing scientists will be prominently incorporated into all published peer-reviewed journal papers, academic theses, technical reports, and software repositories.  
  > 4. We shall provide [Target Institution] with copies of all research publications arising from the utilization of this dataset."*

---

### Annexure C: SoilDepth-AI Technical Research Summary
- **Purpose:** Explains why the specific temporal period, sensor depths, and parameters are necessary for scientific validation of root-zone physics-informed machine learning.
- **Key Contents:**
  - 1-page summary of multi-sensor fusion (Sentinel-1 SAR, Sentinel-2 MSI, SMAP L3, ERA5-Land).
  - Explanation of the 4 discrete target depths ($5\text{ cm}$, $10\text{ cm}$, $20\text{ cm}$, $50\text{ cm}$) and layer-average validation requirements.
  - Statement of the mathematical evaluation criteria (RMSE $\le 0.04\text{ m}^3/\text{m}^3$, Kling-Gupta Efficiency $\ge 0.70$).
  - Confirmation that the AI models do not replace field monitoring but extend its spatial coverage to surrounding agrarian micro-watersheds.

---

### Annexure D: Spatial Bounding Box & Station Specifications
- **Purpose:** Provides geospatial coordinates, elevations, and WGS84 geographic bounding boxes for GIS analysts and data centre curators.
- **Specifications Table:**

| Target Station ID | Institution | Benchmark Coordinates (Lat, Lon) | Benchmark Elevation | Study Area Buffer Bounding Box (WGS84) |
| :--- | :--- | :--- | :--- | :--- |
| `IITM-PUNE-COSMOS` | IITM / MoES | $18.5372^\circ\text{ N}, 73.8051^\circ\text{ E}$ | $560.0\text{ m}$ AMSL | $[73.70^\circ\text{ E}, 18.45^\circ\text{ N}, 73.90^\circ\text{ E}, 18.60^\circ\text{ N}]$ |
| `IMD-AGRIMET-PUNE` | IMD NDC | $18.5308^\circ\text{ N}, 73.8507^\circ\text{ E}$ | $559.0\text{ m}$ AMSL | $[73.75^\circ\text{ E}, 18.45^\circ\text{ N}, 73.95^\circ\text{ E}, 18.60^\circ\text{ N}]$ |
| `MPKV-RAHURI-CAAST` | MPKV Rahuri | $19.3932^\circ\text{ N}, 74.6475^\circ\text{ E}$ | $512.0\text{ m}$ AMSL | $[74.55^\circ\text{ E}, 19.30^\circ\text{ N}, 74.75^\circ\text{ E}, 19.50^\circ\text{ N}]$ |
| `NIASM-BARAMATI-FLUX` | ICAR-NIASM | $18.1506^\circ\text{ N}, 74.5772^\circ\text{ E}$ | $555.0\text{ m}$ AMSL | $[74.45^\circ\text{ E}, 18.05^\circ\text{ N}, 74.70^\circ\text{ E}, 18.25^\circ\text{ N}]$ |
| `POCRA-AMRAVATI-DARYAPUR` | PoCRA PMU | $20.9254^\circ\text{ N}, 77.3142^\circ\text{ E}$ | $288.0\text{ m}$ AMSL | $[77.15^\circ\text{ E}, 20.80^\circ\text{ N}, 77.45^\circ\text{ E}, 21.05^\circ\text{ N}]$ |
| `POCRA-JALNA-BADNAPUR` | PoCRA PMU | $19.8651^\circ\text{ N}, 75.8824^\circ\text{ E}$ | $512.0\text{ m}$ AMSL | $[75.75^\circ\text{ E}, 19.75^\circ\text{ N}, 76.00^\circ\text{ E}, 20.00^\circ\text{ N}]$ |

---

## 3. Institution-Specific Annexure E Specifications

### 1. Packet 04: IMD NDC Pune — Annexure E
- **Instrument:** Government of India Bharatkosh Non-Tax Receipt Portal Payment Challan & IMD Form A Requisition Form.
- **Workflow:**
  1. Register academic account on `https://dsp.imdpune.gov.in`.
  2. Complete online Data Requisition Application referencing Station ID `43063` (Pune Agrimet) for 2015-01-01 to 2023-12-31.
  3. Upload Annexure A & B (University letterhead endorsement & non-commercial undertaking).
  4. Receive official NDC proforma invoice stating payment amount under Category II (Academic/Research).
  5. Remit fee on `https://bharatkosh.gov.in` selecting:
     - Ministry: `081 - Earth Sciences`
     - Purpose: `Sale of Meteorological Data (IMD)`
     - PAO: `028680 - PAO (IMD), Pune`
  6. Upload Bharatkosh payment receipt / challan to DSP portal.

### 2. Packet 02 & 03: ICAR-NIASM & MPKV Rahuri — Annexure E
- **Instrument:** Bilateral Academic Research Memorandum of Understanding (MOU) / Data Sharing Agreement.
- **Key Terms in MOU Draft:**
  - Non-commercial scientific collaboration in accordance with ICAR Rules for Intellectual Property Management.
  - Joint data interpretation and co-authorship for participating institutional scientists.
  - Data transfer limited to specified research personnel.
  - Final copy of SoilDepth-AI evaluation report and code delivered to institution.

### 3. Packet 05: Maharashtra PoCRA PMU — Annexure E
- **Instrument:** Government Department Academic Collaboration Undertaking & Agricultural Decision Support Impact Statement.
- **Key Terms:**
  - Affirmation that predictive models developed will be made available to PoCRA PMU to assist in micro-watershed drought advisory.
  - Explicit confirmation that farmer privacy and field-level GPS locations will not be made public in identifiable format.

---

## 4. Attachment Compilation Checklist Prior to Dispatch

| Dispatch Packet | Primary Letter | Annexure A (Letterhead Endorsement) | Annexure B (Non-Commercial Undertaking) | Annexure C (Research Summary) | Annexure D (Coords & Bounding Box) | Annexure E (Institution Specific) | Final Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `SOILDEPTH-REQ-2026-001` (IITM COSMOS) | Ready | Required from PI | Ready | Ready | Ready | Academic Collaboration Proposal | `READY_FOR_SUBMISSION` |
| `SOILDEPTH-REQ-2026-002` (ICAR-NIASM) | Ready | Required from PI | Ready | Ready | Ready | Draft ICAR Data Sharing MOU | `READY_FOR_SUBMISSION` |
| `SOILDEPTH-REQ-2026-003` (MPKV Rahuri) | Ready | Required from PI | Ready | Ready | Ready | Draft SAU Research MOU | `READY_FOR_SUBMISSION` |
| `SOILDEPTH-REQ-2026-004` (IMD NDC Pune) | Ready | Required from PI | Ready (IMD Format) | Ready | Ready | Bharatkosh Payment Challan | `READY_FOR_SUBMISSION` |
| `SOILDEPTH-REQ-2026-005` (PoCRA PMU) | Ready | Required from PI | Ready | Ready | Ready | Govt Academic Cooperation Form | `READY_FOR_SUBMISSION` |
