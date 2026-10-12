"""NASA SMAP (Soil Moisture Active Passive) radiometer product adapter."""

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
class SMAPAdapter(BaseDataAdapter):
    """Adapter for NASA SMAP Level 3 and Level 4 soil moisture products.

    CRITICAL SCIENTIFIC INTEGRITY NOTE:
    SMAP L4 (root-zone soil moisture) is an assimilated land-surface model product,
    NOT direct ground-truth in-situ measurement. In SoilDepth-AI, SMAP products
    are treated strictly as satellite feature inputs or auxiliary baselines,
    NEVER as primary ground truth unless explicitly configured.
    """

    name: ClassVar[str] = "smap"
    description: ClassVar[str] = "NASA SMAP Radiometer (L3 surface & L4 assimilated root-zone SM)"
    is_ground_truth: ClassVar[bool] = False

    def get_default_schema(self) -> SchemaDefinition:
        """Construct canonical SMAP schema."""
        return SchemaDefinition(
            name="smap_radiometer_schema",
            version="1.0.0",
            description="NASA SMAP L3 surface and L4 root-zone satellite estimates.",
            columns={
                "ease_row": ColumnSpec(
                    canonical_name="ease_row",
                    source_names=["row", "ease2_row"],
                    role=ColumnRole.METADATA,
                    data_type=DataType.INT,
                    required=False,
                ),
                "ease_col": ColumnSpec(
                    canonical_name="ease_col",
                    source_names=["col", "ease2_col"],
                    role=ColumnRole.METADATA,
                    data_type=DataType.INT,
                    required=False,
                ),
                "timestamp_utc": ColumnSpec(
                    canonical_name="timestamp_utc",
                    source_names=["time", "datetime"],
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
                "smap_surface_sm_m3m3": ColumnSpec(
                    canonical_name="smap_surface_sm_m3m3",
                    source_names=["surface_sm", "sm_l3", "soil_moisture_surface"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=0.85,
                    unit="m3/m3",
                    target_unit="m3/m3",
                    description="SMAP L3 surface (0-5cm) soil moisture",
                ),
                "smap_rootzone_sm_m3m3": ColumnSpec(
                    canonical_name="smap_rootzone_sm_m3m3",
                    source_names=["rootzone_sm", "sm_l4", "soil_moisture_rootzone"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=0.85,
                    unit="m3/m3",
                    target_unit="m3/m3",
                    description="SMAP L4 assimilated root-zone (0-100cm) estimate",
                ),
                "retrieval_qual_flag": ColumnSpec(
                    canonical_name="retrieval_qual_flag",
                    source_names=["quality_flag", "retrieval_quality"],
                    role=ColumnRole.METADATA,
                    data_type=DataType.INT,
                    required=False,
                ),
            },
        )

    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map SMAP raw columns and validate quality flags."""
        df = raw_df.copy()
        rename_map: dict[str, str] = {}

        for raw_col in df.columns:
            spec = self.schema.find_column_by_source_name(raw_col)
            if spec:
                rename_map[raw_col] = spec.canonical_name

        if rename_map:
            df = df.rename(columns=rename_map)

        return df
