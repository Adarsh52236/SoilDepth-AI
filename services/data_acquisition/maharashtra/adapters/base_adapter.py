"""
SoilDepth-AI — Base Environmental Data Adapter
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Abstract interface and shared utilities for all modality-specific data adapters.
"""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd


class BaseEnvironmentalAdapter(ABC):
    """Abstract base class for modular environmental data adapters."""

    def __init__(self, name: str, source: str, raw_dir: Path):
        self.name = name
        self.source = source
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.retrieval_metadata: Dict[str, Any] = {}

    @abstractmethod
    def acquire(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetches raw environmental data and saves original response files."""
        pass

    @abstractmethod
    def extract_features(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Parses raw files into standardized feature columns without target leakage."""
        pass

    @abstractmethod
    def validate_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Applies schema, coordinate, range, and physical consistency validations."""
        pass

    @staticmethod
    def compute_sha256(filepath: Union[str, Path]) -> str:
        """Calculates SHA-256 hash of an immutable local file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def create_manifest_record(
        self,
        filepath: Path,
        spatial_resolution: str,
        temporal_resolution: str,
        units: str,
        crs: str,
        status: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Creates a standardized manifest entry for immutable audit tracking."""
        return {
            "adapter": self.name,
            "source": self.source,
            "filename": filepath.name,
            "relative_path": str(filepath.relative_to(filepath.parents[4])),
            "size_bytes": filepath.stat().st_size if filepath.exists() else 0,
            "sha256": self.compute_sha256(filepath) if filepath.exists() else "UNAVAILABLE",
            "spatial_resolution": spatial_resolution,
            "temporal_resolution": temporal_resolution,
            "units": units,
            "coordinate_reference_system": crs,
            "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "notes": notes,
        }

