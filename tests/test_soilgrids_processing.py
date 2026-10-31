"""
SoilDepth-AI — Tests for SoilGrids 250m Raster-to-Tabular Extraction and Physical Plausibility
"""

import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image

from dataset.SoilGrids.scripts.process_soilgrids import (
    RAW_SOILGRIDS_DIR,
    PROCESSED_SOILGRIDS_DIR,
    AUDIT_SOILGRIDS_DIR,
    EXPECTED_STATION_ID,
    EXPECTED_LATITUDE,
    EXPECTED_LONGITUDE,
    EXPECTED_ELEVATION_M,
    EXPECTED_RASTER_WIDTH,
    EXPECTED_RASTER_HEIGHT,
    EXPECTED_CRS,
    EXPECTED_PROPERTIES,
    EXPECTED_DEPTH_INTERVALS,
    discover_and_validate_rasters,
    verify_raster_spatial_metadata,
    extract_and_scale_properties,
    validate_physical_consistency,
)


def test_soilgrids_programmatic_discovery_all_32():
    """Verify programmatically discovering all 32 GeoTIFF files across 8 properties and 4 depths."""
    assert RAW_SOILGRIDS_DIR.exists()
    rasters = discover_and_validate_rasters(RAW_SOILGRIDS_DIR)
    assert len(rasters) == 32

    for prop in EXPECTED_PROPERTIES.keys():
        for depth in EXPECTED_DEPTH_INTERVALS:
            assert (prop, depth) in rasters
            fpath = rasters[(prop, depth)]
            assert fpath.exists()
            assert fpath.stat().st_size > 300000  # All rasters are >300 KB


def test_soilgrids_raster_metadata_and_affine_transform():
    """Verify raster width, height, georeferencing, and station pixel col=453, row=413."""
    rasters = discover_and_validate_rasters(RAW_SOILGRIDS_DIR)
    sample_raster = rasters[("bulk_density", "0-5cm")]

    meta = verify_raster_spatial_metadata(sample_raster, EXPECTED_LATITUDE, EXPECTED_LONGITUDE)
    assert meta["width"] == EXPECTED_RASTER_WIDTH
    assert meta["height"] == EXPECTED_RASTER_HEIGHT
    assert meta["pixel_col"] == 453
    assert meta["pixel_row"] == 413
    assert pytest.approx(meta["exact_col"], abs=0.5) == 452.7
    assert pytest.approx(meta["exact_row"], abs=0.5) == 412.6


def test_soilgrids_extraction_and_scaling_factors():
    """Verify scaling factor arithmetic and physical values at station pixel."""
    rasters = discover_and_validate_rasters(RAW_SOILGRIDS_DIR)
    extraction_res = extract_and_scale_properties(rasters)

    assert extraction_res["pixel_col"] == 453
    assert extraction_res["pixel_row"] == 413

    records = extraction_res["records"]
    assert len(records) == 32

    # Verify Bulk Density: Raw / 100 -> g/cm3
    bd_0_5 = records["bulk_density_0-5cm"]
    assert bd_0_5["raw_value"] == 130
    assert bd_0_5["physical_value"] == pytest.approx(1.30)
    assert bd_0_5["physical_unit"] == "g/cm³"

    # Verify Clay: Raw / 10 -> %
    clay_0_5 = records["clay_0-5cm"]
    assert clay_0_5["raw_value"] == 247
    assert clay_0_5["physical_value"] == pytest.approx(24.7)
    assert clay_0_5["physical_unit"] == "%"

    # Verify Water Content 10kPa: Raw / 1000 -> m3/m3
    wv10_0_5 = records["water_content_10kPa_0-5cm"]
    assert wv10_0_5["raw_value"] == 390
    assert wv10_0_5["physical_value"] == pytest.approx(0.390)
    assert wv10_0_5["physical_unit"] == "m³/m³"


def test_soilgrids_nodata_and_water_mask_safety():
    """Verify station pixel is not NoData or masked water body."""
    rasters = discover_and_validate_rasters(RAW_SOILGRIDS_DIR)
    extraction_res = extract_and_scale_properties(rasters)
    records = extraction_res["records"]

    for k, v in records.items():
        assert v["raw_value"] != -32768, f"Found NoData -32768 in {k}!"
        # In terrestrial properties (bulk density, clay, sand, silt), zero indicates water body
        if v["property"] in ("bulk_density", "clay", "sand", "silt"):
            assert v["raw_value"] > 0, f"Found zero/water mask in terrestrial property {k}!"


def test_soilgrids_authoritative_physical_plausibility():
    """
    Verify fundamental laws of soil physics:
    1. Texture mass balance = 100.0%
    2. Bulk density increases with depth
    3. Organic carbon decays with depth
    4. Water retention hierarchy holds (wilting < field capacity < drainage)
    """
    rasters = discover_and_validate_rasters(RAW_SOILGRIDS_DIR)
    extraction_res = extract_and_scale_properties(rasters)
    audit = validate_physical_consistency(extraction_res)

    assert audit["overall_physically_consistent"] is True

    # 1. Texture balance
    for d, tex in audit["textural_mass_balance"].items():
        assert tex["is_valid"] is True
        assert tex["sum_pct"] == pytest.approx(100.0)

    # 2. Bulk density monotonicity
    assert audit["bulk_density_monotonicity"]["is_monotonically_increasing"] is True
    bd_vals = audit["bulk_density_monotonicity"]["values_g_cm3"]
    assert bd_vals == [1.30, 1.49, 1.55, 1.58]

    # 3. Organic carbon decay
    assert audit["organic_carbon_decay"]["is_monotonically_decreasing"] is True
    ocd_vals = audit["organic_carbon_decay"]["values_kg_m3"]
    assert ocd_vals == [38.2, 21.1, 13.2, 7.3]

    # 4. Water retention suction hierarchy
    for d, wr in audit["water_retention_hierarchy"].items():
        assert wr["hierarchy_satisfied"] is True
        assert wr["theta_1500kPa_m3_m3"] < wr["theta_33kPa_m3_m3"] < wr["theta_10kPa_m3_m3"]


def test_soilgrids_output_feature_csv_and_audit_report():
    """Verify saved CSV has exactly 1 row, 71 columns, and audit JSON is populated."""
    out_csv = PROCESSED_SOILGRIDS_DIR / f"soilgrids_{EXPECTED_STATION_ID}_features.csv"
    assert out_csv.exists(), f"SoilGrids processed CSV missing at {out_csv}"

    df = pd.read_csv(out_csv)
    assert len(df) == 1
    assert len(df.columns) == 71
    assert df["station_id"].iloc[0] == EXPECTED_STATION_ID
    assert df["raster_pixel_col"].iloc[0] == 453
    assert df["raster_pixel_row"].iloc[0] == 413

    # Audit JSON
    out_json = AUDIT_SOILGRIDS_DIR / "soilgrids_extraction_report.json"
    assert out_json.exists(), f"SoilGrids audit JSON missing at {out_json}"

    with open(out_json, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["total_verified_rasters"] == 32
    assert report["grid_alignment"]["station_pixel_col"] == 453
    assert report["grid_alignment"]["station_pixel_row"] == 413
    assert report["physical_validation_results"]["overall_physically_consistent"] is True

