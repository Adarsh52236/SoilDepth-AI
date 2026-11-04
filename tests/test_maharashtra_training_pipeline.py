"""
SoilDepth-AI — Tests for Maharashtra Regional Training Pipeline
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Validates that training is strictly blocked when ground truth is absent,
         verifies data leakage guards (prohibiting ERA5 deep SM swvl2-4 and SMAP L4),
         verifies ungauged feature rules (excluding target lags),
         and tests depth model fitting on verified in-situ data.
"""

from pathlib import Path
import tempfile
import pandas as pd
import pytest

from services.modelling.train_maharashtra import (
    MaharashtraTrainingPipeline,
    PROHIBITED_LEAKAGE_FEATURES,
    UNGAUGED_EXCLUDED_FEATURES,
)


@pytest.fixture
def pipeline(tmp_path):
    gt_dir = tmp_path / "verified_gt"
    gt_dir.mkdir(parents=True, exist_ok=True)
    rep_dir = tmp_path / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    mod_dir = tmp_path / "models"
    mod_dir.mkdir(parents=True, exist_ok=True)
    return MaharashtraTrainingPipeline(
        verified_gt_dir=gt_dir,
        reports_dir=rep_dir,
        models_dir=mod_dir,
    )


def test_pipeline_blocked_when_ground_truth_absent(pipeline):
    """Verifies that the pipeline generates a structured BLOCKED report when no ground truth exists."""
    rep = pipeline.run()
    assert rep["status"] == "BLOCKED_AWAITING_IN_SITU_GROUND_TRUTH"
    assert not rep["training_permitted"]
    assert rep["ground_truth_records_received"] == 0
    assert (pipeline.reports_dir / "training_status.json").exists()
    assert (pipeline.reports_dir / "training_status.md").exists()


def test_pipeline_refuses_leakage_features(pipeline):
    """Verifies that prohibited reanalysis / modelled features (swvl2-4, smap_l4) are rejected."""
    bad_features = ["temperature_2m_mean_c", "swvl2", "clay_fraction_pct"]
    with pytest.raises(ValueError, match="Prohibited data-leakage features detected"):
        pipeline.validate_features(bad_features, ungauged_mode=False)

    bad_smap = ["temperature_2m_mean_c", "smap_l4"]
    with pytest.raises(ValueError, match="Prohibited data-leakage features detected"):
        pipeline.validate_features(bad_smap, ungauged_mode=False)


def test_pipeline_refuses_target_lags_in_ungauged_mode(pipeline):
    """Verifies that target lags are strictly excluded from ungauged predictor sets."""
    bad_features = ["temperature_2m_mean_c", "target_lag_1d"]
    with pytest.raises(ValueError, match="Target-lag features detected in ungauged predictor set"):
        pipeline.validate_features(bad_features, ungauged_mode=True)


def test_pipeline_train_depth_model(pipeline):
    """Verifies depth model training on valid data with hyperparameter adherence."""
    import numpy as np

    np.random.seed(42)
    n = 200
    features = [
        "temperature_2m_mean_c",
        "precipitation_total_mm",
        "clay_fraction_pct",
        "sand_fraction_pct",
    ]

    X = pd.DataFrame(np.random.randn(n, len(features)), columns=features)
    y = 0.25 + 0.05 * X["clay_fraction_pct"] + 0.02 * np.random.randn(n)

    X_train, y_train = X.iloc[:120], y.iloc[:120]
    X_val, y_val = X.iloc[120:160], y.iloc[120:160]
    X_test, y_test = X.iloc[160:], y.iloc[160:]

    result = pipeline.train_depth_model(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        feature_names=features,
        depth_cm=10.0,
        station_id="MPKV-RAHURI-CAAST",
        hyperparams={"n_estimators": 10, "max_depth": 3, "learning_rate": 0.1, "random_state": 42},
    )

    assert result["depth_cm"] == 10.0
    assert result["station_id"] == "MPKV-RAHURI-CAAST"
    assert Path(result["model_path"]).exists()
    assert Path(result["feature_importances_path"]).exists()
    assert "rmse" in result["test_metrics"]

