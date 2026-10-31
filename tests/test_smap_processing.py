"""
SoilDepth-AI — Tests for SMAP L3 Preprocessing and Quality Verification
"""

import json
import hashlib
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from dataset.SMAP.scripts.process_smap import (
    RAW_SMAP_CSV,
    PROCESSED_SMAP_DIR,
    AUDIT_SMAP_DIR,
    EXPECTED_STATION_ID,
    EXPECTED_LATITUDE,
    EXPECTED_LONGITUDE,
    EXPECTED_RAW_ROWS,
    RAW_DATE_MIN,
    RAW_DATE_MAX,
    STUDY_TIMELINE_START,
    STUDY_TIMELINE_END,
    EXPECTED_CALENDAR_DAYS,
    FILL_VALUE,
    VALID_RETRIEVAL_FLAG,
    validate_smap_raw_schema,
    process_smap_daily_features,
    compute_file_sha256,
)


def test_smap_raw_file_immutability():
    """Verify raw SMAP CSV exists and its SHA-256 hash matches authoritative record."""
    assert RAW_SMAP_CSV.exists(), f"Raw SMAP CSV not found at {RAW_SMAP_CSV}"
    assert RAW_SMAP_CSV.stat().st_size == 1451447

    sha256 = compute_file_sha256(RAW_SMAP_CSV)
    assert sha256 == "90170af47eba10a840712b6af5bbb4740bd944cc7491d1e97f05368120f08e13"


def test_smap_raw_schema_and_coordinates():
    """Verify raw CSV schema, row count, coordinates, and date bounds."""
    df_raw = pd.read_csv(RAW_SMAP_CSV)
    info = validate_smap_raw_schema(df_raw)

    assert info["station_id"] == EXPECTED_STATION_ID
    assert info["latitude"] == pytest.approx(EXPECTED_LATITUDE, abs=1e-4)
    assert info["longitude"] == pytest.approx(EXPECTED_LONGITUDE, abs=1e-4)
    assert info["row_count"] == EXPECTED_RAW_ROWS
    assert info["min_date"] == RAW_DATE_MIN
    assert info["max_date"] == RAW_DATE_MAX
    assert info["duplicate_dates"] == 0


def test_smap_fill_value_conversion():
    """Verify fill value -9999.0 is completely converted to NaN in processed outputs."""
    proc_csv = PROCESSED_SMAP_DIR / "smap_daily_features.csv"
    assert proc_csv.exists(), f"Processed SMAP CSV missing at {proc_csv}"
    df = pd.read_csv(proc_csv)

    for col in ["smap_sm_daily_mean_m3_m3", "smap_sm_am_m3_m3", "smap_sm_pm_m3_m3"]:
        valid_vals = df[col].dropna()
        assert (valid_vals != FILL_VALUE).all(), f"Found fill value {FILL_VALUE} in {col}!"
        assert (valid_vals >= 0.0).all(), f"Found negative VWC in {col}!"
        assert (valid_vals <= 0.60).all(), f"Found physically impossible VWC > 0.60 in {col}!"


def test_smap_quality_flag_interpretation():
    """
    Verify flag interpretation:
    - Flag 9.0 (attempted AND successful) -> valid.
    - Flag 13.0 (attempted but NOT successful; constant 0.42768) -> invalid (rejected).
    - Flags 7.0 & 15.0 (skipped, not successful) -> invalid (rejected).
    """
    proc_csv = PROCESSED_SMAP_DIR / "smap_daily_features.csv"
    df = pd.read_csv(proc_csv)

    # All valid AM records must have qual_flag == 9.0
    valid_am = df[df["smap_is_valid_am"] == True]
    assert (valid_am["smap_qual_flag_am"] == VALID_RETRIEVAL_FLAG).all()
    assert len(valid_am) == 1461

    # All valid PM records must have qual_flag == 9.0
    valid_pm = df[df["smap_is_valid_pm"] == True]
    assert (valid_pm["smap_qual_flag_pm"] == VALID_RETRIEVAL_FLAG).all()
    assert len(valid_pm) == 1175

    # Rows with flag 13.0 must have smap_is_valid == False and smap_sm == NaN
    flag_13_am = df[df["smap_qual_flag_am"] == 13.0]
    assert len(flag_13_am) == 40
    assert (flag_13_am["smap_is_valid_am"] == False).all()
    assert flag_13_am["smap_sm_am_m3_m3"].isna().all()

    flag_13_pm = df[df["smap_qual_flag_pm"] == 13.0]
    assert len(flag_13_pm) == 27
    assert (flag_13_pm["smap_is_valid_pm"] == False).all()
    assert flag_13_pm["smap_sm_pm_m3_m3"].isna().all()


