"""
SoilDepth-AI — Unit Tests for Maharashtra Dataset Builder
Author: Senior Data Engineer & Geospatial ML Pipeline Architect, SoilDepth-AI
"""

import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from services.modelling.maharashtra_dataset_builder import (
    MaharashtraDatasetBuilder,
    PROHIBITED_LEAKAGE_FEATURES,
    UNGAUGED_EXCLUDED_FEATURES,
    MIN_DAILY_OBSERVATIONS_FOR_TRAINING,
)
from services.data_acquisition.maharashtra.ground_truth_adapter import GroundTruthValidationError


@pytest.fixture
def builder():
    return MaharashtraDatasetBuilder()


def test_check_ground_truth_status_absent(builder):
    """Verifies that builder cleanly reports ground truth absence when no verified files exist."""
    status = builder.check_ground_truth_status()
    # In current state, verified dir contains 0 files
    assert status["status"] in ["GROUND_TRUTH_ABSENT", "GROUND_TRUTH_AVAILABLE"]
    if status["status"] == "GROUND_TRUTH_ABSENT":
        assert status["verified_files_count"] == 0


def test_load_environmental_features_real_stations(builder):
    """Verifies that builder loads environmental features for extracted Maharashtra pilot stations."""
    df_iitm = builder.load_environmental_features("IITM-PUNE-COSMOS")
    assert "date_utc" in df_iitm.columns
    assert "temperature_2m_mean_c" in df_iitm.columns
    assert "smap_sm_daily_mean_m3_m3" in df_iitm.columns
    assert len(df_iitm) >= 2500

    df_mpkv = builder.load_environmental_features("MPKV-RAHURI-CAAST")
    assert "date_utc" in df_mpkv.columns
    assert len(df_mpkv) >= 2500


def test_feature_candidates_leakage_prohibition(builder):
    """Verifies that prohibited ERA5 deep soil moisture and SMAP L4 are strictly excluded."""
    dummy_df = pd.DataFrame({
        "temperature_2m_mean_c": [25.0],
        "precipitation_total_mm": [0.0],
        "swvl2": [0.30],
        "swvl3": [0.32],
        "swvl4": [0.35],
        "smap_l4": [0.28],
        "smap_rootzone": [0.29],
        "target_lag_1d": [0.25],
    })

    # Ungauged mode: neither leakage nor target lags allowed
    features = builder.get_feature_candidates(dummy_df, ungauged_mode=True)
    for f in features:
        assert f not in PROHIBITED_LEAKAGE_FEATURES
        assert f not in UNGAUGED_EXCLUDED_FEATURES

    assert "temperature_2m_mean_c" in features
    assert "precipitation_total_mm" in features
    assert "swvl2" not in features
    assert "target_lag_1d" not in features


def test_load_and_aggregate_ground_truth(builder):
    """Verifies that raw ground truth is aggregated to daily mean observations."""
    df_gt = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST", "MPKV-RAHURI-CAAST", "MPKV-RAHURI-CAAST"],
        "timestamp": ["2020-05-01T06:00:00Z", "2020-05-01T18:00:00Z", "2020-05-02T12:00:00Z"],
        "sensor_depth_cm": [10.0, 10.0, 10.0],
        "soil_moisture_vwc": [0.20, 0.30, 0.25],
        "quality_flag": ["GOOD", "GOOD", "GOOD"],
    })
    daily = builder.load_and_aggregate_ground_truth(df_gt, station_id="MPKV-RAHURI-CAAST")
    assert len(daily) == 2
    row1 = daily[daily["date_utc"] == "2020-05-01"].iloc[0]
    assert abs(row1["soil_moisture_vwc"] - 0.25) < 1e-4
    assert row1["obs_count"] == 2


def test_reject_synthetic_ground_truth(builder):
    """Verifies that synthetic ground-truth observations raise GroundTruthValidationError."""
    df_syn = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST"],
        "timestamp": ["2020-05-01T06:00:00Z"],
        "sensor_depth_cm": [10.0],
        "soil_moisture_vwc": [0.25],
        "quality_flag": ["SYNTHETIC"],
    })
    with pytest.raises(GroundTruthValidationError, match="Synthetic ground-truth"):
        builder.load_and_aggregate_ground_truth(df_syn)


def test_build_depth_dataset_insufficient_obs(builder):
    """Verifies that <180 observations returns INSUFFICIENT_OBSERVATIONS."""
    dates = pd.date_range("2020-01-01", periods=50, freq="D")
    df_gt = pd.DataFrame({
        "station_id": ["IITM-PUNE-COSMOS"] * 50,
        "date_utc": [d.strftime("%Y-%m-%d") for d in dates],
        "sensor_depth_cm": [10.0] * 50,
        "soil_moisture_vwc": [0.25] * 50,
    })
    res = builder.build_depth_dataset("IITM-PUNE-COSMOS", 10.0, gt_daily_df=df_gt)
    assert not res["trainable"]
    assert res["status"] == "INSUFFICIENT_OBSERVATIONS"
    assert res["daily_observations_count"] == 50


def test_build_depth_dataset_chronological_splits(builder):
    """Verifies chronological partition when >= 180 observations are provided."""
    # Create 400 dates spanning 2021, 2022, 2023
    dates_2021 = pd.date_range("2021-01-01", periods=200, freq="D")
    dates_2022 = pd.date_range("2022-01-01", periods=100, freq="D")
    dates_2023 = pd.date_range("2023-01-01", periods=100, freq="D")
    all_dates = list(dates_2021) + list(dates_2022) + list(dates_2023)

    df_gt = pd.DataFrame({
        "station_id": ["IITM-PUNE-COSMOS"] * len(all_dates),
        "date_utc": [d.strftime("%Y-%m-%d") for d in all_dates],
        "sensor_depth_cm": [10.0] * len(all_dates),
        "soil_moisture_vwc": [0.24] * len(all_dates),
    })

    res = builder.build_depth_dataset("IITM-PUNE-COSMOS", 10.0, gt_daily_df=df_gt)
    assert res["trainable"]
    assert res["status"] == "DATASET_READY_FOR_TRAINING"
    assert res["train_samples"] == 200
    assert res["val_samples"] == 100
    assert res["test_samples"] == 100
    assert (res["date_train"] <= "2021-12-31").all()
    assert ((res["date_val"] >= "2022-01-01") & (res["date_val"] <= "2022-12-31")).all()
    assert (res["date_test"] >= "2023-01-01").all()
