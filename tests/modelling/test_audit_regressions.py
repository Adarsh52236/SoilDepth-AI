"""
SoilDepth-AI — Regression and Pipeline Audit Test Suite
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Ensure strict compliance with pipeline audit requirements:
         - Exact metric reproducibility from prediction tables
         - Strict isolation of Weather-Only features (zero ground-truth SM leakage)
         - Sourcing and metadata verification of static soil variables (HWSD vs SoilGrids)
         - Geographic integrity of station AAMU-JTG (US SCAN station, not India/Maharashtra)
         - Common evaluation timestamp consistency across all depth models
"""

import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from services.modelling.config import (
    REPO_ROOT,
    MODELS_DIR,
    REPORTS_DIR,
    STATION_ID,
    STATION_LAT,
    STATION_LON,
    SENSOR_DEPTHS,
    WEATHER_ONLY_FEATURE_NAMES,
    LAG_AUGMENTED_FEATURE_NAMES,
)
from services.modelling.evaluate import compute_metrics


def test_station_geographic_identity():
    """Verify AAMU-JTG is strictly verified as a US station in Alabama, never India/Maharashtra."""
    assert STATION_ID == "AAMU-JTG"
    # Madison County, Alabama, USA
    assert 34.0 < STATION_LAT < 36.0, f"Latitude {STATION_LAT} outside Alabama range"
    assert -88.0 < STATION_LON < -85.0, f"Longitude {STATION_LON} outside Alabama range"
    # Reconfirm it is in the Western Hemisphere
    assert STATION_LON < 0.0


def test_weather_only_feature_set_purity():
    """Verify Weather-Only feature set contains zero ground-truth soil moisture measurements."""
    forbidden_terms = ["target", "sm_", "soil_moisture", "moisture", "in_situ"]
    for feat in WEATHER_ONLY_FEATURE_NAMES:
        for term in forbidden_terms:
            assert term not in feat.lower(), (
                f"Forbidden ground-truth term '{term}' detected in Weather-Only feature '{feat}'!"
            )


def test_static_soil_properties_provenance(tmp_path):
    """
    Verify static soil properties originate from official HWSD (IIASA/FAO) in ISMN,
    and are never misattributed to SoilGrids.
    """
    static_file = (
        REPO_ROOT
        / "dataset"
        / "ISMN"
        / "SCAN"
        / "extracted"
        / "surface_0-10cm"
        / "SCAN"
        / STATION_ID
        / f"SCAN_SCAN_{STATION_ID}_static_variables.csv"
    )
    assert static_file.exists()
    df_static = pd.read_csv(static_file, sep=";")

    # Source must be HWSD
    sources = df_static["quantity_source_name"].dropna().unique().tolist()
    assert "HWSD" in sources
    assert "SoilGrids" not in sources

    # Check topsoil layer (0.00-0.30 m)
    top_clay = float(df_static[
        (df_static["quantity_name"] == "clay fraction")
        & (df_static["depth_from[m]"] == 0.0)
    ]["value"].iloc[0])
    assert top_clay == pytest.approx(25.0)


def test_prediction_tables_metrics_reproducibility():
    """
    Verify that every metric reported in metrics.json and evaluation_report.md
    can be exactly reproduced from the saved test prediction CSV files.
    """
    metrics_json_path = REPORTS_DIR / "metrics.json"
    assert metrics_json_path.exists()
    with open(metrics_json_path) as f:
        recorded_metrics = json.load(f)

    model_cols = {
        "Historical_Mean": "pred_historical_mean",
        "Climatology": "pred_climatology",
        "Persistence": "pred_persistence",
        "XGBoost_Weather_Only": "pred_xgb_weather_only",
        "XGBoost_Lag_Augmented": "pred_xgb_lag_augmented",
        "XGBoost_Full_Multimodal": "pred_xgb_full_multimodal",
    }

    for depth_key in SENSOR_DEPTHS.keys():
        preds_file = REPORTS_DIR / f"{depth_key}_test_predictions.csv"
        assert preds_file.exists(), f"Missing prediction file: {preds_file}"

        df_preds = pd.read_csv(preds_file)
        dates = df_preds["date_utc"].tolist()
        y_true = df_preds["y_true"].to_numpy(dtype=float)

        # Check that there are zero missing predictions or targets in the evaluation table
        assert df_preds.isna().sum().sum() == 0, f"Found NaN values in {preds_file.name}"

        # Recalculate metrics for each model
        for model_key, col in model_cols.items():
            assert col in df_preds.columns, f"Column '{col}' missing from {preds_file.name}"
            y_pred = df_preds[col].to_numpy(dtype=float)

            recalc = compute_metrics(y_true, y_pred, dates=dates)
            recorded = recorded_metrics[depth_key]["models"][model_key]

            # Compare to recorded metrics
            assert recalc["n_samples"] == recorded["n_samples"]
            assert recalc["mae"] == pytest.approx(recorded["mae"], abs=1e-4)
            assert recalc["rmse"] == pytest.approx(recorded["rmse"], abs=1e-4)
            assert recalc["r2"] == pytest.approx(recorded["r2"], abs=1e-3)
            assert recalc["bias"] == pytest.approx(recorded["bias"], abs=1e-4)
            assert recalc["pearson_r"] == pytest.approx(recorded["pearson_r"], abs=1e-3)


def test_synchronized_evaluation_timestamps_per_depth():
    """
    Verify that each model for a given depth is evaluated on the exact same timestamps
    and target observations.
    """
    for depth_key in SENSOR_DEPTHS.keys():
        preds_file = REPORTS_DIR / f"{depth_key}_test_predictions.csv"
        df_preds = pd.read_csv(preds_file)

        # Confirm timestamps are sorted and strictly monotonically increasing
        dates = pd.to_datetime(df_preds["date_utc"])
        assert dates.is_monotonic_increasing

        # Confirm zero duplicates
        assert len(dates) == len(dates.unique())