def test_smap_date_continuity_and_missingness():
    """Verify exact 3,287 days, 89 pre-mission, 83 granule gaps, and 0 duplicates."""
    proc_csv = PROCESSED_SMAP_DIR / "smap_daily_features.csv"
    df = pd.read_csv(proc_csv)

    assert len(df) == EXPECTED_CALENDAR_DAYS

    dates = pd.to_datetime(df["date_utc"])
    assert dates.iloc[0] == pd.Timestamp(STUDY_TIMELINE_START)
    assert dates.iloc[-1] == pd.Timestamp(STUDY_TIMELINE_END)
    assert dates.is_monotonic_increasing
    assert dates.duplicated().sum() == 0

    diffs = dates.diff().dropna()
    assert (diffs == pd.Timedelta(days=1)).all()

    # Pre-mission days count
    pre_mission = df[df["smap_retrieval_status"] == "PRE_MISSION"]
    assert len(pre_mission) == 89
    assert (pre_mission["smap_has_valid_retrieval"] == False).all()
    assert pre_mission["smap_sm_daily_mean_m3_m3"].isna().all()

    # Granule gap days count
    granule_gaps = df[df["smap_retrieval_status"] == "NO_GRANULE"]
    assert len(granule_gaps) == 83
    assert (granule_gaps["smap_has_valid_retrieval"] == False).all()
    assert granule_gaps["smap_sm_daily_mean_m3_m3"].isna().all()


def test_smap_daily_mean_derivation_rules():
    """Verify exact mathematical averaging of AM and PM passes."""
    proc_csv = PROCESSED_SMAP_DIR / "smap_daily_features.csv"
    df = pd.read_csv(proc_csv)

    # 1. When passes_count == 2: mean of AM and PM
    both_valid = df[df["smap_valid_passes_count"] == 2]
    assert len(both_valid) == 770
    expected_means = (both_valid["smap_sm_am_m3_m3"] + both_valid["smap_sm_pm_m3_m3"]) / 2.0
    np.testing.assert_allclose(both_valid["smap_sm_daily_mean_m3_m3"].values, expected_means.values, rtol=1e-5)

    # 2. When passes_count == 1 (AM only): matches AM
    am_only = df[df["smap_retrieval_status"] == "VALID_AM_ONLY"]
    assert len(am_only) == 691
    np.testing.assert_allclose(am_only["smap_sm_daily_mean_m3_m3"].values, am_only["smap_sm_am_m3_m3"].values, rtol=1e-5)

    # 3. When passes_count == 1 (PM only): matches PM
    pm_only = df[df["smap_retrieval_status"] == "VALID_PM_ONLY"]
    assert len(pm_only) == 405
    np.testing.assert_allclose(pm_only["smap_sm_daily_mean_m3_m3"].values, pm_only["smap_sm_pm_m3_m3"].values, rtol=1e-5)

    # 4. Total valid days
    assert len(both_valid) + len(am_only) + len(pm_only) == 1866


def test_smap_quality_report_json():
    """Verify machine-readable quality report JSON exists and reflects verified counts."""
    report_json = AUDIT_SMAP_DIR / "smap_quality_report.json"
    assert report_json.exists(), f"Audit report missing at {report_json}"

    with open(report_json, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert audit["station_id"] == EXPECTED_STATION_ID
    assert audit["study_period"]["total_calendar_days"] == EXPECTED_CALENDAR_DAYS
    assert audit["raw_data_coverage"]["pre_mission_days"] == 89
    assert audit["raw_data_coverage"]["no_granule_gap_days"] == 83
    assert audit["retrieval_counts"]["valid_am_retrievals"] == 1461
    assert audit["retrieval_counts"]["valid_pm_retrievals"] == 1175
    assert audit["retrieval_counts"]["days_with_at_least_one_valid"] == 1866

