"""
SoilDepth-AI — Maharashtra Phase 2E Ground-Truth Acquisition Campaign Tests
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Validates Phase 2E institutional request letter completeness, status evidence auditing,
         depth compatibility classifications, ingestion protocol gates, training readiness matrix,
         and absence of unsupported submission claims.
"""

from pathlib import Path
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "metadata"
DOCS_DIR = REPO_ROOT / "docs" / "data_acquisition" / "maharashtra"
REQUESTS_DIR = DOCS_DIR / "requests"


# ==============================================================================
# 1. INSTITUTIONAL REQUEST LETTERS TESTS
# ==============================================================================
def test_institutional_request_drafts_exist():
    """Verifies that individual formal academic request drafts exist and are populated."""
    expected_requests = [
        "iitm_moes_cosmos_pune_request.md",
        "icar_niasm_baramati_request.md",
        "mpkv_rahuri_caast_request.md",
        "imd_national_data_centre_request.md",
        "maharashtra_pocra_pmu_request.md",
    ]

    for req_file in expected_requests:
        fp = REQUESTS_DIR / req_file
        assert fp.exists(), f"Missing request draft: {req_file}"
        assert fp.stat().st_size > 1500, f"Request draft is too short: {req_file}"

        content = fp.read_text(encoding="utf-8")
        # Must be explicitly marked as drafted / not yet submitted
        assert "DRAFTED_NOT_SENT" in content, f"Request {req_file} must have status DRAFTED_NOT_SENT"
        # Must state non-commercial academic research objective
        assert "SoilDepth-AI" in content
        assert "academic" in content.lower()
        # Must request specific depths and VWC
        assert "soil moisture" in content.lower()
        assert "coordinates" in content.lower() or "latitude" in content.lower()
        # Must specify formats and attribution
        assert "licensing" in content.lower() or "attribution" in content.lower() or "undertaking" in content.lower()


def test_no_unsupported_submission_claims():
    """Verifies that no station is marked as REQUEST_SENT without submission evidence."""
    reg_csv = METADATA_DIR / "station_registry.csv"
    cov_csv = METADATA_DIR / "station_coverage_matrix.csv"
    readiness_csv = METADATA_DIR / "station_training_readiness_matrix.csv"

    for path in [reg_csv, cov_csv, readiness_csv]:
        assert path.exists(), f"Missing {path}"
        df = pd.read_csv(path)
        # REQUEST_SENT must not appear in any active status column
        for col in ["request_status", "current_request_status"]:
            if col in df.columns:
                sent_count = (df[col] == "REQUEST_SENT").sum()
                assert sent_count == 0, f"Unsupported status claim REQUEST_SENT found in {path.name} ({sent_count} rows)"


# ==============================================================================
# 2. DEPTH COMPATIBILITY MATRIX TESTS
# ==============================================================================
def test_depth_compatibility_matrix():
    """Verifies 16 stations in depth compatibility matrix and strict interpolation prohibition."""
    matrix_csv = METADATA_DIR / "depth_compatibility_matrix.csv"
    assert matrix_csv.exists(), f"Missing {matrix_csv}"

    df = pd.read_csv(matrix_csv)
    assert len(df) == 16, f"Expected 16 stations, found {len(df)}"

    required_cols = [
        "station_id", "station_name", "district", "sensor_modality",
        "installed_sensor_depths_cm", "model1_5cm_compatibility",
        "model1_10cm_compatibility", "model1_20cm_compatibility",
        "model1_50cm_compatibility", "prohibited_interpolation_flag",
        "scientific_recommendation"
    ]
    assert list(df.columns) == required_cols

    # Strict interpolation prohibition
    assert (df["prohibited_interpolation_flag"] == "PROHIBITED_NO_SYNTHETIC_INTERPOLATION").all()

    # CRNS stations must be marked as AREA_INTEGRATED_MEASUREMENT
    pune_row = df[df["station_id"] == "IITM-PUNE-COSMOS"].iloc[0]
    assert pune_row["model1_10cm_compatibility"] == "AREA_INTEGRATED_MEASUREMENT"
    assert pune_row["model1_20cm_compatibility"] == "AREA_INTEGRATED_MEASUREMENT"

    # MPKV Rahuri has 10cm and 20cm approximate defensible matches
    rahuri_row = df[df["station_id"] == "MPKV-RAHURI-CAAST"].iloc[0]
    assert rahuri_row["model1_10cm_compatibility"] == "APPROXIMATE_DEFENSIBLE_MATCH"
    assert rahuri_row["model1_20cm_compatibility"] == "APPROXIMATE_DEFENSIBLE_MATCH"
    assert rahuri_row["model1_50cm_compatibility"] == "DIFFERENT_DEPTH_SEPARATE_MODEL"


# ==============================================================================
# 3. STATION TRAINING READINESS MATRIX & PILOT TESTS
# ==============================================================================
def test_station_training_readiness_matrix():
    """Verifies prioritized acquisition tiers and the 3-station minimum pilot cluster."""
    readiness_csv = METADATA_DIR / "station_training_readiness_matrix.csv"
    assert readiness_csv.exists(), f"Missing {readiness_csv}"

    df = pd.read_csv(readiness_csv)
    assert len(df) == 16

    # All stations currently blocked awaiting ground truth
    assert (df["training_readiness_verdict"] == "READY_PREDICTORS_AWAITING_GROUND_TRUTH").all()

    # Pilot candidates
    pilot_stations = set(df[df["pilot_candidate_flag"] == True]["station_id"])
    expected_pilot = {"IMD-AGRIMET-PUNE", "MPKV-RAHURI-CAAST", "NIASM-BARAMATI-FLUX", "IITM-PUNE-COSMOS"}
    assert expected_pilot.issubset(pilot_stations)

    # Tier 1 count
    tier1_count = (df["priority_tier"] == "TIER_1_IMMEDIATE").sum()
    assert tier1_count == 3  # IMD, MPKV, NIASM


# ==============================================================================
# 4. PROTOCOL & STATUS DOCUMENTATION TESTS
# ==============================================================================
def test_protocol_and_status_documents_exist():
    """Verifies that the 10-gate ingestion protocol and acquisition status reports are complete."""
    protocol_doc = DOCS_DIR / "ground_truth_ingestion_protocol.md"
    status_doc = DOCS_DIR / "ground_truth_acquisition_status.md"
    priority_doc = DOCS_DIR / "institutional_data_request_priority.md"

    for doc in [protocol_doc, status_doc, priority_doc]:
        assert doc.exists(), f"Missing document: {doc.name}"
        assert doc.stat().st_size > 2000, f"Document is too short: {doc.name}"

    proto_text = protocol_doc.read_text(encoding="utf-8")
    assert "Gate 1" in proto_text and "Gate 10" in proto_text
    assert "SHA-256" in proto_text
    assert "DATA_VERIFIED" in proto_text
    assert "PROHIBITED" in proto_text.upper()

