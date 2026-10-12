"""Schema definitions and column role specifications for SoilDepth-AI preprocessing."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ColumnRole(StrEnum):
    """Semantic role of a column within the SoilDepth-AI dataset."""

    ID = "id"  # Identifier (e.g. station_id, plot_id, sensor_id)
    TIMESTAMP = "timestamp"  # Temporal coordinate (e.g. timestamp_utc)
    LATITUDE = "latitude"  # Spatial latitude coordinate [-90, +90]
    LONGITUDE = "longitude"  # Spatial longitude coordinate [-180, +180]
    DEPTH = "depth"  # Sensor/measurement depth (e.g. depth_m >= 0)
    TARGET = "target"  # Downstream ML target label (e.g. soil_moisture_m3m3)
    FEATURE = "feature"  # Predictive feature / covariate
    METADATA = "metadata"  # Auxiliary info, flags, or data provenance


class DataType(StrEnum):
    """Supported canonical data types."""

    FLOAT = "float"
    INT = "int"
    STRING = "string"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    CATEGORY = "category"


class ColumnSpec(BaseModel):
    """Specification and scientific constraints for a single canonical column."""

    canonical_name: str
    source_names: list[str] = Field(
        default_factory=list,
        description="Possible names or aliases in the raw dataset mapping to this column.",
    )
    role: ColumnRole
    data_type: DataType
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: list[Any] | None = None
    unit: str | None = None
    target_unit: str | None = None
    description: str | None = None

    @field_validator("source_names", mode="after")
    @classmethod
    def ensure_canonical_in_source_names(cls, v: list[str], info: Any) -> list[str]:
        # Always allow the canonical name itself as a source name
        return v


class SchemaDefinition(BaseModel):
    """Declarative schema defining expected columns, constraints and semantic roles."""

    name: str = "generic_soil_moisture_schema"
    version: str = "1.0.0"
    description: str = "Standard schema for soil moisture and environmental covariates."
    columns: dict[str, ColumnSpec] = Field(default_factory=dict)

    def find_column_by_source_name(self, raw_name: str) -> ColumnSpec | None:
        """Find a ColumnSpec matching a given raw column name (case-insensitive)."""
        raw_clean = raw_name.strip().lower()
        for col_name, spec in self.columns.items():
            if col_name.lower() == raw_clean:
                return spec
            for alias in spec.source_names:
                if alias.strip().lower() == raw_clean:
                    return spec
        return None

    def get_columns_by_role(self, role: ColumnRole) -> list[ColumnSpec]:
        """Retrieve all columns assigned to a specific role."""
        return [col for col in self.columns.values() if col.role == role]

    def canonical_mapping(self) -> dict[str, str]:
        """Generate a mapping from all source aliases to canonical names."""
        mapping: dict[str, str] = {}
        for canonical, spec in self.columns.items():
            mapping[canonical] = canonical
            for alias in spec.source_names:
                mapping[alias] = canonical
        return mapping

    def required_columns(self) -> list[str]:
        """List all required canonical column names."""
        return [col for col, spec in self.columns.items() if spec.required]

    def target_columns(self) -> list[str]:
        """List all canonical columns designated as ML targets."""
        return [col for col, spec in self.columns.items() if spec.role == ColumnRole.TARGET]

    def id_columns(self) -> list[str]:
        """List all canonical columns designated as identifiers."""
        return [col for col, spec in self.columns.items() if spec.role == ColumnRole.ID]
