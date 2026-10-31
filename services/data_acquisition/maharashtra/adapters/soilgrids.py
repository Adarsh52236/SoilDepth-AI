"""
SoilDepth-AI — SoilGrids 250m Static Soil Property Adapter
Pilot Station: IITM-PUNE-COSMOS
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Discovers, retrieves, parses, scales, and physically validates static soil
         physical and hydraulic properties from ISRIC SoilGrids v2.0 OGC WCS for IITM Pune.
"""

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from PIL import Image

from ..config import (
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
    "bdod": 100.0,       # cg/cm³ -> g/cm³
    "clay": 10.0,        # g/kg -> %
    "sand": 10.0,        # g/kg -> %
    "silt": 10.0,        # g/kg -> %
    "ocd": 10.0,         # hg/m³ -> kg/m³
    "wv0010": 1000.0,    # 10 * cm³/dm³ -> m³/m³
    "wv0033": 1000.0,    # 10 * cm³/dm³ -> m³/m³
    "wv1500": 1000.0,    # 10 * cm³/dm³ -> m³/m³
}


class SoilGridsAdapter(BaseEnvironmentalAdapter):
    """ISRIC SoilGrids v2.0 WCS data adapter."""

    def __init__(self, raw_dir: Path = SOILGRIDS_RAW_DIR):
        super().__init__(
            name="SoilGrids",
            source="ISRIC — World Soil Information (SoilGrids v2.0 250m WCS)",
            raw_dir=raw_dir,
        )

    def acquire(self, start_date: str = "", end_date: str = "") -> Dict[str, Any]:
        """
        Retrieves all 32 GeoTIFF tiles (8 properties x 4 depths) via ISRIC OGC WCS 2.0.1.
        """
        manifest_records = []
        acquired_files = []

        print(f"[{self.name}] Acquiring 32 SoilGrids v2.0 GeoTIFFs for {STATION_ID}...")

        # Small 0.01 deg bounding box around station (18.5372, 73.8051)
        sub_x1 = round(STATION_LONGITUDE - 0.005, 4)
        sub_x2 = round(STATION_LONGITUDE + 0.005, 4)
        sub_y1 = round(STATION_LATITUDE - 0.005, 4)
        sub_y2 = round(STATION_LATITUDE + 0.005, 4)

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
                        temporal_resolution="Static edaphic estimate",
                        units=f"Raw Integer (Scale {SCALE_FACTORS[prop]})",
                        crs="EPSG:4326 (WGS84)",
                        status="VERIFIED_RAW_SAVED",
                        notes=f"SoilGrids {prop} mean at {depth}",
                    )
                )
                acquired_files.append(str(filepath.relative_to(self.raw_dir)))

        return {
            "status": "ACQUISITION_SUCCESS",
            "files_acquired": acquired_files,
            "manifest_records": manifest_records,
        }

    def extract_features(self, start_date: str = "", end_date: str = "") -> pd.DataFrame:
        """
        Parses all 32 GeoTIFFs, extracts station pixel values, applies scale factors,
        and constructs the static edaphic feature row.
        """
        raw_values: Dict[str, int] = {}
        scaled_values: Dict[str, float] = {}

        for prop in SOILGRIDS_PROPERTIES:
            prop_dir = self.raw_dir / prop
            scale = SCALE_FACTORS[prop]

            for depth in SOILGRIDS_DEPTHS:
                depth_tag = depth.replace("-", "_")
                filename = f"{prop}_mean_{depth}.tif"
                filepath = prop_dir / filename

                if not filepath.exists():
                    self.acquire()

                with Image.open(filepath) as img:
                    arr = np.array(img)
                    # Extract center pixel of downloaded 4x4 or 3x3 crop
                    center_r = arr.shape[0] // 2
                    center_c = arr.shape[1] // 2
                    raw_dn = int(arr[center_r, center_c])

                raw_col = f"soilgrids_{prop}_{depth_tag}_raw"
                scaled_col = f"soilgrids_{prop}_{depth_tag}"

                raw_values[raw_col] = raw_dn
                if prop in ["wv0010", "wv0033", "wv1500"]:
                    scaled_val = round(raw_dn / scale, 4)
                elif prop in ["clay", "sand", "silt", "ocd"]:
                    scaled_val = round(raw_dn / scale, 2)
                else:  # bdod
                    scaled_val = round(raw_dn / scale, 3)

                scaled_values[scaled_col] = scaled_val

        # Merge into single row matching AAMU-JTG schema
        record: Dict[str, Any] = {
            "station_id": STATION_ID,
            "latitude": STATION_LATITUDE,
            "longitude": STATION_LONGITUDE,
            "elevation_m": BENCHMARK_ELEVATION_M,
            "raster_crs": "EPSG:4326",
        }

        # Interleave raw and scaled features
        for prop in SOILGRIDS_PROPERTIES:
            for depth in SOILGRIDS_DEPTHS:
                depth_tag = depth.replace("-", "_")
                raw_col = f"soilgrids_{prop}_{depth_tag}_raw"
                scaled_col = f"soilgrids_{prop}_{depth_tag}"
                record[raw_col] = raw_values[raw_col]
                record[scaled_col] = scaled_values[scaled_col]

        return pd.DataFrame([record])

    def validate_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validates soil texture closure, bulk density, and hydraulic suction hierarchy."""
        issues = []
        checks = {}

        for depth in SOILGRIDS_DEPTHS:
            depth_tag = depth.replace("-", "_")
            c = float(df[f"soilgrids_clay_{depth_tag}"].iloc[0])
            s = float(df[f"soilgrids_sand_{depth_tag}"].iloc[0])
            si = float(df[f"soilgrids_silt_{depth_tag}"].iloc[0])
            tex_sum = round(c + s + si, 2)
            checks[f"texture_sum_{depth}"] = tex_sum

            # Mass balance closure within +/- 3%
            if abs(tex_sum - 100.0) > 3.0:
                issues.append(f"Texture sum at {depth} is {tex_sum}%, exceeds 100 +/- 3% tolerance")

            bdod = float(df[f"soilgrids_bdod_{depth_tag}"].iloc[0])
            checks[f"bdod_{depth}"] = bdod
            if bdod < PHYSICAL_LIMITS["soil_bulk_density_g_cm3"]["min"] or bdod > PHYSICAL_LIMITS["soil_bulk_density_g_cm3"]["max"]:
                issues.append(f"Bulk density at {depth} ({bdod} g/cm3) out of bounds")

            # Suction hierarchy: wv1500 (wilting point) < wv0033 (field cap) < wv0010 (rapid drainage)
            wv10 = float(df[f"soilgrids_wv0010_{depth_tag}"].iloc[0])
            wv33 = float(df[f"soilgrids_wv0033_{depth_tag}"].iloc[0])
            wv1500 = float(df[f"soilgrids_wv1500_{depth_tag}"].iloc[0])

            checks[f"suction_hierarchy_{depth}"] = bool(wv1500 < wv33 < wv10)
            if not (wv1500 < wv33 < wv10):
                issues.append(f"Suction hierarchy violated at {depth}: wv1500={wv1500}, wv33={wv33}, wv10={wv10}")

        return {
            "adapter": self.name,
            "is_valid": len(issues) == 0,
            "texture_checks": checks,
            "issues": issues,
        }

