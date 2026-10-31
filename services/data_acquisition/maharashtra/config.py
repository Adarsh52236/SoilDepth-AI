"""
SoilDepth-AI — Maharashtra Environmental Acquisition Configuration
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Central multi-station configuration defining spatial bounds, coordinates,
         station registries, study timeline, timezone conventions, paths,
         and physical quality validation boundaries.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
MAHARASHTRA_DATA_ROOT = REPO_ROOT / "dataset" / "Maharashtra" / "COSMOS"
METADATA_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "metadata"


# ==============================================================================
# 1. STATION CONFIGURATION DATACLASS
# ==============================================================================
@dataclass
class StationConfig:
    """Encapsulates spatial, administrative, and storage metadata for an individual station."""
    station_id: str
    station_name: str
    network_source: str
    latitude: float
    longitude: float
    benchmark_elevation_m: float
    elevation_tolerance_m: float = 50.0
    district: str = "Pune"
    region: str = "Western Maharashtra"
    state: str = "Maharashtra"
    country: str = "India"
    utm_zone: int = 43
    utm_epsg: str = "EPSG:32643"
    start_date: str = "2017-01-01"
    end_date: str = "2023-12-31"
    expected_daily_rows: int = 2556
    bbox_radius_deg: float = 0.015  # ~3 km buffer
    primary_crops: List[str] = field(default_factory=list)
    available_sensor_depths_cm: List[float] = field(default_factory=list)
    station_easting: Optional[float] = None
    station_northing: Optional[float] = None

    @property
    def bbox_west(self) -> float:
        return round(self.longitude - self.bbox_radius_deg, 4)

    @property
    def bbox_south(self) -> float:
        return round(self.latitude - self.bbox_radius_deg, 4)

    @property
    def bbox_east(self) -> float:
        return round(self.longitude + self.bbox_radius_deg, 4)

    @property
    def bbox_north(self) -> float:
        return round(self.latitude + self.bbox_radius_deg, 4)

    @property
    def raw_dir(self) -> Path:
        # Preserve backwards compatibility for Pune directory naming
        folder_name = "IITM-PUNE" if self.station_id == "IITM-PUNE-COSMOS" else self.station_id
        return MAHARASHTRA_DATA_ROOT / "raw" / folder_name

    @property
    def processed_dir(self) -> Path:
        # Preserve backwards compatibility for Pune directory naming
        folder_name = "IITM-PUNE" if self.station_id == "IITM-PUNE-COSMOS" else self.station_id
        return MAHARASHTRA_DATA_ROOT / "processed" / folder_name

    @property
    def era5_raw_dir(self) -> Path:
        return self.raw_dir / "era5_land"

    @property
    def soilgrids_raw_dir(self) -> Path:
        return self.raw_dir / "soilgrids"

    @property
    def dem_raw_dir(self) -> Path:
        return self.raw_dir / "dem"

    @property
    def sentinel1_raw_dir(self) -> Path:
        return self.raw_dir / "sentinel1"

    @property
    def sentinel2_raw_dir(self) -> Path:
        return self.raw_dir / "sentinel2"

    @property
    def smap_raw_dir(self) -> Path:
        return self.raw_dir / "smap"

    @property
    def daily_features_csv(self) -> Path:
        return self.processed_dir / "daily_environmental_features.csv"

    @property
    def static_features_csv(self) -> Path:
        return self.processed_dir / "static_environmental_features.csv"

    @property
    def acquisition_manifest_json(self) -> Path:
        return self.processed_dir / "acquisition_manifest.json"

    @property
    def quality_report_json(self) -> Path:
        return self.processed_dir / "quality_report.json"

    @property
    def quality_report_md(self) -> Path:
        return self.processed_dir / "quality_report.md"


# ==============================================================================
# 2. STATION REGISTRY DICTIONARY
# ==============================================================================
PUNE_CONFIG = StationConfig(
    station_id="IITM-PUNE-COSMOS",
    station_name="IITM Pune COSMOS-India Station",
    network_source="COSMOS-India / MoES-NERC",
    latitude=18.5372,
    longitude=73.8051,
    benchmark_elevation_m=560.0,
    elevation_tolerance_m=50.0,
    district="Pune",
    region="Western Maharashtra",
    state="Maharashtra",
    country="India",
    utm_zone=43,
    utm_epsg="EPSG:32643",
    station_easting=373885.96,
    station_northing=2050039.05,
    start_date="2017-01-01",
    end_date="2023-12-31",
    expected_daily_rows=2556,
    bbox_radius_deg=0.015,
    primary_crops=["Sugarcane", "Wheat", "Maize"],
    available_sensor_depths_cm=[30.0],  # CRNS 0-30 cm integrated
)

RAHURI_CONFIG = StationConfig(
    station_id="MPKV-RAHURI-CAAST",
    station_name="MPKV Rahuri CAAST Precision Agriculture Network",
    network_source="ICAR-NAHEP CAAST / MPKV Rahuri",
    latitude=19.3932,
    longitude=74.6475,
    benchmark_elevation_m=512.0,
    elevation_tolerance_m=50.0,
    district="Ahmednagar",
    region="Western Maharashtra",
    state="Maharashtra",
    country="India",
    utm_zone=43,
    utm_epsg="EPSG:32643",
    start_date="2017-01-01",
    end_date="2023-12-31",
    expected_daily_rows=2556,
    bbox_radius_deg=0.015,
    primary_crops=["Sugarcane", "Wheat", "Chickpea", "Soybean"],
    available_sensor_depths_cm=[10.0, 20.0, 30.0, 60.0],
)

BARAMATI_CONFIG = StationConfig(
    station_id="NIASM-BARAMATI-FLUX",
    station_name="ICAR-NIASM Baramati Eddy Covariance & Soil Station",
    network_source="ICAR-NIASM Baramati",
    latitude=18.1506,
    longitude=74.5772,
    benchmark_elevation_m=555.0,
    elevation_tolerance_m=40.0,
    district="Pune",
    region="Western Maharashtra",
    state="Maharashtra",
    country="India",
    utm_zone=43,
    utm_epsg="EPSG:32643",
    start_date="2017-01-01",
    end_date="2023-12-31",
    expected_daily_rows=2556,
    bbox_radius_deg=0.015,
    primary_crops=["Sorghum", "Chickpea", "Sugarcane", "Wheat"],
    available_sensor_depths_cm=[10.0, 20.0, 30.0, 50.0],
)

STATION_CONFIGS: Dict[str, StationConfig] = {
    PUNE_CONFIG.station_id: PUNE_CONFIG,
    RAHURI_CONFIG.station_id: RAHURI_CONFIG,
    BARAMATI_CONFIG.station_id: BARAMATI_CONFIG,
}


def get_station_config(station_id: str) -> StationConfig:
    """
    Returns StationConfig for a requested station ID.
    If not in pre-defined dict, attempts to dynamically construct from station_registry.csv.
    """
    if station_id in STATION_CONFIGS:
        return STATION_CONFIGS[station_id]

    registry_csv = METADATA_DIR / "station_registry.csv"
    if registry_csv.exists():
        import pandas as pd
        df = pd.read_csv(registry_csv)
        match = df[df["station_id"] == station_id]
        if not match.empty:
            row = match.iloc[0]
            depths_str = str(row.get("sensor_depths_cm", ""))
            depths = []
            for d in depths_str.split(","):
                d_clean = d.strip().replace("cm", "").replace("depth-integrated", "").strip()
                try:
                    depths.append(float(d_clean))
                except ValueError:
                    pass

            crops_str = str(row.get("primary_crops", ""))
            crops = [c.strip() for c in crops_str.split(",") if c.strip()]

            cfg = StationConfig(
                station_id=str(row["station_id"]),
                station_name=str(row["station_name"]),
                network_source=str(row["institution"]),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                benchmark_elevation_m=float(row["elevation_m"]),
                district=str(row["district"]),
                region=str(row["region"]),
                primary_crops=crops,
                available_sensor_depths_cm=depths,
            )
            STATION_CONFIGS[station_id] = cfg
            return cfg

    raise KeyError(f"Unknown station_id: '{station_id}'. Available: {list(STATION_CONFIGS.keys())}")


# ==============================================================================
# 3. BACKWARDS-COMPATIBLE MODULE-LEVEL CONSTANTS (IITM-PUNE PILOT)
# ==============================================================================
STATION_ID = PUNE_CONFIG.station_id
STATION_NAME = PUNE_CONFIG.station_name
NETWORK_SOURCE = PUNE_CONFIG.network_source

STATION_LATITUDE = PUNE_CONFIG.latitude
STATION_LONGITUDE = PUNE_CONFIG.longitude
BENCHMARK_ELEVATION_M = PUNE_CONFIG.benchmark_elevation_m
ELEVATION_TOLERANCE_M = PUNE_CONFIG.elevation_tolerance_m

DISTRICT = PUNE_CONFIG.district
STATE = PUNE_CONFIG.state
COUNTRY = PUNE_CONFIG.country

UTM_ZONE = PUNE_CONFIG.utm_zone
UTM_EPSG = PUNE_CONFIG.utm_epsg
STATION_EASTING = PUNE_CONFIG.station_easting
STATION_NORTHING = PUNE_CONFIG.station_northing

BBOX_WEST = PUNE_CONFIG.bbox_west
BBOX_SOUTH = PUNE_CONFIG.bbox_south
BBOX_EAST = PUNE_CONFIG.bbox_east
BBOX_NORTH = PUNE_CONFIG.bbox_north

TIMEZONE_NAME = "Asia/Kolkata"
UTC_OFFSET_HOURS = 5.5
DATE_CONVENTION = "UTC (00:00:00 to 23:59:59 UTC daily epochs)"

START_DATE = PUNE_CONFIG.start_date
END_DATE = PUNE_CONFIG.end_date
EXPECTED_DAILY_ROWS = PUNE_CONFIG.expected_daily_rows
EXPECTED_HOURLY_ROWS = EXPECTED_DAILY_ROWS * 24

RAW_DIR = PUNE_CONFIG.raw_dir
PROCESSED_DIR = PUNE_CONFIG.processed_dir

ERA5_RAW_DIR = PUNE_CONFIG.era5_raw_dir
SOILGRIDS_RAW_DIR = PUNE_CONFIG.soilgrids_raw_dir
DEM_RAW_DIR = PUNE_CONFIG.dem_raw_dir
SENTINEL1_RAW_DIR = PUNE_CONFIG.sentinel1_raw_dir
SENTINEL2_RAW_DIR = PUNE_CONFIG.sentinel2_raw_dir
SMAP_RAW_DIR = PUNE_CONFIG.smap_raw_dir

DAILY_FEATURES_CSV = PUNE_CONFIG.daily_features_csv
STATIC_FEATURES_CSV = PUNE_CONFIG.static_features_csv
ACQUISITION_MANIFEST_JSON = PUNE_CONFIG.acquisition_manifest_json
QUALITY_REPORT_JSON = PUNE_CONFIG.quality_report_json
QUALITY_REPORT_MD = PUNE_CONFIG.quality_report_md

# ==============================================================================
# 4. SATELLITE & REMOTE SENSING QUALITY THRESHOLDS
# ==============================================================================
S1_MAX_STALENESS_DAYS = 30.0
S1_POLARIZATIONS = ["vv", "vh"]

S2_MAX_STALENESS_DAYS = 45.0
S2_SCALE_FACTOR = 10000.0
VALID_LAND_SCL_CODES: Set[int] = {2, 4, 5, 6}

SMAP_MAX_STALENESS_DAYS = 14.0
SMAP_FILL_VALUE = -9999.0
SMAP_VALID_QUALITY_FLAG = 0.0

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
