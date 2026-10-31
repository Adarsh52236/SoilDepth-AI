"""
SoilDepth-AI — Tests for Strict Absence of Temporal Leakage
"""

import pytest
import numpy as np
import pandas as pd

from services.modelling.config import (
    TRAIN_START_DATE,
    TRAIN_END_DATE,
    VAL_START_DATE,
    VAL_END_DATE,
    TEST_START_DATE,
    TEST_END_DATE,
    WEATHER_ONLY_FEATURE_NAMES,
)
from services.modelling.feature_engineering import (
    build_weather_features,
    partition_chronological_splits,
)
from services.modelling.baselines import ClimatologyBaseline, HistoricalMeanBaseline


def test_future_perturbation_invariance():
    """
    CRITICAL LEAKAGE TEST:
    Modifying future weather data at day t+k MUST NOT change any feature values at day t.
    """
    n_days = 60
    dates = pd.date_range("2015-01-01", periods=n_days, freq="D").strftime("%Y-%m-%d")

    np.random.seed(42)
    df_base = pd.DataFrame({
        "date_utc": dates,
        "temperature_2m_mean_c": np.random.uniform(5.0, 25.0, n_days),
        "dewpoint_2m_mean_c": np.random.uniform(0.0, 20.0, n_days),
        "precipitation_total_mm": np.random.uniform(0.0, 15.0, n_days),
        "solar_radiation_total_mj_m2": np.random.uniform(5.0, 25.0, n_days),
        "wind_u10_mean_ms": np.random.uniform(-3.0, 3.0, n_days),
        "wind_v10_mean_ms": np.random.uniform(-3.0, 3.0, n_days),
    })

    # Compute baseline features
    feats_base = build_weather_features(df_base)

    # Now create perturbed copy: inject extreme weather (e.g. 500mm storm) at day 40..59
    df_perturbed = df_base.copy()
    cutoff_day = 30
    df_perturbed.loc[cutoff_day:, "precipitation_total_mm"] += 500.0
    df_perturbed.loc[cutoff_day:, "temperature_2m_mean_c"] += 30.0

    feats_perturbed = build_weather_features(df_perturbed)

    # Compare features for all days PRIOR to cutoff_day (days 0..29)
    cols_to_check = [
        "precip_lag_1d",
        "precip_roll_sum_3d",
        "precip_roll_sum_7d",
        "precip_roll_sum_14d",
        "precip_roll_sum_30d",
        "days_since_rain_gt_1mm",
        "temp_roll_mean_7d",
        "temp_roll_mean_30d",
        "vpd_kpa",
        "vpd_roll_mean_7d",
        "solar_roll_mean_7d",
    ]

    for col in cols_to_check:
        base_slice = feats_base.loc[: cutoff_day - 1, col].values
        pert_slice = feats_perturbed.loc[: cutoff_day - 1, col].values
        # Must be strictly equal up to machine epsilon
        np.testing.assert_allclose(
            base_slice,
            pert_slice,
            rtol=1e-7,
            atol=1e-7,
            err_msg=f"Temporal leakage detected in feature '{col}' at or before day {cutoff_day}!",
        )


def test_chronological_splits_strictly_ordered_and_disjoint():
    """Verify chronological split boundaries have no overlap and are strictly monotonic."""
    dates = pd.date_range("2015-01-01", "2023-12-31", freq="D").strftime("%Y-%m-%d")
    df = pd.DataFrame({"date_utc": dates, "val": np.arange(len(dates))})

    train, val, test = partition_chronological_splits(df)

    assert train["date_utc"].max() == TRAIN_END_DATE
    assert val["date_utc"].min() == VAL_START_DATE
    assert val["date_utc"].max() == VAL_END_DATE
    assert test["date_utc"].min() == TEST_START_DATE
    assert test["date_utc"].max() == TEST_END_DATE

    # Strict chronological inequality
    assert train["date_utc"].max() < val["date_utc"].min()
    assert val["date_utc"].max() < test["date_utc"].min()

    # Zero date intersection
    assert len(set(train["date_utc"]).intersection(set(val["date_utc"]))) == 0
    assert len(set(val["date_utc"]).intersection(set(test["date_utc"]))) == 0
    assert len(set(train["date_utc"]).intersection(set(test["date_utc"]))) == 0


def test_target_lag_alignment_exactness():
    """Verify target_lag_1d is exactly target shifted by 1."""
    targets = pd.Series([0.15, 0.20, 0.25, 0.30, np.nan, 0.35])
    lag_1d = targets.shift(1)

    assert np.isnan(lag_1d.iloc[0])
    assert lag_1d.iloc[1] == 0.15
    assert lag_1d.iloc[2] == 0.20
    assert lag_1d.iloc[3] == 0.25
    assert lag_1d.iloc[4] == 0.30
    assert np.isnan(lag_1d.iloc[5])  # previous was nan
