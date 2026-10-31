"""
SoilDepth-AI — SoilGrids 250m Edaphic Adapter
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Ingests ISRIC SoilGrids v2.0 properties across 4 depths via OGC WCS 2.0.1,
         validates physical units, verifies 100% texture mass balance closure,
         and derives explicit pedotransfer hydraulic features across Maharashtra stations.
"""

import io
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from PIL import Image

from ..config import (
    StationConfig,
    PUNE_CONFIG,
    STATION_ID,
    STATION_LATITUDE,
    STATION_LONGITUDE,
    BENCHMARK_ELEVATION_M,
    SOILGRIDS_RAW_DIR,
    SOILGRIDS_PROPERTIES,
    SOILGRIDS_DEPTHS,
    PHYSICAL_LIMITS,
)
from .base_adapter import BaseEnvironmentalAdapter

SCALE_FACTORS = {
    "bdod": 100.0,       # cg/cm³ -> g/cm³ (fine earth bulk density)
    "clay": 10.0,        # g/kg -> % (clay content < 2 µm)
    "sand": 10.0,        # g/kg -> % (sand content 50–2000 µm)
    "silt": 10.0,        # g/kg -> % (silt content 2–50 µm)
    "ocd": 10.0,         # hg/m³ -> kg/m³ (organic carbon density)
    "wv0010": 1000.0,    # 10 * cm³/dm³ -> m³/m³ (volumetric water retention at -10 kPa)
    "wv0033": 1000.0,    # 10 * cm³/dm³ -> m³/m³ (volumetric water retention at -33 kPa, FC)
    "wv1500": 1000.0,    # 10 * cm³/dm³ -> m³/m³ (volumetric water retention at -1500 kPa, PWP)
}


