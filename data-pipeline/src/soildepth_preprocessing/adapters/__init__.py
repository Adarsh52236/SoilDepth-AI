"""Data adapters for heterogeneous environmental, remote sensing, and in-situ sources."""

from __future__ import annotations

from soildepth_preprocessing.adapters.base import AdapterRegistry, BaseDataAdapter
from soildepth_preprocessing.adapters.dem import DEMAdapter
from soildepth_preprocessing.adapters.era5 import ERA5LandAdapter
from soildepth_preprocessing.adapters.generic_tabular import GenericTabularAdapter
from soildepth_preprocessing.adapters.ismn import ISMNAdapter
from soildepth_preprocessing.adapters.sentinel import SentinelAdapter
from soildepth_preprocessing.adapters.smap import SMAPAdapter
from soildepth_preprocessing.adapters.soilgrids import SoilGridsAdapter

__all__ = [
    "AdapterRegistry",
    "BaseDataAdapter",
    "DEMAdapter",
    "ERA5LandAdapter",
    "GenericTabularAdapter",
    "ISMNAdapter",
    "SMAPAdapter",
    "SentinelAdapter",
    "SoilGridsAdapter",
]
