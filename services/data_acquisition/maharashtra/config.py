"""
SoilDepth-AI — Maharashtra Environmental Acquisition Configuration
Pilot Station: IITM-PUNE-COSMOS
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Central configuration defining spatial bounds, coordinates, study timeline,
         timezone conventions, paths, and physical quality validation boundaries.
"""

from pathlib import Path
from typing import Dict, List, Set, Any

REPO_ROOT = Path(__file__).resolve().parents[3]

# ==============================================================================
# 1. STATION & GEOGRAPHIC IDENTIFIERS
# ==============================================================================
STATION_ID = "IITM-PUNE-COSMOS"
STATION_NAME = "IITM Pune COSMOS-India Station"
NETWORK_SOURCE = "COSMOS-India / MoES-NERC"

STATION_LATITUDE = 18.5372
STATION_LONGITUDE = 73.8051
BENCHMARK_ELEVATION_M = 560.0
ELEVATION_TOLERANCE_M = 50.0  # Urban/hilly fringe of Pashan/Vetal Hill

DISTRICT = "Pune"
STATE = "Maharashtra"
COUNTRY = "India"

# UTM Projection for Pune (WGS84 / UTM Zone 43N, EPSG:32643)
UTM_ZONE = 43
UTM_EPSG = "EPSG:32643"
STATION_EASTING = 373885.96
STATION_NORTHING = 2050039.05

# Spatial Bounding Box for extraction queries (~3 km buffer)
BBOX_WEST = 73.7901
BBOX_SOUTH = 18.5222
BBOX_EAST = 73.8201
BBOX_NORTH = 18.5522

# ==============================================================================
# 2. TEMPORAL BOUNDS & TIMEZONE CONVENTIONS
# ==============================================================================
# Primary temporal convention: Monotonic UTC calendar day (00:00:00 to 23:59:59 UTC).
# In Indian Standard Time (IST, UTC+05:30), daytime satellite passes over Pune
# (Sentinel-2 ~10:45 IST / 05:15 UTC; Sentinel-1 descending ~06:15 IST / 00:45 UTC;
# Sentinel-1 ascending ~18:30 IST / 13:00 UTC; SMAP AM ~06:00 IST / 00:30 UTC)
# all fall precisely within the same UTC calendar day.
TIMEZONE_NAME = "Asia/Kolkata"
UTC_OFFSET_HOURS = 5.5
DATE_CONVENTION = "UTC (00:00:00 to 23:59:59 UTC daily epochs)"

START_DATE = "2017-01-01"
END_DATE = "2023-12-31"
EXPECTED_DAILY_ROWS = 2556  # 7 full calendar years (2020 leap year: 366 days)
EXPECTED_HOURLY_ROWS = EXPECTED_DAILY_ROWS * 24  # 61,344 hours

# ==============================================================================
# 3. DIRECTORY STORAGE ARCHITECTURE
# ==============================================================================
MAHARASHTRA_DATA_ROOT = REPO_ROOT / "dataset" / "Maharashtra" / "COSMOS"
RAW_DIR = MAHARASHTRA_DATA_ROOT / "raw" / "IITM-PUNE"
PROCESSED_DIR = MAHARASHTRA_DATA_ROOT / "processed" / "IITM-PUNE"

# Subdirectories for raw modal extracts
ERA5_RAW_DIR = RAW_DIR / "era5_land"
SOILGRIDS_RAW_DIR = RAW_DIR / "soilgrids"
DEM_RAW_DIR = RAW_DIR / "dem"
SENTINEL1_RAW_DIR = RAW_DIR / "sentinel1"
SENTINEL2_RAW_DIR = RAW_DIR / "sentinel2"
SMAP_RAW_DIR = RAW_DIR / "smap"

# Processed output files
DAILY_FEATURES_CSV = PROCESSED_DIR / "daily_environmental_features.csv"
STATIC_FEATURES_CSV = PROCESSED_DIR / "static_environmental_features.csv"
ACQUISITION_MANIFEST_JSON = PROCESSED_DIR / "acquisition_manifest.json"
QUALITY_REPORT_JSON = PROCESSED_DIR / "quality_report.json"
QUALITY_REPORT_MD = PROCESSED_DIR / "quality_report.md"

# ==============================================================================
# 4. SATELLITE & REMOTE SENSING QUALITY THRESHOLDS
# ==============================================================================
# S1 SAR Quality Parameters
S1_MAX_STALENESS_DAYS = 30.0
S1_POLARIZATIONS = ["vv", "vh"]

# S2 Optical Quality Parameters
S2_MAX_STALENESS_DAYS = 45.0
S2_SCALE_FACTOR = 10000.0  # Digital Number (DN) to BOA reflectance
# Scene Classification Layer (SCL) filtering:
# Retain: 2=Dark Area, 4=Vegetation, 5=Bare Soil, 6=Water.
# Exclude: 0=No Data, 1=Defective, 3=Cloud Shadow, 7=Unclassified (conservative),
# 8=Cloud Medium, 9=Cloud High, 10=Cirrus, 11=Snow/Ice.
VALID_LAND_SCL_CODES: Set[int] = {2, 4, 5, 6}

# SMAP L3 Radiometer Quality Parameters
SMAP_MAX_STALENESS_DAYS = 14.0
SMAP_FILL_VALUE = -9999.0
SMAP_VALID_QUALITY_FLAG = 0.0  # Quality 0 = Good retrieval

# SoilGrids v2.0 Properties and Standard Depths
SOILGRIDS_PROPERTIES = [
    "bdod", "clay", "sand", "silt", "ocd", "wv0010", "wv0033", "wv1500"
]
SOILGRIDS_DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm"]

# ==============================================================================
# 5. PHYSICAL BOUNDARY CHECKS
# ==============================================================================
PHYSICAL_LIMITS: Dict[str, Dict[str, float]] = {
    "temperature_c": {"min": 0.0, "max": 50.0},
    "dewpoint_c": {"min": -10.0, "max": 35.0},
    "precipitation_mm": {"min": 0.0, "max": 400.0},
    "solar_radiation_mj": {"min": 0.0, "max": 45.0},
    "wind_speed_ms": {"min": 0.0, "max": 40.0},
    "reflectance": {"min": 0.0, "max": 1.0},
    "ndvi": {"min": -1.0, "max": 1.0},
    "evi": {"min": -1.0, "max": 1.5},
    "s1_backscatter_db": {"min": -40.0, "max": 5.0},
    "soil_bulk_density_g_cm3": {"min": 0.8, "max": 2.0},
    "soil_texture_pct": {"min": 0.0, "max": 100.0},
    "volumetric_moisture": {"min": 0.0, "max": 0.65},
}

