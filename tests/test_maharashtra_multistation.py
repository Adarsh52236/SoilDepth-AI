"""
SoilDepth-AI — Maharashtra Phase 2D Multi-Station & Expansion Tests
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Validates multi-station configuration, independent station manifests and outputs,
         station coordinates and DEM elevations, ground-truth schema normalization and
         depth integrity, crop registry agronomic consistency, missingness preservation,
         and leakage prevention across multiple Maharashtra stations.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from services.data_acquisition.maharashtra.config import (
    StationConfig,
    PUNE_CONFIG,
    RAHURI_CONFIG,
    BARAMATI_CONFIG,
    STATION_CONFIGS,
    get_station_config,
    REPO_ROOT,
    MAHARASHTRA_DATA_ROOT,
    METADATA_DIR,
)
from services.data_acquisition.maharashtra.ground_truth_adapter import (
    MaharashtraGroundTruthAdapter,
    NORMALIZED_COLUMNS,
    GroundTruthValidationError,
)

PUNE_PROCESSED_DIR = MAHARASHTRA_DATA_ROOT / "processed" / "IITM-PUNE"
RAHURI_PROCESSED_DIR = MAHARASHTRA_DATA_ROOT / "processed" / "MPKV-RAHURI-CAAST"


# ==============================================================================
# 1. MULTI-STATION CONFIGURATION TESTS
# ==============================================================================
def test_multistation_config_loading():
    """Verifies pre-configured stations and dynamic loading from station_registry.csv."""
    assert "IITM-PUNE-COSMOS" in STATION_CONFIGS
    assert "MPKV-RAHURI-CAAST" in STATION_CONFIGS
    assert "NIASM-BARAMATI-FLUX" in STATION_CONFIGS

    # Test get_station_config helper
    cfg_pune = get_station_config("IITM-PUNE-COSMOS")
    assert cfg_pune.station_id == "IITM-PUNE-COSMOS"
    assert cfg_pune.latitude == 18.5372
    assert cfg_pune.longitude == 73.8051

    cfg_rahuri = get_station_config("MPKV-RAHURI-CAAST")
    assert cfg_rahuri.station_id == "MPKV-RAHURI-CAAST"
    assert cfg_rahuri.latitude == 19.3932
    assert cfg_rahuri.longitude == 74.6475
    assert cfg_rahuri.benchmark_elevation_m == 512.0

    # Test dynamic loading of another station from CSV
    cfg_imd = get_station_config("IMD-AGRIMET-PUNE")
    assert cfg_imd.station_id == "IMD-AGRIMET-PUNE"
    assert cfg_imd.latitude == 18.5308
    assert cfg_imd.longitude == 73.8507

    # Unknown station raises KeyError
    with pytest.raises(KeyError):
        get_station_config("NON_EXISTENT_STATION")


def test_station_path_isolation():
    """Verifies that each station resolves to completely distinct raw and processed paths."""
    cfg_pune = PUNE_CONFIG
    cfg_rahuri = RAHURI_CONFIG

    assert cfg_pune.raw_dir != cfg_rahuri.raw_dir
    assert cfg_pune.processed_dir != cfg_rahuri.processed_dir
    assert cfg_pune.daily_features_csv != cfg_rahuri.daily_features_csv
    assert cfg_pune.static_features_csv != cfg_rahuri.static_features_csv
    assert cfg_pune.acquisition_manifest_json != cfg_rahuri.acquisition_manifest_json

    # Pune backwards-compatible folder name
    assert cfg_pune.raw_dir.name == "IITM-PUNE"
    assert cfg_rahuri.raw_dir.name == "MPKV-RAHURI-CAAST"


# ==============================================================================
# 2. INDEPENDENT STATION MANIFESTS & FEATURE PARITY TESTS
# ==============================================================================
def test_independent_station_manifests():
    """Verifies that Pune and Rahuri have independent manifests with station-specific metadata."""
    pune_manifest_path = PUNE_PROCESSED_DIR / "acquisition_manifest.json"
    rahuri_manifest_path = RAHURI_PROCESSED_DIR / "acquisition_manifest.json"

    assert pune_manifest_path.exists(), f"Missing {pune_manifest_path}"
    assert rahuri_manifest_path.exists(), f"Missing {rahuri_manifest_path}"

    with open(pune_manifest_path, "r", encoding="utf-8") as f:
        pune_man = json.load(f)
    with open(rahuri_manifest_path, "r", encoding="utf-8") as f:
        rahuri_man = json.load(f)

    assert pune_man["station_id"] == "IITM-PUNE-COSMOS"
    assert rahuri_man["station_id"] == "MPKV-RAHURI-CAAST"
    assert pune_man["latitude"] != rahuri_man["latitude"]
    assert pune_man["longitude"] != rahuri_man["longitude"]
    assert pune_man["benchmark_elevation_m"] == 560.0
    assert rahuri_man["benchmark_elevation_m"] == 512.0

    assert len(pune_man["manifest_entries"]) == 43
    assert len(rahuri_man["manifest_entries"]) == 43


def test_station_feature_parity_and_coordinate_correctness():
    """Verifies daily and static tables for both stations match schemas and differ in values."""
    pune_daily = pd.read_csv(PUNE_PROCESSED_DIR / "daily_environmental_features.csv")
    rahuri_daily = pd.read_csv(RAHURI_PROCESSED_DIR / "daily_environmental_features.csv")

    assert len(pune_daily) == 2556
    assert len(rahuri_daily) == 2556
    assert list(pune_daily.columns) == list(rahuri_daily.columns)
    assert len(pune_daily.columns) == 71

    # Station coordinates strictly preserved per row
    assert (pune_daily["station_id"] == "IITM-PUNE-COSMOS").all()
    assert (pune_daily["latitude"] == 18.5372).all()
    assert (pune_daily["longitude"] == 73.8051).all()

    assert (rahuri_daily["station_id"] == "MPKV-RAHURI-CAAST").all()
    assert (rahuri_daily["latitude"] == 19.3932).all()
    assert (rahuri_daily["longitude"] == 74.6475).all()

    # Temperature and precipitation must differ between distinct geographic locations
    assert not np.allclose(pune_daily["temperature_2m_mean_c"], rahuri_daily["temperature_2m_mean_c"])
    assert not np.allclose(pune_daily["precipitation_total_mm"], rahuri_daily["precipitation_total_mm"])

    # Static tables
    pune_static = pd.read_csv(PUNE_PROCESSED_DIR / "static_environmental_features.csv")
    rahuri_static = pd.read_csv(RAHURI_PROCESSED_DIR / "static_environmental_features.csv")

    assert pune_static["station_id"].iloc[0] == "IITM-PUNE-COSMOS"
    assert rahuri_static["station_id"].iloc[0] == "MPKV-RAHURI-CAAST"
    assert float(pune_static["elevation_m"].iloc[0]) == 591.58
    assert float(rahuri_static["elevation_m"].iloc[0]) == 514.52


# ==============================================================================
# 3. GROUND-TRUTH ADAPTER SCHEMA & DEPTH INTEGRITY TESTS
# ==============================================================================
def test_ground_truth_adapter_normalization():
    """Verifies that heterogeneous input frames are normalized into strict SoilDepth-AI schema."""
    adapter = MaharashtraGroundTruthAdapter()

    # Synthetic mock telemetry from an IMD or SAU logger
    raw_df = pd.DataFrame({
        "Datetime_IST": ["2022-06-15 08:30:00", "2022-06-16 08:30:00", "2022-06-17 08:30:00"],
        "Depth_cm": [10.0, 10.0, 10.0],
        "VWC_pct": [32.5, 34.1, 29.8],
        "Flag": ["GOOD", "GOOD", "GOOD"],
    })

    mapping = {
        "timestamp": "Datetime_IST",
        "sensor_depth_cm": "Depth_cm",
        "soil_moisture_vwc": "VWC_pct",
        "quality_flag": "Flag",
    }

    df_norm = adapter.normalize(
        df=raw_df,
        column_mapping=mapping,
        source_dataset="MPKV-CAAST-IoT",
        default_station_id="MPKV-RAHURI-CAAST",
        input_vwc_unit="%",
        input_timezone="Asia/Kolkata",
    )

    assert list(df_norm.columns) == NORMALIZED_COLUMNS
    assert len(df_norm) == 3
    assert (df_norm["station_id"] == "MPKV-RAHURI-CAAST").all()
    assert (df_norm["sensor_depth_cm"] == 10.0).all()
    # 32.5% -> 0.325 m3/m3
    assert df_norm["soil_moisture_vwc"].iloc[0] == 0.325
    assert df_norm["measurement_unit"].iloc[0] == "m3/m3"
    # 08:30 IST is 03:00 UTC
    assert df_norm["timestamp"].iloc[0] == "2022-06-15T03:00:00Z"

    val_res = adapter.validate(df_norm)
    assert val_res["is_valid"] == True
    assert val_res["good_records"] == 3


def test_ground_truth_rejection_of_interpolated_depths():
    """Verifies that synthetic inter-depth interpolation is detected and strictly rejected."""
    adapter = MaharashtraGroundTruthAdapter()

    # Raw telemetry containing an explicit interpolation indicator column
    interp_df = pd.DataFrame({
        "Datetime": ["2022-06-15 00:00:00"],
        "Depth": [20.0],
        "VWC": [0.28],
        "is_interpolated": [True],
    })

    mapping = {
        "timestamp": "Datetime",
        "sensor_depth_cm": "Depth",
        "soil_moisture_vwc": "VWC",
    }

    with pytest.raises(GroundTruthValidationError, match="Interpolated sensor observations detected"):
        adapter.normalize(
            df=interp_df,
            column_mapping=mapping,
            source_dataset="Mock-Interpolated",
            default_station_id="MPKV-RAHURI-CAAST",
        )


def test_ground_truth_validation_range_and_duplicates():
    """Verifies rejection of out-of-bounds VWC, invalid depths, and duplicate timestamps."""
    adapter = MaharashtraGroundTruthAdapter()

    invalid_df = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST", "MPKV-RAHURI-CAAST", "MPKV-RAHURI-CAAST"],
        "timestamp": ["2022-06-15T00:00:00Z", "2022-06-15T00:00:00Z", "2022-06-16T00:00:00Z"],
        "latitude": [19.3932, 19.3932, 19.3932],
        "longitude": [74.6475, 74.6475, 74.6475],
        "sensor_depth_cm": [10.0, 10.0, -5.0],  # Duplicate on row 1, invalid negative depth on row 2
        "soil_moisture_vwc": [0.35, 0.85, 0.25],  # Row 1 is 0.85 (> 0.65 physical limit)
        "measurement_unit": ["m3/m3", "m3/m3", "m3/m3"],
        "quality_flag": ["GOOD", "GOOD", "GOOD"],
        "source_dataset": ["Test", "Test", "Test"],
        "source_record_id": ["1", "2", "3"],
    })

    val_res = adapter.validate(invalid_df)
    assert val_res["is_valid"] == False
    assert val_res["duplicate_count"] == 1
    assert val_res["out_of_bounds_count"] == 1
    assert val_res["invalid_depth_count"] == 1


# ==============================================================================
# 4. CROP REGISTRY AGRONOMIC CONSISTENCY TESTS
# ==============================================================================
def test_crop_registry_agronomic_consistency():
    """Verifies crop registry for 10 crops, FAO-56 bounds, and non-empty metadata."""
    crop_csv = METADATA_DIR / "crop_registry.csv"
    assert crop_csv.exists(), f"Missing {crop_csv}"

    df_crops = pd.read_csv(crop_csv)
    assert len(df_crops) == 10

    expected_crops = {
        "Soybean", "Cotton", "Lowland Rice (Paddy)", "Wheat", "Sugarcane",
        "Maize (Corn)", "Chickpea (Bengal Gram)", "Pigeon pea (Red Gram / Tur)",
        "Groundnut (Peanut)", "Grain Sorghum (Jowar)"
    }
    assert set(df_crops["crop_name"]) == expected_crops

    # FAO-56 coefficient consistency
    for _, r in df_crops.iterrows():
        kc_ini = float(r["initial_kc"])
        kc_mid = float(r["mid_season_kc"])
        kc_end = float(r["end_season_kc"])
        p = float(r["allowable_depletion_p"])

        assert 0.20 <= kc_ini <= 1.20, f"Unreasonable initial Kc for {r['crop_name']}"
        assert 0.90 <= kc_mid <= 1.35, f"Unreasonable mid Kc for {r['crop_name']}"
        assert 0.20 <= kc_end <= 1.00, f"Unreasonable end Kc for {r['crop_name']}"
        assert 0.15 <= p <= 0.80, f"Unreasonable depletion p for {r['crop_name']}"


# ==============================================================================
# 5. LEAKAGE PREVENTION & MISSINGNESS PRESERVATION TESTS
# ==============================================================================
def test_temporal_and_spatial_leakage_safeguards():
    """Verifies absence of target columns, past-only shift(1), and zero ERA5 deep SM."""
    for sdir in [PUNE_PROCESSED_DIR, RAHURI_PROCESSED_DIR]:
        df = pd.read_csv(sdir / "daily_environmental_features.csv")

        # Zero target columns allowed
        for col in df.columns:
            assert "target" not in col.lower()
            assert "sm_5cm" not in col.lower()
            assert "sm_50cm" not in col.lower()
            assert "swvl" not in col.lower()

        # Antecedent weather memory uses shift(1)
        # Verify that precip_lag_1d on day D equals precipitation_total_mm on day D-1
        assert (df["precip_lag_1d"].iloc[1:].values == df["precipitation_total_mm"].iloc[:-1].values).all()

        # SMAP unpopulated state preserved
        assert df["smap_sm_daily_mean_m3_m3"].isna().all()
        assert (df["smap_has_valid_retrieval"] == False).all()
