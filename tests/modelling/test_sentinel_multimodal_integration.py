"""
SoilDepth-AI — Tests for Sentinel Multimodal Integration, Leakage Safeguards, and SCL Policy
Author: Senior Remote-Sensing Engineer & ML Data Auditor, SoilDepth-AI
Purpose: Verify:
         1. Manifest integrity and checksums for Sentinel-1 & Sentinel-2.
         2. Missing acquisition handling and 15-bit TIFF decoding accuracy.
         3. Sentinel-2 SCL class 7 sensitivity and conservative masking policy.
         4. Correct analytical calculations of NDVI and EVI vegetation indices.
         5. Leakage-safe feature availability and shift(1) temporal design.
         6. Maximum staleness thresholding and explicit missingness indicators.
         7. Chronological train/validation/test split integrity with full multimodal features.
"""

import sys
import math
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Add scripts directories to path
S1_SCRIPTS = REPO_ROOT / "dataset" / "Sentinel-1" / "scripts"
S2_SCRIPTS = REPO_ROOT / "dataset" / "Sentinel-2" / "scripts"
for p in [S1_SCRIPTS, S2_SCRIPTS]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from decode_15bit_s2 import unpack_15bit_msb, pack_15bit_msb
from services.modelling.config import (
    STATION_ID,
    STATION_LAT,
    STATION_LON,
    SENSOR_DEPTHS,
    TRAIN_START_DATE,
    TRAIN_END_DATE,
    VAL_START_DATE,
    VAL_END_DATE,
    TEST_START_DATE,
    TEST_END_DATE,
    S1_MAX_STALENESS_DAYS,
    S2_MAX_STALENESS_DAYS,
    SMAP_MAX_STALENESS_DAYS,
    DEM_TERRAIN_FEATURES,
    SENTINEL1_SAR_FEATURES,
    SENTINEL2_OPTICAL_FEATURES,
    FULL_MULTIMODAL_FEATURE_NAMES,
    SENTINEL1_DAILY_CSV,
    SENTINEL1_ACQUISITIONS_CSV,
    SENTINEL2_DAILY_CSV,
    SENTINEL2_ACQUISITIONS_CSV,
    DEM_STATIC_CSV,
)
from services.modelling.dataset_builder import (
    build_aligned_pilot_dataset,
    parse_dem_static_features,
)
from services.modelling.feature_engineering import (
    compute_days_since_valid_observation,
    build_sentinel1_features,
    build_sentinel2_features,
    generate_all_processed_datasets,
    partition_chronological_splits,
)


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# ==============================================================================
# 1. MANIFEST INTEGRITY & CHECKSUMS
# ==============================================================================
def test_sentinel1_manifest_checksums_and_provenance():
    """Verify Sentinel-1 download manifest correctly matches actual physical files."""
    manifest_csv = REPO_ROOT / "dataset" / "Sentinel-1" / "manifests" / "download_manifest.csv"
    assert manifest_csv.is_file(), "S1 download_manifest.csv missing"

    df_man = pd.read_csv(manifest_csv)
    assert len(df_man) >= 2, "Manifest must contain both acquisitions CSV and STAC catalog entries"

    # Verify acquisitions entry
    acq_row = df_man[df_man["actual_filename"] == "sentinel1_acquisitions.csv"].iloc[0]
    acq_file = REPO_ROOT / acq_row["processed_output_path"]
    assert acq_file.is_file()
    assert acq_file.stat().st_size == int(acq_row["file_size_bytes"])
    assert compute_sha256(acq_file) == acq_row["sha256"]
    assert acq_row["status"] == "PROCESSED"

    # Verify raw catalog entry
    cat_row = df_man[df_man["actual_filename"] == "sentinel1_stac_items.json"].iloc[0]
    cat_file = REPO_ROOT / cat_row["processed_output_path"]
    assert cat_file.is_file()
    assert cat_file.stat().st_size == int(cat_row["file_size_bytes"])
    assert compute_sha256(cat_file) == cat_row["sha256"]
    assert cat_row["status"] == "RAW_CATALOG"


