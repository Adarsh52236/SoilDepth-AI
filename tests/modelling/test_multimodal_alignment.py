"""
SoilDepth-AI — Tests for Multimodal Alignment (ERA5-Land + ISMN + SMAP L3 + SoilGrids)
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from services.modelling.config import (
    STATION_ID,
    SENSOR_DEPTHS,
    TRAIN_START_DATE,
    TRAIN_END_DATE,
    VAL_START_DATE,
    VAL_END_DATE,
    TEST_START_DATE,
    TEST_END_DATE,
    SOILGRIDS_EDAPHIC_FEATURES,
    SMAP_TIME_SERIES_FEATURES,
    MULTIMODAL_FEATURE_NAMES,
)
from services.modelling.dataset_builder import (
    build_aligned_pilot_dataset,
    parse_static_soil_properties,
    parse_soilgrids_static_properties,
)
from services.modelling.feature_engineering import (
    build_weather_features,
    build_smap_features,
    prepare_depth_modeling_dataset,
    partition_chronological_splits,
    generate_all_processed_datasets,
)


def test_multimodal_interim_alignment():
    """Verify aligned interim dataset contains both SMAP time-varying and ISMN targets."""
    df_aligned, audit = build_aligned_pilot_dataset(include_smap=True, include_soilgrids=True)

    assert len(df_aligned) == 3287
    assert df_aligned["station_id"].iloc[0] == STATION_ID

    # Verify SMAP columns merged properly
    assert "smap_sm_daily_mean_m3_m3" in df_aligned.columns
    assert "smap_has_valid_retrieval" in df_aligned.columns
    assert "smap_retrieval_status" in df_aligned.columns

    # Verify ISMN targets exist and are within physical bounds
    for depth_key in SENSOR_DEPTHS.keys():
        target_col = f"target_{depth_key}"
        assert target_col in df_aligned.columns
        valid_targets = df_aligned[target_col].dropna()
        assert (valid_targets >= 0.0).all()
        assert (valid_targets <= 0.60).all()

    # Verify audit contains SMAP and SoilGrids sections
    assert "smap_alignment_audit" in audit
    assert "soilgrids_static_properties" in audit
    assert audit["smap_alignment_audit"]["smap_valid_days_count"] == 1866


def test_depth_matched_soilgrids_static_properties():
    """Verify each sensor depth receives its corresponding depth-matched SoilGrids layer."""
    soilgrids_props = parse_soilgrids_static_properties()
    assert len(soilgrids_props) == 4

    # Verify known layers
    assert "0_5cm" in soilgrids_props
    assert "5_15cm" in soilgrids_props
    assert "15_30cm" in soilgrids_props
    assert "30_60cm" in soilgrids_props

    # Verify properties at surface 0-5cm: Clay=24.7%, BD=1.30
    assert soilgrids_props["0_5cm"]["soilgrids_clay_pct"] == pytest.approx(24.7)
    assert soilgrids_props["0_5cm"]["soilgrids_bdod_g_cm3"] == pytest.approx(1.30)

    # Verify properties at deep 30-60cm: Clay=33.9%, BD=1.58
    assert soilgrids_props["30_60cm"]["soilgrids_clay_pct"] == pytest.approx(33.9)
    assert soilgrids_props["30_60cm"]["soilgrids_bdod_g_cm3"] == pytest.approx(1.58)


def test_no_smap_future_leakage():
    """
    CRITICAL TEMPORAL LEAKAGE TEST FOR SATELLITE FEATURES:
    Altering SMAP observations at future days (t >= cutoff) MUST NOT alter
    any lagged or rolling SMAP features at day t-1 or earlier.
    """
    n_days = 60
    dates = pd.date_range("2015-04-01", periods=n_days, freq="D").strftime("%Y-%m-%d")

    np.random.seed(42)
    sample_sm = np.random.uniform(0.15, 0.40, n_days)
    sample_valid = np.random.choice([True, False], size=n_days, p=[0.6, 0.4])

    df_base = pd.DataFrame({
        "date_utc": dates,
        "smap_sm_daily_mean_m3_m3": sample_sm,
        "smap_has_valid_retrieval": sample_valid,
    })

    feats_base = build_smap_features(df_base)

    # Create perturbed future data starting at day 30
    cutoff_day = 30
    df_perturbed = df_base.copy()
    df_perturbed.loc[cutoff_day:, "smap_sm_daily_mean_m3_m3"] = 0.58
    df_perturbed.loc[cutoff_day:, "smap_has_valid_retrieval"] = True

    feats_perturbed = build_smap_features(df_perturbed)

    # Check that for all days 0..29, features are strictly identical
    smap_cols_to_check = [
        "smap_sm_lag_1d",
        "smap_sm_roll_mean_3d",
        "smap_sm_roll_mean_7d",
        "smap_days_since_valid_retrieval",
    ]

    for col in smap_cols_to_check:
        base_slice = feats_base.loc[: cutoff_day - 1, col].values
        pert_slice = feats_perturbed.loc[: cutoff_day - 1, col].values
        np.testing.assert_allclose(
            base_slice,
            pert_slice,
            rtol=1e-7,
            atol=1e-7,
            err_msg=f"Future temporal leakage detected in SMAP feature '{col}' at or before day {cutoff_day}!",
        )


def test_smap_is_input_feature_never_ground_truth_target():
    """Verify that target columns strictly come from ISMN in-situ ground probes, not SMAP."""
    datasets = generate_all_processed_datasets()

    for depth_key, df_d in datasets.items():
        assert "target" in df_d.columns
        assert "smap_sm_daily_mean_m3_m3" in df_d.columns

        # Target column is target_<depth_key> (from ISMN SCAN)
        # Verify target is NOT identical to SMAP
        valid_both = df_d.dropna(subset=["target", "smap_sm_daily_mean_m3_m3"])
        assert len(valid_both) > 1000

        # Correlation between satellite surface and deep ground probe (50cm) must reflect physical lag, not identity
        if depth_key == "sm_50cm":
            corr = np.corrcoef(valid_both["target"], valid_both["smap_sm_daily_mean_m3_m3"])[0, 1]
            assert corr < 0.85, "Suspiciously high correlation: SMAP may be masquerading as deep ground truth!"


def test_multimodal_chronological_splits():
    """Verify multimodal dataset supports strict train/val/test splits without leakage."""
    datasets = generate_all_processed_datasets()
    df_5cm = datasets["sm_5cm"]

    train, val, test = partition_chronological_splits(df_5cm)

    assert train["date_utc"].max() == TRAIN_END_DATE
    assert val["date_utc"].min() == VAL_START_DATE
    assert val["date_utc"].max() == VAL_END_DATE
    assert test["date_utc"].min() == TEST_START_DATE
    assert test["date_utc"].max() == TEST_END_DATE

    assert len(set(train["date_utc"]).intersection(set(val["date_utc"]))) == 0
    assert len(set(val["date_utc"]).intersection(set(test["date_utc"]))) == 0
    assert len(set(train["date_utc"]).intersection(set(test["date_utc"]))) == 0

