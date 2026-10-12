"""Digital Elevation Model (DEM) topographic adapter and raster extension interface."""

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
class DEMAdapter(BaseDataAdapter):
    """Adapter for Digital Elevation Models (e.g. SRTM, Copernicus DEM 30m).

    Includes elevation, slope, aspect, and Topographic Wetness Index (TWI).
    Also documents the raster ingestion extension interface for future multi-dimensional rasters.
    """

    name: ClassVar[str] = "dem"
    description: ClassVar[str] = "Digital Elevation Model topography and terrain covariates"
    is_ground_truth: ClassVar[bool] = False

    def get_default_schema(self) -> SchemaDefinition:
        """Construct canonical DEM schema."""
        return SchemaDefinition(
            name="dem_topography_schema",
            version="1.0.0",
            description="Topographic terrain indices derived from digital elevation models.",
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
                "elevation_m": ColumnSpec(
                    canonical_name="elevation_m",
                    source_names=["elevation", "elev", "alt", "altitude"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=True,
                    min_value=-500.0,
                    max_value=9000.0,
                    unit="m",
                    target_unit="m",
                ),
                "slope_deg": ColumnSpec(
                    canonical_name="slope_deg",
                    source_names=["slope"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=90.0,
                    unit="deg",
                    target_unit="deg",
                ),
                "aspect_deg": ColumnSpec(
                    canonical_name="aspect_deg",
                    source_names=["aspect"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=360.0,
                    unit="deg",
                    target_unit="deg",
                ),
                "twi": ColumnSpec(
                    canonical_name="twi",
                    source_names=["topographic_wetness_index"],
                    role=ColumnRole.FEATURE,
                    data_type=DataType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=30.0,
                ),
            },
        )

    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map DEM terrain columns to canonical names."""
        df = raw_df.copy()
        rename_map: dict[str, str] = {}

        for raw_col in df.columns:
            spec = self.schema.find_column_by_source_name(raw_col)
            if spec:
                rename_map[raw_col] = spec.canonical_name

        if rename_map:
            df = df.rename(columns=rename_map)

        return df


class RasterAdapterExtensionPoint:
    """Architectural extension point for future GeoTIFF / NetCDF / Zarr ingestion.

    When multi-dimensional raster grids (e.g. from Sentinel-1 or NetCDF ERA5) are ingested,
    this interface defines how spatial rasters must be sampled at ground sensor coordinates
    or reprojected onto target grids using xarray, rioxarray, and rasterio.
    """

    @classmethod
    def sample_raster_at_points(
        cls,
        raster_path: str,
        coordinates: list[tuple[float, float]],
    ) -> list[float]:
        """Placeholder for sampling spatial rasters at discrete point coordinates.

        Dependencies: rasterio, xarray.
        Raises NotImplementedError until full raster ingestion phase is initiated.
        """
        raise NotImplementedError(
            "Raster grid extraction is planned for the geospatial integration phase. "
            "Tabular point samples must be provided in the current preprocessing phase."
        )
