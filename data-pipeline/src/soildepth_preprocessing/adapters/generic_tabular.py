"""Generic tabular adapter for standard CSV, Parquet, and Excel datasets."""

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
class GenericTabularAdapter(BaseDataAdapter):
    """Universal adapter mapping tabular files to a user-specified or generic schema."""

    name: ClassVar[str] = "generic_tabular"
    description: ClassVar[str] = "Universal tabular data adapter with alias-based column mapping"
    is_ground_truth: ClassVar[bool] = False

    def get_default_schema(self) -> SchemaDefinition:
        """Construct standard generic soil moisture schema."""
        return SchemaDefinition(
            name="generic_soil_moisture_schema",
            version="1.0.0",
            description="Default schema for in-situ ground sensors and environmental features.",
            columns={
                "station_id": ColumnSpec(
                    canonical_name="station_id",
                    source_names=["station", "site_id", "site", "id"],
                    role=ColumnRole.ID,
                    data_type=DataType.STRING,
                    required=True,
                ),
                "timestamp_utc": ColumnSpec(
                    canonical_name="timestamp_utc",
                    source_names=["timestamp", "datetime", "date_time", "time", "date"],
                    role=ColumnRole.TIMESTAMP,
                    data_type=DataType.DATETIME,
                    required=True,
                ),
                "latitude": ColumnSpec(
                    canonical_name="latitude",
                    source_names=["lat", "y"],
                    role=ColumnRole.LATITUDE,
                    data_type=DataType.FLOAT,
                    required=True,
                    min_value=-90.0,
                    max_value=90.0,
                ),
                "longitude": ColumnSpec(
                    canonical_name="longitude",
                    source_names=["lon", "long", "x"],
                    role=ColumnRole.LONGITUDE,
                    data_type=DataType.FLOAT,
                    required=True,
                    min_value=-180.0,
                    max_value=180.0,
                ),
                "depth_m": ColumnSpec(
                    canonical_name="depth_m",
                    source_names=["depth", "sensor_depth", "depth_cm"],
                    role=ColumnRole.DEPTH,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=10.0,
                    unit="m",
                    target_unit="m",
                ),
                "soil_moisture": ColumnSpec(
                    canonical_name="soil_moisture",
                    source_names=["sm", "sm_vwc", "sm_pct", "soil_moisture_m3m3", "vwc"],
                    role=ColumnRole.TARGET,
                    data_type=DataType.FLOAT,
                    required=True,
                    min_value=0.0,
                    max_value=1.0,
                    unit="m3/m3",
                    target_unit="m3/m3",
                    description="Volumetric water content in m3/m3",
                ),
                "air_temperature_c": ColumnSpec(
                    canonical_name="air_temperature_c",
                    source_names=["t2m", "temp", "temperature", "temp_c", "air_temp"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=-60.0,
                    max_value=60.0,
                    unit="degC",
                    target_unit="degC",
                ),
                "precipitation_mm": ColumnSpec(
                    canonical_name="precipitation_mm",
                    source_names=["precip", "rain", "tp", "precipitation"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=1000.0,
                    unit="mm",
                    target_unit="mm",
                ),
            },
        )

    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map raw columns to canonical column names without ambiguous guessing."""
        df = raw_df.copy()
        rename_map: dict[str, str] = {}

        # Look up matching canonical column for each raw column
        for raw_col in df.columns:
            spec = self.schema.find_column_by_source_name(raw_col)
            if spec:
                rename_map[raw_col] = spec.canonical_name

        if rename_map:
            df = df.rename(columns=rename_map)

        return df
