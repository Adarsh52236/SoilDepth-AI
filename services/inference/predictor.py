"""
SoilDepth-AI — Model 1 Production Predictor Engine
Author: Senior Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Production inference service for Model 1 discrete point-sensor depth estimation.
         Loads the 4 selected ground-sensor-independent models:
           - 5.08 cm:  sm_5cm_weather_only_xgb.json   (25 features)
           - 10.16 cm: sm_10cm_weather_only_xgb.json  (25 features)
           - 20.32 cm: sm_20cm_full_multimodal_xgb.json (58 features)
           - 50.80 cm: sm_50cm_weather_only_xgb.json  (25 features)
         Enforces strict zero-leakage, input validation, physical bounds checks,
         and outputs standardized Pydantic/JSON responses.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb

from services.modelling.config import (
    REPO_ROOT,
    MODELS_DIR,
    STATION_ID,
    STATION_LAT,
    STATION_LON,
    STATION_ELEV_M,
    SENSOR_DEPTHS,
    WEATHER_ONLY_FEATURE_NAMES,
    FULL_MULTIMODAL_FEATURE_NAMES,
    PHYSICAL_SM_MIN,
    PHYSICAL_SM_MAX,
)
from services.inference.schemas import (
    DepthPrediction,
    ValidationInfo,
    Model1PredictionResponse,
    Model1BatchPredictionResponse,
    ModelDetail,
    ModelCatalogResponse,
)


# ==============================================================================
# SELECTED OPERATIONAL GROUND-SENSOR-INDEPENDENT MODELS
# ==============================================================================
SELECTED_MODELS_CONFIG: Dict[str, Dict[str, Any]] = {
    "sm_5cm": {
        "nominal_depth_cm": 5.08,
        "depth_m": 0.0508,
        "model_file": "sm_5cm_weather_only_xgb.json",
        "model_configuration": "XGBoost Weather-Only",
        "feature_set_name": "WEATHER_ONLY_FEATURE_NAMES",
        "feature_count": 25,
        "val_rmse": 0.0393,
        "test_rmse": 0.0496,
        "test_r2": 0.5220,
        "test_pearson_r": 0.7401,
        "hwsd_layer": "0.00-0.30",
    },
    "sm_10cm": {
        "nominal_depth_cm": 10.16,
        "depth_m": 0.1016,
        "model_file": "sm_10cm_weather_only_xgb.json",
        "model_configuration": "XGBoost Weather-Only",
        "feature_set_name": "WEATHER_ONLY_FEATURE_NAMES",
        "feature_count": 25,
        "val_rmse": 0.0242,
        "test_rmse": 0.0371,
        "test_r2": 0.5882,
        "test_pearson_r": 0.8150,
        "hwsd_layer": "0.00-0.30",
    },
    "sm_20cm": {
        "nominal_depth_cm": 20.32,
        "depth_m": 0.2032,
        "model_file": "sm_20cm_full_multimodal_xgb.json",
        "model_configuration": "XGBoost Full Multimodal",
        "feature_set_name": "FULL_MULTIMODAL_FEATURE_NAMES",
        "feature_count": 58,
        "val_rmse": 0.0154,
        "test_rmse": 0.0277,
        "test_r2": 0.4959,
        "test_pearson_r": 0.8309,
        "hwsd_layer": "0.00-0.30",
    },
    "sm_50cm": {
        "nominal_depth_cm": 50.80,
        "depth_m": 0.5080,
        "model_file": "sm_50cm_weather_only_xgb.json",
        "model_configuration": "XGBoost Weather-Only",
        "feature_set_name": "WEATHER_ONLY_FEATURE_NAMES",
        "feature_count": 25,
        "val_rmse": 0.0128,
        "test_rmse": 0.0289,
        "test_r2": 0.3573,
        "test_pearson_r": 0.7829,
        "hwsd_layer": "0.30-1.00",
    },
}

# Fixed station physical properties for AAMU-JTG
STATION_STATIC_DEFAULTS = {
    "hwsd_topsoil": {
        "clay_fraction_pct": 25.0,
        "sand_fraction_pct": 53.0,
        "silt_fraction_pct": 22.0,
        "organic_carbon_pct": 0.98,
        "saturation_m3_m3": 0.43,
    },
    "hwsd_subsoil": {
        "clay_fraction_pct": 39.0,
        "sand_fraction_pct": 41.0,
        "silt_fraction_pct": 20.0,
        "organic_carbon_pct": 0.39,
        "saturation_m3_m3": 0.44,
    },
    "soilgrids_20cm": {
        "soilgrids_clay_pct": 32.8,
        "soilgrids_sand_pct": 14.9,
        "soilgrids_silt_pct": 52.3,
        "soilgrids_bdod_g_cm3": 1.55,
        "soilgrids_ocd_kg_m3": 13.2,
        "soilgrids_wv0010_m3_m3": 0.38,
        "soilgrids_wv0033_m3_m3": 0.338,
        "soilgrids_wv1500_m3_m3": 0.154,
    },
    "dem_terrain": {
        "dem_elevation_m": 245.47,
        "dem_slope_deg": 4.9156,
        "dem_aspect_sin": -0.1622,
        "dem_aspect_cos": -0.9868,
    },
}

FORBIDDEN_GROUND_SENSOR_COLUMNS = {
    "target",
    "target_lag_1d",
    "target_sm_5cm",
    "target_sm_10cm",
    "target_sm_20cm",
    "target_sm_50cm",
    "sm_0.050800_0.050800",
    "sm_0.101600_0.101600",
    "sm_0.203200_0.203200",
    "sm_0.508000_0.508000",
    "in_situ_sm",
    "ismn_sm",
    "probe_sm",
    "deep_vwc",
    "smap_l4",
}


class Model1Predictor:
    """
    Production inference engine for SoilDepth-AI Model 1.
    Loads and serves the 4 ground-sensor-independent models across point depths.
    """

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = Path(models_dir) if models_dir else MODELS_DIR
        self.station_id = STATION_ID
        self.models: Dict[str, xgb.XGBRegressor] = {}
        self.features_per_depth: Dict[str, List[str]] = {}
        self._load_models()

    def _load_models(self) -> None:
        """Loads and verifies all four serialized XGBoost JSON models."""
        for depth_key, cfg in SELECTED_MODELS_CONFIG.items():
            model_path = self.models_dir / cfg["model_file"]
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Selected Model 1 artifact missing: {model_path}. "
                    "Ensure Model 1 training has completed successfully."
                )

            # Assign feature ordering
            if cfg["feature_set_name"] == "WEATHER_ONLY_FEATURE_NAMES":
                features = list(WEATHER_ONLY_FEATURE_NAMES)
            elif cfg["feature_set_name"] == "FULL_MULTIMODAL_FEATURE_NAMES":
                features = list(FULL_MULTIMODAL_FEATURE_NAMES)
            else:
                raise ValueError(f"Unknown feature set: {cfg['feature_set_name']}")

            assert len(features) == cfg["feature_count"], (
                f"Feature count mismatch for {depth_key}: "
                f"expected {cfg['feature_count']}, got {len(features)}"
            )

            reg = xgb.XGBRegressor()
            reg.load_model(str(model_path))

            self.models[depth_key] = reg
            self.features_per_depth[depth_key] = features

    def get_model_catalog(self) -> ModelCatalogResponse:
        """Returns metadata description of the active operational Model 1 ensemble."""
        details = {}
        for d_key, cfg in SELECTED_MODELS_CONFIG.items():
            details[d_key] = ModelDetail(
                depth_key=d_key,
                nominal_depth_cm=cfg["nominal_depth_cm"],
                depth_m=cfg["depth_m"],
                model_file=cfg["model_file"],
                model_configuration=cfg["model_configuration"],
                feature_count=cfg["feature_count"],
                features_required=self.features_per_depth[d_key],
                val_rmse=cfg["val_rmse"],
                test_rmse=cfg["test_rmse"],
                test_r2=cfg["test_r2"],
                test_pearson_r=cfg["test_pearson_r"],
            )

        return ModelCatalogResponse(
            station_id=self.station_id,
            station_lat=STATION_LAT,
            station_lon=STATION_LON,
            station_elev_m=STATION_ELEV_M,
            model_version="1.0.0",
            status="OPERATIONAL",
            ground_sensor_dependence="NONE (100% Ground-Sensor-Independent)",
            models=details,
        )

    def _sanitize_and_validate_record(
        self,
        raw_record: Dict[str, Any],
        date_str: Optional[str] = None,
    ) -> Tuple[Dict[str, float], ValidationInfo]:
        """
        Validates input fields, strips any forbidden ground-truth columns,
        auto-computes calendar seasonality if missing, fills station static defaults,
        and verifies numeric conversion.
        """
        val_info = ValidationInfo()
        cleaned: Dict[str, Any] = {}

        # 1. Guard against in-situ target leakage
        for k, v in raw_record.items():
            k_lower = str(k).lower().strip()
            if k_lower in FORBIDDEN_GROUND_SENSOR_COLUMNS or "target" in k_lower or "sm_0." in k_lower:
                val_info.warnings.append(
                    f"Forbidden ground-sensor column '{k}' was detected and stripped to guarantee ungauged integrity."
                )
                continue
            cleaned[k] = v

        # 2. Extract or infer date for cyclical DOY
        rec_date = date_str or cleaned.get("date_utc") or cleaned.get("date")
        if rec_date:
            try:
                dt = pd.to_datetime(rec_date)
                doy = dt.dayofyear
                if "doy_sin" not in cleaned:
                    cleaned["doy_sin"] = float(np.sin(2.0 * np.pi * doy / 365.25))
                    val_info.missing_features_filled_with_default.append("doy_sin")
                if "doy_cos" not in cleaned:
                    cleaned["doy_cos"] = float(np.cos(2.0 * np.pi * doy / 365.25))
                    val_info.missing_features_filled_with_default.append("doy_cos")
            except Exception as e:
                val_info.warnings.append(f"Could not parse date '{rec_date}': {e}")

        # 3. Check and populate static properties if missing
        # Topsoil HWSD
        for prop, default_val in STATION_STATIC_DEFAULTS["hwsd_topsoil"].items():
            if prop not in cleaned or pd.isna(cleaned[prop]):
                cleaned[prop] = default_val
                if prop not in val_info.missing_features_filled_with_default:
                    val_info.missing_features_filled_with_default.append(prop)

        # SoilGrids 20cm
        for prop, default_val in STATION_STATIC_DEFAULTS["soilgrids_20cm"].items():
            if prop not in cleaned or pd.isna(cleaned[prop]):
                cleaned[prop] = default_val
                if prop not in val_info.missing_features_filled_with_default:
                    val_info.missing_features_filled_with_default.append(prop)

        # DEM terrain
        for prop, default_val in STATION_STATIC_DEFAULTS["dem_terrain"].items():
            if prop not in cleaned or pd.isna(cleaned[prop]):
                cleaned[prop] = default_val
                if prop not in val_info.missing_features_filled_with_default:
                    val_info.missing_features_filled_with_default.append(prop)

        # 4. Convert values to float; handle NaN safely
        numeric_cleaned: Dict[str, float] = {}
        for k, v in cleaned.items():
            if k in ("date_utc", "date", "station_id"):
                continue
            try:
                if v is None or pd.isna(v) or v == "":
                    numeric_cleaned[k] = np.nan
                else:
                    val_float = float(v)
                    # Plausibility check for infinite values
                    if np.isinf(val_float):
                        val_info.warnings.append(f"Infinite value in feature '{k}' converted to NaN")
                        numeric_cleaned[k] = np.nan
                    else:
                        numeric_cleaned[k] = val_float
            except (ValueError, TypeError):
                val_info.warnings.append(f"Non-numeric value in feature '{k}': '{v}' converted to NaN")
                numeric_cleaned[k] = np.nan

        return numeric_cleaned, val_info

    def _predict_depth(
        self,
        depth_key: str,
        features_dict: Dict[str, float],
        val_info: ValidationInfo,
    ) -> DepthPrediction:
        """Runs inference for a single target depth using its designated model."""
        cfg = SELECTED_MODELS_CONFIG[depth_key]
        model = self.models[depth_key]
        required_features = self.features_per_depth[depth_key]

        # Extract features in the exact ordering expected by model
        row_values = []
        for feat in required_features:
            # Special check for 50cm subsoil HWSD
            if depth_key == "sm_50cm" and feat in STATION_STATIC_DEFAULTS["hwsd_subsoil"]:
                val = features_dict.get(feat, STATION_STATIC_DEFAULTS["hwsd_subsoil"][feat])
            else:
                val = features_dict.get(feat, np.nan)
            row_values.append(val)

        X = np.array([row_values], dtype=float)

        raw_pred = float(model.predict(X)[0])

        # Physical clamping to valid soil moisture range [0.0, 0.60 m³/m³]
        clamped_pred = raw_pred
        if clamped_pred < PHYSICAL_SM_MIN:
            clamped_pred = PHYSICAL_SM_MIN
            val_info.clamped_predictions.append(f"{depth_key} (raw {raw_pred:.5f} < {PHYSICAL_SM_MIN})")
        elif clamped_pred > PHYSICAL_SM_MAX:
            clamped_pred = PHYSICAL_SM_MAX
            val_info.clamped_predictions.append(f"{depth_key} (raw {raw_pred:.5f} > {PHYSICAL_SM_MAX})")

        return DepthPrediction(
            nominal_depth_cm=cfg["nominal_depth_cm"],
            depth_m=cfg["depth_m"],
            volumetric_soil_moisture=round(clamped_pred, 5),
            units="m³/m³",
            model_id=f"{depth_key}_{cfg['model_file'].replace('.json', '')}",
            model_file=cfg["model_file"],
            model_configuration=cfg["model_configuration"],
            feature_count=cfg["feature_count"],
        )

    def predict_single(
        self,
        data: Dict[str, Any],
        date_str: Optional[str] = None,
    ) -> Model1PredictionResponse:
        """
        Executes single-day inference across all four sensor depths.
        """
        rec_date = str(date_str or data.get("date_utc") or data.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        cleaned_features, val_info = self._sanitize_and_validate_record(data, date_str=rec_date)

        # Check critical base weather features
        critical_weather = ["temperature_2m_mean_c", "precipitation_total_mm"]
        missing_critical = [f for f in critical_weather if f not in cleaned_features or np.isnan(cleaned_features[f])]
        if missing_critical:
            val_info.warnings.append(f"Missing critical meteorological inputs: {missing_critical}. Model will use default split branches.")

        predictions: Dict[str, DepthPrediction] = {}
        for depth_key in SELECTED_MODELS_CONFIG.keys():
            predictions[depth_key] = self._predict_depth(depth_key, cleaned_features, val_info)

        status = "WARNING" if val_info.warnings else "SUCCESS"

        return Model1PredictionResponse(
            station_id=self.station_id,
            date=rec_date,
            model_version="1.0.0",
            inference_timestamp_utc=datetime.now(timezone.utc).isoformat(),
            status=status,
            predictions=predictions,
            validation_info=val_info,
        )

    def predict_batch(
        self,
        records: List[Dict[str, Any]],
    ) -> Model1BatchPredictionResponse:
        """
        Executes multi-day batch inference across a sequence of daily records.
        """
        if not records:
            raise ValueError("Input batch record list is empty")

        results: List[Model1PredictionResponse] = []
        dates: List[str] = []

        for rec in records:
            resp = self.predict_single(rec)
            results.append(resp)
            dates.append(resp.date)

        sorted_dates = sorted(dates)
        overall_status = "WARNING" if any(r.status == "WARNING" for r in results) else "SUCCESS"

        return Model1BatchPredictionResponse(
            station_id=self.station_id,
            model_version="1.0.0",
            batch_size=len(results),
            date_start=sorted_dates[0] if sorted_dates else None,
            date_end=sorted_dates[-1] if sorted_dates else None,
            status=overall_status,
            results=results,
        )

    def predict_dataframe(
        self,
        df: pd.DataFrame,
    ) -> Model1BatchPredictionResponse:
        """
        Executes batch inference directly from a pandas DataFrame.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty")

        records = df.to_dict(orient="records")
        return self.predict_batch(records)

    def predict_csv(
        self,
        csv_path: Union[str, Path],
    ) -> Model1BatchPredictionResponse:
        """
        Loads an input CSV and executes batch inference.
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Inference input CSV not found at {path}")

        df = pd.read_csv(path)
        return self.predict_dataframe(df)

