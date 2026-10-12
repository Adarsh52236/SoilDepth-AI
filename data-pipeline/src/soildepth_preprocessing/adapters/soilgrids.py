"""ISRIC SoilGrids 250m physical soil properties adapter."""

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
class SoilGridsAdapter(BaseDataAdapter):
    """Adapter for ISRIC SoilGrids global 250m physical soil property layers.

    Provides static soil texture and physical characteristics across standardized depth intervals:
    0-5cm, 5-15cm, 15-30cm, 30-60cm, and 60-100cm.
    """

    name: ClassVar[str] = "soilgrids"
    description: ClassVar[str] = "ISRIC SoilGrids 250m static physical soil properties"
    is_ground_truth: ClassVar[bool] = False

    def get_default_schema(self) -> SchemaDefinition:
        """Construct canonical SoilGrids schema."""
        return SchemaDefinition(
            name="soilgrids_physical_properties_schema",
            version="1.0.0",
            description="Static soil texture, bulk density, and organic carbon fractions.",
            columns={
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
                "clay_pct": ColumnSpec(
                    canonical_name="clay_pct",
                    source_names=["clay", "clay_0_5cm", "clay_content"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=100.0,
                    unit="%",
                    target_unit="%",
                ),
                "sand_pct": ColumnSpec(
                    canonical_name="sand_pct",
                    source_names=["sand", "sand_0_5cm", "sand_content"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=100.0,
                    unit="%",
                    target_unit="%",
                ),
                "silt_pct": ColumnSpec(
                    canonical_name="silt_pct",
                    source_names=["silt", "silt_0_5cm", "silt_content"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=100.0,
                    unit="%",
                    target_unit="%",
                ),
                "bulk_density_g_cm3": ColumnSpec(
                    canonical_name="bulk_density_g_cm3",
                    source_names=["bdod", "bulk_density", "bdod_0_5cm"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.5,
                    max_value=2.5,
                    unit="g/cm3",
                    target_unit="g/cm3",
                ),
                "soc_g_kg": ColumnSpec(
                    canonical_name="soc_g_kg",
                    source_names=["soc", "soil_organic_carbon", "soc_0_5cm"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=500.0,
                    unit="g/kg",
                    target_unit="g/kg",
                ),
            },
        )

    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map SoilGrids columns and normalize raw ISRIC unit scalings.

        ISRIC raw GeoTIFFs often use integers (e.g. clay in g/kg or cg/kg, bulk density in cg/cm3).
        """
        df = raw_df.copy()
        rename_map: dict[str, str] = {}

        for raw_col in df.columns:
            spec = self.schema.find_column_by_source_name(raw_col)
            if spec:
                rename_map[raw_col] = spec.canonical_name

        if rename_map:
            df = df.rename(columns=rename_map)

        # Scale bulk density if in cg/cm3 (e.g. values around 130-160 -> 1.3-1.6 g/cm3)
        if "bulk_density_g_cm3" in df.columns:
            bd_series = pd.to_numeric(df["bulk_density_g_cm3"], errors="coerce")
            if (bd_series > 50.0).any():
                df["bulk_density_g_cm3"] = bd_series / 100.0

        return df