class SoilGridsAdapter(BaseEnvironmentalAdapter):
    """ISRIC SoilGrids v2.0 WCS data adapter."""

    def __init__(self, station_config: Optional[StationConfig] = None, raw_dir: Optional[Path] = None):
        cfg = station_config or PUNE_CONFIG
        self.station_config = cfg
        target_raw_dir = raw_dir if raw_dir is not None else cfg.soilgrids_raw_dir
        super().__init__(
            name="SoilGrids",
            source="ISRIC — World Soil Information (SoilGrids v2.0 250m WCS)",
            raw_dir=target_raw_dir,
            station_config=cfg,
        )

    def acquire(self, start_date: str = "", end_date: str = "") -> Dict[str, Any]:
        """
        Retrieves all 32 GeoTIFF tiles (8 properties x 4 depths) via ISRIC OGC WCS 2.0.1.
        """
        manifest_records = []
        acquired_files = []

        print(f"[{self.name}] Acquiring 32 SoilGrids v2.0 GeoTIFFs for {self.station_config.station_id}...")

        sub_x1 = round(self.station_config.longitude - 0.005, 4)
        sub_x2 = round(self.station_config.longitude + 0.005, 4)
        sub_y1 = round(self.station_config.latitude - 0.005, 4)
        sub_y2 = round(self.station_config.latitude + 0.005, 4)

        for prop in SOILGRIDS_PROPERTIES:
            prop_dir = self.raw_dir / prop
            prop_dir.mkdir(parents=True, exist_ok=True)

            for depth in SOILGRIDS_DEPTHS:
                filename = f"{prop}_mean_{depth}.tif"
                filepath = prop_dir / filename

                if filepath.exists() and filepath.stat().st_size > 300:
                    pass
                else:
                    url = (
                        f"https://maps.isric.org/mapserv?map=/map/{prop}.map&"
                        f"SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&"
                        f"COVERAGEID={prop}_{depth}_mean&"
                        f"SUBSET=X({sub_x1},{sub_x2})&SUBSET=Y({sub_y1},{sub_y2})&"
                        f"SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/4326&"
                        f"OUTPUTCRS=http://www.opengis.net/def/crs/EPSG/0/4326"
                    )
                    req = urllib.request.Request(url, headers={"User-Agent": "SoilDepth-AI/1.0"})
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        content = resp.read()

                    with open(filepath, "wb") as f:
                        f.write(content)
                    print(f"  -> Downloaded: {prop}/{filename} ({len(content)} bytes)")

                manifest_records.append(
                    self.create_manifest_record(
                        filepath=filepath,
                        spatial_resolution="250 m",
                        temporal_resolution="Static edaphic baseline",
                        units=f"Raw Integer DN (Scale {SCALE_FACTORS[prop]})",
                        crs="EPSG:4326 (WGS84)",
                        status="VERIFIED_RAW_SAVED",
                        notes=f"SoilGrids {prop} mean at {depth} for {self.station_config.station_id}",
                        collection_identifier=f"isric-soilgrids-{prop}",
                        temporal_coverage="Static (SoilGrids v2.0 2020 Release)",
                        download_url_or_id=f"https://maps.isric.org/mapserv?map=/map/{prop}.map&COVERAGEID={prop}_{depth}_mean",
                    )
                )
                try:
                    acquired_files.append(str(filepath.relative_to(self.raw_dir)))
                except ValueError:
                    acquired_files.append(str(filepath.name))

        return {
            "status": "ACQUISITION_SUCCESS",
            "files_acquired": acquired_files,
            "manifest_records": manifest_records,
        }

    def _determine_sampling_pixel(self) -> Tuple[int, int]:
        """
        Determines the optimal pixel row and column inside the acquired GeoTIFF.
        Defaults to center pixel (h//2, w//2). If the center pixel lands on an
        ISRIC water mask or NoData cell (<= 0), selects the nearest valid terrestrial pixel.
        """
        ref_file = self.raw_dir / "clay" / "clay_mean_0-5cm.tif"
        if not ref_file.exists():
            self.acquire()

        with Image.open(ref_file) as img:
            arr = np.array(img)
            h, w = arr.shape
            mid_r, mid_c = h // 2, w // 2

            if arr[mid_r, mid_c] > 0:
                return mid_r, mid_c

            # Search nearest valid terrestrial pixel (> 0)
            valid_coords = []
            for r in range(h):
                for c in range(w):
                    if arr[r, c] > 0:
                        dist = math.hypot(r - mid_r, c - mid_c)
                        valid_coords.append((dist, r, c))

            if valid_coords:
                valid_coords.sort(key=lambda x: x[0])
                best_r, best_c = valid_coords[0][1], valid_coords[0][2]
                print(f"[{self.name}] Center pixel ({mid_r}, {mid_c}) is masked NoData/water; sampled nearest valid pixel ({best_r}, {best_c})")
                return best_r, best_c

            return mid_r, mid_c

    def extract_features(self, start_date: str = "", end_date: str = "") -> pd.DataFrame:
        """
        Parses all 32 GeoTIFFs, extracts station pixel values, applies scale factors,
        constructs mass-balance closure checks, and derives explicit hydraulic features.
        """
        samp_r, samp_c = self._determine_sampling_pixel()

        raw_values: Dict[str, int] = {}
        scaled_values: Dict[str, float] = {}

        for prop in SOILGRIDS_PROPERTIES:
            prop_dir = self.raw_dir / prop
            scale = SCALE_FACTORS[prop]

            for depth in SOILGRIDS_DEPTHS:
                depth_tag = depth.replace("-", "_")
                filepath = prop_dir / f"{prop}_mean_{depth}.tif"

                if not filepath.exists():
                    self.acquire()

                with Image.open(filepath) as img:
                    arr = np.array(img)
                    val = int(arr[samp_r, samp_c])

                col_raw = f"soilgrids_{prop}_{depth_tag}_raw"
                col_scaled = f"soilgrids_{prop}_{depth_tag}"

                raw_values[col_raw] = val
                scaled_values[col_scaled] = round(val / scale, 4)

        # Build feature dictionary
        features: Dict[str, Any] = {
            "station_id": self.station_config.station_id,
            "latitude": self.station_config.latitude,
            "longitude": self.station_config.longitude,
        }
        features.update(raw_values)
        features.update(scaled_values)

        # Mass balance & Derived hydraulic features per depth interval
        for depth in SOILGRIDS_DEPTHS:
            d = depth.replace("-", "_")
            c = features[f"soilgrids_clay_{d}"]
            s = features[f"soilgrids_sand_{d}"]
            si = features[f"soilgrids_silt_{d}"]
            raw_sum = round(c + s + si, 2)
            features[f"soilgrids_texture_sum_{d}"] = raw_sum

            # Derived Available Water Capacity (AWC = FC - WP)
            fc = features[f"soilgrids_wv0033_{d}"]
            wp = features[f"soilgrids_wv1500_{d}"]
            sat = features[f"soilgrids_wv0010_{d}"]

            awc = max(0.0, round(fc - wp, 4))
            drainable_porosity = max(0.0, round(sat - fc, 4))

            features[f"derived_awc_{d}"] = awc
            features[f"derived_field_capacity_{d}"] = fc
            features[f"derived_wilting_point_{d}"] = wp
            features[f"derived_drainable_porosity_{d}"] = drainable_porosity

        return pd.DataFrame([features])

    def validate_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validates physical range constraints and texture mass balance closure."""
        issues = []
        row = df.iloc[0]

        # 1. Texture closure: Clay + Sand + Silt == 100% (+-1.0% tolerance)
        for depth in SOILGRIDS_DEPTHS:
            d = depth.replace("-", "_")
            tot = row[f"soilgrids_texture_sum_{d}"]
            if abs(tot - 100.0) > 1.0:
                issues.append(f"Texture sum at {depth} is {tot}%, violates 100% mass balance closure")

            # Check hydraulic order: WP < FC <= SAT
            wp = row[f"derived_wilting_point_{d}"]
            fc = row[f"derived_field_capacity_{d}"]
            sat = row[f"soilgrids_wv0010_{d}"]
            if not (wp < fc <= sat):
                issues.append(f"Hydraulic suction inversion at {depth}: WP={wp}, FC={fc}, SAT={sat}")

            # Bulk density range
            bd = row[f"soilgrids_bdod_{d}"]
            if not (0.8 <= bd <= 2.0):
                issues.append(f"Bulk density {bd} g/cm3 at {depth} outside physical range [0.8, 2.0]")

        return {
            "adapter": self.name,
            "station_id": self.station_config.station_id,
            "texture_mass_balance_closure_verified": True if not any("Texture sum" in i for i in issues) else False,
            "hydraulic_suction_order_verified": True if not any("Hydraulic suction inversion" in i for i in issues) else False,
            "derived_features_distinguished": True,
            "is_valid": len(issues) == 0,
            "issues": issues,
        }
