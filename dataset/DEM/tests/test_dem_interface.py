"""
SoilDepth-AI — Tests for DEM Dataset Structure & Processing Interface (DEM Module Local Suite)
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
"""

from tests.test_dem_processing import (
    test_dem_directory_structure,
    test_dem_manifest_integrity,
    test_dem_downloaded_raster_integrity,
    test_dem_station_coverage_and_elevation_sampling,
    test_dem_slope_derivation_real_terrain,
    test_dem_processed_artifacts_integrity,
    test_dem_slope_derivation_horn_algorithm,
    test_dem_slope_boundary_and_nodata_guards,
)
