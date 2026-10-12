"""Unit tests for feature engineering, time-series transformations, and splits."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from soildepth_preprocessing.config import RollingConfig, SplitConfig
from soildepth_preprocessing.transformations import (
    LearnedStandardScaler,
    generate_lag_features,
    generate_rolling_features,
    normalize_datetimes,
    split_dataset,
)


def test_normalize_datetimes() -> None:
    df = pd.DataFrame(
        {
            "timestamp_utc": [
                "2026-01-01 10:00:00",
                "2026-01-02 11:30:00",
            ]
        }
    )
    df_norm = normalize_datetimes(df, "timestamp_utc", target_tz="UTC")
    assert df_norm["timestamp_utc"].dt.tz is not None
    assert str(df_norm["timestamp_utc"].dt.tz) == "UTC"


def test_lag_features_past_only() -> None:
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S1", "S1", "S1"],
            "timestamp_utc": pd.date_range("2026-01-01", periods=4, freq="D"),
            "precipitation_mm": [10.0, 20.0, 30.0, 40.0],
        }
    )
    df_lag = generate_lag_features(
        df,
        lags_config={"precipitation_mm": [1, 2]},
        time_col="timestamp_utc",
        group_col="station_id",
    )

    assert "precipitation_mm_lag_1" in df_lag.columns
    assert "precipitation_mm_lag_2" in df_lag.columns

    # Lag 1: first row is NaN, second row is 10.0, third row is 20.0
    assert pd.isna(df_lag["precipitation_mm_lag_1"].iloc[0])
    assert df_lag["precipitation_mm_lag_1"].iloc[1] == 10.0
    assert df_lag["precipitation_mm_lag_1"].iloc[2] == 20.0

    # Lag 2: first two rows are NaN, third row is 10.0
    assert pd.isna(df_lag["precipitation_mm_lag_2"].iloc[0])
    assert pd.isna(df_lag["precipitation_mm_lag_2"].iloc[1])
    assert df_lag["precipitation_mm_lag_2"].iloc[2] == 10.0


def test_lag_features_peering_into_future_prohibited() -> None:
    df = pd.DataFrame(
        {
            "precipitation_mm": [10.0, 20.0],
        }
    )
    # Negative lag (peering into future) must raise ValueError
    with pytest.raises(ValueError, match="future-data leakage"):
        generate_lag_features(df, lags_config={"precipitation_mm": [-1]})

    # Zero lag must also raise ValueError
    with pytest.raises(ValueError, match="positive integers"):
        generate_lag_features(df, lags_config={"precipitation_mm": [0]})


def test_rolling_features_closed_left() -> None:
    df = pd.DataFrame(
        {
            "precipitation_mm": [10.0, 20.0, 30.0, 40.0],
        }
    )
    r_cfg = RollingConfig(column="precipitation_mm", window=2, agg="mean")
    df_roll = generate_rolling_features(df, [r_cfg])

    roll_col = "precipitation_mm_roll_mean_2"
    assert roll_col in df_roll.columns
    # Row 0: closed='left' means no prior data -> NaN
    assert pd.isna(df_roll[roll_col].iloc[0])
    # Row 1: only Row 0 is strictly prior -> 10.0
    assert df_roll[roll_col].iloc[1] == pytest.approx(10.0)
    # Row 2: prior 2 values (Row 0=10, Row 1=20) -> mean 15.0
    assert df_roll[roll_col].iloc[2] == pytest.approx(15.0)


def test_temporal_split() -> None:
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "soil_moisture": np.linspace(0.2, 0.4, 10),
        }
    )
    config = SplitConfig(
        method="temporal",
        train_ratio=0.7,
        val_ratio=0.2,
        test_ratio=0.1,
        temporal_column="timestamp_utc",
    )
    df_split = split_dataset(df, config)

    assert (df_split["split"] == "train").sum() == 7
    assert (df_split["split"] == "val").sum() == 2
    assert (df_split["split"] == "test").sum() == 1

    # Verify strict chronological separation: max train < min val <= max val < min test
    train_max = df_split[df_split["split"] == "train"]["timestamp_utc"].max()
    val_min = df_split[df_split["split"] == "val"]["timestamp_utc"].min()
    val_max = df_split[df_split["split"] == "val"]["timestamp_utc"].max()
    test_min = df_split[df_split["split"] == "test"]["timestamp_utc"].min()

    assert train_max < val_min
    assert val_max < test_min


def test_group_split() -> None:
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S1", "S2", "S2", "S3", "S3", "S4", "S4"],
            "soil_moisture": [0.2] * 8,
        }
    )
    config = SplitConfig(
        method="group",
        train_ratio=0.5,
        val_ratio=0.25,
        test_ratio=0.25,
        group_column="station_id",
    )
    df_split = split_dataset(df, config)

    train_stations = set(df_split[df_split["split"] == "train"]["station_id"])
    val_stations = set(df_split[df_split["split"] == "val"]["station_id"])
    test_stations = set(df_split[df_split["split"] == "test"]["station_id"])

    # Station sets must be completely disjoint (no entity leakage!)
    assert train_stations.isdisjoint(val_stations)
    assert train_stations.isdisjoint(test_stations)
    assert val_stations.isdisjoint(test_stations)


def test_learned_standard_scaler_prevents_leakage() -> None:
    train_df = pd.DataFrame({"feature": [10.0, 20.0, 30.0]})  # Mean=20, std=10
    test_df = pd.DataFrame({"feature": [100.0, 200.0]})  # Out-of-distribution test set

    scaler = LearnedStandardScaler(columns=["feature"])
    scaler.fit(train_df)

    assert scaler.means_["feature"] == pytest.approx(20.0)
    assert scaler.stds_["feature"] == pytest.approx(10.0)

    # Transform test set using strictly training statistics
    scaled_test = scaler.transform(test_df)
    # (100 - 20) / 10 = 8.0
    assert scaled_test["feature"].iloc[0] == pytest.approx(8.0)
    # (200 - 20) / 10 = 18.0
    assert scaled_test["feature"].iloc[1] == pytest.approx(18.0)
