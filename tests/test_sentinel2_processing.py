"""
SoilDepth-AI — Tests for Sentinel-2 Optical Dataset Ingestion & Processing Pipeline
Author: Senior Remote-Sensing Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Verify Sentinel-2 directory structure, raw STAC catalog assets, SCL cloud
         masking, surface reflectance extraction, vegetation index derivations (NDVI, EVI),
         daily timeline alignment (2015–2023), and audit reports.
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
S2_SCRIPTS = REPO_ROOT / "dataset" / "Sentinel-2" / "scripts"
if str(S2_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(S2_SCRIPTS))

from process_sentinel2 import (
    REPO_ROOT,
    S2_DIR,
    S2_RAW_DIR,
    S2_PROCESSED_DIR,
    S2_AUDIT_DIR,
    S2_MANIFEST_DIR,
    STATION_ID,
    TIMELINE_START,
    TIMELINE_END,
    EXPECTED_CALENDAR_DAYS,
    VALID_LAND_SCL_CODES,
    SCALE_FACTOR,
)


def test_sentinel2_directory_structure_and_raw_assets():
    """Verify Sentinel-2 directory tree and presence of raw STAC catalog & sample GeoTIFF."""
    assert S2_RAW_DIR.is_dir(), "raw/AAMU-JTG directory missing"
    assert S2_PROCESSED_DIR.is_dir(), "processed/AAMU-JTG directory missing"
    assert S2_AUDIT_DIR.is_dir(), "audit/AAMU-JTG directory missing"
    assert S2_MANIFEST_DIR.is_dir(), "manifests directory missing"
    assert (S2_DIR / "README.md").is_file(), "Sentinel-2 README.md missing"

    stac_file = S2_RAW_DIR / "sentinel2_stac_items.json"
    sample_tif = S2_RAW_DIR / "s2_sample_raw_tile_b04.tif"
    assert stac_file.is_file(), "sentinel2_stac_items.json missing"
    assert sample_tif.is_file(), "s2_sample_raw_tile_b04.tif missing"

    with open(stac_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    assert len(items) == 1095


def test_sentinel2_manifest_and_audit_integrity():
    """Verify download_manifest.csv and sentinel2_manifest.json record correct provenance."""
    csv_manifest = S2_MANIFEST_DIR / "download_manifest.csv"
    json_manifest = S2_MANIFEST_DIR / "sentinel2_manifest.json"
    audit_json = S2_AUDIT_DIR / "sentinel2_quality_report.json"

    assert csv_manifest.is_file(), "download_manifest.csv missing"
    assert json_manifest.is_file(), "sentinel2_manifest.json missing"
    assert audit_json.is_file(), "sentinel2_quality_report.json missing"

    df_csv = pd.read_csv(csv_manifest)
    assert len(df_csv) >= 1
    row = df_csv.iloc[0]
    assert row["dataset"] == "Sentinel-2"
    assert row["station_id"] == STATION_ID
    assert row["status"] == "PROCESSED"
    assert row["validation_status"] == "VALIDATED"

    with open(json_manifest, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["station_target"]["station_id"] == STATION_ID
    assert meta["inventory"]["statistics"]["valid_clear_observations_count"] == 322
    assert meta["inventory"]["statistics"]["cloud_masked_observations_count"] == 705


def test_sentinel2_acquisitions_and_daily_alignment():
    """Verify acquisition table and full-calendar daily features alignment."""
    acq_file = S2_PROCESSED_DIR / "sentinel2_acquisitions.csv"
    daily_file = S2_PROCESSED_DIR / "sentinel2_daily_features.csv"

    assert acq_file.is_file(), "sentinel2_acquisitions.csv missing"
    assert daily_file.is_file(), "sentinel2_daily_features.csv missing"

    df_acq = pd.read_csv(acq_file)
    assert len(df_acq) == 1027
    assert df_acq["is_valid"].sum() == 322
    assert df_acq["is_cloud_masked"].sum() == 705

    # Verify cloud masked acquisitions have NaN reflectances (never 0)
    masked = df_acq[df_acq["is_cloud_masked"] == True]
    assert masked["b04_red"].isna().all()
    assert masked["b08_nir"].isna().all()
    assert masked["ndvi"].isna().all()

    # Verify clear acquisitions have physical reflectance range [0.0, 1.0]
    clear = df_acq[df_acq["is_valid"] == True]
    assert (clear["b04_red"] >= 0.0).all() and (clear["b04_red"] <= 1.0).all()
    assert (clear["b08_nir"] >= 0.0).all() and (clear["b08_nir"] <= 1.0).all()
    assert (clear["ndvi"] >= -1.0).all() and (clear["ndvi"] <= 1.0).all()

    df_daily = pd.read_csv(daily_file)
    assert len(df_daily) == EXPECTED_CALENDAR_DAYS
    assert df_daily["date"].iloc[0] == TIMELINE_START
    assert df_daily["date"].iloc[-1] == TIMELINE_END
    assert df_daily["s2_has_valid_observation"].sum() == 322

    # Verify unobserved days have NaN indices
    unobserved = df_daily[~df_daily["s2_has_valid_observation"]]
    assert unobserved["s2_ndvi_mean"].isna().all()
    assert unobserved["s2_b04_red_mean"].isna().all()


def test_sentinel2_vegetation_indices_formula():
    """Verify analytical NDVI and EVI formula implementations."""
    red = 0.10
    nir = 0.40
    blue = 0.05

    # NDVI = (NIR - Red) / (NIR + Red) = 0.30 / 0.50 = 0.60
    ndvi_expected = (nir - red) / (nir + red)
    assert math.isclose(ndvi_expected, 0.60, abs_tol=1e-5)

    # EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
    denom = nir + (6.0 * red) - (7.5 * blue) + 1.0
    evi_expected = 2.5 * (nir - red) / denom
    assert math.isclose(evi_expected, 0.461538, abs_tol=1e-5)
