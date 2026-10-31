"""
SoilDepth-AI — Tests for DEM Dataset Structure, USGS 3DEP Ingestion & Processing Interface
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Verify DEM directory structure, downloaded USGS 3DEP 1-arc-second GeoTIFF
         integrity, georeferencing extraction, station spatial coverage, elevation sampling
         against SCAN benchmark (241.0 m), Horn (1981) 3x3 slope derivation,
         manifest ledgers, and processing artifacts.
"""

import math
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from PIL import Image

from dataset.DEM.scripts.process_dem import (
    REPO_ROOT,
    DEM_DIR,
    DEM_RAW_DIR,
    DEM_PROCESSED_DIR,
    DEM_AUDIT_DIR,
    DEM_MANIFEST_DIR,
    STATION_REGISTRY,
    STANDARD_NODATA_VALUES,
    compute_file_sha256,
    extract_geotiff_spatial_metadata,
    inspect_dem_raster,
    check_station_coverage,
    extract_station_elevation,
    derive_station_slope,
    process_dem,
)

EXPECTED_TIF_NAME = "USGS_1_n35w087.tif"
EXPECTED_XML_NAME = "USGS_1_n35w087.xml"
EXPECTED_TIF_SHA256 = "85f708645dd49c09b0921d2af60ec8e5b2b88f8b1f573abd7af6f07275db186a"
EXPECTED_XML_SHA256 = "c935c500352635073a938d41b3f3268d88a2a0e6b2a39559f1c4a03ece3f5748"
EXPECTED_TIF_SIZE = 56024342


def test_dem_directory_structure():
    """Verify standard DEM directory tree exists and raw directory contains downloaded USGS 3DEP assets."""
    station_id = "AAMU-JTG"
    raw_station_dir = DEM_DIR / "raw" / station_id
    assert raw_station_dir.is_dir(), "raw/AAMU-JTG directory missing"
    assert (DEM_DIR / "processed" / station_id).is_dir(), "processed/AAMU-JTG directory missing"
    assert (DEM_DIR / "audit" / station_id).is_dir(), "audit/AAMU-JTG directory missing"
    assert (DEM_DIR / "scripts").is_dir(), "scripts directory missing"
    assert (DEM_DIR / "manifests").is_dir(), "manifests directory missing"
    assert (DEM_DIR / "tests").is_dir(), "tests directory missing"
    assert (DEM_DIR / "README.md").is_file(), "DEM README.md missing"

    # Confirm raw directory contains downloaded USGS assets
    tif_file = raw_station_dir / EXPECTED_TIF_NAME
    xml_file = raw_station_dir / EXPECTED_XML_NAME
    assert tif_file.is_file(), f"Expected GeoTIFF file {tif_file} not found"
    assert xml_file.is_file(), f"Expected metadata XML {xml_file} not found"
    assert tif_file.stat().st_size == EXPECTED_TIF_SIZE


def test_dem_manifest_integrity():
    """Verify JSON template and CSV manifest record the actual USGS 3DEP acquisition details."""
    json_path = DEM_MANIFEST_DIR / "dem_manifest_template.json"
    csv_path = DEM_MANIFEST_DIR / "download_manifest.csv"

    assert json_path.is_file(), "dem_manifest_template.json missing"
    assert csv_path.is_file(), "download_manifest.csv missing"

    # Check JSON manifest structure
    with open(json_path, "r", encoding="utf-8") as f:
        meta_json = json.load(f)

    assert meta_json["station_target"]["station_id"] == "AAMU-JTG"
    assert meta_json["station_target"]["latitude"] == 34.78534
    assert meta_json["station_target"]["longitude"] == -86.55906
    assert meta_json["station_target"]["benchmark_elevation_m"] == 241.0
    inv = meta_json["current_inventory"]
    assert inv["selected_source"] == "USGS"
    assert inv["actual_filename"] == EXPECTED_TIF_NAME
    assert inv["file_size_bytes"] == EXPECTED_TIF_SIZE
    assert inv["sha256"] == EXPECTED_TIF_SHA256
    assert inv["status"] == "PROCESSED"
    assert inv["validation_status"] == "VALIDATED"
    assert inv["extraction_status"] == "SUCCESS"

    # Check CSV manifest structure
    df_csv = pd.read_csv(csv_path)
    assert len(df_csv) >= 1
    row = df_csv[df_csv["station_id"] == "AAMU-JTG"].iloc[0]
    assert row["dataset"] == "DEM"
    assert row["source_agency"] == "USGS"
    assert row["actual_filename"] == EXPECTED_TIF_NAME
    assert int(row["file_size_bytes"]) == EXPECTED_TIF_SIZE
    assert row["sha256"] == EXPECTED_TIF_SHA256
    assert row["status"] == "PROCESSED"
    assert row["validation_status"] == "VALIDATED"
    assert row["extraction_status"] == "SUCCESS"


