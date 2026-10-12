"""SoilDepth-AI Data Preprocessing Pipeline.

A reusable, auditable, and scientifically robust data preprocessing framework
for soil moisture estimation and environmental data integration.
"""

from __future__ import annotations

from soildepth_preprocessing.adapters import AdapterRegistry, BaseDataAdapter
from soildepth_preprocessing.cleaning import CleaningResult, clean_dataset
from soildepth_preprocessing.config import (
    CleaningConfig,
    IngestionConfig,
    ModelReadinessConfig,
    PipelineConfig,
    TransformationConfig,
    load_config_from_yaml,
)
from soildepth_preprocessing.pipeline import PipelineResult, PreprocessingPipeline
from soildepth_preprocessing.quality_report import QualityReport, generate_quality_report
from soildepth_preprocessing.readers import read_tabular, read_tabular_chunks
from soildepth_preprocessing.schema import ColumnRole, ColumnSpec, DataType, SchemaDefinition
from soildepth_preprocessing.transformations import (
    LearnedStandardScaler,
    apply_transformations,
    generate_lag_features,
    generate_rolling_features,
    split_dataset,
)
from soildepth_preprocessing.validation import (
    ValidationResult,
    validate_model_readiness,
    validate_schema,
)

__version__ = "0.1.0"

__all__ = [
    "AdapterRegistry",
    "BaseDataAdapter",
    "CleaningConfig",
    "CleaningResult",
    "ColumnRole",
    "ColumnSpec",
    "DataType",
    "IngestionConfig",
    "LearnedStandardScaler",
    "ModelReadinessConfig",
    "PipelineConfig",
    "PipelineResult",
    "PreprocessingPipeline",
    "QualityReport",
    "SchemaDefinition",
    "TransformationConfig",
    "ValidationResult",
    "apply_transformations",
    "clean_dataset",
    "generate_lag_features",
    "generate_quality_report",
    "generate_rolling_features",
    "load_config_from_yaml",
    "read_tabular",
    "read_tabular_chunks",
    "split_dataset",
    "validate_model_readiness",
    "validate_schema",
]
