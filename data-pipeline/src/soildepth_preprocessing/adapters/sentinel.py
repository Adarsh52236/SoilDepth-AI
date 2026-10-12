"""Sentinel-1 SAR and Sentinel-2 Multi-Spectral satellite data adapter."""

from __future__ import annotations

from typing import ClassVar

import pandas as pd

from soildepth_preprocessing.adapters.base import AdapterRegistry, BaseDataAdapter
from soildepth_preprocessing.schema import (
    ColumnRole,
    ColumnSpec,
    DataType,
    SchemaDefinition,
)


@AdapterRegistry.register
class SentinelAdapter(BaseDataAdapter):
    """Adapter for Copernicus Sentinel-1 C-band SAR and Sentinel-2 Optical observations.

    Handles radar backscatter coefficients (sigma0 VV/VH) and optical vegetation indices.
    """

    name: ClassVar[str] = "sentinel"
    description: ClassVar[str] = "Copernicus Sentinel-1 SAR and Sentinel-2 Optical features"
    is_ground_truth: ClassVar[bool] = False

    def get_default_schema(self) -> SchemaDefinition:
        """Construct canonical Sentinel schema."""
        return SchemaDefinition(
            name="sentinel_satellite_schema",
            version="1.0.0",
            description="Satellite radar backscatter and optical spectral indices.",
            columns={
                "tile_id": ColumnSpec(
                    canonical_name="tile_id",
                    source_names=["granule_id", "scene_id", "tile"],
                    role=ColumnRole.ID,
                    data_type=DataType.STRING,
                    required=False,
                ),
                "timestamp_utc": ColumnSpec(
                    canonical_name="timestamp_utc",
                    source_names=["acquisition_time", "datetime", "timestamp"],
                    role=ColumnRole.TIMESTAMP,
                    data_type=DataType.DATETIME,
                    required=True,
                ),
                "latitude": ColumnSpec(
                    canonical_name="latitude",
                    source_names=["lat"],
                    role=ColumnRole.LATITUDE,
                    data_type=DataType.FLOAT,
                    required=True,
                    min_value=-90.0,
                    max_value=90.0,
                ),
                "longitude": ColumnSpec(
                    canonical_name="longitude",
                    source_names=["lon"],
                    role=ColumnRole.LONGITUDE,
                    data_type=DataType.FLOAT,
                    required=True,
                    min_value=-180.0,
                    max_value=180.0,
                ),
                "s1_vv_db": ColumnSpec(
                    canonical_name="s1_vv_db",
                    source_names=["vv", "sigma0_vv", "s1_vv"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=-35.0,
                    max_value=5.0,
                    unit="dB",
                    target_unit="dB",
                ),
                "s1_vh_db": ColumnSpec(
                    canonical_name="s1_vh_db",
                    source_names=["vh", "sigma0_vh", "s1_vh"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=-45.0,
                    max_value=0.0,
                    unit="dB",
                    target_unit="dB",
                ),
                "s2_ndvi": ColumnSpec(
                    canonical_name="s2_ndvi",
                    source_names=["ndvi", "normalized_difference_vegetation_index"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=-1.0,
                    max_value=1.0,
                ),
                "s2_ndwi": ColumnSpec(
                    canonical_name="s2_ndwi",
                    source_names=["ndwi"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=-1.0,
                    max_value=1.0,
                ),
                "cloud_probability": ColumnSpec(
                    canonical_name="cloud_probability",
                    source_names=["cloud_prob", "cloud_mask"],
                    role=ColumnRole.METADATA,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=100.0,
                ),
            },
        )

    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map Sentinel columns and compute polarization ratio if VV and VH present."""
        df = raw_df.copy()
        rename_map: dict[str, str] = {}

        for raw_col in df.columns:
            spec = self.schema.find_column_by_source_name(raw_col)
            if spec:
                rename_map[raw_col] = spec.canonical_name

        if rename_map:
            df = df.rename(columns=rename_map)

        # Cross-ratio: VH - VV (in dB difference) represents depolarization ratio
        if "s1_vh_db" in df.columns and "s1_vv_db" in df.columns:
            vh_num = pd.to_numeric(df["s1_vh_db"], errors="coerce")
            vv_num = pd.to_numeric(df["s1_vv_db"], errors="coerce")
            df["s1_vh_vv_ratio_db"] = vh_num - vv_num

        return df
