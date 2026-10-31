"""
SoilDepth-AI — Unit Tests for Baseline & Multimodal Training Pipeline
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Verify:
         1. Strict target isolation (no ground-truth target leakage in predictor sets)
         2. Chronological split integrity (no date overlap, exact boundaries)
         3. Model training reproducibility (fixed seed gives identical predictions)
         4. Model serialization and artifact re-loading fidelity (.json load_model)
         5. Residual diagnostics calculation accuracy
         6. Dry-run training readiness audit
         7. Isolated pipeline execution with synthetic data (verifying artifacts)
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import xgboost as xgb

from services.modelling.config import (
    PROCESSED_DATA_DIR,
    SENSOR_DEPTHS,
    TRAIN_START_DATE,
    TRAIN_END_DATE,
    VAL_START_DATE,
    VAL_END_DATE,
    TEST_START_DATE,
    TEST_END_DATE,
    WEATHER_ONLY_FEATURE_NAMES,
    LAG_AUGMENTED_FEATURE_NAMES,
    FULL_MULTIMODAL_FEATURE_NAMES,
    XGB_HYPERPARAMS,
)
from services.modelling.feature_engineering import partition_chronological_splits
from services.modelling.evaluate import compute_metrics, compute_residual_diagnostics
from services.modelling.train_xgboost import (
    train_and_evaluate_depth,
    run_dry_run_audit,
)


def test_target_isolation_in_full_multimodal_features():
    """Verify that none of the 58 predictors contain ground-truth soil moisture targets."""
    forbidden_tokens = ["target", "sm_5cm", "sm_10cm", "sm_20cm", "sm_50cm", "in_situ"]
    for feat in FULL_MULTIMODAL_FEATURE_NAMES:
        for token in forbidden_tokens:
            assert token not in feat.lower(), f"Forbidden target token '{token}' in feature '{feat}'!"

    # Verify count is exactly 58
    assert len(FULL_MULTIMODAL_FEATURE_NAMES) == 58


def test_chronological_split_integrity():
    """Verify partition_chronological_splits enforces non-overlapping chronological bounds."""
    for depth_key in SENSOR_DEPTHS.keys():
        csv_path = PROCESSED_DATA_DIR / f"AAMU-JTG_{depth_key}_daily.csv"
        assert csv_path.exists(), f"Processed CSV missing: {csv_path}"
        df = pd.read_csv(csv_path)

        df_train, df_val, df_test = partition_chronological_splits(df)

        assert len(df_train) == 2192, f"Train count mismatch: {len(df_train)}"
        assert len(df_val) == 365, f"Val count mismatch: {len(df_val)}"
        assert len(df_test) == 730, f"Test count mismatch: {len(df_test)}"
        assert len(df_train) + len(df_val) + len(df_test) == 3287

        # Date boundaries
        assert df_train["date_utc"].min() == TRAIN_START_DATE
        assert df_train["date_utc"].max() == TRAIN_END_DATE
        assert df_val["date_utc"].min() == VAL_START_DATE
        assert df_val["date_utc"].max() == VAL_END_DATE
        assert df_test["date_utc"].min() == TEST_START_DATE
        assert df_test["date_utc"].max() == TEST_END_DATE

        # Zero set intersection
        train_dates = set(df_train["date_utc"])
        val_dates = set(df_val["date_utc"])
        test_dates = set(df_test["date_utc"])

        assert len(train_dates & val_dates) == 0, "Train and Val dates overlap!"
        assert len(val_dates & test_dates) == 0, "Val and Test dates overlap!"
        assert len(train_dates & test_dates) == 0, "Train and Test dates overlap!"


def test_model_training_reproducibility():
    """Verify that training with fixed random_state yields identical predictions."""
    np.random.seed(42)
    n = 100
    X_train = np.random.randn(n, 10)
    y_train = np.sin(X_train[:, 0]) + 0.5 * X_train[:, 1]
    X_test = np.random.randn(20, 10)

    model1 = xgb.XGBRegressor(
        n_estimators=50,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
    )
    model1.fit(X_train, y_train)
    preds1 = model1.predict(X_test)

    model2 = xgb.XGBRegressor(
        n_estimators=50,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
    )
    model2.fit(X_train, y_train)
    preds2 = model2.predict(X_test)

    np.testing.assert_array_equal(preds1, preds2)


def test_model_artifact_save_and_reload(tmp_path):
    """Verify that an XGBoost model saved to .json can be reloaded and outputs identical predictions."""
    np.random.seed(42)
    X = np.random.randn(80, 5)
    y = 2.0 * X[:, 0] - X[:, 1] + 0.1 * np.random.randn(80)

    model = xgb.XGBRegressor(n_estimators=25, max_depth=3, random_state=42)
    model.fit(X, y)
    orig_preds = model.predict(X)

    model_file = tmp_path / "test_model.json"
    model.save_model(str(model_file))
    assert model_file.exists()

    reloaded_model = xgb.XGBRegressor()
    reloaded_model.load_model(str(model_file))
    reloaded_preds = reloaded_model.predict(X)

    np.testing.assert_allclose(orig_preds, reloaded_preds, rtol=1e-5, atol=1e-5)


def test_residual_diagnostics_calculation():
    """Verify residual diagnostics calculation (mean, std, median, skewness, quantiles)."""
    y_true = np.array([0.20, 0.25, 0.30, 0.35, 0.40])
    # Predictions with constant bias of +0.02
    y_pred = y_true + 0.02
    res = compute_residual_diagnostics(y_true, y_pred)

    assert res["n_samples"] == 5
    assert res["residual_mean"] == pytest.approx(0.02, abs=1e-4)
    assert res["residual_std"] == pytest.approx(0.0, abs=1e-4)
    assert res["residual_median"] == pytest.approx(0.02, abs=1e-4)
    assert res["residual_max_abs"] == pytest.approx(0.02, abs=1e-4)
    assert res["residual_skewness"] == pytest.approx(0.0, abs=1e-4)


def test_dry_run_audit_passes():
    """Verify that the dry-run training readiness audit runs and confirms READY_FOR_TRAINING."""
    audit_results = run_dry_run_audit()
    assert len(audit_results) == 4
    for depth_key, res in audit_results.items():
        assert res["status"] == "READY_FOR_TRAINING"
        assert res["total_days"] == 3287
        assert res["feature_count"] == 58
        assert res["train_valid_targets"] > 1500
        assert res["val_valid_targets"] > 100
        assert res["test_valid_targets"] > 400


def test_train_and_evaluate_depth_in_isolation(tmp_path):
    """
    Test train_and_evaluate_depth using synthetic data in an isolated tmp_path
    to verify artifact creation (models, predictions with residuals, diagnostics).
    """
    dates = pd.date_range("2015-01-01", "2023-12-31", freq="D").strftime("%Y-%m-%d").tolist()
    n = len(dates)
    np.random.seed(42)

    df_synth = pd.DataFrame({"date_utc": dates})
    # Populate all 58 features
    for feat in FULL_MULTIMODAL_FEATURE_NAMES:
        df_synth[feat] = np.random.randn(n)

    # Populate targets and lag
    df_synth["target"] = 0.25 + 0.05 * np.sin(np.linspace(0, 20, n)) + 0.01 * np.random.randn(n)
    df_synth["target_lag_1d"] = df_synth["target"].shift(1)

    models_dir = tmp_path / "models"
    reports_dir = tmp_path / "reports"

    res = train_and_evaluate_depth(
        depth_key="sm_5cm",
        df_depth=df_synth,
        models_dir=models_dir,
        reports_dir=reports_dir,
        include_full_multimodal=True,
    )

    # Check depth results
    assert "Historical_Mean" in res["models"]
    assert "Climatology" in res["models"]
    assert "Persistence" in res["models"]
    assert "XGBoost_Weather_Only" in res["models"]
    assert "XGBoost_Lag_Augmented" in res["models"]
    assert "XGBoost_Full_Multimodal" in res["models"]

    # Check artifacts on disk
    assert (models_dir / "sm_5cm_weather_only_xgb.json").exists()
    assert (models_dir / "sm_5cm_lag_augmented_xgb.json").exists()
    assert (models_dir / "sm_5cm_full_multimodal_xgb.json").exists()
    assert (models_dir / "sm_5cm_full_multimodal_feature_importances.csv").exists()

    preds_file = reports_dir / "sm_5cm_test_predictions.csv"
    assert preds_file.exists()
    df_preds = pd.read_csv(preds_file)

    expected_cols = [
        "date_utc", "y_true",
        "pred_historical_mean", "res_historical_mean",
        "pred_climatology", "res_climatology",
        "pred_persistence", "res_persistence",
        "pred_xgb_weather_only", "res_xgb_weather_only",
        "pred_xgb_lag_augmented", "res_xgb_lag_augmented",
        "pred_xgb_full_multimodal", "res_xgb_full_multimodal",
    ]
    for col in expected_cols:
        assert col in df_preds.columns, f"Missing column in predictions: {col}"

    val_preds_file = reports_dir / "sm_5cm_val_predictions.csv"
    assert val_preds_file.exists()

    diag_file = reports_dir / "sm_5cm_residual_diagnostics.json"
    assert diag_file.exists()
    with open(diag_file) as f:
        diag_data = json.load(f)
    assert "XGBoost_Full_Multimodal" in diag_data
    assert "test" in diag_data["XGBoost_Full_Multimodal"]
    assert "validation" in diag_data["XGBoost_Full_Multimodal"]
    assert "residual_mean" in diag_data["XGBoost_Full_Multimodal"]["test"]

    # Check plot artifacts
    assert (reports_dir / "plots" / "sm_5cm_scatter_pred_vs_obs.png").exists()
    assert (reports_dir / "plots" / "sm_5cm_residuals_distribution.png").exists()
    assert (reports_dir / "plots" / "sm_5cm_timeseries_hydrograph.png").exists()

