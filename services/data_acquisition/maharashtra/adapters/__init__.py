"""
SoilDepth-AI — Maharashtra Data Acquisition Adapters
Modular adapters for ERA5-Land, Sentinel-1, Sentinel-2, SMAP L3, SoilGrids, and DEM.
"""

from .base_adapter import BaseEnvironmentalAdapter
from .era5_land import ERA5LandAdapter
from .sentinel1 import Sentinel1Adapter
from .sentinel2 import Sentinel2Adapter
from .smap_l3 import SMAPAdapter
from .soilgrids import SoilGridsAdapter
from .dem import DEMAdapter

__all__ = [
    "BaseEnvironmentalAdapter",
    "ERA5LandAdapter",
    "Sentinel1Adapter",
    "Sentinel2Adapter",
    "SMAPAdapter",
    "SoilGridsAdapter",
    "DEMAdapter",
]

