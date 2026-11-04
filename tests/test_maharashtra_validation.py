"""
SoilDepth-AI — Tests for Maharashtra Validation Framework
Author: Senior ML Research Scientist & Hydrological Modeling Lead, SoilDepth-AI
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from services.modelling.validate_maharashtra import MaharashtraValidationFramework


@pytest.fixture
def framework(tmp_path):
    return MaharashtraValidationFramework(reports_dir=tmp_path / "reports")


def test_compute_validation_metrics(framework):
    """Verifies calculation of MAE, RMSE, ubRMSE, Bias, Pearson r."""
    y_true = np.array([0.20, 0.25, 0.30, 0.35])
    # Add constant bias of +0.05
    y_pred = y_true + 0.05

    m = framework.compute_validation_metrics(y_true, y_pred)
    assert m["n_samples"] == 4
    assert abs(m["mae"] - 0.05) < 1e-4
    assert abs(m["rmse"] - 0.05) < 1e-4
    assert abs(m["bias"] - 0.05) < 1e-4
    # Because RMSE == Bias, ubRMSE should be 0.0
    assert abs(m["ubrmse"] - 0.0) < 1e-4
    assert abs(m["pearson_r"] - 1.0) < 1e-4


def test_chronological_splits(framework):
    """Verifies chronological train/val/test partitioning."""
    dates = pd.date_range("2017-01-01", "2023-12-31", freq="D")
    df = pd.DataFrame({
        "date_utc": dates.strftime("%Y-%m-%d"),
        "val": range(len(dates)),
    })
    df_train, df_val, df_test = framework.create_chronological_splits(df)

    assert (df_train["date_utc"] <= "2021-12-31").all()
    assert ((df_val["date_utc"] >= "2022-01-01") & (df_val["date_utc"] <= "2022-12-31")).all()
    assert (df_test["date_utc"] >= "2023-01-01").all()


def test_loso_splits(framework):
    """Verifies Leave-One-Station-Out cross-validation split logic."""
    df = pd.DataFrame({
        "station_id": ["PUNE", "PUNE", "RAHURI", "RAHURI", "BARAMATI"],
        "vwc": [0.2, 0.22, 0.3, 0.31, 0.25],
    })
    splits = framework.create_loso_splits(df)
    assert len(splits) == 3

    for held_out_sid, df_tr, df_te in splits:
        assert (df_te["station_id"] == held_out_sid).all()
        assert held_out_sid not in df_tr["station_id"].values


def test_evaluate_model_hierarchy(framework):
    """Verifies evaluation of full baseline hierarchy."""
    dates_tr = pd.date_range("2020-01-01", periods=100, freq="D").strftime("%Y-%m-%d")
    dates_te = pd.date_range("2021-01-01", periods=30, freq="D").strftime("%Y-%m-%d")

    y_tr = pd.Series([0.25] * 100)
    y_te = pd.Series([0.28] * 30)

    weather_preds = np.full(30, 0.27)
    multimodal_preds = np.full(30, 0.278)

    hierarchy = framework.evaluate_model_hierarchy(
        y_train=y_tr,
        y_test=y_te,
        dates_train=pd.Series(dates_tr),
        dates_test=pd.Series(dates_te),
        weather_preds=weather_preds,
        multimodal_preds=multimodal_preds,
    )

    assert "historical_mean" in hierarchy
    assert "climatology" in hierarchy
    assert "persistence" in hierarchy
    assert "weather_only_xgb" in hierarchy
    assert "full_multimodal_xgb" in hierarchy


def test_generate_validation_protocol_report(framework):
    """Verifies generation of formal validation protocol report."""
    md = framework.generate_validation_protocol_report()
    assert "Maharashtra Scientific Validation Protocol" in md
    assert "Temporal Partitioning" in md
    assert "Leave-One-Station-Out" in md
