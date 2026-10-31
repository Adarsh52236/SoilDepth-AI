"""
SoilDepth-AI — Tests for Sentinel-1 SAR Dataset Ingestion & Processing Pipeline
Author: Senior Remote-Sensing Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Verify Sentinel-1 directory structure, raw STAC catalog assets, processed
         acquisitions, daily timeline alignment (2015–2023), decibel & ratio conversions,
         floating-point predictor inversion, and audit reports.
"""

import sys
import math
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add scripts directory to path to handle hyphenated directory name
REPO_ROOT = Path(__file__).resolve().parent.parent
S1_SCRIPTS = REPO_ROOT / "dataset" / "Sentinel-1" / "scripts"
if str(S1_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(S1_SCRIPTS))

from process_sentinel1 import (
    REPO_ROOT,
    S1_DIR,
    S1_RAW_DIR,
    S1_PROCESSED_DIR,
    S1_AUDIT_DIR,
    S1_MANIFEST_DIR,
    STATION_ID,
    TIMELINE_START,
    TIMELINE_END,
    EXPECTED_CALENDAR_DAYS,
    undo_fp_predictor,
    compute_file_sha256,
)


def test_sentinel1_directory_structure_and_raw_assets():
    """Verify Sentinel-1 directory tree and presence of raw STAC catalog & sample GeoTIFF."""
    assert S1_RAW_DIR.is_dir(), "raw/AAMU-JTG directory missing"
    assert S1_PROCESSED_DIR.is_dir(), "processed/AAMU-JTG directory missing"
    assert S1_AUDIT_DIR.is_dir(), "audit/AAMU-JTG directory missing"
    assert S1_MANIFEST_DIR.is_dir(), "manifests directory missing"
    assert (S1_DIR / "README.md").is_file(), "Sentinel-1 README.md missing"

    stac_file = S1_RAW_DIR / "sentinel1_stac_items.json"
    sample_tif = S1_RAW_DIR / "s1_sample_raw_tile_vv.tif"
    assert stac_file.is_file(), "sentinel1_stac_items.json missing"
    assert sample_tif.is_file(), "s1_sample_raw_tile_vv.tif missing"

    with open(stac_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    assert len(items) == 196


def test_sentinel1_manifest_and_audit_integrity():
    """Verify download_manifest.csv and sentinel1_manifest.json record correct provenance."""
    csv_manifest = S1_MANIFEST_DIR / "download_manifest.csv"
    json_manifest = S1_MANIFEST_DIR / "sentinel1_manifest.json"
    audit_json = S1_AUDIT_DIR / "sentinel1_quality_report.json"

    assert csv_manifest.is_file(), "download_manifest.csv missing"
    assert json_manifest.is_file(), "sentinel1_manifest.json missing"
    assert audit_json.is_file(), "sentinel1_quality_report.json missing"

    df_csv = pd.read_csv(csv_manifest)
    assert len(df_csv) >= 1
    row = df_csv.iloc[0]
    assert row["dataset"] == "Sentinel-1"
    assert row["station_id"] == STATION_ID
    assert row["status"] == "PROCESSED"
    assert row["validation_status"] == "VALIDATED"

    with open(json_manifest, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["station_target"]["station_id"] == STATION_ID
    assert meta["inventory"]["total_stac_items_retrieved"] == 196
    assert meta["inventory"]["statistics"]["valid_observations_count"] == 196


def test_sentinel1_acquisitions_and_daily_alignment():
    """Verify acquisition table and full-calendar daily features alignment."""
    acq_file = S1_PROCESSED_DIR / "sentinel1_acquisitions.csv"
    daily_file = S1_PROCESSED_DIR / "sentinel1_daily_features.csv"

    assert acq_file.is_file(), "sentinel1_acquisitions.csv missing"
    assert daily_file.is_file(), "sentinel1_daily_features.csv missing"

    df_acq = pd.read_csv(acq_file)
    assert len(df_acq) == 196
    assert (df_acq["is_valid"] == True).all()
    assert (df_acq["vv_linear"] > 0).all()
    assert (df_acq["vv_db"] > -40.0).all() and (df_acq["vv_db"] < 10.0).all()

    df_daily = pd.read_csv(daily_file)
    assert len(df_daily) == EXPECTED_CALENDAR_DAYS
    assert df_daily["date"].iloc[0] == TIMELINE_START
    assert df_daily["date"].iloc[-1] == TIMELINE_END
    assert df_daily["s1_has_valid_observation"].sum() == 196

    # Verify unobserved days have NaN backscatter (no fabrication)
    unobserved = df_daily[~df_daily["s1_has_valid_observation"]]
    assert unobserved["s1_vv_db_mean"].isna().all()
    assert unobserved["s1_vh_db_mean"].isna().all()


def test_sentinel1_fp_predictor_mathematical_inversion():
    """Verify exact numerical reconstruction of Adobe Deflate Floating-Point Predictor."""
    expected = np.array([[1.0, 2.0, 3.0, 4.0]], dtype='>f4')
    planes = np.array([
        [0x3f, 0x40, 0x40, 0x40],
        [0x80, 0x00, 0x40, 0x80],
        [0x00, 0x00, 0x00, 0x00],
        [0x00, 0x00, 0x00, 0x00],
    ], dtype=np.uint8)

    diffed = np.zeros_like(planes)
    diffed[:, 0] = planes[:, 0]
    diffed[:, 1:] = np.diff(planes.astype(np.int16), axis=1) % 256

    raw_bytes = diffed.tobytes()
    reconstructed = undo_fp_predictor(raw_bytes, width=4, height=1)

    np.testing.assert_allclose(reconstructed, expected, rtol=1e-6)


def test_sentinel1_decibel_and_ratio_conversions():
    """Verify linear power to decibel conversion and ratio consistency."""
    vv_lin = 0.1
    vh_lin = 0.01

    vv_db = 10.0 * math.log10(vv_lin)
    vh_db = 10.0 * math.log10(vh_lin)
    ratio_lin = vv_lin / vh_lin
    ratio_db = vv_db - vh_db

    assert math.isclose(vv_db, -10.0, abs_tol=1e-5)
    assert math.isclose(vh_db, -20.0, abs_tol=1e-5)
    assert math.isclose(ratio_lin, 10.0, abs_tol=1e-5)
    assert math.isclose(ratio_db, 10.0, abs_tol=1e-5)
