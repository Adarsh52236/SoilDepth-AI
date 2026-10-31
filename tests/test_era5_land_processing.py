"""
SoilDepth-AI — Test Suite for ERA5-Land Processing & Validation (Station AAMU-JTG)
Author: Senior Data Engineer, SoilDepth-AI
Tests:
  - Raw NetCDF integrity & coordinate alignment
  - Timestamp continuity & zero gaps
  - Temperature & dewpoint unit conversion (°C) & thermodynamic bounds
  - Hourly precipitation accumulation semantics & clipping
  - Solar radiation flux conversion (W/m² & MJ/m²) & diurnal bounds
  - Daily aggregation completeness (3,287 days, exactly 24h per day)
"""

import pytest
import pandas as pd
import numpy as np
import xarray as xr
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "dataset" / "ERA5_LAND" / "raw" / "AAMU-JTG" / "hourly"
PROCESSED_DIR = REPO_ROOT / "dataset" / "ERA5_LAND" / "processed" / "AAMU-JTG"
HOURLY_CSV = PROCESSED_DIR / "ERA5Land_AAMU-JTG_2015-2023_hourly.csv"
DAILY_CSV = PROCESSED_DIR / "ERA5Land_AAMU-JTG_2015-2023_daily.csv"

EXPECTED_HOURLY_ROWS = 78888
EXPECTED_DAILY_ROWS = 3287


def test_raw_files_exist_and_readable():
    """Verify all 4 raw NetCDF files are present and readable."""
    nc_files = list(RAW_DIR.glob("*.nc"))
    assert len(nc_files) == 4, f"Expected 4 NetCDF files, found {len(nc_files)}"

    for f in nc_files:
        ds = xr.open_dataset(f)
        assert "valid_time" in ds.coords or "time" in ds.coords
        assert "latitude" in ds.coords and "longitude" in ds.coords
        assert len(ds["valid_time"]) == EXPECTED_HOURLY_ROWS
        ds.close()


def test_hourly_csv_structure_and_counts():
    """Verify processed hourly CSV format, row count, and column names."""
    assert HOURLY_CSV.exists(), f"Hourly processed CSV not found at {HOURLY_CSV}"
    df = pd.read_csv(HOURLY_CSV)

    assert len(df) == EXPECTED_HOURLY_ROWS, f"Expected {EXPECTED_HOURLY_ROWS} rows, got {len(df)}"

    expected_cols = [
        "timestamp_utc", "station_id", "latitude_station", "longitude_station",
        "latitude_era5_grid", "longitude_era5_grid", "temperature_2m_c",
        "dewpoint_2m_c", "precipitation_mm", "solar_radiation",
        "wind_u10_ms", "wind_v10_ms"
    ]
    assert list(df.columns) == expected_cols, f"Column mismatch: {list(df.columns)}"

    # Zero missing values across entire table
    assert df.isna().sum().sum() == 0, f"Found missing values: {df.isna().sum()}"


def test_hourly_timestamps_alignment_and_continuity():
    """Verify exact 2015-2023 time span, 1-hour uniform frequency, and zero duplicates."""
    df = pd.read_csv(HOURLY_CSV)
    dt_series = pd.to_datetime(df["timestamp_utc"])

    assert dt_series.iloc[0] == pd.Timestamp("2015-01-01 00:00:00")
    assert dt_series.iloc[-1] == pd.Timestamp("2023-12-31 23:00:00")

    # Zero duplicates
    assert dt_series.duplicated().sum() == 0

    # Exactly 1-hour step between all consecutive records
    diffs = dt_series.diff().dropna()
    irregular = (diffs != pd.Timedelta(hours=1)).sum()
    assert irregular == 0, f"Found {irregular} irregular time intervals."


def test_thermodynamic_and_physical_bounds():
    """Verify temperature, dewpoint, wind, and non-negativity bounds."""
    df = pd.read_csv(HOURLY_CSV)

    # Temperature in sensible climatic range for Alabama
    assert -20.0 <= df["temperature_2m_c"].min() <= 0.0
    assert 30.0 <= df["temperature_2m_c"].max() <= 45.0

    # Thermodynamic law: dewpoint temperature must never exceed air temperature!
    # Allow tiny numerical precision tolerance of 0.05 C
    diff_dp = df["dewpoint_2m_c"] - df["temperature_2m_c"]
    violations = (diff_dp > 0.05).sum()
    assert violations == 0, f"Found {violations} hours where dewpoint exceeded air temperature!"

    # Precipitation non-negativity
    assert df["precipitation_mm"].min() >= 0.0
    assert df["precipitation_mm"].max() < 100.0  # Alabama max hourly precipitation < 100 mm

    # Solar radiation non-negativity & upper bound
    assert df["solar_radiation"].min() >= 0.0
    assert df["solar_radiation"].max() <= 1361.0  # Cannot exceed solar constant (W/m²)

    # Wind components
    assert -30.0 <= df["wind_u10_ms"].min() <= df["wind_u10_ms"].max() <= 30.0
    assert -30.0 <= df["wind_v10_ms"].min() <= df["wind_v10_ms"].max() <= 30.0


def test_precipitation_and_solar_accumulation_semantics():
    """Verify hourly accumulation behavior (hourly peaks, decreases, night zeros)."""
    df = pd.read_csv(HOURLY_CSV)
    df["dt"] = pd.to_datetime(df["timestamp_utc"])

    # Hourly precipitation decreases during storm decay (confirms incremental 1h sum, not cumulative run)
    storm_day = df[(df["dt"] >= "2015-01-04") & (df["dt"] < "2015-01-05")]["precipitation_mm"].values
    decreases = (np.diff(storm_day) < 0).sum()
    assert decreases > 0, "Precipitation failed to decrease during rain event; possible cumulative bug!"

    # Night solar radiation in Alabama (e.g. 03:00 to 07:00 UTC) must be zero
    night_hours = df[df["dt"].dt.hour.isin([3, 4, 5, 6])]
    assert night_hours["solar_radiation"].max() == 0.0, "Found non-zero solar radiation during dead night!"


def test_daily_aggregated_completeness_and_metrics():
    """Verify daily aggregation: exactly 3,287 days, all 24h complete, min <= mean <= max."""
    assert DAILY_CSV.exists(), f"Daily processed CSV not found at {DAILY_CSV}"
    df_daily = pd.read_csv(DAILY_CSV)

    assert len(df_daily) == EXPECTED_DAILY_ROWS, f"Expected {EXPECTED_DAILY_ROWS} days, got {len(df_daily)}"
    assert (df_daily["hourly_obs_count"] == 24).all(), "Found days with != 24 hours"
    assert (df_daily["is_complete"] == True).all(), "Found incomplete days marked True"

    # Verify min <= mean <= max for daily temperature
    valid_range = (df_daily["temperature_2m_min_c"] <= df_daily["temperature_2m_mean_c"]) & \
                  (df_daily["temperature_2m_mean_c"] <= df_daily["temperature_2m_max_c"])
    assert valid_range.all(), "Found daily temperature violations where min > mean or mean > max"

    # Verify precipitation sum matches sum of hourly
    df_hourly = pd.read_csv(HOURLY_CSV)
    hourly_total_precip = df_hourly["precipitation_mm"].sum()
    daily_total_precip = df_daily["precipitation_total_mm"].sum()
    assert np.isclose(hourly_total_precip, daily_total_precip, atol=1e-2), \
        f"Hourly total precip {hourly_total_precip} does not match daily sum {daily_total_precip}"
