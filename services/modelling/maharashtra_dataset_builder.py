"""
SoilDepth-AI — Maharashtra Regional Dataset Builder
Author: Senior Data Engineer & Geospatial ML Pipeline Architect, SoilDepth-AI
Purpose: Ingests, aligns, and partitions multi-modal environmental predictors
         (ERA5-Land weather, Sentinel-1 SAR, Sentinel-2 Optical, SMAP L3, SoilGrids, DEM)
         with verified in-situ soil moisture observations across Maharashtra stations.
         Enforces strict scientific protocols:
         1. Excludes ERA5 deep soil moisture (swvl2-4) and SMAP L4 modelled data.
         2. Excludes target lags from ungauged predictor sets.
         3. Enforces chronological splits (Train <=2021, Val 2022, Test 2023).
         4. Requires >= 180 daily observations per sensor depth for model training.
         5. Refuses synthetic or unverified observations with structured reports.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from services.data_acquisition.maharashtra.ground_truth_adapter import (
    MaharashtraGroundTruthAdapter,
    GroundTruthValidationError,
    NORMALIZED_COLUMNS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_VERIFIED_GT_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "ground_truth" / "verified"
DEFAULT_PROCESSED_ENV_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "COSMOS" / "processed"
DEFAULT_INTERIM_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "modelling" / "interim"
DEFAULT_STATION_REGISTRY = REPO_ROOT / "dataset" / "Maharashtra" / "metadata" / "station_registry.csv"

# Prohibited leakage and ungauged features
PROHIBITED_LEAKAGE_FEATURES = {
    "swvl2", "swvl3", "swvl4",
    "era5_swvl2", "era5_swvl3", "era5_swvl4",
    "smap_l4", "smap_rootzone", "smap_profile_vwc",
}

UNGAUGED_EXCLUDED_FEATURES = {
    "target_lag_1d", "target_lag_2d", "target_lag_3d",
    "sm_5cm_lag_1d", "sm_10cm_lag_1d", "sm_20cm_lag_1d", "sm_50cm_lag_1d",
    "soil_moisture_vwc_lag_1d", "soil_moisture_vwc_lag_2d",
}

MIN_DAILY_OBSERVATIONS_FOR_TRAINING = 180


class MaharashtraDatasetBuilder:
    """
    Standardized dataset builder for Maharashtra regional soil moisture modeling.
    """

    def __init__(
        self,
        verified_gt_dir: Optional[Path] = None,
        processed_env_dir: Optional[Path] = None,
        interim_dir: Optional[Path] = None,
        station_registry_path: Optional[Path] = None,
    ):
        self.verified_gt_dir = verified_gt_dir or DEFAULT_VERIFIED_GT_DIR
        self.processed_env_dir = processed_env_dir or DEFAULT_PROCESSED_ENV_DIR
        self.interim_dir = interim_dir or DEFAULT_INTERIM_DIR
        self.station_registry_path = station_registry_path or DEFAULT_STATION_REGISTRY
        self.adapter = MaharashtraGroundTruthAdapter(station_registry_path=self.station_registry_path)

    def check_ground_truth_status(self) -> Dict[str, Any]:
        """
        Scans verified ground-truth directory for authorized in-situ observation files.
        """
        if not self.verified_gt_dir.exists():
            return {
                "status": "GROUND_TRUTH_ABSENT",
                "verified_files_count": 0,
                "verified_files": [],
                "reason": f"Verified ground-truth directory does not exist: {self.verified_gt_dir}",
            }

        valid_exts = [".csv", ".tsv", ".xlsx", ".xls", ".json", ".parquet"]
        gt_files = [
            f for f in self.verified_gt_dir.iterdir()
            if f.is_file() and f.suffix.lower() in valid_exts and not f.name.startswith(".")
        ]

        if not gt_files:
            return {
                "status": "GROUND_TRUTH_ABSENT",
                "verified_files_count": 0,
                "verified_files": [],
                "reason": "Zero verified in-situ ground truth observation files available.",
            }

        return {
            "status": "GROUND_TRUTH_AVAILABLE",
            "verified_files_count": len(gt_files),
            "verified_files": [str(f) for f in gt_files],
            "reason": f"Found {len(gt_files)} verified ground-truth files ready for alignment.",
        }

    def _resolve_station_dir(self, station_id: str) -> Optional[Path]:
        """
        Resolves station processed directory matching station_id or aliases.
        """
        candidates = [
            self.processed_env_dir / station_id,
            self.processed_env_dir / station_id.replace("-COSMOS", ""),
            self.processed_env_dir / f"{station_id}-COSMOS",
        ]
        for c in candidates:
            if c.exists() and (c / "daily_environmental_features.csv").exists():
                return c
        return None

    def load_environmental_features(self, station_id: str) -> pd.DataFrame:
        """
        Loads daily and static environmental features for a given station.
        Standardizes date column to 'date_utc'.
        """
        station_dir = self._resolve_station_dir(station_id)
        if not station_dir:
            raise FileNotFoundError(
                f"Processed environmental features not found for station '{station_id}' "
                f"in {self.processed_env_dir}"
            )

        daily_file = station_dir / "daily_environmental_features.csv"
        df_daily = pd.read_csv(daily_file)

        # Standardize date column
        if "date" in df_daily.columns:
            df_daily["date_utc"] = pd.to_datetime(df_daily["date"]).dt.strftime("%Y-%m-%d")
        elif "date_utc" in df_daily.columns:
            df_daily["date_utc"] = pd.to_datetime(df_daily["date_utc"]).dt.strftime("%Y-%m-%d")
        else:
            raise ValueError(f"No date column found in {daily_file}")

        # Load static features if available
        static_file = station_dir / "static_environmental_features.csv"
        if static_file.exists():
            df_static = pd.read_csv(static_file)
            static_cols = [
                c for c in df_static.columns
                if c not in ["station_id", "latitude", "longitude", "raster_crs", "crs", "source_product", "elevation_discrepancy_explanation"]
                and c not in df_daily.columns
            ]
            if static_cols and len(df_static) > 0:
                static_row = df_static[static_cols].iloc[0]
                static_df = pd.DataFrame([static_row] * len(df_daily), index=df_daily.index)
                df_daily = pd.concat([df_daily, static_df], axis=1)

        return df_daily

    def load_and_aggregate_ground_truth(
        self,
        gt_df_or_path: Union[pd.DataFrame, Path, str],
        station_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Loads, validates, and aggregates ground truth to daily mean observations per (station_id, depth).
        """
        if isinstance(gt_df_or_path, (str, Path)):
            p = Path(gt_df_or_path)
            if not p.exists():
                raise FileNotFoundError(f"Ground truth file not found: {p}")
            ext = p.suffix.lower()
            if ext == ".parquet":
                df_raw = pd.read_parquet(p)
            elif ext == ".json":
                try:
                    df_raw = pd.read_json(p)
                except ValueError:
                    df_raw = pd.read_json(p, lines=True)
            elif ext in [".csv", ".txt"]:
                df_raw = pd.read_csv(p)
            elif ext == ".tsv":
                df_raw = pd.read_csv(p, sep="\t")
            else:
                df_raw = pd.read_excel(p)
        else:
            df_raw = gt_df_or_path.copy()

        # Validate columns
        req_cols = ["station_id", "timestamp", "sensor_depth_cm", "soil_moisture_vwc"]
        for c in req_cols:
            if c not in df_raw.columns:
                raise GroundTruthValidationError(f"Missing required ground-truth column '{c}'")

        # Filter station if specified
        if station_id:
            df_raw = df_raw[df_raw["station_id"] == station_id].copy()

        # Quality flag filter
        if "quality_flag" in df_raw.columns:
            # Strictly reject synthetic flags
            synthetic_mask = df_raw["quality_flag"].astype(str).str.upper().isin(["SYNTHETIC", "INTERPOLATED"])
            if synthetic_mask.any():
                raise GroundTruthValidationError(
                    "Synthetic ground-truth observations detected. Training on synthetic observations is strictly prohibited."
                )
            df_raw = df_raw[df_raw["quality_flag"] == "GOOD"].copy()

        # Physical range validation
        df_raw = df_raw[
            (df_raw["soil_moisture_vwc"] >= 0.0) &
            (df_raw["soil_moisture_vwc"] <= 0.65) &
            df_raw["soil_moisture_vwc"].notna()
        ].copy()

        # Aggregation to daily UTC
        df_raw["date_utc"] = pd.to_datetime(df_raw["timestamp"], utc=True).dt.strftime("%Y-%m-%d")

        daily_agg = df_raw.groupby(["station_id", "sensor_depth_cm", "date_utc"]).agg(
            soil_moisture_vwc=("soil_moisture_vwc", "mean"),
            obs_count=("soil_moisture_vwc", "count"),
        ).reset_index()

        daily_agg["soil_moisture_vwc"] = daily_agg["soil_moisture_vwc"].round(5)
        return daily_agg

    def get_feature_candidates(self, df: pd.DataFrame, ungauged_mode: bool = True) -> List[str]:
        """
        Extracts valid predictor feature candidates, strictly excluding data-leakage and ungauged features.
        """
        exclude_non_features = {
            "date", "date_utc", "station_id", "latitude", "longitude",
            "elevation_diff_benchmark_m", "is_benchmark_consistent", "is_complete",
            "s1_raw_observation_available", "s2_raw_observation_available",
            "smap_raw_observation_available", "s1_observation_source_date",
            "s2_observation_source_date", "smap_observation_source_date",
            "era5_hourly_count", "obs_count", "soil_moisture_vwc",
            "raster_crs", "crs", "source_product", "elevation_discrepancy_explanation",
            "slope_method", "dem_pixel_type",
        }

        features = []
        for col in df.columns:
            if col in exclude_non_features:
                continue
            if col in PROHIBITED_LEAKAGE_FEATURES:
                continue
            if ungauged_mode and col in UNGAUGED_EXCLUDED_FEATURES:
                continue
            # Must be numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                features.append(col)

        return sorted(features)

    def build_depth_dataset(
        self,
        station_id: str,
        depth_cm: float,
        gt_daily_df: Optional[pd.DataFrame] = None,
        ungauged_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Aligns daily environmental predictors with daily ground-truth observations for a given station and depth.
        Partitions chronologically into train (<=2021), val (2022), test (2023).
        """
        # 1. Check ground-truth availability
        if gt_daily_df is None or gt_daily_df.empty:
            return {
                "status": "BLOCKED_AWAITING_IN_SITU_GROUND_TRUTH",
                "station_id": station_id,
                "depth_cm": depth_cm,
                "trainable": False,
                "daily_observations_count": 0,
                "reason": f"No verified in-situ ground truth observations available for {station_id} at {depth_cm} cm.",
            }

        # Filter for this station and depth
        sub_gt = gt_daily_df[
            (gt_daily_df["station_id"] == station_id) &
            (np.isclose(gt_daily_df["sensor_depth_cm"], depth_cm, atol=1.0))
        ].copy()

        daily_obs_count = len(sub_gt)
        if daily_obs_count < MIN_DAILY_OBSERVATIONS_FOR_TRAINING:
            return {
                "status": "INSUFFICIENT_OBSERVATIONS",
                "station_id": station_id,
                "depth_cm": depth_cm,
                "trainable": False,
                "daily_observations_count": daily_obs_count,
                "required_minimum": MIN_DAILY_OBSERVATIONS_FOR_TRAINING,
                "reason": (
                    f"Insufficient observations ({daily_obs_count} days available, "
                    f"minimum {MIN_DAILY_OBSERVATIONS_FOR_TRAINING} required for depth model training)."
                ),
            }

        # 2. Load environmental features
        df_env = self.load_environmental_features(station_id)

        # 3. Inner join on date_utc
        df_merged = pd.merge(df_env, sub_gt[["date_utc", "soil_moisture_vwc"]], on="date_utc", how="inner")
        if len(df_merged) < MIN_DAILY_OBSERVATIONS_FOR_TRAINING:
            return {
                "status": "INSUFFICIENT_ALIGNED_OBSERVATIONS",
                "station_id": station_id,
                "depth_cm": depth_cm,
                "trainable": False,
                "daily_observations_count": len(df_merged),
                "required_minimum": MIN_DAILY_OBSERVATIONS_FOR_TRAINING,
                "reason": f"Only {len(df_merged)} ground-truth observations aligned with 2017-2023 environmental timeline.",
            }

        # 4. Feature candidate selection & safety checks
        feature_names = self.get_feature_candidates(df_merged, ungauged_mode=ungauged_mode)

        # 5. Chronological partition
        train_mask = df_merged["date_utc"] <= "2021-12-31"
        val_mask = (df_merged["date_utc"] >= "2022-01-01") & (df_merged["date_utc"] <= "2022-12-31")
        test_mask = df_merged["date_utc"] >= "2023-01-01"

        df_train = df_merged[train_mask].copy()
        df_val = df_merged[val_mask].copy()
        df_test = df_merged[test_mask].copy()

        return {
            "status": "DATASET_READY_FOR_TRAINING",
            "station_id": station_id,
            "depth_cm": depth_cm,
            "trainable": True,
            "total_samples": len(df_merged),
            "train_samples": len(df_train),
            "val_samples": len(df_val),
            "test_samples": len(df_test),
            "feature_names": feature_names,
            "feature_count": len(feature_names),
            "X_train": df_train[feature_names],
            "y_train": df_train["soil_moisture_vwc"],
            "X_val": df_val[feature_names],
            "y_val": df_val["soil_moisture_vwc"],
            "X_test": df_test[feature_names],
            "y_test": df_test["soil_moisture_vwc"],
            "date_train": df_train["date_utc"],
            "date_val": df_val["date_utc"],
            "date_test": df_test["date_utc"],
        }
