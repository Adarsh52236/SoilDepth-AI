"""Unit tests for schema validation and model-readiness verification."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from soildepth_preprocessing.config import ModelReadinessConfig
from soildepth_preprocessing.schema import (
    ColumnRole,
    ColumnSpec,
    DataType,
    SchemaDefinition,
)
from soildepth_preprocessing.validation import validate_model_readiness, validate_schema


@pytest.fixture
def standard_schema() -> SchemaDefinition:
    return SchemaDefinition(
        name="test_schema",
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
            ),
            "air_temperature_c": ColumnSpec(
                canonical_name="air_temperature_c",
                role=ColumnRole.FEATURE,
                data_type=DataType.FLOAT,
                required=False,
                min_value=-50.0,
                max_value=60.0,
            ),
        },
    )


def test_schema_missing_required_column(standard_schema: SchemaDefinition) -> None:
    df = pd.DataFrame(
        {
            "timestamp_utc": ["2026-01-01"],
            "soil_moisture": [0.25],
        }
    )
    # station_id is required but missing
    result = validate_schema(df, standard_schema)
    assert not result.is_valid
    assert any("station_id" in err for err in result.errors)


def test_schema_physical_bound_violations(standard_schema: SchemaDefinition) -> None:
    df = pd.DataFrame(
        {
            "station_id": ["S1"],
            "timestamp_utc": ["2026-01-01"],
            "soil_moisture": [1.5],  # exceeds max 1.0
            "air_temperature_c": [-75.0],  # below min -50.0
        }
    )
    result = validate_schema(df, standard_schema)
    assert any("soil_moisture" in w for w in result.warnings)
    assert any("air_temperature_c" in w for w in result.warnings)


def test_model_readiness_target_health(standard_schema: SchemaDefinition) -> None:
    config = ModelReadinessConfig()

    # 1. Missing target column entirely
    df_no_target = pd.DataFrame({"station_id": ["S1"], "air_temp": [20.0]})
    res_no_target = validate_model_readiness(df_no_target, standard_schema, config)
    assert not res_no_target.is_valid
    assert any("Target column 'soil_moisture' is missing" in err for err in res_no_target.errors)

    # 2. Entirely null target
    df_null_target = pd.DataFrame(
        {
            "station_id": ["S1", "S2"],
            "soil_moisture": [np.nan, np.nan],
        }
    )
    res_null_target = validate_model_readiness(df_null_target, standard_schema, config)
    assert not res_null_target.is_valid
    assert any("entirely null" in err for err in res_null_target.errors)


def test_model_readiness_constant_feature(standard_schema: SchemaDefinition) -> None:
    config = ModelReadinessConfig()
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S2", "S3", "S4"],
            "soil_moisture": [0.2, 0.3, 0.25, 0.35],
            "air_temperature_c": [20.0, 20.0, 20.0, 20.0],  # Variance = 0
        }
    )
    res = validate_model_readiness(df, standard_schema, config)
    assert any("air_temperature_c" in w and "near-zero variance" in w for w in res.warnings)


def test_model_readiness_identifier_leakage() -> None:
    # A schema where a column is assigned both ID and FEATURE roles
    bad_schema = SchemaDefinition(
        name="bad_schema",
        columns={
            "station_id": ColumnSpec(
                canonical_name="station_id",
                role=ColumnRole.ID,
                data_type=DataType.STRING,
            ),
            "station_feature": ColumnSpec(
                canonical_name="station_id",
                role=ColumnRole.FEATURE,
                data_type=DataType.STRING,
            ),
        },
    )
    df = pd.DataFrame({"station_id": ["S1", "S2"]})
    res = validate_model_readiness(df, bad_schema, ModelReadinessConfig())
    assert not res.is_valid
    assert any("identifier_leakage" in err.lower() for err in res.errors)


def test_model_readiness_temporal_leakage_across_splits(standard_schema: SchemaDefinition) -> None:
    config = ModelReadinessConfig(check_temporal_leakage=True)
    # Test split has an observation timestamp BEFORE train split
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S1"],
            "soil_moisture": [0.2, 0.3],
            "timestamp_utc": ["2026-06-01", "2026-01-01"],
            "split": ["train", "test"],  # Train is June, Test is Jan (future in train!)
        }
    )
    res = validate_model_readiness(df, standard_schema, config)
    assert any("temporal_leakage" in w.lower() for w in res.warnings)


def test_model_readiness_split_entity_overlap(standard_schema: SchemaDefinition) -> None:
    config = ModelReadinessConfig(check_split_overlap=True)
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S1", "S2"],
            "soil_moisture": [0.2, 0.3, 0.25],
            "timestamp_utc": ["2026-01-01", "2026-01-02", "2026-01-01"],
            "split": ["train", "test", "test"],  # S1 appears in both train and test!
        }
    )
    res = validate_model_readiness(df, standard_schema, config)
    assert any("split_entity_overlap" in w.lower() for w in res.warnings)
