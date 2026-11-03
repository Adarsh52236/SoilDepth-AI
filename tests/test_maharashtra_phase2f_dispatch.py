"""
SoilDepth-AI — Maharashtra Phase 2F Institutional Request Dispatch Readiness Tests
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Validates Phase 2F dispatch packets, submission checklist, required attachments,
         institutional contact evidence verification, nine-state taxonomy adherence,
         and anti-fabrication integrity.
"""

from pathlib import Path
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "metadata"
DOCS_DIR = REPO_ROOT / "docs" / "data_acquisition" / "maharashtra"
DISPATCH_DIR = DOCS_DIR / "dispatch"

VALID_9_STATE_TAXONOMY = {
    "MERELY_IDENTIFIED",
    "DRAFTED_NOT_SENT",
    "READY_FOR_SUBMISSION",
    "REQUEST_SUBMITTED",
    "ACKNOWLEDGED",
    "APPROVED",
    "DATA_RECEIVED",
    "DATA_VERIFIED",
    "DATA_REJECTED",
}


# ==============================================================================
# 1. DISPATCH PACKETS EXISTENCE & FORMAT TESTS
# ==============================================================================
def test_dispatch_directory_and_packets_exist():
    """Verifies that all 5 finalized dispatch request packets exist and meet quality benchmarks."""
    assert DISPATCH_DIR.exists() and DISPATCH_DIR.is_dir(), f"Missing dispatch directory: {DISPATCH_DIR}"

    expected_packets = {
        "iitm_cosmos_pune_request.md": "SOILDEPTH-REQ-2026-001",
        "icar_niasm_baramati_request.md": "SOILDEPTH-REQ-2026-002",
        "mpkv_rahuri_caast_request.md": "SOILDEPTH-REQ-2026-003",
        "imd_national_data_centre_request.md": "SOILDEPTH-REQ-2026-004",
        "maharashtra_pocra_pmu_request.md": "SOILDEPTH-REQ-2026-005",
    }

    for req_file, req_id in expected_packets.items():
        fp = DISPATCH_DIR / req_file
        assert fp.exists(), f"Missing dispatch packet: {req_file}"
        assert fp.stat().st_size > 1500, f"Dispatch packet is too short: {req_file}"

        content = fp.read_text(encoding="utf-8")
        # Must be explicitly marked as READY_FOR_SUBMISSION
        assert "READY_FOR_SUBMISSION" in content, f"Packet {req_file} must have status READY_FOR_SUBMISSION"
        # Must have correct request ID
        assert req_id in content, f"Packet {req_file} must cite reference {req_id}"
        # Must cite academic non-commercial objective
        assert "SoilDepth-AI" in content
        assert "academic" in content.lower()
        assert "non-commercial" in content.lower()
        # Must specify depths and soil moisture parameters
        assert "soil moisture" in content.lower()
        assert "coordinates" in content.lower() or "latitude" in content.lower()
        # Must cite annexures
        assert "Annexure" in content
        # Must have attribution / licensing section
        assert "attribution" in content.lower() or "licensing" in content.lower()


# ==============================================================================
# 2. SUBMISSION CHECKLIST VERIFICATION TESTS
# ==============================================================================
def test_submission_checklist_completeness():
    """Verifies submission checklist covers all required columns, SLAs, and evidence criteria."""
    checklist_fp = DISPATCH_DIR / "submission_checklist.md"
    assert checklist_fp.exists(), f"Missing {checklist_fp}"
    assert checklist_fp.stat().st_size > 2000, "Checklist file is too short"

    content = checklist_fp.read_text(encoding="utf-8")

    # Required operational checklist columns / fields
    required_fields = [
        "Request Reference ID",
        "Target Station ID",
        "Target Institution",
        "Final Document Path",
        "Authorized Recipient / Portal",
        "Required Attachments",
        "Required Authorization",
        "Submission Method",
        "Submission Evidence to Retain",
        "Follow-Up Date Field",
        "Current Status",
    ]
    for field in required_fields:
        assert field in content, f"Checklist missing required field: {field}"

    # Verify all 5 packets are listed
    for req_id in ["SOILDEPTH-REQ-2026-001", "SOILDEPTH-REQ-2026-002", "SOILDEPTH-REQ-2026-003",
                   "SOILDEPTH-REQ-2026-004", "SOILDEPTH-REQ-2026-005"]:
        assert req_id in content, f"Missing {req_id} in checklist"

    # All packets in checklist must be marked READY_FOR_SUBMISSION
    assert content.count("`READY_FOR_SUBMISSION`") >= 5


