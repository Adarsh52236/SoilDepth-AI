"""Unit tests for sanitization, deduplication, outlier handling, and target protection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from soildepth_preprocessing.cleaning import (
    clean_dataset,
    convert_units,
    deduplicate_dataframe,
    detect_and_handle_outliers,
    handle_missing_values,
    strip_text_and_replace_sentinels,
    validate_and_clean_coordinates,
)
from soildepth_preprocessing.config import CleaningConfig
from soildepth_preprocessing.schema import (
    ColumnRole,
    ColumnSpec,
    DataType,
    SchemaDefinition,
)


@pytest.fixture
def mock_schema() -> SchemaDefinition:
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
            "latitude": ColumnSpec(
                canonical_name="latitude",
                role=ColumnRole.LATITUDE,
                data_type=DataType.FLOAT,
                required=True,
                min_value=-90.0,
                max_value=90.0,
            ),
            "longitude": ColumnSpec(
                canonical_name="longitude",
                role=ColumnRole.LONGITUDE,
                data_type=DataType.FLOAT,
                required=True,
                min_value=-180.0,
                max_value=180.0,
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
            ),
            "air_temperature_c": ColumnSpec(
                canonical_name="air_temperature_c",
                role=ColumnRole.FEATURE,
                data_type=DataType.FLOAT,
                required=False,
                min_value=-50.0,
                max_value=60.0,
                unit="K",
                target_unit="degC",
            ),
        },
    )


def test_sentinel_replacement_and_whitespace_stripping() -> None:
    df = pd.DataFrame(
        {
            "station_id": [" S1 ", "S2  ", "   "],
            "soil_moisture": [0.25, -999, -9999.0],
            "category": ["A", "NA", "null"],
        }
    )
    config = CleaningConfig()
    cleaned_df, audit = strip_text_and_replace_sentinels(df, config)

    assert cleaned_df["station_id"].iloc[0] == "S1"
    assert cleaned_df["station_id"].iloc[1] == "S2"
    assert pd.isna(cleaned_df["station_id"].iloc[2])  # whitespace-only became NaN
    assert pd.isna(cleaned_df["soil_moisture"].iloc[1])  # -999 became NaN
    assert pd.isna(cleaned_df["soil_moisture"].iloc[2])  # -9999.0 became NaN
    assert pd.isna(cleaned_df["category"].iloc[1])  # "NA" became NaN
    assert pd.isna(cleaned_df["category"].iloc[2])  # "null" became NaN
    assert len(audit) > 0


def test_deduplication() -> None:
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S1", "S2"],
            "timestamp_utc": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "soil_moisture": [0.25, 0.25, 0.30],
        }
    )
    config = CleaningConfig(deduplicate=True, dedup_keys=["station_id", "timestamp_utc"])
    dedup_df, audit, dropped_cnt = deduplicate_dataframe(df, config)

    assert len(dedup_df) == 2
    assert dropped_cnt == 1
    assert len(audit) == 1


def test_coordinate_validation(mock_schema: SchemaDefinition) -> None:
    df = pd.DataFrame(
        {
            "latitude": [45.0, 95.0, -91.0],  # 95.0 and -91.0 invalid
            "longitude": [10.0, 20.0, 200.0],  # 200.0 invalid
        }
    )
    config = CleaningConfig(validate_coordinates=True, invalid_coordinate_action="drop_row")
    cleaned_df, audit, dropped_cnt = validate_and_clean_coordinates(df, mock_schema, config)

    assert len(cleaned_df) == 1  # Only first row valid
    assert dropped_cnt == 2


def test_unit_conversion(mock_schema: SchemaDefinition) -> None:
    df = pd.DataFrame(
        {
            "soil_moisture": [25.0, 30.0],  # Given in %, target is m3/m3
            "air_temperature_c": [293.15, 300.15],  # Given in K, target is degC
        }
    )
    converted_df, audit = convert_units(df, mock_schema)

    assert converted_df["soil_moisture"].iloc[0] == pytest.approx(0.25)
    assert converted_df["soil_moisture"].iloc[1] == pytest.approx(0.30)
    assert converted_df["air_temperature_c"].iloc[0] == pytest.approx(20.0)
    assert converted_df["air_temperature_c"].iloc[1] == pytest.approx(27.0)
    assert len(audit) == 2


def test_never_impute_missing_target_labels(mock_schema: SchemaDefinition) -> None:
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S2", "S3"],
            "soil_moisture": [0.25, np.nan, 0.35],
            "air_temperature_c": [20.0, np.nan, 22.0],
        }
    )

    # Test Policy 1: drop_row
    config_drop = CleaningConfig(
        missing_target_policy="drop_row",
        missing_numeric_policy="fill_value",
        missing_numeric_fill_value=0.0,
    )
    df_dropped, audit, dropped_reasons = handle_missing_values(df, mock_schema, config_drop)

    # The missing target row must be dropped
    assert len(df_dropped) == 2
    assert "missing_target_soil_moisture" in dropped_reasons
    assert df_dropped["station_id"].tolist() == ["S1", "S3"]

    # Test Policy 2: keep (preserved as NaN, NEVER filled with mean/constant)
    config_keep = CleaningConfig(
        missing_target_policy="keep",
        missing_numeric_policy="fill_value",
        missing_numeric_fill_value=999.0,
    )
    df_kept, audit2, _ = handle_missing_values(df, mock_schema, config_keep)
    assert len(df_kept) == 3
    # Target value MUST remain NaN despite missing_numeric_fill_value being set
    assert pd.isna(df_kept["soil_moisture"].iloc[1])
    # But non-target feature is filled per feature policy
    assert df_kept["air_temperature_c"].iloc[1] == 999.0


def test_outlier_detection_flag_and_clip(mock_schema: SchemaDefinition) -> None:
    df = pd.DataFrame(
        {
            "soil_moisture": [0.20, 1.50, -0.10],  # 1.50 and -0.10 violate [0.0, 1.0] bounds
            "air_temperature_c": [20.0, 25.0, 30.0],
        }
    )

    # Flag only (default)
    config_flag = CleaningConfig(outlier_method="bounds", outlier_action="flag_only")
    df_flagged, audit, dropped = detect_and_handle_outliers(df, mock_schema, config_flag)
    assert "is_outlier_soil_moisture" in df_flagged.columns
    assert df_flagged["is_outlier_soil_moisture"].tolist() == [False, True, True]

    # Clip
    config_clip = CleaningConfig(outlier_method="bounds", outlier_action="clip")
    df_clipped, audit2, dropped2 = detect_and_handle_outliers(df, mock_schema, config_clip)
    assert df_clipped["soil_moisture"].iloc[1] == pytest.approx(1.0)
    assert df_clipped["soil_moisture"].iloc[2] == pytest.approx(0.0)


def test_clean_dataset_end_to_end(mock_schema: SchemaDefinition) -> None:
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S1", "S2", "S3"],  # S1 duplicate
            "timestamp_utc": ["2026-01-01", "2026-01-01", "2026-01-01", "2026-01-01"],
            "latitude": [45.0, 45.0, 120.0, 45.0],  # 120.0 invalid latitude
            "longitude": [9.0, 9.0, 9.0, 9.0],
            "soil_moisture": [20.0, 20.0, 30.0, -999.0],  # -999 is sentinel
            "air_temperature_c": [293.15, 293.15, 295.15, 290.15],
        }
    )
    config = CleaningConfig(
        deduplicate=True,
        dedup_keys=["station_id", "timestamp_utc"],
        validate_coordinates=True,
        invalid_coordinate_action="drop_row",
        missing_target_policy="drop_row",
    )
    result = clean_dataset(df, mock_schema, config)

    # 4 initial rows:
    # - 1 duplicate dropped (S1)
    # - 1 invalid coordinate dropped (S2: lat 120)
    # - 1 sentinel target dropped (S3: -999 -> NaN -> dropped target)
    # Exactly 1 row should remain
    assert result.initial_rows == 4
    assert result.final_rows == 1
    assert len(result.data) == 1
    assert result.data["station_id"].iloc[0] == "S1"
    assert result.data["soil_moisture"].iloc[0] == pytest.approx(0.20)
    assert len(result.audit_trail) > 0