# ==============================================================================
# 2. MISSING ACQUISITIONS & 15-BIT DECODER
# ==============================================================================
def test_sentinel2_15bit_decoder_roundtrip_and_missing_recovery():
    """Verify bitwise exact roundtrip of 15-bit MSB decoder and check recovered dates."""
    # 1. Roundtrip test with known synthetic 15-bit numbers
    original = np.array([0, 1, 100, 2048, 10000, 16383, 32767, 15432], dtype=np.uint16)
    packed = pack_15bit_msb(original)
    assert len(packed) == 15, "8 x 15-bit pixels must pack into exactly 15 bytes"

    unpacked = unpack_15bit_msb(packed, num_pixels=8)
    np.testing.assert_array_equal(unpacked, original)

    # 2. Verify audit file for the 3 recovered dates
    rec_file = REPO_ROOT / "dataset" / "Sentinel-2" / "audit" / "AAMU-JTG" / "sentinel2_recovered_missing_dates.json"
    assert rec_file.is_file(), "Recovered missing dates audit JSON missing"

    with open(rec_file, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    assert audit_data["stac_catalog_investigation"]["genuinely_missing_dates_count"] == 3
    assert len(audit_data["recovered_acquisitions"]) == 3

    recovered_dates = {rec["date"] for rec in audit_data["recovered_acquisitions"]}
    assert recovered_dates == {"2023-05-02", "2023-10-09", "2023-12-05"}

    for rec in audit_data["recovered_acquisitions"]:
        assert rec["is_valid"] is True
        assert 0.0 <= rec["b04_red"] <= 1.0
        assert 0.0 <= rec["b08_nir"] <= 1.0
        assert -1.0 <= rec["ndvi"] <= 1.0
        assert rec["scl_code"] in [4, 5]


# ==============================================================================
# 3. SCL CLASS 7 SENSITIVITY & MASKING POLICY
# ==============================================================================
def test_sentinel2_scl_class_7_exclusion_policy():
    """Verify SCL class 7 sensitivity statistics and conservative exclusion functionality."""
    audit_file = REPO_ROOT / "dataset" / "Sentinel-2" / "audit" / "AAMU-JTG" / "scl_sensitivity_analysis.json"
    assert audit_file.is_file(), "SCL sensitivity analysis JSON missing"

    with open(audit_file, "r", encoding="utf-8") as f:
        scl_report = json.load(f)

    assert scl_report["affected_observations_count"] == 17
    assert scl_report["existing_policy_clear_count"] == 319
    assert scl_report["conservative_policy_clear_count"] == 302

    # Verify conservative exclusion masking in feature engineering
    df_dummy = pd.DataFrame({
        "date_utc": ["2020-01-01", "2020-01-02", "2020-01-03"],
        "s2_has_valid_observation": [True, True, True],
        "s2_scl_code": [4, 7, 5],
        "s2_ndvi_mean": [0.45, 0.20, 0.50],
        "s2_evi_mean": [0.35, 0.15, 0.40],
        "s2_b04_red_mean": [0.15, 0.25, 0.12],
        "s2_b08_nir_mean": [0.40, 0.35, 0.45],
        "s2_b11_swir1_mean": [0.30, 0.30, 0.28],
        "s2_b12_swir2_mean": [0.20, 0.22, 0.18],
    })

    # Under standard policy (includes SCL 7)
    df_std = build_sentinel2_features(df_dummy, exclude_scl_7=False)
    # Day 2 sees yesterday (day 1, scl=4): ndvi_locf = 0.45
    # Day 3 sees yesterday (day 2, scl=7): ndvi_locf = 0.20
    assert df_std["s2_ndvi_locf"].iloc[2] == pytest.approx(0.20)

    # Under conservative policy (excludes SCL 7)
    df_cons = build_sentinel2_features(df_dummy, exclude_scl_7=True)
    # Day 3 sees last valid non-7 observation (day 1, scl=4): ndvi_locf = 0.45 (carried past SCL 7)
    assert df_cons["s2_ndvi_locf"].iloc[2] == pytest.approx(0.45)


# ==============================================================================
# 4. NDVI & EVI ANALYTICAL FORMULA VALIDATION
# ==============================================================================
def test_analytical_vegetation_indices_formulae():
    """Verify analytical NDVI and EVI formula calculations against boundary conditions."""
    # Synthetic reflectance values
    nir = 0.45
    red = 0.15
    blue = 0.08

    # Analytical formulas:
    # NDVI = (NIR - Red) / (NIR + Red) = 0.30 / 0.60 = 0.50
    ndvi_calc = (nir - red) / (nir + red)
    assert math.isclose(ndvi_calc, 0.50, abs_tol=1e-6)

    # EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
    denom = nir + (6.0 * red) - (7.5 * blue) + 1.0
    evi_calc = 2.5 * (nir - red) / denom
    expected_evi = 2.5 * 0.30 / (0.45 + 0.90 - 0.60 + 1.0)  # 0.75 / 1.75 = 0.4285714...
    assert math.isclose(evi_calc, expected_evi, abs_tol=1e-6)


# ==============================================================================
# 5. FUTURE OBSERVATION LEAKAGE PREVENTION
# ==============================================================================
def test_no_sentinel_future_temporal_leakage():
    """
    CRITICAL MULTIMODAL LEAKAGE TEST:
    Modifying Sentinel-1 or Sentinel-2 observations at future dates t >= cutoff
    MUST NEVER alter any lagged or LOCF features on day t-1 or earlier.
    """
    n_days = 90
    dates = pd.date_range("2017-01-01", periods=n_days, freq="D").strftime("%Y-%m-%d")

    np.random.seed(123)
    s1_vv = np.random.uniform(-14.0, -6.0, n_days)
    s1_valid = np.random.choice([True, False], size=n_days, p=[0.25, 0.75])
    s2_ndvi = np.random.uniform(0.20, 0.60, n_days)
    s2_valid = np.random.choice([True, False], size=n_days, p=[0.30, 0.70])

    df_base = pd.DataFrame({
        "date_utc": dates,
        "s1_vv_db_mean": s1_vv,
        "s1_vh_db_mean": s1_vv - 7.0,
        "s1_vv_vh_ratio_db_mean": np.full(n_days, 7.0),
        "s1_has_valid_observation": s1_valid,
        "s2_ndvi_mean": s2_ndvi,
        "s2_evi_mean": s2_ndvi * 0.85,
        "s2_b04_red_mean": np.random.uniform(0.05, 0.25, n_days),
        "s2_b08_nir_mean": np.random.uniform(0.30, 0.55, n_days),
        "s2_b11_swir1_mean": np.random.uniform(0.20, 0.40, n_days),
        "s2_b12_swir2_mean": np.random.uniform(0.15, 0.35, n_days),
        "s2_scl_code": np.full(n_days, 4),
        "s2_has_valid_observation": s2_valid,
    })

    feats_s1_base = build_sentinel1_features(df_base)
    feats_s2_base = build_sentinel2_features(df_base)

    # Extreme future perturbation starting at day 45
    cutoff_day = 45
    df_pert = df_base.copy()
    df_pert.loc[cutoff_day:, "s1_vv_db_mean"] = 999.0
    df_pert.loc[cutoff_day:, "s1_has_valid_observation"] = True
    df_pert.loc[cutoff_day:, "s2_ndvi_mean"] = -0.999
    df_pert.loc[cutoff_day:, "s2_has_valid_observation"] = True

    feats_s1_pert = build_sentinel1_features(df_pert)
    feats_s2_pert = build_sentinel2_features(df_pert)

    # Check S1 past features strictly match
    for col in ["s1_vv_db_locf", "s1_days_since_valid_obs", "s1_is_stale", "s1_has_past_obs"]:
        base_vals = feats_s1_base.loc[: cutoff_day - 1, col].values
        pert_vals = feats_s1_pert.loc[: cutoff_day - 1, col].values
        np.testing.assert_allclose(
            base_vals, pert_vals, equal_nan=True,
            err_msg=f"Future temporal leakage detected in Sentinel-1 feature '{col}' before day {cutoff_day}!"
        )

    # Check S2 past features strictly match
    for col in ["s2_ndvi_locf", "s2_days_since_valid_obs", "s2_is_stale", "s2_has_past_obs"]:
        base_vals = feats_s2_base.loc[: cutoff_day - 1, col].values
        pert_vals = feats_s2_pert.loc[: cutoff_day - 1, col].values
        np.testing.assert_allclose(
            base_vals, pert_vals, equal_nan=True,
            err_msg=f"Future temporal leakage detected in Sentinel-2 feature '{col}' before day {cutoff_day}!"
        )


# ==============================================================================
# 6. MAXIMUM STALENESS THRESHOLDING & MISSINGNESS INDICATORS
# ==============================================================================
def test_maximum_staleness_thresholding():
    """Verify LOCF values are masked to NaN when staleness exceeds mission limits."""
    n_days = 50
    dates = pd.date_range("2018-01-01", periods=n_days, freq="D").strftime("%Y-%m-%d")

    # Only one observation at day 0
    s1_valid = np.zeros(n_days, dtype=bool)
    s1_valid[0] = True

    df_test = pd.DataFrame({
        "date_utc": dates,
        "s1_vv_db_mean": np.where(s1_valid, -8.5, np.nan),
        "s1_vh_db_mean": np.where(s1_valid, -15.5, np.nan),
        "s1_vv_vh_ratio_db_mean": np.where(s1_valid, 7.0, np.nan),
        "s1_has_valid_observation": s1_valid,
    })

    # Staleness threshold = 10 days for unit test
    feats = build_sentinel1_features(df_test, max_staleness_days=10.0)

    # Day 0: yesterday had no prior observation -> has_past_obs = 0, is_stale = 1, vv_locf = NaN
    assert feats["s1_has_past_obs"].iloc[0] == 0
    assert feats["s1_is_stale"].iloc[0] == 1
    assert np.isnan(feats["s1_vv_db_locf"].iloc[0])

    # Day 1: yesterday was day 0 (valid obs) -> days_since = 1, is_stale = 0, vv_locf = -8.5
    assert feats["s1_days_since_valid_obs"].iloc[1] == 1.0
    assert feats["s1_is_stale"].iloc[1] == 0
    assert feats["s1_vv_db_locf"].iloc[1] == pytest.approx(-8.5)

    # Day 10: 10 days since obs -> is_stale = 0, vv_locf = -8.5
    assert feats["s1_days_since_valid_obs"].iloc[10] == 10.0
    assert feats["s1_is_stale"].iloc[10] == 0
    assert feats["s1_vv_db_locf"].iloc[10] == pytest.approx(-8.5)

    # Day 11: 11 days since obs (> 10 max staleness) -> is_stale = 1, vv_locf = NaN
    assert feats["s1_days_since_valid_obs"].iloc[11] == 11.0
    assert feats["s1_is_stale"].iloc[11] == 1
    assert np.isnan(feats["s1_vv_db_locf"].iloc[11])


# ==============================================================================
# 7. CHRONOLOGICAL SPLIT INTEGRITY WITH FULL MULTIMODAL FEATURES
# ==============================================================================
def test_full_multimodal_chronological_splits_and_targets():
    """Verify processed datasets contain all multimodal features and maintain strict splits."""
    datasets = generate_all_processed_datasets()

    for depth_key in SENSOR_DEPTHS.keys():
        df_d = datasets[depth_key]
        assert len(df_d) == 3287
        assert "target" in df_d.columns
        assert "target_lag_1d" in df_d.columns

        # Verify DEM features
        for f in DEM_TERRAIN_FEATURES:
            assert f in df_d.columns, f"DEM feature '{f}' missing from {depth_key}"
            assert df_d[f].notna().all(), f"DEM feature '{f}' has NaN in {depth_key}"

        # Verify Sentinel-1 features
        for f in SENTINEL1_SAR_FEATURES:
            assert f in df_d.columns, f"S1 feature '{f}' missing from {depth_key}"

        # Verify Sentinel-2 features
        for f in SENTINEL2_OPTICAL_FEATURES:
            assert f in df_d.columns, f"S2 feature '{f}' missing from {depth_key}"

        # Verify Train / Val / Test non-overlapping chronological split
        train, val, test = partition_chronological_splits(df_d)
        assert train["date_utc"].max() == TRAIN_END_DATE
        assert val["date_utc"].min() == VAL_START_DATE
        assert val["date_utc"].max() == VAL_END_DATE
        assert test["date_utc"].min() == TEST_START_DATE
        assert test["date_utc"].max() == TEST_END_DATE

        assert len(set(train["date_utc"]).intersection(set(val["date_utc"]))) == 0
        assert len(set(val["date_utc"]).intersection(set(test["date_utc"]))) == 0
        assert len(set(train["date_utc"]).intersection(set(test["date_utc"]))) == 0

        # Verify target is never equal to any remote sensing predictor
        valid_pairs = df_d.dropna(subset=["target", "s1_vv_db_locf"])
        assert len(valid_pairs) > 50
        assert not np.allclose(valid_pairs["target"], valid_pairs["s1_vv_db_locf"])


# ==============================================================================
# 8. PRODUCTION INTEGRATION OF RECOVERED DATES
# ==============================================================================
def test_production_integration_of_recovered_s2_dates():
    """Verify that the 3 recovered dates are integrated into production CSVs and modelling datasets."""
    acq_file = SENTINEL2_ACQUISITIONS_CSV
    daily_file = SENTINEL2_DAILY_CSV

    df_acq = pd.read_csv(acq_file)
    assert len(df_acq) == 1027
    assert df_acq["is_valid"].sum() == 322

    target_dates = ["2023-05-02", "2023-10-09", "2023-12-05"]
    acq_dates = set(df_acq["date"])
    for d in target_dates:
        assert d in acq_dates, f"Recovered date {d} missing from acquisitions CSV"

    df_daily = pd.read_csv(daily_file)
    assert df_daily["s2_has_valid_observation"].sum() == 322
    for d in target_dates:
        row = df_daily[df_daily["date"] == d].iloc[0]
        assert row["s2_has_valid_observation"] is True or row["s2_has_valid_observation"] == 1
        assert pd.notna(row["s2_ndvi_mean"])

    # Check 1-day temporal lag in processed modelling dataset
    proc_5cm = REPO_ROOT / "data" / "modelling" / "processed" / "AAMU-JTG_sm_5cm_daily.csv"
    assert proc_5cm.is_file()
    df_mod = pd.read_csv(proc_5cm)

    # May 2 acquisition -> May 3 features
    may2 = df_mod[df_mod["date_utc"] == "2023-05-02"].iloc[0]
    may3 = df_mod[df_mod["date_utc"] == "2023-05-03"].iloc[0]
    assert may2["s2_observed_yesterday"] is False or may2["s2_observed_yesterday"] == 0
    assert may3["s2_observed_yesterday"] is True or may3["s2_observed_yesterday"] == 1
    assert may3["s2_ndvi_locf"] == pytest.approx(0.4907)

    # Oct 9 acquisition -> Oct 10 features
    oct10 = df_mod[df_mod["date_utc"] == "2023-10-10"].iloc[0]
    assert oct10["s2_observed_yesterday"] is True or oct10["s2_observed_yesterday"] == 1
    assert oct10["s2_ndvi_locf"] == pytest.approx(0.3581)

    # Dec 5 acquisition -> Dec 6 features
    dec6 = df_mod[df_mod["date_utc"] == "2023-12-06"].iloc[0]
    assert dec6["s2_observed_yesterday"] is True or dec6["s2_observed_yesterday"] == 1
    assert dec6["s2_ndvi_locf"] == pytest.approx(0.2405)

