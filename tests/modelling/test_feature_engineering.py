"""
SoilDepth-AI — Tests for Feature Engineering Pipeline
"""

import pytest
import numpy as np
import pandas as pd

from services.modelling.feature_engineering import (
    compute_vapor_pressure_deficit,
    compute_horizontal_wind_speed,
    compute_days_since_rain,
    compute_cyclical_doy,
    build_weather_features,
)


def test_vapor_pressure_deficit():
    """Verify VPD calculation matches psychrometric formulation."""
    # When temp == dewpoint (100% relative humidity), VPD must be 0.0
    t = pd.Series([20.0, 0.0, 30.0])
    td = pd.Series([20.0, 0.0, 30.0])
    vpd = compute_vapor_pressure_deficit(t, td)
    assert np.allclose(vpd, 0.0, atol=1e-5)

    # When temp > dewpoint, VPD must be positive
    t = pd.Series([25.0])
    td = pd.Series([15.0])
    vpd = compute_vapor_pressure_deficit(t, td)
    assert vpd.iloc[0] > 0.0

    # Ensure no negative VPD values
    t = pd.Series([10.0])
    td = pd.Series([15.0])  # unphysical td > t
    vpd = compute_vapor_pressure_deficit(t, td)
    assert vpd.iloc[0] == 0.0


def test_horizontal_wind_speed():
    """Verify horizontal wind speed calculation."""
    u = pd.Series([3.0, 0.0, -4.0])
    v = pd.Series([4.0, 5.0, 3.0])
    ws = compute_horizontal_wind_speed(u, v)
    assert np.allclose(ws, [5.0, 5.0, 5.0])


def test_cyclical_doy():
    """Verify DOY sine/cosine coordinates satisfy sin² + cos² == 1.0."""
    dates = pd.date_range("2020-01-01", "2020-12-31", freq="D").strftime("%Y-%m-%d")
    sin_doy, cos_doy = compute_cyclical_doy(pd.Series(dates))

    assert len(sin_doy) == 366
    unit_norm = sin_doy**2 + cos_doy**2
    assert np.allclose(unit_norm, 1.0, atol=1e-5)


def test_days_since_rain():
    """Verify days_since_rain is past-only and increments/resets accurately."""
    # Day 0: rain = 0 mm
    # Day 1: rain = 5 mm (exceeds 1.0)
    # Day 2: rain = 0 mm
    # Day 3: rain = 0 mm
    # Day 4: rain = 10 mm
    precip = pd.Series([0.0, 5.0, 0.0, 0.0, 10.0])
    days_since = compute_days_since_rain(precip, threshold=1.0)

    # Day 1 sees shift(1) = 0.0 -> no rain seen yet
    # Day 2 sees shift(1) = 5.0 on day 1 -> 1 day since rain
    assert days_since.iloc[2] == 1.0
    # Day 3 sees shift(1) = 0.0 on day 2 -> 2 days since rain
    assert days_since.iloc[3] == 2.0
    # Day 4 sees shift(1) = 0.0 on day 3 -> 3 days since rain
    assert days_since.iloc[4] == 3.0


def test_rolling_weather_features_use_past_shift():
    """Verify rolling precipitation windows exclude current day t."""
    df_mini = pd.DataFrame({
        "date_utc": ["2015-01-01", "2015-01-02", "2015-01-03", "2015-01-04"],
        "temperature_2m_mean_c": [10.0, 12.0, 14.0, 16.0],
        "dewpoint_2m_mean_c": [5.0, 6.0, 7.0, 8.0],
        "precipitation_total_mm": [0.0, 10.0, 20.0, 30.0],
        "solar_radiation_total_mj_m2": [10.0, 12.0, 14.0, 16.0],
        "wind_u10_mean_ms": [1.0, 1.0, 1.0, 1.0],
        "wind_v10_mean_ms": [1.0, 1.0, 1.0, 1.0],
    })

    df_feats = build_weather_features(df_mini)

    # On day 2 ("2015-01-03"), current rain is 20.0.
    # But precip_lag_1d must be 10.0 (day 1), NOT 20.0.
    assert df_feats.loc[2, "precip_lag_1d"] == 10.0

    # On day 3 ("2015-01-04"), current rain is 30.0.
    # precip_roll_sum_3d must be sum of days [0, 1, 2] = 0 + 10 + 20 = 30.0 (excludes day 3's 30.0)
    assert df_feats.loc[3, "precip_roll_sum_3d"] == 30.0
