# SoilDepth-AI — Operational Guide: Ground-Truth Acquisition Tracking

**Document ID:** `GUIDE-MAHA-GT-OPS-2026`  
**Phase:** Phase 3: Maharashtra Ground-Truth Acquisition  
**Target Tracker:** [`docs/data_acquisition/maharashtra/operational_ground_truth_tracker.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/operational_ground_truth_tracker.md) & [`dataset/Maharashtra/metadata/operational_ground_truth_tracker.csv`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/dataset/Maharashtra/metadata/operational_ground_truth_tracker.csv)  
**Standard:** SoilDepth-AI High-Assurance Data Provenance Protocol  

---

## 1. Purpose & Core Principles

This operational guide details the exact step-by-step procedures to update the ground-truth tracker after every real-world institutional event.

### Fundamental Rules:
1. **Evidence Precedes Status:** Never promote a status to `SUBMITTED`, `ACKNOWLEDGED`, `DATA_RECEIVED`, or `DATA_VERIFIED` without first depositing tangible documentary evidence into the designated request folder.
2. **Immutable Raw Data:** Original incoming files received from institutions must be stored untouched in `received_datasets/`.
3. **Dual Update:** Whenever a status changes, update both:
   - The structured CSV: `dataset/Maharashtra/metadata/operational_ground_truth_tracker.csv`
   - The markdown document: `docs/data_acquisition/maharashtra/operational_ground_truth_tracker.md`

---

## 2. Step-by-Step Action Procedures

### Action 1: PI Endorsement / Request Letter Signed
**Trigger:** Academic Principal Investigator (PI) or Department Head signs and stamps the printed request packet.

1. **Scan Signed Letter:** Produce a clear, legible PDF scan of the signed letter and all annexures.
2. **Archive Evidence:** Copy the PDF into the request's `signed_letters/` directory:
   ```powershell
   Copy-Item "C:\Scans\IITM_Signed_Letter.pdf" "dataset\Maharashtra\acquisition\SOILDEPTH-REQ-2026-001-IITM-PUNE\signed_letters\SOILDEPTH-REQ-2026-001_Signed_Letter.pdf"
   ```
3. **Update Status:**
   - Change `submission_status` from `DRAFTED` to `APPROVED`.
   - Update notes: `Letter signed by PI; ready for postal/email dispatch`.

---

### Action 2: Formal Dispatch / Submission
**Trigger:** Request packet is mailed via India Post Speed Post, submitted on an online portal (e.g. IMD DSP), or sent via official university email.

1. **Collect Dispatch Evidence:**
   - **For Speed Post:** Scan or photograph the postal receipt showing the tracking barcode (e.g., `EM123456789IN`).
   - **For Email:** Export the sent email message as an `.eml` file or save a full-header screenshot.
   - **For Web Portal:** Download the portal submission confirmation slip or application PDF.
2. **Archive Evidence:**
   - Postal slips & portal receipts go to: `dataset\Maharashtra\acquisition\<REQUEST_DIR>\receipts\`
   - Email evidence goes to: `dataset\Maharashtra\acquisition\<REQUEST_DIR>\email_evidence\`
3. **Update Tracker:**
   - `submission_status`: Promote to `SUBMITTED`.
   - `submission_date`: Record the exact date of dispatch (e.g. `2026-11-10`).
   - `follow_up_date`: Set to **12 to 14 business days** post-dispatch.
   - `acknowledgement_status`: Set to `AWAITING_ACKNOWLEDGEMENT`.
4. **Synchronize Station Registry:**
   - In `dataset/Maharashtra/metadata/station_registry.csv`, update `request_status` to `REQUEST_SUBMITTED`.

---

### Action 3: Target Institution Acknowledges Receipt
**Trigger:** Institution issues a registration ticket number, DSP portal application number, email acknowledgement, or proforma invoice.

1. **Archive Evidence:**
   - Save the institutional email or formal acknowledgement letter in `receipts/` or `email_evidence/`.
2. **Update Tracker:**
   - `submission_status`: Promote to `ACKNOWLEDGED`.
   - `acknowledgement_status`: Record ticket/reference (e.g. `ACKNOWLEDGED (Ticket #IITM-2026-8812)`).
   - If payment is requested (e.g. IMD Bharatkosh), note the proforma invoice number and payment deadline in `notes`.

---

### Action 4: Physical Data Received
**Trigger:** Institution provides raw observation files via email attachment, cloud link, or portal download.

1. **Deposit Raw Datasets (UNMODIFIED):**
   - Place original raw files into:
     `dataset\Maharashtra\acquisition\<REQUEST_DIR>\received_datasets\`
2. **Compute Cryptographic Hash:**
   ```powershell
   Get-FileHash -Algorithm SHA256 "dataset\Maharashtra\acquisition\<REQUEST_DIR>\received_datasets\raw_data.csv"
   ```
3. **Update Tracker:**
   - `submission_status`: Promote to `DATA_RECEIVED`.
   - Record raw filename and SHA-256 hash in the request notes.

---

### Action 5: Data Quality Verification & Training Ingestion
**Trigger:** Raw data undergoes high-assurance verification against the Data Receipt Checklist.

1. **Execute Ingestion Validation:**
   Run the ingestion adapter in strict validation mode:
   ```python
   from services.data_acquisition.maharashtra.ground_truth_adapter import MaharashtraGroundTruthAdapter

   adapter = MaharashtraGroundTruthAdapter()
   df_norm = adapter.ingest_file(
       file_path="dataset/Maharashtra/acquisition/SOILDEPTH-REQ-2026-003-MPKV-RAHURI/received_datasets/raw_data.csv",
       column_mapping={
           "timestamp": "Datetime_IST",
           "sensor_depth_cm": "Depth_cm",
           "soil_moisture_vwc": "VWC_Percent",
           "quality_flag": "QC_Flag",
       },
       source_dataset="MPKV_RAHURI_CAAST",
       default_station_id="MPKV-RAHURI-CAAST",
       input_vwc_unit="%",
       input_timezone="Asia/Kolkata",
       strict=True,
   )
   ```
2. **Complete Data Receipt Checklist:**
   - Open [`docs/data_acquisition/maharashtra/data_receipt_checklist.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/data_receipt_checklist.md).
   - Verify all 7 quality dimensions (timestamps, units, sensor depth, modality, coordinates, quality flags, missingness $\ge 180$ days).
3. **Branch Decision:**
   - **If Validation Passes 100%:**
     1. Promote normalized file to: `dataset/Maharashtra/ground_truth/verified/<STATION_ID>_in_situ_verified.csv`.
     2. Update `submission_status` to `DATA_VERIFIED`.
     3. Update `station_registry.csv` (`data_received_status: DATA_RECEIVED`, `verification_status: DATA_VERIFIED`).
     4. Unblock supervised regional training:
        ```powershell
        python services/modelling/train_maharashtra.py --ground-truth-file dataset/Maharashtra/ground_truth/verified/<STATION_ID>_in_situ_verified.csv
        ```
   - **If Validation Fails:**
     1. Change `submission_status` to `DATA_REJECTED` (or `ACTION_REQUIRED`).
     2. Document failure reasons in the request README.md.
     3. Initiate formal inquiry with institutional data provider.

---

## 3. Automated Helper Script Usage

A dedicated tracking verification and update utility is provided:
```powershell
# Validate tracker integrity and check for evidence adherence:
python services/data_acquisition/maharashtra/tracker_manager.py --validate

# View current operational summary:
python services/data_acquisition/maharashtra/tracker_manager.py --summary
```
