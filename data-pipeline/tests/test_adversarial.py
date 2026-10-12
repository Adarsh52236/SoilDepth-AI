"""Adversarial tests for hardening against invalid conversions, leakage, and data corruption."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from soildepth_preprocessing.cleaning import clean_dataset, convert_units, deduplicate_dataframe
from soildepth_preprocessing.config import (
    CleaningConfig,
    ModelReadinessConfig,
    TransformationConfig,
)
from soildepth_preprocessing.schema import (
    ColumnRole,
    ColumnSpec,
    DataType,
    SchemaDefinition,
)
from soildepth_preprocessing.transformations import (
    apply_transformations,
    generate_lag_features,
)
from soildepth_preprocessing.validation import validate_model_readiness


@pytest.fixture
def adversarial_schema() -> SchemaDefinition:
    return SchemaDefinition(
        name="adversarial_schema",
        columns={
            "station_id": ColumnSpec(
                canonical_name="station_id",
                role=ColumnRole.ID,
                data_type=DataType.STRING,
                required=True,
            ),
            "timestamp_utc": ColumnSpec(
                canonical_name="timestamp_utc",
                role=ColumnRole.TIMESTAMP,
                data_type=DataType.DATETIME,
                required=True,
            ),
            "soil_moisture": ColumnSpec(
                canonical_name="soil_moisture",
                role=ColumnRole.TARGET,
                data_type=DataType.FLOAT,
                required=True,
                min_value=0.0,
                max_value=1.0,
                unit="%",
                target_unit="m3/m3",
                description="Volumetric soil moisture",
            ),
            "clay_pct": ColumnSpec(
                canonical_name="clay_pct",
                role=ColumnRole.FEATURE,
                data_type=DataType.FLOAT,
                required=False,
                min_value=0.0,
                max_value=100.0,
                unit="%",
                target_unit="m3/m3",  # Intentionally erroneous/adversarial config
                description="Soil clay fraction percentage",
            ),
            "air_temperature_c": ColumnSpec(
                canonical_name="air_temperature_c",
                role=ColumnRole.FEATURE,
                data_type=DataType.FLOAT,
                required=False,
                min_value=-50.0,
                max_value=60.0,
                unit="K",
                target_unit="m",  # Incompatible dimensions
                description="Air temperature in Kelvin",
            ),
        },
    )


def test_adversarial_invalid_unit_conversion_rejected(
    adversarial_schema: SchemaDefinition,
) -> None:
    # 1. Attempting to convert clay percentage into volumetric water content (m3/m3)
    df_clay = pd.DataFrame({"clay_pct": [35.0, 40.0]})
    schema_clay = SchemaDefinition(
        name="clay_schema",
        columns={"clay_pct": adversarial_schema.columns["clay_pct"]},
    )
    with pytest.raises(ValueError, match="Semantically invalid unit conversion"):
        convert_units(df_clay, schema_clay)

    # 2. Incompatible physical dimensions (Temperature K to Distance meters)
    df_temp = pd.DataFrame({"air_temperature_c": [293.15, 295.15]})
    schema_temp = SchemaDefinition(
        name="temp_schema",
        columns={"air_temperature_c": adversarial_schema.columns["air_temperature_c"]},
    )
    with pytest.raises(ValueError, match="Dimensionally incompatible"):
        convert_units(df_temp, schema_temp)


def test_adversarial_conflicting_duplicate_observations_detected() -> None:
    # Two sensor transmissions with the same station, time, and depth, but conflicting readings
    df = pd.DataFrame(
        {
            "station_id": ["STN_A", "STN_A", "STN_B"],
            "timestamp_utc": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "depth_m": [0.10, 0.10, 0.10],
            "soil_moisture": [0.15, 0.45, 0.20],  # STN_A has conflicting values!
        }
    )
    config = CleaningConfig(
        deduplicate=True,
        dedup_keys=["station_id", "timestamp_utc", "depth_m"],
        report_conflicting_duplicates=True,
    )
    cleaned_df, audit, dropped = deduplicate_dataframe(df, config)

    # Must detect conflicting duplicate
    assert any(a.action == "conflicting_duplicate_detected" for a in audit)
    assert len(cleaned_df) == 2


def test_adversarial_negative_or_zero_lag_strictly_rejected() -> None:
    df = pd.DataFrame({"val": [1, 2, 3]})
    with pytest.raises(ValueError, match="future-data leakage"):
        generate_lag_features(df, lags_config={"val": [-1]})

    with pytest.raises(ValueError, match="future-data leakage"):
        generate_lag_features(df, lags_config={"val": [-5]})

    with pytest.raises(ValueError, match="positive integers"):
        generate_lag_features(df, lags_config={"val": [0]})


def test_adversarial_target_imputation_prohibited_under_all_policies() -> None:
    schema = SchemaDefinition(
        name="schema",
        columns={
            "soil_moisture": ColumnSpec(
                canonical_name="soil_moisture",
                role=ColumnRole.TARGET,
                data_type=DataType.FLOAT,
            ),
            "temp": ColumnSpec(
                canonical_name="temp",
                role=ColumnRole.FEATURE,
                data_type=DataType.FLOAT,
            ),
        },
    )
    df = pd.DataFrame(
        {
            "soil_moisture": [0.20, np.nan, 0.40],
            "temp": [10.0, np.nan, 30.0],
        }
    )

    # Adversarial config: user asks to interpolate numbers
    config_interpolate = CleaningConfig(
        missing_target_policy="keep",
        missing_numeric_policy="interpolate",
    )
    res = clean_dataset(df, schema, config_interpolate)

    # Feature was interpolated: (10 + 30)/2 = 20
    assert res.data["temp"].iloc[1] == pytest.approx(20.0)
    # Target was NOT interpolated: must remain NaN!
    assert pd.isna(res.data["soil_moisture"].iloc[1])


def test_adversarial_unanchored_null_id_and_timestamp_dropped() -> None:
    schema = SchemaDefinition(
        name="schema",
        columns={
            "station_id": ColumnSpec(
                canonical_name="station_id",
                role=ColumnRole.ID,
                data_type=DataType.STRING,
            ),
            "timestamp_utc": ColumnSpec(
                canonical_name="timestamp_utc",
                role=ColumnRole.TIMESTAMP,
                data_type=DataType.DATETIME,
            ),
            "soil_moisture": ColumnSpec(
                canonical_name="soil_moisture",
                role=ColumnRole.TARGET,
                data_type=DataType.FLOAT,
            ),
        },
    )
    df = pd.DataFrame(
        {
            "station_id": ["S1", np.nan, "S3"],  # S2 has null station_id
            "timestamp_utc": ["2026-01-01", "2026-01-02", np.nan],  # S3 has null timestamp
            "soil_moisture": [0.25, 0.25, 0.25],
        }
    )
    config = CleaningConfig(
        missing_id_policy="drop_row",
        missing_timestamp_policy="drop_row",
    )
    result = clean_dataset(df, schema, config)

    # Only row 0 (S1) is completely anchored
    assert result.final_rows == 1
    assert result.data["station_id"].iloc[0] == "S1"
    assert "missing_id_station_id" in result.dropped_row_reasons
    assert "missing_timestamp_timestamp_utc" in result.dropped_row_reasons


def test_adversarial_temporal_leakage_in_splits_detected() -> None:
    schema = SchemaDefinition(
        name="schema",
        columns={
            "timestamp_utc": ColumnSpec(
                canonical_name="timestamp_utc",
                role=ColumnRole.TIMESTAMP,
                data_type=DataType.DATETIME,
            ),
            "soil_moisture": ColumnSpec(
                canonical_name="soil_moisture",
                role=ColumnRole.TARGET,
                data_type=DataType.FLOAT,
            ),
        },
    )
    # Adversarial split where test set is in 2025 and train set is in 2026
    df = pd.DataFrame(
        {
            "timestamp_utc": ["2026-06-01", "2025-01-01"],
            "soil_moisture": [0.25, 0.30],
            "split": ["train", "test"],
        }
    )
    readiness_res = validate_model_readiness(df, schema, ModelReadinessConfig())
    assert any("temporal_leakage" in w.lower() for w in readiness_res.warnings)


def test_adversarial_out_of_order_time_series_sorted_before_lags() -> None:
    df = pd.DataFrame(
        {
            "timestamp_utc": ["2026-01-03", "2026-01-01", "2026-01-02"],  # Deliberately shuffled
            "val": [30.0, 10.0, 20.0],
        }
    )
    config = TransformationConfig(
        lags={"val": [1]},
    )
    # Transformations sort by timestamp_utc before computing lag
    df_transformed = apply_transformations(df, config, timestamp_col="timestamp_utc")

    # Chronological sequence: 2026-01-01 (val=10), 2026-01-02 (val=20), 2026-01-03 (val=30)
    assert df_transformed["val"].tolist() == [10.0, 20.0, 30.0]
    # Lag 1 of 20 is 10; Lag 1 of 30 is 20
    assert pd.isna(df_transformed["val_lag_1"].iloc[0])
    assert df_transformed["val_lag_1"].iloc[1] == 10.0
    assert df_transformed["val_lag_1"].iloc[2] == 20.0
