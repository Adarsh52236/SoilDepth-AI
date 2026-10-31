"""
SoilDepth-AI — Tests for Evaluation & Metrics Suite
"""

import pytest
import numpy as np

from services.modelling.evaluate import compute_metrics, format_metrics_markdown_table


def test_compute_metrics_perfect_prediction():
    """Verify metrics on identical true and predicted vectors."""
    y = np.array([0.20, 0.25, 0.30, 0.35, 0.40])
    metrics = compute_metrics(y, y)

    assert metrics["n_samples"] == 5
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["r2"] == 1.0
    assert metrics["bias"] == 0.0
    assert metrics["pearson_r"] == 1.0


def test_compute_metrics_constant_bias():
    """Verify metrics when predictions have a known constant bias offset."""
    y_true = np.array([0.10, 0.20, 0.30, 0.40])
    # Constant offset of +0.05
    y_pred = y_true + 0.05
    metrics = compute_metrics(y_true, y_pred)

    assert metrics["n_samples"] == 4
    assert metrics["mae"] == pytest.approx(0.05, abs=1e-5)
    assert metrics["rmse"] == pytest.approx(0.05, abs=1e-5)
    assert metrics["bias"] == pytest.approx(0.05, abs=1e-5)
    # Correlation must still be perfectly 1.0 under linear shift
    assert metrics["pearson_r"] == pytest.approx(1.0, abs=1e-4)


def test_compute_metrics_masks_nans():
    """Verify compute_metrics ignores NaN pairs cleanly."""
    y_true = np.array([0.20, np.nan, 0.30, 0.40, 0.50])
    y_pred = np.array([0.22, 0.25, np.nan, 0.38, 0.48])
    dates = ["2022-01-01", "2022-01-02", "2022-01-03", "2022-01-04", "2022-01-05"]

    metrics = compute_metrics(y_true, y_pred, dates=dates)

    # Valid indices: 0 (2022-01-01), 3 (2022-01-04), 4 (2022-01-05) -> 3 valid samples
    assert metrics["n_samples"] == 3
    assert metrics["n_excluded"] == 2
    assert metrics["start_date"] == "2022-01-01"
    assert metrics["end_date"] == "2022-01-05"


def test_compute_metrics_empty_or_all_nan():
    """Verify edge case where no valid pairs exist."""
    y_true = np.array([np.nan, np.nan])
    y_pred = np.array([0.20, 0.30])
    metrics = compute_metrics(y_true, y_pred)

    assert metrics["n_samples"] == 0
    assert metrics["mae"] is None
    assert metrics["rmse"] is None
    assert metrics["r2"] is None


def test_format_metrics_markdown_table():
    """Verify markdown table formatter outputs valid markdown syntax."""
    sample_res = {
        "m1": {
            "depth": "sm_5cm",
            "config": "Test Model",
            "n_samples": 100,
            "mae": 0.025,
            "rmse": 0.035,
            "r2": 0.85,
            "bias": 0.001,
            "pearson_r": 0.92,
            "start_date": "2022-01-01",
            "end_date": "2023-12-31",
        }
    }
    table = format_metrics_markdown_table(sample_res)
    assert "| Depth | Model Configuration |" in table
    assert "sm_5cm" in table
    assert "0.0250" in table