def test_dem_downloaded_raster_integrity():
    """Verify downloaded USGS 3DEP GeoTIFF dimensions, tags, data ranges, and checksum."""
    tif_file = DEM_RAW_DIR / "AAMU-JTG" / EXPECTED_TIF_NAME
    profile = inspect_dem_raster(tif_file, station_id="AAMU-JTG")

    assert profile["is_valid"] is True
    assert profile["file_name"] == EXPECTED_TIF_NAME
    assert profile["file_size_bytes"] == EXPECTED_TIF_SIZE
    assert profile["sha256"] == EXPECTED_TIF_SHA256
    assert profile["width"] == 3612
    assert profile["height"] == 3612
    assert profile["min_elevation"] >= 100.0
    assert profile["max_elevation"] <= 600.0

    meta = profile["spatial_metadata"]
    assert meta["has_geotiff_tags"] is True
    assert math.isclose(meta["dx"], 0.000277777778, rel_tol=1e-4)
    assert math.isclose(meta["dy"], 0.000277777778, rel_tol=1e-4)
    assert meta["x_min"] <= -86.55906 <= meta["x_max"]
    assert meta["y_min"] <= 34.78534 <= meta["y_max"]


def test_dem_station_coverage_and_elevation_sampling():
    """Verify station AAMU-JTG pixel coordinate extraction and physical elevation consistency."""
    tif_file = DEM_RAW_DIR / "AAMU-JTG" / EXPECTED_TIF_NAME
    with Image.open(tif_file) as img:
        spatial_meta = extract_geotiff_spatial_metadata(img)
        arr = np.array(img, dtype=float)

    has_cov, col_idx, row_idx, msg = check_station_coverage(
        spatial_meta, lat=34.78534, lon=-86.55906
    )
    assert has_cov is True
    assert col_idx == 1593
    assert row_idx == 779

    val, valid, elev_msg = extract_station_elevation(
        arr, col_idx, row_idx, nodata_value=spatial_meta["nodata_tag_value"]
    )
    assert valid is True
    assert math.isclose(val, 245.47, abs_tol=0.1)

    # Verify difference against ground truth benchmark (241.0 m) is within tolerance (15 m)
    diff = abs(val - 241.0)
    assert diff < 5.0, f"Elevation difference ({diff:.2f} m) exceeds 5.0 m"


def test_dem_slope_derivation_real_terrain():
    """Verify Horn 3x3 slope calculation and aspect on the real USGS elevation grid around AAMU-JTG."""
    tif_file = DEM_RAW_DIR / "AAMU-JTG" / EXPECTED_TIF_NAME
    with Image.open(tif_file) as img:
        spatial_meta = extract_geotiff_spatial_metadata(img)
        arr = np.array(img, dtype=float)

    slope_info = derive_station_slope(
        arr=arr,
        col_idx=1593,
        row_idx=779,
        dx=spatial_meta["dx"],
        dy=spatial_meta["dy"],
        lat=34.78534,
        horizontal_units="degrees",
        nodata_value=spatial_meta["nodata_tag_value"],
    )

    assert slope_info["slope_coverage_valid"] is True
    assert slope_info["status"] == "VALID"
    # Ground slope in low-relief agricultural terrain: ~4.9 degrees
    assert math.isclose(slope_info["slope_deg"], 4.9156, abs_tol=0.01)
    # Aspect is approximately 189 degrees (facing south-southwest)
    assert math.isclose(slope_info["aspect_deg"], 189.33, abs_tol=0.5)
    assert slope_info["aspect_sin"] is not None
    assert slope_info["aspect_cos"] is not None


