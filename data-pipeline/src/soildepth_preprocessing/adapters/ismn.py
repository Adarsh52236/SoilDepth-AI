"""International Soil Moisture Network (ISMN) in-situ ground sensor adapter."""

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
class ISMNAdapter(BaseDataAdapter):
    """Adapter for International Soil Moisture Network (ISMN) in-situ ground stations.

    ISMN provides verified in-situ ground measurements which serve as the primary
    ground-truth reference for SoilDepth-AI training and validation.
    """

    name: ClassVar[str] = "ismn"
    description: ClassVar[str] = (
        "ISMN in-situ ground sensor network adapter (Ground Truth Reference)"
    )
    is_ground_truth: ClassVar[bool] = True

    def get_default_schema(self) -> SchemaDefinition:
        """Construct canonical ISMN schema."""
        return SchemaDefinition(
            name="ismn_ground_truth_schema",
            version="1.0.0",
            description="Verified in-situ ground station soil moisture observations.",
            columns={
                "network": ColumnSpec(
                    canonical_name="network",
                    source_names=["network_name", "net"],
                    role=ColumnRole.METADATA,
                    data_type=DataType.STRING,
                    required=False,
                ),
                "station_id": ColumnSpec(
                    canonical_name="station_id",
                    source_names=["station", "station_name", "site"],
                    role=ColumnRole.ID,
                    data_type=DataType.STRING,
                    required=True,
                ),
                "timestamp_utc": ColumnSpec(
                    canonical_name="timestamp_utc",
                    source_names=["date_time", "datetime", "timestamp"],
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
                "depth_from_m": ColumnSpec(
                    canonical_name="depth_from_m",
                    source_names=["depth_from", "depth_min"],
                    role=ColumnRole.DEPTH,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=5.0,
                    unit="m",
                    target_unit="m",
                ),
                "depth_to_m": ColumnSpec(
                    canonical_name="depth_to_m",
                    source_names=["depth_to", "depth_max"],
                    role=ColumnRole.DEPTH,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=5.0,
                    unit="m",
                    target_unit="m",
                ),
                "soil_moisture": ColumnSpec(
                    canonical_name="soil_moisture",
                    source_names=["sm", "soil_moisture_val", "sm_m3m3"],
                    role=ColumnRole.TARGET,
                    data_type=DataType.FLOAT,
                    required=True,
                    min_value=0.0,
                    max_value=0.85,  # Soil volumetric water content physical saturation upper limit
                    unit="m3/m3",
                    target_unit="m3/m3",
                    description="In-situ volumetric water content (m3/m3)",
                ),
                "quality_flag": ColumnSpec(
                    canonical_name="quality_flag",
                    source_names=["qflag", "flag"],
                    role=ColumnRole.METADATA,
                    data_type=DataType.STRING,
                    required=False,
                    allowed_values=["G", "M", "D", "C"],  # G=Good, M=Dubious, D=Bad, C=Corrupt
                ),
                "sensor": ColumnSpec(
                    canonical_name="sensor",
                    source_names=["sensor_type", "sensor_name"],
                    role=ColumnRole.METADATA,
                    data_type=DataType.STRING,
                    required=False,
                ),
            },
        )

    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map ISMN columns and filter suspect quality flags when available."""
        df = raw_df.copy()
        rename_map: dict[str, str] = {}

        for raw_col in df.columns:
            spec = self.schema.find_column_by_source_name(raw_col)
            if spec:
                rename_map[raw_col] = spec.canonical_name

        if rename_map:
            df = df.rename(columns=rename_map)

        # Handle depth conversion if raw depth is in cm
        if (
            "depth_from_m" in df.columns
            and "depth_to_m" in df.columns
            and ((df["depth_from_m"] > 5.0).any() or (df["depth_to_m"] > 5.0).any())
        ):
            df["depth_from_m"] = df["depth_from_m"] / 100.0
            df["depth_to_m"] = df["depth_to_m"] / 100.0

        return df
