"""
SoilDepth-AI — Maharashtra Environmental Data Acquisition Pipeline Tests
Pilot Station: IITM-PUNE-COSMOS
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Validates date alignment, timezone consistency, satellite quality filtering,
         missing observation preservation, duplicate handling, physical feature units,
         leakage prevention, and manifest reproducibility for Maharashtra Phase 2B.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAHARASHTRA_PROCESSED_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "COSMOS" / "processed" / "IITM-PUNE"
DAILY_FEATURES_CSV = MAHARASHTRA_PROCESSED_DIR / "daily_environmental_features.csv"
STATIC_FEATURES_CSV = MAHARASHTRA_PROCESSED_DIR / "static_environmental_features.csv"
MANIFEST_JSON = MAHARASHTRA_PROCESSED_DIR / "acquisition_manifest.json"
QUALITY_REPORT_JSON = MAHARASHTRA_PROCESSED_DIR / "quality_report.json"


@pytest.fixture(scope="module")
def daily_df():
    """Loads the daily environmental feature matrix."""
    assert DAILY_FEATURES_CSV.exists(), f"Daily features file missing: {DAILY_FEATURES_CSV}"
    df = pd.read_csv(DAILY_FEATURES_CSV)
    return df


@pytest.fixture(scope="module")
def static_df():
    """Loads the static environmental feature table."""
    assert STATIC_FEATURES_CSV.exists(), f"Static features file missing: {STATIC_FEATURES_CSV}"
    df = pd.read_csv(STATIC_FEATURES_CSV)
    return df


@pytest.fixture(scope="module")
def manifest_data():
    """Loads the acquisition manifest."""
    assert MANIFEST_JSON.exists(), f"Manifest file missing: {MANIFEST_JSON}"
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# TEST 1: CHRONOLOGICAL DATE ALIGNMENT
# ==============================================================================
def test_date_alignment(daily_df):
    """Verifies exact 2,556 daily rows, start/end bounds, and strict monotonicity."""
    assert len(daily_df) == 2556, f"Expected 2,556 daily rows, found {len(daily_df)}"
    assert daily_df["date"].iloc[0] == "2017-01-01", f"First date must be 2017-01-01, got {daily_df['date'].iloc[0]}"
    assert daily_df["date"].iloc[-1] == "2023-12-31", f"Last date must be 2023-12-31, got {daily_df['date'].iloc[-1]}"
    assert daily_df["date"].is_monotonic_increasing, "Date series must be strictly monotonic increasing"

    expected_dates = pd.date_range("2017-01-01", "2023-12-31", freq="D").strftime("%Y-%m-%d")
    assert (daily_df["date"].values == expected_dates.values).all(), "Calendar dates mismatch expected daily sequence"


# ==============================================================================
# TEST 2: TIMEZONE CONSISTENCY
# ==============================================================================
def test_timezone_consistency(manifest_data):
    """Verifies documented UTC daily convention and Indian Standard Time (IST) offset handling."""
    assert "UTC" in manifest_data["timezone_convention"]
    assert "Asia/Kolkata" in manifest_data["local_timezone"]
    assert "UTC+5.5" in manifest_data["local_timezone"]


# ==============================================================================
# TEST 3: DUPLICATE HANDLING
# ==============================================================================
def test_duplicate_handling(daily_df):
    """Verifies that no date appears more than once."""
    dup_count = daily_df["date"].duplicated().sum()
    assert dup_count == 0, f"Found {dup_count} duplicate dates in daily feature matrix"


# ==============================================================================
# TEST 4: SATELLITE QUALITY FILTERING & SCL MASKING
# ==============================================================================
def test_satellite_quality_filtering(daily_df):
    """Verifies that cloudy/masked satellite dates do not contain synthetic optical data."""
    # When no valid observation occurred on a day, daily mean values must be NaN
    masked_s2 = daily_df[daily_df["s2_has_valid_observation"] == False]
    assert len(masked_s2) > 0, "Expected days without valid Sentinel-2 clear observations"
    assert masked_s2["s2_ndvi_mean"].isna().all(), "Masked/absent S2 dates must have NaN ndvi_mean"
    assert masked_s2["s2_evi_mean"].isna().all(), "Masked/absent S2 dates must have NaN evi_mean"

    # When valid observation occurred, values must be within physical ranges
    valid_s2 = daily_df[daily_df["s2_has_valid_observation"] == True]
    if len(valid_s2) > 0:
        assert (valid_s2["s2_ndvi_mean"] >= -1.0).all() and (valid_s2["s2_ndvi_mean"] <= 1.0).all()
        assert (valid_s2["s2_evi_mean"] >= -1.0).all() and (valid_s2["s2_evi_mean"] <= 1.5).all()


# ==============================================================================
# TEST 5: MISSING OBSERVATIONS PRESERVATION
# ==============================================================================
def test_missing_observations_preservation(daily_df):
    """Verifies missing satellite data is preserved as missing without fabrication."""
    # Sentinel-1 missingness check
    s1_valid = daily_df["s1_has_valid_observation"]
    assert s1_valid.dtype == bool
    assert (~s1_valid).sum() > 0, "Missing Sentinel-1 acquisitions must be preserved as False"

    # SMAP missingness check (awaiting credentials)
    smap_valid = daily_df["smap_has_valid_retrieval"]
    assert smap_valid.dtype == bool
    # SMAP columns must not have fabricated numbers
    assert daily_df["smap_sm_daily_mean_m3_m3"].isna().all(), "Unacquired SMAP data must be preserved as NaN"


# ==============================================================================
# TEST 6: PHYSICAL UNITS & BOUNDS
# ==============================================================================
def test_feature_units_and_physical_bounds(daily_df, static_df):
    """Verifies physical bounds on temperatures, rain, solar, wind, soil, and elevation."""
    # Weather bounds
    assert (daily_df["temperature_2m_mean_c"] >= 5.0).all() and (daily_df["temperature_2m_mean_c"] <= 45.0).all()
    assert (daily_df["precipitation_total_mm"] >= 0.0).all()
    assert (daily_df["solar_radiation_total_mj_m2"] >= 0.0).all()
    assert (daily_df["wind_speed_10m_ms"] >= 0.0).all()
    assert (daily_df["vpd_kpa"] >= 0.0).all()

    # SoilGrids bounds on static table
    assert len(static_df) == 1, "Static table must contain exactly one row for IITM-Pune"
    for depth in ["0_5cm", "5_15cm", "15_30cm", "30_60cm"]:
        clay = float(static_df[f"soilgrids_clay_{depth}"].iloc[0])
        sand = float(static_df[f"soilgrids_sand_{depth}"].iloc[0])
        silt = float(static_df[f"soilgrids_silt_{depth}"].iloc[0])
        total_texture = clay + sand + silt
        assert 95.0 <= total_texture <= 105.0, f"Texture closure violation at {depth}: {total_texture}%"

        bdod = float(static_df[f"soilgrids_bdod_{depth}"].iloc[0])
        assert 1.0 <= bdod <= 1.8, f"Bulk density out of bounds at {depth}: {bdod} g/cm3"

        wv10 = float(static_df[f"soilgrids_wv0010_{depth}"].iloc[0])
        wv33 = float(static_df[f"soilgrids_wv0033_{depth}"].iloc[0])
        wv1500 = float(static_df[f"soilgrids_wv1500_{depth}"].iloc[0])
        assert wv1500 < wv33 < wv10, f"Suction hierarchy violated at {depth}: {wv1500} < {wv33} < {wv10}"

    # DEM bounds
    elev = float(static_df["elevation_m"].iloc[0])
    assert 500.0 <= elev <= 650.0, f"Copernicus DEM elevation {elev} m deviates from expected Pune plateau"
    assert float(static_df["slope_deg"].iloc[0]) >= 0.0


# ==============================================================================
# TEST 7: STRICT LEAKAGE PREVENTION
# ==============================================================================
def test_leakage_prevention(daily_df):
    """Verifies that no target columns exist and memory features use past-only shift(1)."""
    # 1. No target columns
    forbidden_targets = [
        "target", "target_sm_5cm", "target_sm_10cm", "target_sm_20cm", "target_sm_50cm",
        "ground_truth", "ismn", "cosmos", "target_lag_1d"
    ]
    for col in daily_df.columns:
        for f in forbidden_targets:
            assert f != col.lower(), f"Target column '{col}' detected in predictor matrix!"

    # 2. Verify precip_lag_1d is exactly precipitation_total_mm shifted by 1
    expected_lag1 = daily_df["precipitation_total_mm"].shift(1).fillna(0.0)
    assert np.allclose(daily_df["precip_lag_1d"].values[1:], expected_lag1.values[1:], atol=1e-4)

    # 3. Verify rolling sums are past-only
    expected_roll3 = daily_df["precipitation_total_mm"].shift(1).rolling(3, min_periods=1).sum()
    assert np.allclose(daily_df["precip_roll_sum_3d"].values[3:], expected_roll3.values[3:], atol=1e-4)


# ==============================================================================
# TEST 8: REPRODUCIBILITY & MANIFEST HASHES
# ==============================================================================
def test_reproducibility_and_manifest(manifest_data):
    """Verifies manifest ledger integrity and cryptographic hash recording."""
    assert manifest_data["station_id"] == "IITM-PUNE-COSMOS"
    entries = manifest_data["manifest_entries"]
    assert len(entries) > 0, "Manifest must contain file records"
    for e in entries:
        assert "filename" in e
        assert "sha256" in e
        assert "units" in e
        assert "coordinate_reference_system" in e

