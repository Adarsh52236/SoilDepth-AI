"""Base adapter definitions and adapter registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pandas as pd

from soildepth_preprocessing.schema import SchemaDefinition


class BaseDataAdapter(ABC):
    """Abstract base class for source-specific data ingestion adapters."""

    name: ClassVar[str] = "base"
    description: ClassVar[str] = "Base adapter interface"
    is_ground_truth: ClassVar[bool] = False
    data_modality: ClassVar[str] = "tabular"
    raster_supported: ClassVar[bool] = False
    implementation_status: ClassVar[str] = "implemented_tabular"

    def __init__(self, schema: SchemaDefinition | None = None) -> None:
        self.schema = schema or self.get_default_schema()

    @abstractmethod
    def get_default_schema(self) -> SchemaDefinition:
        """Provide standard default schema for this specific source."""
        pass

    @abstractmethod
    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize raw source columns, types, and structure into canonical representations."""
        pass

    def get_metadata(self) -> dict[str, Any]:
        """Return adapter provenance, source semantics, modality and ground-truth status."""
        return {
            "adapter_name": self.name,
            "description": self.description,
            "is_ground_truth": self.is_ground_truth,
            "data_modality": self.data_modality,
            "raster_supported": self.raster_supported,
            "implementation_status": self.implementation_status,
        }


class AdapterRegistry:
    """Central registry for discovering and loading data adapters."""

    _registry: ClassVar[dict[str, type[BaseDataAdapter]]] = {}

    @classmethod
    def register(cls, adapter_cls: type[BaseDataAdapter]) -> type[BaseDataAdapter]:
        """Register an adapter class by its unique name."""
        cls._registry[adapter_cls.name.lower()] = adapter_cls
        return adapter_cls

    @classmethod
    def get(cls, name: str) -> type[BaseDataAdapter]:
        """Retrieve an adapter class by name."""
        name_clean = name.strip().lower()
        if name_clean not in cls._registry:
            valid = sorted(cls._registry.keys())
            raise KeyError(f"Adapter '{name}' not found. Available adapters: {valid}")
        return cls._registry[name_clean]

    @classmethod
    def list_adapters(cls) -> list[str]:
        """List all registered adapter names."""
        return sorted(cls._registry.keys())