def test_dem_processed_artifacts_integrity():
    """Verify processed CSV and audit JSON contain all required features and correct provenance."""
    csv_file = DEM_PROCESSED_DIR / "AAMU-JTG" / "dem_AAMU-JTG_features.csv"
    audit_file = DEM_AUDIT_DIR / "AAMU-JTG" / "dem_quality_report.json"

    assert csv_file.is_file(), "Processed features CSV not found"
    assert audit_file.is_file(), "Quality report JSON not found"

    df = pd.read_csv(csv_file)
    assert len(df) == 1
    assert df["station_id"].iloc[0] == "AAMU-JTG"
    assert math.isclose(df["elevation_m"].iloc[0], 245.47, abs_tol=0.1)
    assert math.isclose(df["slope_deg"].iloc[0], 4.9156, abs_tol=0.01)
    assert df["slope_coverage_valid"].iloc[0] == True
    assert df["is_benchmark_consistent"].iloc[0] == True
    assert df["source_file"].iloc[0] == EXPECTED_TIF_NAME
    assert df["sha256"].iloc[0] == EXPECTED_TIF_SHA256

    with open(audit_file, "r", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["status"] == "PROCESSED"
    assert audit["validation_status"] == "VALIDATED"
    assert audit["extraction_status"] == "SUCCESS"
    assert audit["raw_source"]["filename"] == EXPECTED_TIF_NAME
    assert audit["station_extraction"]["extracted_elevation_m"] == 245.47


def test_dem_slope_derivation_horn_algorithm():
    """Verify Horn 3x3 slope calculation on synthetic inclined plane with known analytical gradient."""
    delta_x = 30.0  # meters
    delta_y = 30.0  # meters
    grid_size = 5

    x = np.arange(grid_size) * delta_x
    y = np.arange(grid_size) * delta_y
    xx, yy = np.meshgrid(x, y)
    arr = 200.0 + 0.1 * xx

    slope_res = derive_station_slope(
        arr=arr,
        col_idx=2,
        row_idx=2,
        dx=delta_x,
        dy=delta_y,
        lat=34.78534,
        horizontal_units="meters",
    )

    assert slope_res["slope_coverage_valid"] is True
    assert slope_res["status"] == "VALID"
    expected_slope = math.degrees(math.atan(0.1))
    assert math.isclose(slope_res["slope_deg"], expected_slope, abs_tol=1e-3)
    assert math.isclose(slope_res["slope_rise_run"], 0.1, abs_tol=1e-5)


def test_dem_slope_boundary_and_nodata_guards():
    """Verify slope algorithm guards against border proximity and NoData neighborhood cells."""
    arr = np.full((5, 5), 241.0, dtype=float)

    # 1. Border pixel (row_idx = 0) -> incomplete 3x3 window
    border_res = derive_station_slope(
        arr=arr,
        col_idx=2,
        row_idx=0,
        dx=30.0,
        dy=30.0,
        lat=34.78534,
        horizontal_units="meters",
    )
    assert border_res["slope_coverage_valid"] is False
    assert border_res["status"] == "INSUFFICIENT_COVERAGE_BORDER"
    assert border_res["slope_deg"] is None

    # 2. Pixel surrounded by a NoData cell
    arr_with_nodata = arr.copy()
    arr_with_nodata[1, 2] = -9999.0  # Adjacent cell to center (2, 2)
    nodata_res = derive_station_slope(
        arr=arr_with_nodata,
        col_idx=2,
        row_idx=2,
        dx=30.0,
        dy=30.0,
        lat=34.78534,
        horizontal_units="meters",
        nodata_value=-9999.0,
    )
    assert nodata_res["slope_coverage_valid"] is False
    assert nodata_res["status"] == "INSUFFICIENT_COVERAGE_NODATA"
    assert nodata_res["slope_deg"] is None
