"""
SoilDepth-AI — Modelling Configuration
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Centralized configuration containing paths, station coordinates, sensor depth mappings,
         chronological train/validation/test split definitions, feature specifications,
         and model training hyperparameters for baseline pipelines.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


# ==============================================================================
# 1. PATH CONFIGURATION
# ==============================================================================
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ERA5_DAILY_CSV = REPO_ROOT / "dataset" / "ERA5_LAND" / "processed" / "AAMU-JTG" / "ERA5Land_AAMU-JTG_2015-2023_daily.csv"
ERA5_HOURLY_CSV = REPO_ROOT / "dataset" / "ERA5_LAND" / "processed" / "AAMU-JTG" / "ERA5Land_AAMU-JTG_2015-2023_hourly.csv"
SCAN_EXTRACTED_DIR = REPO_ROOT / "dataset" / "ISMN" / "SCAN" / "extracted"
SMAP_DAILY_CSV = REPO_ROOT / "dataset" / "SMAP" / "processed" / "AAMU-JTG" / "smap_daily_features.csv"
SOILGRIDS_STATIC_CSV = REPO_ROOT / "dataset" / "SoilGrids" / "processed" / "AAMU-JTG" / "soilgrids_AAMU-JTG_features.csv"
DEM_STATIC_CSV = REPO_ROOT / "dataset" / "DEM" / "processed" / "AAMU-JTG" / "dem_AAMU-JTG_features.csv"
SENTINEL1_DAILY_CSV = REPO_ROOT / "dataset" / "Sentinel-1" / "processed" / "AAMU-JTG" / "sentinel1_daily_features.csv"
SENTINEL1_ACQUISITIONS_CSV = REPO_ROOT / "dataset" / "Sentinel-1" / "processed" / "AAMU-JTG" / "sentinel1_acquisitions.csv"
SENTINEL2_DAILY_CSV = REPO_ROOT / "dataset" / "Sentinel-2" / "processed" / "AAMU-JTG" / "sentinel2_daily_features.csv"
SENTINEL2_ACQUISITIONS_CSV = REPO_ROOT / "dataset" / "Sentinel-2" / "processed" / "AAMU-JTG" / "sentinel2_acquisitions.csv"

INTERIM_DATA_DIR = REPO_ROOT / "data" / "modelling" / "interim"
PROCESSED_DATA_DIR = REPO_ROOT / "data" / "modelling" / "processed"

MODELS_DIR = REPO_ROOT / "models" / "baselines" / "AAMU-JTG"
REPORTS_DIR = REPO_ROOT / "reports" / "modelling" / "AAMU-JTG"


# ==============================================================================
# 2. STATION & COORDINATE VERIFICATION
# ==============================================================================
STATION_ID = "AAMU-JTG"
STATION_LAT = 34.78534
STATION_LON = -86.55906
STATION_ELEV_M = 241.0

ERA5_GRID_LAT = 34.80000
ERA5_GRID_LON = -86.60000
MAX_COORD_TOLERANCE_DEG = 0.001


# ==============================================================================
# 3. SENSOR DEPTH DEFINITIONS & PROVENANCE
# ==============================================================================
@dataclass(frozen=True)
class SensorDepthConfig:
    depth_key: str
    nominal_depth_cm: float
    depth_m: float
    extracted_subdir: str
    file_pattern: str
    hwsd_depth_layer: str  # '0.00-0.30' or '0.30-1.00'
    description: str
    soilgrids_layer_tag: str = ""


SENSOR_DEPTHS: Dict[str, SensorDepthConfig] = {
    "sm_5cm": SensorDepthConfig(
        depth_key="sm_5cm",
        nominal_depth_cm=5.08,
        depth_m=0.0508,
        extracted_subdir="surface_0-10cm",
        file_pattern="*sm_0.050800_0.050800*.stm",
        hwsd_depth_layer="0.00-0.30",
        description="Point-sensor proxy at ~5 cm (0.0508 m) depth; surface boundary zone",
        soilgrids_layer_tag="0_5cm",
    ),
    "sm_10cm": SensorDepthConfig(
        depth_key="sm_10cm",
        nominal_depth_cm=10.16,
        depth_m=0.1016,
        extracted_subdir="middle_10-30cm",
        file_pattern="*sm_0.101600_0.101600*.stm",
        hwsd_depth_layer="0.00-0.30",
        description="Point-sensor proxy at ~10 cm (0.1016 m) depth; upper root-zone proxy",
        soilgrids_layer_tag="5_15cm",
    ),
    "sm_20cm": SensorDepthConfig(
        depth_key="sm_20cm",
        nominal_depth_cm=20.32,
        depth_m=0.2032,
        extracted_subdir="middle_10-30cm",
        file_pattern="*sm_0.203200_0.203200*.stm",
        hwsd_depth_layer="0.00-0.30",
        description="Point-sensor proxy at ~20 cm (0.2032 m) depth; mid root-zone proxy",
        soilgrids_layer_tag="15_30cm",
    ),
    "sm_50cm": SensorDepthConfig(
        depth_key="sm_50cm",
        nominal_depth_cm=50.80,
        depth_m=0.5080,
        extracted_subdir="deep_30-60cm",
        file_pattern="*sm_0.508000_0.508000*.stm",
        hwsd_depth_layer="0.30-1.00",
        description="Point-sensor proxy at ~50 cm (0.5080 m) depth; deep root-zone proxy",
        soilgrids_layer_tag="30_60cm",
    ),
}


# ==============================================================================
# 4. DATA QUALITY & COMPLETENESS THRESHOLDS
# ==============================================================================
MIN_VALID_HOURS_PER_DAY = 18  # 75% threshold (18/24) to avoid diurnal sampling bias
ACCEPTED_QFLAGS = ("G",)       # ISMN 'G' = Good
ACCEPTED_PFLAGS = ("V", "E")  # ISMN 'V' = Validated, 'E' = Estimated (standard valid)
PHYSICAL_SM_MIN = 0.0          # m³/m³ volumetric water content
PHYSICAL_SM_MAX = 0.60         # m³/m³ max porosity threshold for mineral soils


# ==============================================================================
# 5. CHRONOLOGICAL DATA SPLITS
# ==============================================================================
TRAIN_START_DATE = "2015-01-01"
TRAIN_END_DATE = "2020-12-31"   # 6 full years (2,192 days)

VAL_START_DATE = "2021-01-01"
VAL_END_DATE = "2021-12-31"     # 1 full year (365 days)

TEST_START_DATE = "2022-01-01"
TEST_END_DATE = "2023-12-31"    # 2 full years (730 days)


# ==============================================================================
# 6. FEATURE SPECIFICATION
# ==============================================================================
BASE_WEATHER_FEATURES = [
    "temperature_2m_mean_c",
    "temperature_2m_min_c",
    "temperature_2m_max_c",
    "dewpoint_2m_mean_c",
    "vpd_kpa",
    "precipitation_total_mm",
    "solar_radiation_total_mj_m2",
    "wind_speed_10m_ms",
]

WEATHER_MEMORY_FEATURES = [
    "precip_lag_1d",
    "precip_roll_sum_3d",
    "precip_roll_sum_7d",
    "precip_roll_sum_14d",
    "precip_roll_sum_30d",
    "days_since_rain_gt_1mm",
    "temp_roll_mean_7d",
    "temp_roll_mean_30d",
    "vpd_roll_mean_7d",
    "solar_roll_mean_7d",
]

CYCLICAL_FEATURES = [
    "doy_sin",
    "doy_cos",
]

EDAPHIC_FEATURES = [
    "clay_fraction_pct",
    "sand_fraction_pct",
    "silt_fraction_pct",
    "organic_carbon_pct",
    "saturation_m3_m3",
]

# Feature Set 1: Weather + Edaphic + Seasonality (Remote Sensing / Weather-only proxy)
WEATHER_ONLY_FEATURE_NAMES = (
    BASE_WEATHER_FEATURES
    + WEATHER_MEMORY_FEATURES
    + CYCLICAL_FEATURES
    + EDAPHIC_FEATURES
)

# Feature Set 2: Lag-Augmented (includes past-only observed soil moisture lag-1)
LAG_AUGMENTED_FEATURE_NAMES = (
    WEATHER_ONLY_FEATURE_NAMES
    + ["target_lag_1d"]
)

# Feature Set 3: SoilGrids Static Properties (250m resolution, depth-matched)
SOILGRIDS_EDAPHIC_FEATURES = [
    "soilgrids_clay_pct",
    "soilgrids_sand_pct",
    "soilgrids_silt_pct",
    "soilgrids_bdod_g_cm3",
    "soilgrids_ocd_kg_m3",
    "soilgrids_wv0010_m3_m3",
    "soilgrids_wv0033_m3_m3",
    "soilgrids_wv1500_m3_m3",
]

# Maximum staleness thresholds (days) for forward-carried remote sensing observations
SMAP_MAX_STALENESS_DAYS = 14.0
S1_MAX_STALENESS_DAYS = 30.0
S2_MAX_STALENESS_DAYS = 45.0

# Feature Set 4: SMAP L3 Enhanced 9km Time-Series Features (strictly past-only)
SMAP_TIME_SERIES_FEATURES = [
    "smap_sm_daily_mean_m3_m3",
    "smap_sm_lag_1d",
    "smap_sm_roll_mean_3d",
    "smap_sm_roll_mean_7d",
    "smap_has_valid_retrieval",
    "smap_days_since_valid_retrieval",
]

# Feature Set 5: Terrain / Geomorphology Features (USGS 3DEP DEM 30m)
DEM_TERRAIN_FEATURES = [
    "dem_elevation_m",
    "dem_slope_deg",
    "dem_aspect_sin",
    "dem_aspect_cos",
]

# Feature Set 6: Sentinel-1 SAR C-Band Features (strictly past-only, LOCF, capped by staleness)
SENTINEL1_SAR_FEATURES = [
    "s1_vv_db_locf",
    "s1_vh_db_locf",
    "s1_vv_vh_ratio_db_locf",
    "s1_days_since_valid_obs",
    "s1_is_stale",
    "s1_has_past_obs",
]

# Feature Set 7: Sentinel-2 Multispectral Surface Reflectance Features (strictly past-only, LOCF)
SENTINEL2_OPTICAL_FEATURES = [
    "s2_ndvi_locf",
    "s2_evi_locf",
    "s2_b04_red_locf",
    "s2_b08_nir_locf",
    "s2_b11_swir1_locf",
    "s2_b12_swir2_locf",
    "s2_days_since_valid_obs",
    "s2_is_stale",
    "s2_has_past_obs",
]

# Feature Set 8: Base Multimodal Remote Sensing (Weather + SoilGrids + SMAP L3)
MULTIMODAL_FEATURE_NAMES = (
    WEATHER_ONLY_FEATURE_NAMES
    + SOILGRIDS_EDAPHIC_FEATURES
    + SMAP_TIME_SERIES_FEATURES
)

# Feature Set 9: Full Multimodal Earth Observation Suite (Weather + SoilGrids + DEM + SMAP + S1 + S2)
FULL_MULTIMODAL_FEATURE_NAMES = (
    WEATHER_ONLY_FEATURE_NAMES
    + SOILGRIDS_EDAPHIC_FEATURES
    + DEM_TERRAIN_FEATURES
    + SMAP_TIME_SERIES_FEATURES
    + SENTINEL1_SAR_FEATURES
    + SENTINEL2_OPTICAL_FEATURES
)


# ==============================================================================
# 7. MODEL TRAINING HYPERPARAMETERS (XGBoost)
# ==============================================================================
XGB_HYPERPARAMS = {
    "n_estimators": 400,
    "max_depth": 5,
    "learning_rate": 0.03,
    "subsample": 0.85,
    "colsample_bytree": 0.85,
    "min_child_weight": 3,
    "gamma": 0.0,
    "random_state": 42,
    "early_stopping_rounds": 35,
    "eval_metric": "rmse",
}
