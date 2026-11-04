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
         depth-appropriate static soil defaults (preventing topsoil contamination of subsoil),
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
    RegionNotAvailableResponse,
)


class RegionModelNotAvailableError(ValueError):
    """Raised when an inference request is routed to an uncalibrated regional model."""
    def __init__(self, region: str, reason: Optional[str] = None):
        self.region = region
        self.reason = reason or (
            f"Model weights for region '{region}' are not available. "
            "Supervised training for Maharashtra regional models is strictly prohibited "
            "until verified in-situ ground truth data is received from authorized institutions. "
            "Using Alabama Model 1 weights for Maharashtra inference is strictly forbidden."
        )
        super().__init__(self.reason)


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
        "edaphic_source_layer": "HWSD Topsoil (0.00-0.30m)",
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
        "edaphic_source_layer": "HWSD Topsoil (0.00-0.30m)",
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
        "edaphic_source_layer": "HWSD Topsoil (0.00-0.30m) & SoilGrids 15-30cm",
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
        "edaphic_source_layer": "HWSD Subsoil (0.30-1.00m)",
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

    def get_model_catalog(self, region: str = "alabama") -> Union[ModelCatalogResponse, RegionNotAvailableResponse]:
        """Returns metadata description of the active operational Model 1 ensemble."""
        if region.lower() in ["maharashtra", "mh"]:
            return RegionNotAvailableResponse(
                status="MODEL_NOT_AVAILABLE",
                region="maharashtra",
                message="Maharashtra regional models are not yet calibrated or deployed.",
                reason=(
                    "Supervised training for Maharashtra regional models is strictly prohibited "
                    "until verified in-situ ground truth data is received from authorized institutions. "
                    "Using Alabama Model 1 weights for Maharashtra inference is strictly forbidden."
                ),
                candidate_stations_count=16,
                ground_truth_records_received=0,
                alabama_baseline_status="COMPLETED_AND_INDEPENDENTLY_VALIDATED",
            )

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
                training_station_id="AAMU-JTG",
                training_period="2015-01-01 to 2020-12-31",
                validation_period="2021-01-01 to 2021-12-31",
                test_period="2022-01-01 to 2023-12-31",
                edaphic_source_layer=cfg.get("edaphic_source_layer", ""),
                limitations="Trained on single SCAN pilot station AAMU-JTG (Alabama, USA). Point-sensor depth proxy.",
            )

        return ModelCatalogResponse(
            station_id=self.station_id,
            station_lat=STATION_LAT,
            station_lon=STATION_LON,
            station_elev_m=STATION_ELEV_M,
            model_version="1.0.0",
            status="OPERATIONAL",
            ground_sensor_dependence="NONE (100% Ground-Sensor-Independent)",
            training_station_id="AAMU-JTG",
            training_period="2015-01-01 to 2020-12-31",
            target_geography="AAMU-JTG, Alabama, USA (Pilot Benchmark)",
            limitations=(
                "Model 1 weights are trained exclusively on Alabama AAMU-JTG data and must "
                "not be used as Maharashtra-trained weights without regional retuning on verified local ground truth."
            ),
            models=details,
        )

    def _sanitize_and_validate_record(
        self,
        raw_record: Dict[str, Any],
        date_str: Optional[str] = None,
    ) -> Tuple[Dict[str, float], ValidationInfo, Dict[str, Dict[str, float]]]:
        """
        Validates input fields, strips any forbidden ground-truth columns,
        auto-computes calendar seasonality if missing, parses explicit or depth-specific
        static soil/DEM properties, tracks missing defaults per depth without topsoil
        contamination of subsoil, and converts values to clean numeric floats.
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

        # 3. Parse static properties: isolate topsoil, subsoil, SoilGrids, and DEM inputs
        topsoil_user: Dict[str, float] = {}
        subsoil_user: Dict[str, float] = {}
        soilgrids_user: Dict[str, float] = {}
        dem_user: Dict[str, float] = {}

        # Unpack nested sub-dictionaries if supplied
        for dict_key, target_dict in [
            ("hwsd_topsoil", topsoil_user),
            ("topsoil", topsoil_user),
            ("hwsd_subsoil", subsoil_user),
            ("subsoil", subsoil_user),
            ("soilgrids", soilgrids_user),
            ("soilgrids_20cm", soilgrids_user),
            ("dem", dem_user),
            ("dem_terrain", dem_user),
        ]:
            if isinstance(raw_record.get(dict_key), dict):
                for pk, pv in raw_record[dict_key].items():
                    try:
                        if pd.notna(pv) and pv != "":
                            target_dict[pk] = float(pv)
                    except (ValueError, TypeError):
                        pass

        # Unpack flattened keys
        for k, v in cleaned.items():
            if isinstance(v, dict) or not isinstance(k, str):
                continue
            k_clean = k.strip()

            # Subsoil-specific prefixes/suffixes
            for prop in STATION_STATIC_DEFAULTS["hwsd_subsoil"]:
                if k_clean in (f"subsoil_{prop}", f"hwsd_subsoil_{prop}", f"{prop}_subsoil", f"{prop}_50cm", f"{prop}_30_100"):
                    try:
                        if pd.notna(v) and v != "":
                            subsoil_user[prop] = float(v)
                    except (ValueError, TypeError):
                        pass

            # Topsoil-specific prefixes/suffixes
            for prop in STATION_STATIC_DEFAULTS["hwsd_topsoil"]:
                if k_clean in (f"topsoil_{prop}", f"hwsd_topsoil_{prop}", f"{prop}_topsoil", f"{prop}_0_30"):
                    try:
                        if pd.notna(v) and v != "":
                            topsoil_user[prop] = float(v)
                    except (ValueError, TypeError):
                        pass
                elif k_clean == prop and prop not in topsoil_user:
                    # Generic property passed at root (e.g. clay_fraction_pct)
                    try:
                        if pd.notna(v) and v != "":
                            topsoil_user[prop] = float(v)
                    except (ValueError, TypeError):
                        pass

            # SoilGrids features
            for prop in STATION_STATIC_DEFAULTS["soilgrids_20cm"]:
                if k_clean in (f"soilgrids_{prop}", prop):
                    try:
                        if pd.notna(v) and v != "":
                            soilgrids_user[prop] = float(v)
                    except (ValueError, TypeError):
                        pass

            # DEM features
            for prop in STATION_STATIC_DEFAULTS["dem_terrain"]:
                if k_clean in (f"dem_{prop}", prop):
                    try:
                        if pd.notna(v) and v != "":
                            dem_user[prop] = float(v)
                    except (ValueError, TypeError):
                        pass

        # 4. Check and track missing static defaults
        # Topsoil HWSD missingness (for 5cm, 10cm, 20cm)
        for prop in STATION_STATIC_DEFAULTS["hwsd_topsoil"]:
            if prop not in topsoil_user or pd.isna(topsoil_user[prop]):
                if prop not in val_info.missing_features_filled_with_default:
                    val_info.missing_features_filled_with_default.append(prop)

        # Subsoil HWSD missingness (for 50cm) — explicitly distinguished from topsoil
        for prop in STATION_STATIC_DEFAULTS["hwsd_subsoil"]:
            if prop not in subsoil_user or pd.isna(subsoil_user[prop]):
                sub_key = f"subsoil_{prop}"
                if sub_key not in val_info.missing_features_filled_with_default:
                    val_info.missing_features_filled_with_default.append(sub_key)

        # SoilGrids missingness (for 20cm multimodal)
        for prop in STATION_STATIC_DEFAULTS["soilgrids_20cm"]:
            if prop not in soilgrids_user or pd.isna(soilgrids_user[prop]):
                if prop not in val_info.missing_features_filled_with_default:
                    val_info.missing_features_filled_with_default.append(prop)

        # DEM terrain missingness (for 20cm multimodal)
        for prop in STATION_STATIC_DEFAULTS["dem_terrain"]:
            if prop not in dem_user or pd.isna(dem_user[prop]):
                if prop not in val_info.missing_features_filled_with_default:
                    val_info.missing_features_filled_with_default.append(prop)

        # 5. Convert root features to float; handle NaN safely
        numeric_cleaned: Dict[str, float] = {}
        for k, v in cleaned.items():
            if k in ("date_utc", "date", "station_id") or isinstance(v, dict):
                continue
            try:
                if v is None or pd.isna(v) or v == "":
                    numeric_cleaned[k] = np.nan
                else:
                    val_float = float(v)
                    if np.isinf(val_float):
                        val_info.warnings.append(f"Infinite value in feature '{k}' converted to NaN")
                        numeric_cleaned[k] = np.nan
                    else:
                        numeric_cleaned[k] = val_float
            except (ValueError, TypeError):
                val_info.warnings.append(f"Non-numeric value in feature '{k}': '{v}' converted to NaN")
                numeric_cleaned[k] = np.nan

        static_context = {
            "topsoil": topsoil_user,
            "subsoil": subsoil_user,
            "soilgrids": soilgrids_user,
            "dem": dem_user,
        }

        return numeric_cleaned, val_info, static_context

    def _predict_depth(
        self,
        depth_key: str,
        features_dict: Dict[str, float],
        val_info: ValidationInfo,
        static_context: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> DepthPrediction:
        """
        Runs inference for a single target depth using its designated model.
        Guarantees that HWSD subsoil features for sm_50cm strictly receive subsoil
        properties/defaults, completely immune to topsoil contamination.
        """
        cfg = SELECTED_MODELS_CONFIG[depth_key]
        model = self.models[depth_key]
        required_features = self.features_per_depth[depth_key]

        topsoil_inputs = static_context.get("topsoil", {}) if static_context else {}
        subsoil_inputs = static_context.get("subsoil", {}) if static_context else {}
        soilgrids_inputs = static_context.get("soilgrids", {}) if static_context else {}
        dem_inputs = static_context.get("dem", {}) if static_context else {}

        # Extract features in the exact ordering expected by model
        row_values = []
        for feat in required_features:
            if depth_key == "sm_50cm" and feat in STATION_STATIC_DEFAULTS["hwsd_subsoil"]:
                # Subsoil depth (50 cm): strictly use user subsoil input if provided,
                # otherwise use subsoil default (39% clay, 41% sand, 20% silt, 0.39% SOC, 0.44 sat).
                # NEVER fallback to topsoil defaults!
                if feat in subsoil_inputs and pd.notna(subsoil_inputs[feat]):
                    val = subsoil_inputs[feat]
                else:
                    val = STATION_STATIC_DEFAULTS["hwsd_subsoil"][feat]
            elif depth_key in ("sm_5cm", "sm_10cm", "sm_20cm") and feat in STATION_STATIC_DEFAULTS["hwsd_topsoil"]:
                # Topsoil depths (5, 10, 20 cm): use user topsoil input if provided, otherwise topsoil default.
                if feat in topsoil_inputs and pd.notna(topsoil_inputs[feat]):
                    val = topsoil_inputs[feat]
                elif feat in features_dict and pd.notna(features_dict[feat]):
                    val = features_dict[feat]
                else:
                    val = STATION_STATIC_DEFAULTS["hwsd_topsoil"][feat]
            elif feat in STATION_STATIC_DEFAULTS["soilgrids_20cm"]:
                # SoilGrids features: use user input if provided, otherwise SoilGrids default
                if feat in soilgrids_inputs and pd.notna(soilgrids_inputs[feat]):
                    val = soilgrids_inputs[feat]
                elif feat in features_dict and pd.notna(features_dict[feat]):
                    val = features_dict[feat]
                else:
                    val = STATION_STATIC_DEFAULTS["soilgrids_20cm"][feat]
            elif feat in STATION_STATIC_DEFAULTS["dem_terrain"]:
                # DEM terrain features: use user input if provided, otherwise DEM terrain default
                if feat in dem_inputs and pd.notna(dem_inputs[feat]):
                    val = dem_inputs[feat]
                elif feat in features_dict and pd.notna(features_dict[feat]):
                    val = features_dict[feat]
                else:
                    val = STATION_STATIC_DEFAULTS["dem_terrain"][feat]
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
        region: str = "alabama",
    ) -> Model1PredictionResponse:
        """
        Executes single-day inference across all four sensor depths.
        """
        if region.lower() in ["maharashtra", "mh"]:
            raise RegionModelNotAvailableError(region)

        rec_date = str(date_str or data.get("date_utc") or data.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        cleaned_features, val_info, static_context = self._sanitize_and_validate_record(data, date_str=rec_date)

        # Check critical base weather features
        critical_weather = ["temperature_2m_mean_c", "precipitation_total_mm"]
        missing_critical = [f for f in critical_weather if f not in cleaned_features or np.isnan(cleaned_features[f])]
        if missing_critical:
            val_info.warnings.append(f"Missing critical meteorological inputs: {missing_critical}. Model will use default split branches.")

        predictions: Dict[str, DepthPrediction] = {}
        for depth_key in SELECTED_MODELS_CONFIG.keys():
            predictions[depth_key] = self._predict_depth(
                depth_key, cleaned_features, val_info, static_context=static_context
            )

        status = "WARNING" if val_info.warnings else "SUCCESS"

        return Model1PredictionResponse(
            station_id=self.station_id,
            date=rec_date,
            model_version="1.0.0",
            inference_timestamp_utc=datetime.now(timezone.utc).isoformat(),
            status=status,
            units="m³/m³",
            predictions=predictions,
            validation_info=val_info,
        )

    def predict_batch(
        self,
        records: List[Dict[str, Any]],
        region: str = "alabama",
    ) -> Model1BatchPredictionResponse:
        """
        Executes multi-day batch inference over a list of daily feature records.
        """
        if region.lower() in ["maharashtra", "mh"]:
            raise RegionModelNotAvailableError(region)

        if not records:
            raise ValueError("Input records list cannot be empty for batch prediction.")

        results: List[Model1PredictionResponse] = []
        for rec in records:
            res = self.predict_single(rec, region=region)
            results.append(res)

        # Extract date bounds
        dates = [r.date for r in results]
        date_start = min(dates) if dates else None
        date_end = max(dates) if dates else None

        has_warnings = any(r.status == "WARNING" for r in results)
        overall_status = "WARNING" if has_warnings else "SUCCESS"

        return Model1BatchPredictionResponse(
            station_id=self.station_id,
            model_version="1.0.0",
            batch_size=len(results),
            date_start=date_start,
            date_end=date_end,
            status=overall_status,
            units="m³/m³",
            results=results,
        )

    def predict_dataframe(
        self,
        df: pd.DataFrame,
    ) -> Model1BatchPredictionResponse:
        """
        Convenience wrapper to run batch inference on a pandas DataFrame.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty.")

        records = df.to_dict(orient="records")
        return self.predict_batch(records)
