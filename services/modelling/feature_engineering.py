"""
SoilDepth-AI — Feature Engineering Pipeline
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Derive scientifically sound, temporal-leakage-free meteorological,
         seasonal, edaphic, and autoregressive lag features for SoilDepth-AI.
         All rolling and lag statistics strictly use past observations (shift >= 1).
"""

import math
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd

from services.modelling.config import (
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    SOILGRIDS_STATIC_CSV,
    DEM_STATIC_CSV,
    STATION_ID,
    SENSOR_DEPTHS,
    TRAIN_START_DATE,
    TRAIN_END_DATE,
    VAL_START_DATE,
    VAL_END_DATE,
    TEST_START_DATE,
    TEST_END_DATE,
    BASE_WEATHER_FEATURES,
    WEATHER_MEMORY_FEATURES,
    CYCLICAL_FEATURES,
    EDAPHIC_FEATURES,
    SOILGRIDS_EDAPHIC_FEATURES,
    DEM_TERRAIN_FEATURES,
    SMAP_TIME_SERIES_FEATURES,
    SENTINEL1_SAR_FEATURES,
    SENTINEL2_OPTICAL_FEATURES,
    WEATHER_ONLY_FEATURE_NAMES,
    LAG_AUGMENTED_FEATURE_NAMES,
    MULTIMODAL_FEATURE_NAMES,
    FULL_MULTIMODAL_FEATURE_NAMES,
    S1_MAX_STALENESS_DAYS,
    S2_MAX_STALENESS_DAYS,
    SMAP_MAX_STALENESS_DAYS,
)


def compute_vapor_pressure_deficit(temp_c: pd.Series, dewpoint_c: pd.Series) -> pd.Series:
    """
    Computes Vapor Pressure Deficit (VPD in kPa) using the Tetens formula.
    Saturation vapor pressure:
        e_s(T) = 0.61078 * exp((17.27 * T) / (T + 237.3))  [kPa]
    Actual vapor pressure:
        e_a(Td) = 0.61078 * exp((17.27 * Td) / (Td + 237.3)) [kPa]
    VPD = max(0.0, e_s - e_a)
    """
    es = 0.61078 * np.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea = 0.61078 * np.exp((17.27 * dewpoint_c) / (dewpoint_c + 237.3))
    vpd = np.maximum(0.0, es - ea)
    return pd.Series(vpd, index=temp_c.index, name="vpd_kpa")


def compute_horizontal_wind_speed(u10: pd.Series, v10: pd.Series) -> pd.Series:
    """Computes 10m horizontal wind speed in m/s from u and v components."""
    ws = np.sqrt(u10**2 + v10**2)
    return pd.Series(ws, index=u10.index, name="wind_speed_10m_ms")


def compute_days_since_rain(precip_mm: pd.Series, threshold: float = 1.0, max_cap: float = 60.0) -> pd.Series:
    """
    Computes days elapsed since last rainfall event exceeding threshold (mm).
    Strictly past-only: checks past_precip = precip_mm.shift(1).
    If it rained yesterday (day t-1), day t has days_since_rain = 1.0.
    """
    past_rain = precip_mm.shift(1).values
    n = len(past_rain)
    days_since = np.full(n, np.nan)
    last_rain_day = -9999

    for i in range(n):
        val = past_rain[i]
        # val corresponds to rain on day i-1
        if not np.isnan(val) and val >= threshold:
            last_rain_day = i - 1
        if last_rain_day >= 0:
            days_since[i] = float(min(i - last_rain_day, max_cap))
        else:
            # Prior to first observed rainfall event, cap monotonically up to max_cap
            days_since[i] = float(min(i + 1, max_cap))

    return pd.Series(days_since, index=precip_mm.index, name="days_since_rain_gt_1mm")


