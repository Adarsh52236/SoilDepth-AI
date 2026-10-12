"""Pipeline configuration models and YAML parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from soildepth_preprocessing.schema import SchemaDefinition


class IngestionConfig(BaseModel):
    """Configuration for data ingestion and reader handling."""

    format: Literal["auto", "csv", "tsv", "parquet", "json", "jsonl", "excel"] = "auto"
    encoding: str = "utf-8"
    delimiter: str | None = None
    chunk_size: int | None = None
    sheet_name: str | int | None = 0
    compression: str | None = None


class CleaningConfig(BaseModel):
    """Configuration for data quality, cleaning, and sanitization."""

    # Deduplication
    deduplicate: bool = True
    dedup_keys: list[str] | None = None
    dedup_keep: Literal["first", "last", "drop_all"] = "first"
    report_conflicting_duplicates: bool = True

    # Missing value handling
    strip_whitespace: bool = True
    sentinel_null_values: list[Any] = Field(
        default_factory=lambda: [
            -999,
            -9999,
            -9999.0,
            "-999",
            "-9999",
            "NA",
            "N/A",
            "null",
            "NULL",
            "nan",
            "NaN",
            "",
            "None",
            "none",
        ]
    )
    # Target columns must NEVER be automatically imputed
    missing_target_policy: Literal["drop_row", "keep"] = "drop_row"
    missing_id_policy: Literal["drop_row", "keep"] = "drop_row"
    missing_timestamp_policy: Literal["drop_row", "keep"] = "drop_row"
    missing_numeric_policy: Literal["keep", "drop_row", "fill_value", "interpolate"] = "keep"
    missing_numeric_fill_value: float | None = None
    missing_categorical_policy: Literal["keep", "drop_row", "fill_value"] = "keep"
    missing_categorical_fill_value: str = "MISSING"

    # Provenance
    preserve_raw_values: bool = False

    # Outliers and physical limits
    outlier_method: Literal["none", "bounds", "iqr", "zscore"] = "bounds"
    outlier_action: Literal["flag_only", "clip", "drop_row", "nullify"] = "flag_only"
    outlier_iqr_multiplier: float = 1.5
    outlier_zscore_threshold: float = 3.0

    # Geospatial / coordinate sanitization
    validate_coordinates: bool = True
    invalid_coordinate_action: Literal["flag_only", "drop_row", "nullify"] = "drop_row"


class RollingConfig(BaseModel):
    """Configuration for a single rolling window transformation."""

    column: str
    window: int
    agg: Literal["mean", "std", "min", "max", "sum"] = "mean"
    min_periods: int = 1
    new_column_name: str | None = None


class SplitConfig(BaseModel):
    """Configuration for train/validation/test splitting."""

    method: Literal["temporal", "group", "none"] = "none"
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    temporal_column: str = "timestamp_utc"
    group_column: str | None = None
    split_column_name: str = "split"


class TransformationConfig(BaseModel):
    """Configuration for feature engineering and temporal/spatial transformations."""

    normalize_units: bool = True
    timezone: str = "UTC"
    timestamp_format: str | None = None

    # Lags must strictly be positive integers (peering into future is prohibited)
    lags: dict[str, list[int]] | None = None
    rolling_windows: list[RollingConfig] | None = None
    split: SplitConfig = Field(default_factory=SplitConfig)


class ModelReadinessConfig(BaseModel):
    """Configuration for downstream ML safety and data leakage checks."""

    check_target_health: bool = True
    max_target_missing_ratio: float = 0.05
    check_constant_features: bool = True
    variance_threshold: float = 1e-6
    check_id_leakage: bool = True
    check_temporal_leakage: bool = True
    check_split_overlap: bool = True
    check_high_correlation: bool = True
    high_correlation_threshold: float = 0.98


class PipelineConfig(BaseModel):
    """Top-level pipeline configuration."""

    pipeline_name: str = "SoilDepth-AI-Preprocessing"
    pipeline_version: str = "0.1.0"
    adapter: str = "generic_tabular"
    schema_def: SchemaDefinition = Field(
        default_factory=SchemaDefinition,
        alias="schema",
    )
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    cleaning: CleaningConfig = Field(default_factory=CleaningConfig)
    transformations: TransformationConfig = Field(default_factory=TransformationConfig)
    readiness: ModelReadinessConfig = Field(default_factory=ModelReadinessConfig)

    class Config:
        populate_by_name = True


def load_config_from_yaml(config_path: str | Path) -> PipelineConfig:
    """Load and validate a PipelineConfig from a YAML file."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"YAML configuration root must be a mapping, got {type(data).__name__}")

    return PipelineConfig.model_validate(data)


def save_config_to_yaml(config: PipelineConfig, output_path: str | Path) -> None:
    """Export a PipelineConfig instance to a YAML file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(by_alias=True), f, sort_keys=False, indent=2)
