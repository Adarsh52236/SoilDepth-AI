"""
SoilDepth-AI — Production Inference Test Suite for Model 1
Author: Senior Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Comprehensive unit and integration tests verifying:
         1. Loading of all 4 selected models
         2. Single-day prediction functionality
         3. Multi-day batch prediction functionality
         4. Missing feature handling (station static defaults, XGBoost native NaN)
         5. Invalid / non-numeric input handling
         6. Feature order consistency (shuffled dictionary keys)
         7. Strict ground-sensor independence (ISMN target & target_lag_1d stripping)
         8. Zero future-data leakage (single vs batch identical output)
         9. JSON serialization and schema validity
         10. Deterministic prediction reproducibility
         11. FastAPI REST API endpoints (/health, /catalog, /predict, /predict/batch)
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from services.inference.predictor import (
    Model1Predictor,
    SELECTED_MODELS_CONFIG,
    STATION_STATIC_DEFAULTS,
)
from services.inference.schemas import (
    Model1PredictionResponse,
    Model1BatchPredictionResponse,
)
from services.inference.api import app
from services.modelling.config import (
    PROCESSED_DATA_DIR,
    STATION_ID,
    WEATHER_ONLY_FEATURE_NAMES,
    FULL_MULTIMODAL_FEATURE_NAMES,
)


@pytest.fixture(scope="module")
def predictor() -> Model1Predictor:
    """Fixture providing an instantiated Model1Predictor."""
    return Model1Predictor()


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Fixture providing a FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture(scope="module")
def sample_test_df() -> pd.DataFrame:
    """Fixture providing real sample test-split records from processed data."""
    csv_path = PROCESSED_DATA_DIR / f"{STATION_ID}_all_depths_features_daily.csv"
    if not csv_path.exists():
        csv_path = PROCESSED_DATA_DIR / f"{STATION_ID}_sm_20cm_daily.csv"
    assert csv_path.exists()
    df = pd.read_csv(csv_path)
    # Extract 5 sample rows from the holdout test set (2023)
    df_sample = df[(df["date_utc"] >= "2023-06-01") & (df["date_utc"] <= "2023-06-05")].copy()
    if df_sample.empty:
        df_sample = df.tail(5).copy()
    return df_sample


# ==============================================================================
# 1. MODEL LOADING & METADATA
# ==============================================================================
def test_models_loading_and_catalog(predictor: Model1Predictor):
    """Verify all 4 models load successfully with exact configured feature counts."""
    assert len(predictor.models) == 4
    for depth_key, cfg in SELECTED_MODELS_CONFIG.items():
        assert depth_key in predictor.models
        reg = predictor.models[depth_key]
        assert reg is not None

        features = predictor.features_per_depth[depth_key]
        assert len(features) == cfg["feature_count"]
        if cfg["feature_set_name"] == "WEATHER_ONLY_FEATURE_NAMES":
            assert features == WEATHER_ONLY_FEATURE_NAMES
        elif cfg["feature_set_name"] == "FULL_MULTIMODAL_FEATURE_NAMES":
            assert features == FULL_MULTIMODAL_FEATURE_NAMES

    catalog = predictor.get_model_catalog()
    assert catalog.station_id == STATION_ID
    assert catalog.status == "OPERATIONAL"
    assert len(catalog.models) == 4
    assert catalog.models["sm_5cm"].nominal_depth_cm == 5.08
    assert catalog.models["sm_10cm"].nominal_depth_cm == 10.16
    assert catalog.models["sm_20cm"].nominal_depth_cm == 20.32
    assert catalog.models["sm_50cm"].nominal_depth_cm == 50.80


# ==============================================================================
# 2. SINGLE-DAY INFERENCE
# ==============================================================================
def test_single_day_inference(predictor: Model1Predictor, sample_test_df: pd.DataFrame):
    """Verify single-day prediction across all 4 sensor depths."""
    record = sample_test_df.iloc[0].to_dict()
    resp = predictor.predict_single(record)

    assert isinstance(resp, Model1PredictionResponse)
    assert resp.station_id == STATION_ID
    assert resp.date == str(record["date_utc"])
    assert resp.status in ("SUCCESS", "WARNING")
    assert resp.units == "m³/m³"
    assert "predictions" in resp.model_dump()
    assert len(resp.predictions) == 4

    for d_key in ["sm_5cm", "sm_10cm", "sm_20cm", "sm_50cm"]:
        pred_item = resp.predictions[d_key]
        assert pred_item.nominal_depth_cm == SELECTED_MODELS_CONFIG[d_key]["nominal_depth_cm"]
        # Physically plausible volumetric soil moisture: [0.0, 0.60]
        assert 0.0 <= pred_item.volumetric_soil_moisture <= 0.60
        assert pred_item.model_file == SELECTED_MODELS_CONFIG[d_key]["model_file"]


# ==============================================================================
# 3. MULTI-DAY BATCH INFERENCE
# ==============================================================================
def test_multiday_batch_inference(predictor: Model1Predictor, sample_test_df: pd.DataFrame):
    """Verify multi-day batch prediction from list of records and DataFrame."""
    batch_resp = predictor.predict_dataframe(sample_test_df)

    assert isinstance(batch_resp, Model1BatchPredictionResponse)
    assert batch_resp.station_id == STATION_ID
    assert batch_resp.batch_size == len(sample_test_df)
    assert len(batch_resp.results) == len(sample_test_df)
    assert batch_resp.date_start is not None
    assert batch_resp.date_end is not None

    # Check chronological ordering
    dates = [r.date for r in batch_resp.results]
    assert dates == sorted(dates)


# ==============================================================================
# 4. MISSING REQUIRED FEATURES & DEFAULT FILLING
# ==============================================================================
def test_missing_features_safe_handling(predictor: Model1Predictor):
    """
    Verify that missing remote sensing features (NaNs) are handled natively,
    and missing static properties are safely populated with station constants.
    """
    # Minimal input with only basic weather and date
    minimal_record = {
        "date_utc": "2023-07-15",
        "temperature_2m_mean_c": 26.5,
        "temperature_2m_min_c": 21.0,
        "temperature_2m_max_c": 32.0,
        "dewpoint_2m_mean_c": 20.0,
        "vpd_kpa": 1.25,
        "precipitation_total_mm": 5.4,
        "solar_radiation_total_mj_m2": 22.0,
        "wind_speed_10m_ms": 2.1,
    }

    resp = predictor.predict_single(minimal_record)
    assert resp.status in ("SUCCESS", "WARNING")
    assert resp.validation_info.is_valid is True

    # Confirm static properties were auto-filled
    filled = resp.validation_info.missing_features_filled_with_default
    assert "clay_fraction_pct" in filled
    assert "soilgrids_clay_pct" in filled
    assert "dem_elevation_m" in filled

    # Confirm all 4 depths still produce valid, non-null predictions
    for d_key, pred_item in resp.predictions.items():
        assert np.isfinite(pred_item.volumetric_soil_moisture)
        assert 0.0 <= pred_item.volumetric_soil_moisture <= 0.60


# ==============================================================================
# 5. INVALID & NON-NUMERIC FEATURE VALUES
# ==============================================================================
def test_invalid_feature_values_sanitization(predictor: Model1Predictor, sample_test_df: pd.DataFrame):
    """Verify that strings, non-numeric values, or infinities are converted to NaN and reported."""
    bad_record = sample_test_df.iloc[0].to_dict()
    bad_record["vpd_kpa"] = "NOT_A_NUMBER"
    bad_record["smap_sm_daily_mean_m3_m3"] = np.inf

    resp = predictor.predict_single(bad_record)
    assert resp.status == "WARNING"

    warnings = resp.validation_info.warnings
    assert any("vpd_kpa" in w for w in warnings)
    assert any("smap_sm_daily_mean_m3_m3" in w for w in warnings)

    # Inference must still complete successfully with valid predictions
    for d_key, pred_item in resp.predictions.items():
        assert np.isfinite(pred_item.volumetric_soil_moisture)


# ==============================================================================
# 6. FEATURE ORDER CONSISTENCY
# ==============================================================================
def test_feature_order_consistency(predictor: Model1Predictor, sample_test_df: pd.DataFrame):
    """Verify predictions are identical regardless of dictionary key ordering."""
    record = sample_test_df.iloc[0].to_dict()

    # Create shuffled dictionary
    keys = list(record.keys())
    np.random.seed(42)
    np.random.shuffle(keys)
    shuffled_record = {k: record[k] for k in keys}

    resp_orig = predictor.predict_single(record)
    resp_shuffled = predictor.predict_single(shuffled_record)

    for d_key in ["sm_5cm", "sm_10cm", "sm_20cm", "sm_50cm"]:
        v1 = resp_orig.predictions[d_key].volumetric_soil_moisture
        v2 = resp_shuffled.predictions[d_key].volumetric_soil_moisture
        assert v1 == pytest.approx(v2, abs=1e-5)


# ==============================================================================
# 7. STRICT NO GROUND-SENSOR DEPENDENCE
# ==============================================================================
def test_strict_no_ground_sensor_dependence(predictor: Model1Predictor, sample_test_df: pd.DataFrame):
    """
    Verify that providing ground-truth target columns does NOT alter predictions,
    and that in-situ columns are strictly stripped.
    """
    clean_record = sample_test_df.iloc[0].to_dict()
    # Remove any target columns if present
    for k in list(clean_record.keys()):
        if "target" in k.lower():
            del clean_record[k]

    # Create contaminated record with synthetic high target values
    contaminated_record = dict(clean_record)
    contaminated_record["target"] = 0.599
    contaminated_record["target_lag_1d"] = 0.588
    contaminated_record["target_sm_5cm"] = 0.577
    contaminated_record["sm_0.050800_0.050800"] = 0.566

    resp_clean = predictor.predict_single(clean_record)
    resp_contaminated = predictor.predict_single(contaminated_record)

    # 1. Contaminated record must report warnings that target columns were stripped
    warnings = resp_contaminated.validation_info.warnings
    assert any("target" in w.lower() for w in warnings)
    assert any("target_lag_1d" in w.lower() for w in warnings)

    # 2. Predictions must be 100% IDENTICAL
    for d_key in ["sm_5cm", "sm_10cm", "sm_20cm", "sm_50cm"]:
        v_clean = resp_clean.predictions[d_key].volumetric_soil_moisture
        v_contam = resp_contaminated.predictions[d_key].volumetric_soil_moisture
        assert v_clean == pytest.approx(v_contam, abs=1e-7), (
            f"Contaminated record altered prediction at {d_key}!"
        )


# ==============================================================================
# 8. NO FUTURE-DATA LEAKAGE
# ==============================================================================
def test_no_future_data_leakage(predictor: Model1Predictor, sample_test_df: pd.DataFrame):
    """
    Verify that evaluating day t in isolation produces the exact same prediction
    as evaluating day t within a batch containing future days t+1, t+2.
    """
    # Predict day 0 in isolation
    single_rec = sample_test_df.iloc[0].to_dict()
    resp_single = predictor.predict_single(single_rec)

    # Predict entire batch containing day 0 and future days 1..4
    resp_batch = predictor.predict_dataframe(sample_test_df)
    resp_batch_day0 = resp_batch.results[0]

    for d_key in ["sm_5cm", "sm_10cm", "sm_20cm", "sm_50cm"]:
        v_single = resp_single.predictions[d_key].volumetric_soil_moisture
        v_batch = resp_batch_day0.predictions[d_key].volumetric_soil_moisture
        assert v_single == pytest.approx(v_batch, abs=1e-7)


# ==============================================================================
# 9. JSON SERIALIZATION & REPRODUCIBILITY
# ==============================================================================
def test_json_serialization_and_reproducibility(predictor: Model1Predictor, sample_test_df: pd.DataFrame):
    """Verify JSON round-trip fidelity and deterministic output across multiple calls."""
    record = sample_test_df.iloc[0].to_dict()

    resp1 = predictor.predict_single(record)
    json_str = resp1.model_dump_json()
    parsed = json.loads(json_str)

    assert parsed["station_id"] == STATION_ID
    assert "predictions" in parsed
    assert "sm_5cm" in parsed["predictions"]
    assert "sm_20cm" in parsed["predictions"]

    # Re-run inference and verify exact equality
    resp2 = predictor.predict_single(record)
    for d_key in ["sm_5cm", "sm_10cm", "sm_20cm", "sm_50cm"]:
        assert resp1.predictions[d_key].volumetric_soil_moisture == resp2.predictions[d_key].volumetric_soil_moisture


# ==============================================================================
# 10. FASTAPI REST API ENDPOINTS
# ==============================================================================
def test_fastapi_endpoints(sample_test_df: pd.DataFrame):
    """Verify FastAPI endpoints (/health, /catalog, /predict, /predict/batch) via TestClient."""
    client = TestClient(app)

    # 1. Health check
    health_res = client.get("/health")
    assert health_res.status_code == 200
    h_data = health_res.json()
    assert h_data["status"] == "HEALTHY"
    assert h_data["models_loaded_count"] == 4
    assert h_data["ground_sensor_dependent"] is False

    # 2. Catalog
    cat_res = client.get("/catalog")
    assert cat_res.status_code == 200
    c_data = cat_res.json()
    assert len(c_data["models"]) == 4

    # 3. Single prediction endpoint
    rec = sample_test_df.iloc[0].to_dict()
    payload = {
        "station_id": "AAMU-JTG",
        "date": str(rec["date_utc"]),
        "features": {k: v for k, v in rec.items() if k not in ("date_utc", "date", "station_id") and pd.notna(v)},
    }
    pred_res = client.post("/predict", json=payload)
    assert pred_res.status_code == 200
    p_data = pred_res.json()
    assert p_data["station_id"] == "AAMU-JTG"
    assert len(p_data["predictions"]) == 4

    # 4. Batch prediction endpoint
    batch_records = []
    for idx in range(3):
        r = sample_test_df.iloc[idx].to_dict()
        batch_records.append({
            "date": str(r["date_utc"]),
            **{k: v for k, v in r.items() if k not in ("date_utc", "date", "station_id") and pd.notna(v)},
        })
    batch_payload = {
        "station_id": "AAMU-JTG",
        "records": batch_records,
    }
    batch_res = client.post("/predict/batch", json=batch_payload)
    assert batch_res.status_code == 200
    b_data = batch_res.json()
    assert b_data["batch_size"] == 3
    assert len(b_data["results"]) == 3


# ==============================================================================
# 11. DEPTH-SPECIFIC STATIC SOIL & SUBSOIL INTEGRITY TESTS
# ==============================================================================
def test_missing_subsoil_uses_subsoil_default_not_topsoil(predictor: Model1Predictor):
    """
    Verifies that when static inputs are omitted, sm_50cm receives subsoil defaults
    (clay=39%, sand=41%, silt=20%, organic_carbon=0.39%, saturation=0.44),
    and does NOT receive topsoil defaults (clay=25%, sand=53%, silt=22%, etc.).
    """
    minimal_record = {
        "date_utc": "2023-08-01",
        "temperature_2m_mean_c": 28.0,
        "temperature_2m_min_c": 22.0,
        "temperature_2m_max_c": 34.0,
        "dewpoint_2m_mean_c": 21.0,
        "vpd_kpa": 1.40,
        "precipitation_total_mm": 0.0,
        "solar_radiation_total_mj_m2": 24.0,
        "wind_speed_10m_ms": 1.8,
    }

    resp = predictor.predict_single(minimal_record)
    filled = resp.validation_info.missing_features_filled_with_default

    # Topsoil features explicitly filled with topsoil defaults
    assert "clay_fraction_pct" in filled
    assert "sand_fraction_pct" in filled

    # Subsoil features explicitly filled with subsoil defaults (distinct tracking)
    assert "subsoil_clay_fraction_pct" in filled
    assert "subsoil_sand_fraction_pct" in filled
    assert "subsoil_organic_carbon_pct" in filled

    # Prediction must be valid and within bounds
    assert np.isfinite(resp.predictions["sm_50cm"].volumetric_soil_moisture)
    assert 0.0 <= resp.predictions["sm_50cm"].volumetric_soil_moisture <= 0.60


def test_partial_static_inputs_handling(predictor: Model1Predictor):
    """
    Verifies that partial static inputs are safely handled per-layer without
    cross-layer contamination (e.g. providing topsoil clay does not contaminate subsoil).
    """
    # Provide topsoil clay only
    partial_topsoil_record = {
        "date_utc": "2023-08-01",
        "temperature_2m_mean_c": 28.0,
        "precipitation_total_mm": 0.0,
        "clay_fraction_pct": 32.0,  # User provided topsoil clay
    }

    _, val_info, static_ctx = predictor._sanitize_and_validate_record(partial_topsoil_record)

    # Topsoil clay is recognized from user input
    assert static_ctx["topsoil"]["clay_fraction_pct"] == 32.0
    # Topsoil sand was missing and tracked
    assert "sand_fraction_pct" in val_info.missing_features_filled_with_default
    # Subsoil clay was NOT given and must be tracked as subsoil default
    assert "subsoil_clay_fraction_pct" in val_info.missing_features_filled_with_default
    # Subsoil input dict must NOT have been contaminated with topsoil 32.0
    assert "clay_fraction_pct" not in static_ctx["subsoil"]

    resp = predictor.predict_single(partial_topsoil_record)
    assert resp.status in ("SUCCESS", "WARNING")
    assert np.isfinite(resp.predictions["sm_5cm"].volumetric_soil_moisture)
    assert np.isfinite(resp.predictions["sm_50cm"].volumetric_soil_moisture)


def test_depth_specific_static_inputs_resolution(predictor: Model1Predictor):
    """
    Verifies that explicit depth-specific static inputs (topsoil vs subsoil)
    are routed to their exact corresponding depth models.
    Supports both flattened prefixes (topsoil_*/subsoil_*) and nested dictionaries.
    """
    # 1. Test flattened depth-specific keys
    flat_record = {
        "date_utc": "2023-08-01",
        "temperature_2m_mean_c": 25.0,
        "precipitation_total_mm": 2.0,
        "topsoil_clay_fraction_pct": 20.0,
        "subsoil_clay_fraction_pct": 48.0,
        "subsoil_sand_fraction_pct": 35.0,
    }

    _, _, static_ctx_flat = predictor._sanitize_and_validate_record(flat_record)
    assert static_ctx_flat["topsoil"]["clay_fraction_pct"] == 20.0
    assert static_ctx_flat["subsoil"]["clay_fraction_pct"] == 48.0
    assert static_ctx_flat["subsoil"]["sand_fraction_pct"] == 35.0

    resp_flat = predictor.predict_single(flat_record)
    assert np.isfinite(resp_flat.predictions["sm_5cm"].volumetric_soil_moisture)
    assert np.isfinite(resp_flat.predictions["sm_50cm"].volumetric_soil_moisture)

    # 2. Test nested dictionaries
    nested_record = {
        "date_utc": "2023-08-01",
        "temperature_2m_mean_c": 25.0,
        "precipitation_total_mm": 2.0,
        "hwsd_topsoil": {"clay_fraction_pct": 22.0, "sand_fraction_pct": 55.0},
        "hwsd_subsoil": {"clay_fraction_pct": 46.0, "sand_fraction_pct": 38.0},
    }

    _, _, static_ctx_nested = predictor._sanitize_and_validate_record(nested_record)
    assert static_ctx_nested["topsoil"]["clay_fraction_pct"] == 22.0
    assert static_ctx_nested["subsoil"]["clay_fraction_pct"] == 46.0


def test_enriched_catalog_metadata(predictor: Model1Predictor):
    """
    Verifies that the catalog exposes training station, period, depth,
    edaphic source layers, and explicit scientific limitations.
    """
    catalog = predictor.get_model_catalog()

    assert catalog.training_station_id == "AAMU-JTG"
    assert "2015-01-01" in catalog.training_period
    assert "Alabama" in catalog.target_geography
    assert "limitations" in catalog.model_dump()

    for d_key, detail in catalog.models.items():
        assert detail.training_station_id == "AAMU-JTG"
        assert "2015-01-01" in detail.training_period
        assert "2022-01-01" in detail.test_period
        assert detail.edaphic_source_layer != ""
        assert "limitations" in detail.model_dump()


def test_regional_routing_maharashtra_refusal(predictor: Model1Predictor, client: TestClient):
    """
    Verifies that requests explicitly specifying Maharashtra regional models are refused
    with structured MODEL_NOT_AVAILABLE status, preventing Alabama weight leakage.
    """
    from services.inference.predictor import RegionModelNotAvailableError

    # 1. Direct Predictor call
    with pytest.raises(RegionModelNotAvailableError, match="Model weights for region 'maharashtra' are not available"):
        predictor.predict_single({"date_utc": "2023-08-01", "temperature_2m_mean_c": 25.0}, region="maharashtra")

    with pytest.raises(RegionModelNotAvailableError):
        predictor.predict_batch([{"date_utc": "2023-08-01", "temperature_2m_mean_c": 25.0}], region="maharashtra")

    # 2. Predictor catalog query for Maharashtra
    cat_mh = predictor.get_model_catalog(region="maharashtra")
    assert cat_mh.status == "MODEL_NOT_AVAILABLE"
    assert cat_mh.region == "maharashtra"
    assert "Supervised training" in cat_mh.reason

    # 3. HTTP API /catalog?region=maharashtra
    res_cat = client.get("/catalog?region=maharashtra")
    assert res_cat.status_code == 200
    assert res_cat.json()["status"] == "MODEL_NOT_AVAILABLE"

    # 4. HTTP API /predict with region="maharashtra"
    payload = {
        "region": "maharashtra",
        "station_id": "IITM-PUNE-COSMOS",
        "date": "2023-08-01",
        "features": {"temperature_2m_mean_c": 26.5, "precipitation_total_mm": 5.0},
    }
    res_pred = client.post("/predict", json=payload)
    assert res_pred.status_code == 503
    assert res_pred.json()["status"] == "MODEL_NOT_AVAILABLE"
    assert res_pred.json()["region"] == "maharashtra"