# ==============================================================================
# 3. INSTITUTIONAL CONTACT VERIFICATION TESTS
# ==============================================================================
def test_institutional_contact_verification():
    """Verifies contact evidence audit and strict quarantine of unverified candidate stations."""
    contact_fp = DISPATCH_DIR / "institutional_contact_verification.md"
    assert contact_fp.exists(), f"Missing {contact_fp}"
    assert contact_fp.stat().st_size > 2000, "Contact verification document is too short"

    content = contact_fp.read_text(encoding="utf-8")

    # Check verified routes for active 5 packets
    assert "VERIFIED_INSTITUTIONAL_CONTACT" in content
    assert "VERIFIED_PORTAL_ROUTE" in content
    assert "VERIFIED_GOVT_CONTACT" in content

    # Check specific contact emails documented
    assert "director@tropmet.res.in" in content or "hmru-cosmos@tropmet.res.in" in content
    assert "director.niasm@icar.gov.in" in content
    assert "dr_mpkv@rediffmail.com" in content or "caast.csawm2018@gmail.com" in content
    assert "dsp.imdpune.gov.in" in content
    assert "pmu.pocra@gov.in" in content

    # Unverified candidate stations 6-16 must be flagged as CONTACT_VERIFICATION_REQUIRED
    assert "CONTACT_VERIFICATION_REQUIRED" in content
    for unverified_stn in ["AICRPDA-SOLAPUR", "NBSSLUP-NAGPUR-HQ", "PDKV-AKOLA-CRS",
                           "CICR-NAGPUR-FARM", "VNMKV-PARBHANI-CRS", "NHP-CWC-PUNE"]:
        assert unverified_stn in content, f"Candidate station {unverified_stn} must be in contact verification table"


# ==============================================================================
# 4. REQUIRED ATTACHMENTS SPECIFICATION TESTS
# ==============================================================================
def test_required_attachments_specification():
    """Verifies that Annexures A through E are exhaustively specified with templates and checklists."""
    attach_fp = DISPATCH_DIR / "required_attachments.md"
    assert attach_fp.exists(), f"Missing {attach_fp}"
    assert attach_fp.stat().st_size > 2000, "Required attachments document is too short"

    content = attach_fp.read_text(encoding="utf-8")

    # All standard annexures must be detailed
    assert "Annexure A" in content and "Institutional Endorsement" in content
    assert "Annexure B" in content and "Non-Commercial Academic Research Undertaking" in content
    assert "Annexure C" in content and "Technical Research Summary" in content
    assert "Annexure D" in content and "Bounding Box" in content
    assert "Annexure E" in content

    # Institution-specific instruments must be detailed
    assert "Bharatkosh" in content  # For IMD
    assert "081" in content          # Ministry of Earth Sciences code
    assert "Memorandum of Understanding" in content or "MOU" in content  # For SAU / ICAR


# ==============================================================================
# 5. METADATA NINE-STATE TAXONOMY & REGISTRY CONSISTENCY
# ==============================================================================
def test_nine_state_taxonomy_adherence():
    """Verifies that all registries and matrices adhere strictly to the 9-state taxonomy."""
    reg_csv = METADATA_DIR / "station_registry.csv"
    cov_csv = METADATA_DIR / "station_coverage_matrix.csv"
    readiness_csv = METADATA_DIR / "station_training_readiness_matrix.csv"

    for path in [reg_csv, cov_csv, readiness_csv]:
        assert path.exists(), f"Missing {path}"
        df = pd.read_csv(path)

        status_col = "request_status" if "request_status" in df.columns else "current_request_status"
        assert status_col in df.columns, f"No status column found in {path.name}"

        # Every status value must belong to VALID_9_STATE_TAXONOMY
        unique_statuses = set(df[status_col].dropna().unique())
        invalid_statuses = unique_statuses - VALID_9_STATE_TAXONOMY
        assert not invalid_statuses, f"Invalid taxonomy status values in {path.name}: {invalid_statuses}"

        # Exactly 6 stations must be READY_FOR_SUBMISSION (covering the 5 packets)
        ready_count = (df[status_col] == "READY_FOR_SUBMISSION").sum()
        assert ready_count == 6, f"Expected 6 READY_FOR_SUBMISSION in {path.name}, got {ready_count}"

        # Exactly 10 stations must be MERELY_IDENTIFIED
        identified_count = (df[status_col] == "MERELY_IDENTIFIED").sum()
        assert identified_count == 10, f"Expected 10 MERELY_IDENTIFIED in {path.name}, got {identified_count}"

        # Zero stations submitted, acknowledged, approved, received, or verified yet
        for unreached_state in ["REQUEST_SUBMITTED", "ACKNOWLEDGED", "APPROVED", "DATA_RECEIVED", "DATA_VERIFIED", "REQUEST_SENT"]:
            count = (df[status_col] == unreached_state).sum()
            assert count == 0, f"Premature status claim {unreached_state} in {path.name}: {count} rows"


# ==============================================================================
# 6. PHASE 2F REPORT & ZERO-CONTACT INTEGRITY
# ==============================================================================
def test_phase2f_readiness_report():
    """Verifies that the Phase 2F readiness report is complete and confirms zero-contact integrity."""
    report_fp = DOCS_DIR / "phase2f_dispatch_readiness.md"
    assert report_fp.exists(), f"Missing {report_fp}"
    assert report_fp.stat().st_size > 2500, "Phase 2F report is too short"

    content = report_fp.read_text(encoding="utf-8")
    assert "Phase 2F" in content
    assert "READY_FOR_SUBMISSION" in content
    assert "Zero-Contact" in content or "zero premature contact" in content.lower()
    assert "Bharatkosh" in content
    assert "Action Required" in content
    assert "BLOCKED" in content

