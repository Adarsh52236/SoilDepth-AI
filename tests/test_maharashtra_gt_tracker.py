"""
SoilDepth-AI — Phase 3 Maharashtra Ground-Truth Tracker & Acquisition Tests
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Tests Phase 3 operational tracker completeness, evidence repository structure,
         data-receipt checklist dimensions, operational update guide, and anti-fabrication gates.
"""

from pathlib import Path
import tempfile
import pandas as pd
import pytest

from services.data_acquisition.maharashtra.tracker_manager import (
    GroundTruthTrackerManager,
    VALID_STATUSES,
    EXPECTED_REQUEST_IDS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
METADATA_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "metadata"
DOCS_DIR = REPO_ROOT / "docs" / "data_acquisition" / "maharashtra"
ACQUISITION_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "acquisition"


# ==============================================================================
# 1. TRACKER EXISTENCE & SCHEMA TESTS
# ==============================================================================
def test_operational_tracker_exists_and_complete():
    """Verifies that the CSV and Markdown trackers exist and cover all 5 requests."""
    csv_path = METADATA_DIR / "operational_ground_truth_tracker.csv"
    md_path = DOCS_DIR / "operational_ground_truth_tracker.md"

    assert csv_path.exists(), f"Missing tracker CSV: {csv_path}"
    assert md_path.exists(), f"Missing tracker Markdown: {md_path}"
    assert md_path.stat().st_size > 2000, "Tracker Markdown document is too short"

    df = pd.read_csv(csv_path)
    assert len(df) == 5, f"Expected 5 institutional requests, found {len(df)}"

    required_cols = [
        "request_id",
        "institution",
        "station_ids",
        "contact_route",
        "requested_period",
        "requested_depths",
        "submission_status",
        "acknowledgement_status",
        "expected_delivery_format",
        "follow_up_date",
        "submission_date",
        "evidence_directory",
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column in tracker: {col}"

    assert list(df["request_id"]) == EXPECTED_REQUEST_IDS


def test_operational_tracker_status_taxonomy():
    """Verifies that all 5 requests use valid six-state status taxonomy."""
    csv_path = METADATA_DIR / "operational_ground_truth_tracker.csv"
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        status = row["submission_status"]
        assert status in VALID_STATUSES, f"Invalid status '{status}' for {row['request_id']}"


def test_anti_fabrication_no_unsupported_submission():
    """Verifies that no request is prematurely marked SUBMITTED without physical dispatch."""
    csv_path = METADATA_DIR / "operational_ground_truth_tracker.csv"
    df = pd.read_csv(csv_path)

    # Currently, all 5 requests are DRAFTED awaiting physical dispatch
    for _, row in df.iterrows():
        assert row["submission_status"] == "DRAFTED", (
            f"Request {row['request_id']} must have status DRAFTED until physical dispatch evidence is deposited."
        )
        assert row["submission_date"] == "PENDING"
        assert row["follow_up_date"] == "PENDING_DISPATCH"


# ==============================================================================
# 2. EVIDENCE & REPOSITORY FOLDER STRUCTURE TESTS
# ==============================================================================
def test_request_evidence_repositories_exist():
    """Verifies dedicated evidence directories exist for all 5 requests with required subfolders."""
    assert ACQUISITION_DIR.exists(), f"Missing acquisition root: {ACQUISITION_DIR}"

    expected_dirs = [
        "SOILDEPTH-REQ-2026-001-IITM-PUNE",
        "SOILDEPTH-REQ-2026-002-ICAR-NIASM",
        "SOILDEPTH-REQ-2026-003-MPKV-RAHURI",
        "SOILDEPTH-REQ-2026-004-IMD-PUNE",
        "SOILDEPTH-REQ-2026-005-POCRA-PMU",
    ]
    subdirs = ["signed_letters", "email_evidence", "receipts", "received_datasets"]

    for edir_name in expected_dirs:
        edir = ACQUISITION_DIR / edir_name
        assert edir.exists(), f"Missing request folder: {edir}"
        assert (edir / "README.md").exists(), f"Missing README in {edir}"

        for sub in subdirs:
            sub_path = edir / sub
            assert sub_path.exists() and sub_path.is_dir(), f"Missing subfolder: {sub_path}"


# ==============================================================================
# 3. DATA-RECEIPT CHECKLIST TESTS
# ==============================================================================
def test_data_receipt_checklist_dimensions():
    """Verifies that the data-receipt checklist covers all 7 mandatory quality dimensions."""
    chk_path = DOCS_DIR / "data_receipt_checklist.md"
    assert chk_path.exists(), f"Missing checklist: {chk_path}"
    assert chk_path.stat().st_size > 2000, "Checklist document is too short"

    content = chk_path.read_text(encoding="utf-8")

    # 7 mandatory dimensions
    assert "Timestamps" in content
    assert "Units" in content
    assert "Sensor Depth" in content
    assert "Measurement Modality" in content
    assert "Station Coordinates" in content or "Coordinates" in content
    assert "Quality Flags" in content
    assert "Missingness" in content

    # Key integrity clauses
    assert "Anti-Interpolation" in content or "ZERO synthetic depth interpolation" in content
    assert "180" in content  # >= 180 daily observations threshold
    assert "0.65" in content  # VWC physical upper bound


# ==============================================================================
# 4. OPERATIONAL UPDATE GUIDE TESTS
# ==============================================================================
def test_operational_guide_actions():
    """Verifies that the operational guide covers all real-world institutional actions."""
    guide_path = DOCS_DIR / "tracker_operational_guide.md"
    assert guide_path.exists(), f"Missing guide: {guide_path}"
    assert guide_path.stat().st_size > 2000, "Operational guide is too short"

    content = guide_path.read_text(encoding="utf-8")

    assert "Action 1" in content and "APPROVED" in content
    assert "Action 2" in content and "SUBMITTED" in content
    assert "Action 3" in content and "ACKNOWLEDGED" in content
    assert "Action 4" in content and "DATA_RECEIVED" in content
    assert "Action 5" in content and "DATA_VERIFIED" in content


# ==============================================================================
# 5. TRACKER MANAGER UTILITY TESTS
# ==============================================================================
def test_tracker_manager_validation():
    """Verifies that the tracker manager successfully validates current state."""
    mgr = GroundTruthTrackerManager()
    res = mgr.validate_tracker()
    assert res["is_valid"], f"Tracker manager validation failed: {res['issues']}"
    assert res["total_requests"] == 5


def test_tracker_manager_catches_unsupported_status(tmp_path):
    """Verifies that marking SUBMITTED without evidence files raises validation issues."""
    test_csv = tmp_path / "test_tracker.csv"
    df = pd.read_csv(METADATA_DIR / "operational_ground_truth_tracker.csv")
    # Mark first row as SUBMITTED without depositing evidence in receipts/
    df.loc[0, "submission_status"] = "SUBMITTED"
    df.to_csv(test_csv, index=False)

    mgr = GroundTruthTrackerManager(tracker_csv=test_csv)
    res = mgr.validate_tracker()
    assert not res["is_valid"]
    assert any("Anti-Fabrication Violation" in iss for iss in res["issues"])
