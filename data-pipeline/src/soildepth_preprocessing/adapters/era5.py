"""ERA5-Land reanalysis adapter for meteorological and modeled soil variables."""

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
class ERA5LandAdapter(BaseDataAdapter):
    """Adapter for ECMWF ERA5-Land atmospheric reanalysis.

    Note: ERA5-Land soil moisture layers (swvl1-4) are reanalysis model outputs,
    NOT direct ground-truth measurements. They are treated as predictive features.
    """

    name: ClassVar[str] = "era5"
    description: ClassVar[str] = (
        "ECMWF ERA5-Land Reanalysis (Atmospheric and modeled soil variables)"
    )
    is_ground_truth: ClassVar[bool] = False

    def get_default_schema(self) -> SchemaDefinition:
        """Construct canonical ERA5-Land schema."""
        return SchemaDefinition(
            name="era5_land_schema",
            version="1.0.0",
            description="ECMWF ERA5-Land hourly and daily reanalysis covariates.",
            columns={
                "grid_id": ColumnSpec(
                    canonical_name="grid_id",
                    source_names=["cell_id", "grid_point"],
                    role=ColumnRole.ID,
                    data_type=DataType.STRING,
                    required=False,
                ),
                "timestamp_utc": ColumnSpec(
                    canonical_name="timestamp_utc",
                    source_names=["time", "valid_time", "datetime"],
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
                "air_temperature_c": ColumnSpec(
                    canonical_name="air_temperature_c",
                    source_names=["t2m", "temperature_2m"],
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
                    source_names=["tp", "total_precipitation"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=1000.0,
                    unit="mm",
                    target_unit="mm",
                ),
                "era5_swvl1_m3m3": ColumnSpec(
                    canonical_name="era5_swvl1_m3m3",
                    source_names=["swvl1", "soil_water_l1"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=1.0,
                    unit="m3/m3",
                    target_unit="m3/m3",
                    description="Modeled soil moisture 0-7cm",
                ),
                "era5_swvl2_m3m3": ColumnSpec(
                    canonical_name="era5_swvl2_m3m3",
                    source_names=["swvl2", "soil_water_l2"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=1.0,
                    unit="m3/m3",
                    target_unit="m3/m3",
                    description="Modeled soil moisture 7-28cm",
                ),
            },
        )

    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map ERA5 raw columns and convert standard atmospheric units."""
        df = raw_df.copy()
        rename_map: dict[str, str] = {}

        for raw_col in df.columns:
            spec = self.schema.find_column_by_source_name(raw_col)
            if spec:
                rename_map[raw_col] = spec.canonical_name

        if rename_map:
            df = df.rename(columns=rename_map)

        # Convert Kelvin to Celsius if raw values appear to be in Kelvin (> 200)
        if "air_temperature_c" in df.columns:
            temp_num = pd.to_numeric(df["air_temperature_c"], errors="coerce")
            if (temp_num > 180.0).any():
                df["air_temperature_c"] = temp_num - 273.15

        # Convert total precipitation from meters to mm if raw values are < 1.0
        if "precipitation_mm" in df.columns:
            precip_num = pd.to_numeric(df["precipitation_mm"], errors="coerce")
            # If all values are tiny (< 0.5), ERA5 expressed them in meters
            if (precip_num > 0).any() and (precip_num.max() < 0.5):
                df["precipitation_mm"] = precip_num * 1000.0

        return df