def compute_cyclical_doy(date_series: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """
    Computes sine and cosine transforms for Day-of-Year to preserve calendar continuity.
    """
    dt = pd.to_datetime(date_series)
    doy = dt.dt.dayofyear
    angles = 2.0 * np.pi * doy / 365.25
    sin_doy = pd.Series(np.sin(angles), index=date_series.index, name="doy_sin")
    cos_doy = pd.Series(np.cos(angles), index=date_series.index, name="doy_cos")
    return sin_doy, cos_doy


def compute_days_since_valid_smap(has_valid_series: pd.Series, max_cap: float = 60.0) -> pd.Series:
    """
    Computes days elapsed since last valid SMAP observation.
    Strictly past-only: checks past_valid = has_valid_series.shift(1).
    """
    past_valid = has_valid_series.shift(1).values
    n = len(past_valid)
    days_since = np.full(n, np.nan)
    last_valid_day = -9999

    for i in range(n):
        val = past_valid[i]
        if val is True or val == 1 or (not pd.isna(val) and val != 0 and val != False):
            last_valid_day = i - 1
        if last_valid_day >= 0:
            days_since[i] = float(min(i - last_valid_day, max_cap))
        else:
            days_since[i] = float(min(i + 1, max_cap))

    return pd.Series(days_since, index=has_valid_series.index, name="smap_days_since_valid_retrieval")


def build_smap_features(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs leakage-safe past-only time-series features from SMAP daily observations.
    All rolling windows and lags strictly use shift(1).
    """
    df = df_daily.copy()

    if "smap_sm_daily_mean_m3_m3" in df.columns:
        smap_past = df["smap_sm_daily_mean_m3_m3"].shift(1)
        df["smap_sm_lag_1d"] = smap_past
        df["smap_sm_roll_mean_3d"] = smap_past.rolling(window=3, min_periods=1).mean()
        df["smap_sm_roll_mean_7d"] = smap_past.rolling(window=7, min_periods=1).mean()

    if "smap_has_valid_retrieval" in df.columns:
        df["smap_days_since_valid_retrieval"] = compute_days_since_valid_smap(
            df["smap_has_valid_retrieval"]
        )

    return df


def compute_days_since_valid_observation(has_valid_series: pd.Series, max_cap: float = 60.0) -> pd.Series:
    """
    Computes days elapsed since last valid observation.
    Strictly past-only: checks past_valid = has_valid_series.shift(1).
    Day t sees whether a valid observation was recorded on day t-1 or earlier.
    """
    past_valid = has_valid_series.shift(1).values
    n = len(past_valid)
    days_since = np.full(n, np.nan)
    last_valid_day = -9999

    for i in range(n):
        val = past_valid[i]
        if val is True or val == 1 or (not pd.isna(val) and val != 0 and val != False):
            last_valid_day = i - 1
        if last_valid_day >= 0:
            days_since[i] = float(min(i - last_valid_day, max_cap))
        else:
            days_since[i] = float(min(i + 1, max_cap))

    return pd.Series(days_since, index=has_valid_series.index)


def build_sentinel1_features(
    df_daily: pd.DataFrame,
    max_staleness_days: float = S1_MAX_STALENESS_DAYS,
) -> pd.DataFrame:
    """
    Constructs leakage-safe past-only time-series features from Sentinel-1 SAR observations.
    All features strictly use shift(1) prior to any forward-filling or rolling statistics,
    ensuring no observation occurring on or after prediction day t enters the feature set.
    Observations older than max_staleness_days are masked with explicit missingness indicators.
    """
    df = df_daily.copy()

    if "s1_has_valid_observation" in df.columns:
        valid_series = df["s1_has_valid_observation"].astype(bool)
        shift_s1 = valid_series.shift(1)
        df["s1_observed_yesterday"] = (shift_s1 == True)

        max_cap = max_staleness_days * 2.0
        days_since = compute_days_since_valid_observation(valid_series, max_cap=max_cap)
        df["s1_days_since_valid_obs"] = days_since

        cum_valid = (shift_s1 == True).cumsum()
        has_past = (cum_valid > 0).astype(int)
        df["s1_has_past_obs"] = has_past

        is_stale = ((days_since > max_staleness_days) | (has_past == 0)).astype(int)
        df["s1_is_stale"] = is_stale

        # Past-only Last Observation Carried Forward (LOCF)
        if "s1_vv_db_mean" in df.columns:
            vv_locf = df["s1_vv_db_mean"].shift(1).ffill()
            df["s1_vv_db_locf"] = np.where(is_stale == 0, vv_locf, np.nan)
            df["s1_vv_db_lag_1d"] = df["s1_vv_db_mean"].shift(1)

        if "s1_vh_db_mean" in df.columns:
            vh_locf = df["s1_vh_db_mean"].shift(1).ffill()
            df["s1_vh_db_locf"] = np.where(is_stale == 0, vh_locf, np.nan)

        if "s1_vv_vh_ratio_db_mean" in df.columns:
            ratio_locf = df["s1_vv_vh_ratio_db_mean"].shift(1).ffill()
            df["s1_vv_vh_ratio_db_locf"] = np.where(is_stale == 0, ratio_locf, np.nan)

    return df


def build_sentinel2_features(
    df_daily: pd.DataFrame,
    max_staleness_days: float = S2_MAX_STALENESS_DAYS,
    exclude_scl_7: bool = False,
) -> pd.DataFrame:
    """
    Constructs leakage-safe past-only time-series features from Sentinel-2 optical observations.
    All features strictly use shift(1) prior to any forward-filling or rolling statistics.
    Supports optional conservative exclusion of SCL class 7 (unclassified).
    Observations older than max_staleness_days are masked with explicit missingness indicators.
    """
    df = df_daily.copy()

    if "s2_has_valid_observation" in df.columns:
        valid_series = df["s2_has_valid_observation"].astype(bool).copy()
        clean_ndvi = df["s2_ndvi_mean"].copy() if "s2_ndvi_mean" in df.columns else pd.Series(np.nan, index=df.index)
        clean_evi = df["s2_evi_mean"].copy() if "s2_evi_mean" in df.columns else pd.Series(np.nan, index=df.index)
        clean_b04 = df["s2_b04_red_mean"].copy() if "s2_b04_red_mean" in df.columns else pd.Series(np.nan, index=df.index)
        clean_b08 = df["s2_b08_nir_mean"].copy() if "s2_b08_nir_mean" in df.columns else pd.Series(np.nan, index=df.index)
        clean_b11 = df["s2_b11_swir1_mean"].copy() if "s2_b11_swir1_mean" in df.columns else pd.Series(np.nan, index=df.index)
        clean_b12 = df["s2_b12_swir2_mean"].copy() if "s2_b12_swir2_mean" in df.columns else pd.Series(np.nan, index=df.index)

        if exclude_scl_7 and "s2_scl_code" in df.columns:
            scl_7_mask = df["s2_scl_code"] == 7
            valid_series.loc[scl_7_mask] = False
            clean_ndvi.loc[scl_7_mask] = np.nan
            clean_evi.loc[scl_7_mask] = np.nan
            clean_b04.loc[scl_7_mask] = np.nan
            clean_b08.loc[scl_7_mask] = np.nan
            clean_b11.loc[scl_7_mask] = np.nan
            clean_b12.loc[scl_7_mask] = np.nan

        shift_s2 = valid_series.shift(1)
        df["s2_observed_yesterday"] = (shift_s2 == True)

        max_cap = max_staleness_days * 2.0
        days_since = compute_days_since_valid_observation(valid_series, max_cap=max_cap)
        df["s2_days_since_valid_obs"] = days_since

        cum_valid = (shift_s2 == True).cumsum()
        has_past = (cum_valid > 0).astype(int)
        df["s2_has_past_obs"] = has_past

        is_stale = ((days_since > max_staleness_days) | (has_past == 0)).astype(int)
        df["s2_is_stale"] = is_stale

        # Past-only LOCF
        df["s2_ndvi_locf"] = np.where(is_stale == 0, clean_ndvi.shift(1).ffill(), np.nan)
        df["s2_evi_locf"] = np.where(is_stale == 0, clean_evi.shift(1).ffill(), np.nan)
        df["s2_b04_red_locf"] = np.where(is_stale == 0, clean_b04.shift(1).ffill(), np.nan)
        df["s2_b08_nir_locf"] = np.where(is_stale == 0, clean_b08.shift(1).ffill(), np.nan)
        df["s2_b11_swir1_locf"] = np.where(is_stale == 0, clean_b11.shift(1).ffill(), np.nan)
        df["s2_b12_swir2_locf"] = np.where(is_stale == 0, clean_b12.shift(1).ffill(), np.nan)
        df["s2_ndvi_lag_1d"] = clean_ndvi.shift(1)

    return df


def build_weather_features(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs all weather, memory, and seasonal features from aligned daily weather.
    Ensures that any rolling sum or average uses shift(1) so that no future or concurrent
    unclosed time windows leak information.
    """
    df = df_daily.copy()

    # Atmospheric diagnostic variables
    df["vpd_kpa"] = compute_vapor_pressure_deficit(
        df["temperature_2m_mean_c"],
        df["dewpoint_2m_mean_c"]
    )
    df["wind_speed_10m_ms"] = compute_horizontal_wind_speed(
        df["wind_u10_mean_ms"],
        df["wind_v10_mean_ms"]
    )

    # Shifted past-only precipitation lags and rolling windows
    # shift(1) means day t sees [t-1, t-2, ...], strictly prior to day t
    precip_past = df["precipitation_total_mm"].shift(1)
    df["precip_lag_1d"] = precip_past

    # Rolling past precipitation sums (past 3, 7, 14, 30 days prior to day t)
    df["precip_roll_sum_3d"] = precip_past.rolling(window=3, min_periods=1).sum()
    df["precip_roll_sum_7d"] = precip_past.rolling(window=7, min_periods=1).sum()
    df["precip_roll_sum_14d"] = precip_past.rolling(window=14, min_periods=1).sum()
    df["precip_roll_sum_30d"] = precip_past.rolling(window=30, min_periods=1).sum()

    # Days since rain >= 1.0mm
    df["days_since_rain_gt_1mm"] = compute_days_since_rain(df["precipitation_total_mm"], threshold=1.0)

    # Shifted past-only thermal & radiation memory
    temp_past = df["temperature_2m_mean_c"].shift(1)
    df["temp_roll_mean_7d"] = temp_past.rolling(window=7, min_periods=1).mean()
    df["temp_roll_mean_30d"] = temp_past.rolling(window=30, min_periods=1).mean()

    vpd_past = df["vpd_kpa"].shift(1)
    df["vpd_roll_mean_7d"] = vpd_past.rolling(window=7, min_periods=1).mean()

    solar_past = df["solar_radiation_total_mj_m2"].shift(1)
    df["solar_roll_mean_7d"] = solar_past.rolling(window=7, min_periods=1).mean()

    # Cyclical day of year
    sin_doy, cos_doy = compute_cyclical_doy(df["date_utc"])
    df["doy_sin"] = sin_doy
    df["doy_cos"] = cos_doy

    return df


def prepare_depth_modeling_dataset(
    df_features: pd.DataFrame,
    depth_key: str,
    static_props: Dict[str, Dict[str, float]],
    soilgrids_props: Optional[Dict[str, Dict[str, float]]] = None,
    dem_props: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Creates a modeling-ready dataset specifically for one target depth.
    Appends depth-specific static soil properties (HWSD and SoilGrids),
    DEM terrain attributes, and target lag-1.
    """
    depth_cfg = SENSOR_DEPTHS[depth_key]
    df_depth = df_features.copy()

    # 1a. Attach static HWSD properties for the sensor layer
    layer_props = static_props.get(depth_cfg.hwsd_depth_layer, {})
    for prop_col in EDAPHIC_FEATURES:
        df_depth[prop_col] = layer_props.get(prop_col, np.nan)

    # 1b. Attach static SoilGrids properties for the sensor layer
    if soilgrids_props and hasattr(depth_cfg, "soilgrids_layer_tag"):
        layer_sg = soilgrids_props.get(depth_cfg.soilgrids_layer_tag, {})
        for prop_col in SOILGRIDS_EDAPHIC_FEATURES:
            df_depth[prop_col] = layer_sg.get(prop_col, np.nan)

    # 1c. Attach static USGS DEM terrain properties
    if dem_props:
        for prop_col in DEM_TERRAIN_FEATURES:
            df_depth[prop_col] = dem_props.get(prop_col, np.nan)

    # 2. Target columns
    target_col = f"target_{depth_key}"
    df_depth["target"] = df_depth[target_col]

    # 3. Create target lag-1 (strictly past observation y_{t-1})
    df_depth["target_lag_1d"] = df_depth["target"].shift(1)

    df_depth["depth_key"] = depth_key
    df_depth["depth_m"] = depth_cfg.depth_m
    df_depth["nominal_depth_cm"] = depth_cfg.nominal_depth_cm

    return df_depth


def partition_chronological_splits(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Partitions a DataFrame into chronological Train, Validation, and Test splits.
    Strictly verifies non-overlapping date boundaries.
    """
    train_mask = (df["date_utc"] >= TRAIN_START_DATE) & (df["date_utc"] <= TRAIN_END_DATE)
    val_mask = (df["date_utc"] >= VAL_START_DATE) & (df["date_utc"] <= VAL_END_DATE)
    test_mask = (df["date_utc"] >= TEST_START_DATE) & (df["date_utc"] <= TEST_END_DATE)

    df_train = df[train_mask].copy()
    df_val = df[val_mask].copy()
    df_test = df[test_mask].copy()

    # Sanity checks
    if len(df_train) == 0:
        raise ValueError(f"Train split is empty for range {TRAIN_START_DATE} to {TRAIN_END_DATE}")
    if len(df_val) == 0:
        raise ValueError(f"Validation split is empty for range {VAL_START_DATE} to {VAL_END_DATE}")
    if len(df_test) == 0:
        raise ValueError(f"Test split is empty for range {TEST_START_DATE} to {TEST_END_DATE}")

    # Verify chronological order and no date overlaps
    train_dates = set(df_train["date_utc"])
    val_dates = set(df_val["date_utc"])
    test_dates = set(df_test["date_utc"])

    if train_dates.intersection(val_dates):
        raise ValueError("Train and Validation dates overlap!")
    if val_dates.intersection(test_dates):
        raise ValueError("Validation and Test dates overlap!")
    if train_dates.intersection(test_dates):
        raise ValueError("Train and Test dates overlap!")

    return df_train, df_val, df_test


def generate_all_processed_datasets(
    interim_csv_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Loads interim aligned data, computes all features, and produces model-ready datasets
    for each depth in data/modelling/processed/.
    """
    if interim_csv_path is None:
        interim_csv_path = INTERIM_DATA_DIR / f"{STATION_ID}_aligned_raw.csv"

    if output_dir is None:
        output_dir = PROCESSED_DATA_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_csv(interim_csv_path)

    # Ingest static variables (HWSD, SoilGrids, and DEM)
    from services.modelling.dataset_builder import (
        parse_static_soil_properties,
        parse_soilgrids_static_properties,
        parse_dem_static_features,
    )
    from services.modelling.config import SCAN_EXTRACTED_DIR, DEM_STATIC_CSV

    static_file = (
        SCAN_EXTRACTED_DIR
        / "surface_0-10cm"
        / "SCAN"
        / STATION_ID
        / f"SCAN_SCAN_{STATION_ID}_static_variables.csv"
    )
    static_props = parse_static_soil_properties(static_file)

    soilgrids_props = {}
    if SOILGRIDS_STATIC_CSV.exists():
        soilgrids_props = parse_soilgrids_static_properties(SOILGRIDS_STATIC_CSV)

    dem_props = {}
    if DEM_STATIC_CSV.exists():
        dem_props = parse_dem_static_features(DEM_STATIC_CSV)

    # Compute shared weather and cyclical features
    df_features = build_weather_features(df_raw)

    # Compute SMAP features if present
    df_features = build_smap_features(df_features)

    # Compute Sentinel-1 SAR features if present
    df_features = build_sentinel1_features(df_features)

    # Compute Sentinel-2 optical features if present
    df_features = build_sentinel2_features(df_features)

    processed_dfs = {}

    for depth_key in SENSOR_DEPTHS.keys():
        df_depth = prepare_depth_modeling_dataset(
            df_features, depth_key, static_props, soilgrids_props, dem_props
        )
        out_file = output_dir / f"{STATION_ID}_{depth_key}_daily.csv"
        df_depth.to_csv(out_file, index=False)
        processed_dfs[depth_key] = df_depth

    # Attach static DEM properties to master combined table as well
    if dem_props:
        for prop_col in DEM_TERRAIN_FEATURES:
            df_features[prop_col] = dem_props.get(prop_col, np.nan)

    # Also save comprehensive combined table
    master_out_file = output_dir / f"{STATION_ID}_all_depths_features_daily.csv"
    df_features.to_csv(master_out_file, index=False)

    return processed_dfs


if __name__ == "__main__":
    datasets = generate_all_processed_datasets()
    print("=" * 80)
    print(f"Feature engineering complete for {len(datasets)} depth datasets.")
    for k, df_d in datasets.items():
        print(f"  [{k}] Total rows: {len(df_d)}, Valid targets: {df_d['target'].notna().sum()}, Columns: {len(df_d.columns)}")
    print("=" * 80)
