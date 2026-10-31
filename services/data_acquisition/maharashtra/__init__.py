"""
SoilDepth-AI — Maharashtra Data Acquisition Pipeline
Package initialization for Pune environmental data ingestion.
"""

from .config import (
    STATION_ID,
    STATION_LATITUDE,
    STATION_LONGITUDE,
    BENCHMARK_ELEVATION_M,
    START_DATE,
    END_DATE,
    EXPECTED_DAILY_ROWS,
)

__all__ = [
    "STATION_ID",
    "STATION_LATITUDE",
    "STATION_LONGITUDE",
    "BENCHMARK_ELEVATION_M",
    "START_DATE",
    "END_DATE",
    "EXPECTED_DAILY_ROWS",
]

