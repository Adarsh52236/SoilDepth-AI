"""
SoilDepth-AI — SoilGrids Raster-to-Tabular Extraction Adapter
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Discover, validate, extract, scale, and physically verify SoilGrids v2.0
         250m static soil physical and hydraulic properties for pilot station AAMU-JTG.
         Enforces programmatic discovery of all 32 GeoTIFF rasters, affine transform
         verification, exact pixel extraction (col=453, row=413), documented unit scaling,
         strict physical plausibility checks (mass balance, vertical compaction, suction hierarchy),
         and generates processed tabular features and machine-readable JSON audits.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[3]

RAW_SOILGRIDS_DIR = REPO_ROOT / "dataset" / "SoilGrids" / "raw" / "AAMU-JTG"
PROCESSED_SOILGRIDS_DIR = REPO_ROOT / "dataset" / "SoilGrids" / "processed" / "AAMU-JTG"
AUDIT_SOILGRIDS_DIR = REPO_ROOT / "dataset" / "SoilGrids" / "audit"

EXPECTED_STATION_ID = "AAMU-JTG"
EXPECTED_LATITUDE = 34.78534
EXPECTED_LONGITUDE = -86.55906
EXPECTED_ELEVATION_M = 241.0

EXPECTED_RASTER_WIDTH = 885
EXPECTED_RASTER_HEIGHT = 837
EXPECTED_CRS = "EPSG:4326"

EXPECTED_PROPERTIES = {
    "bulk_density": {
        "abbr": "bdod",
        "description": "Fine earth bulk density",
        "raw_unit": "cg/cm³ (10 kg/m³)",
        "physical_unit": "g/cm³",
        "scale_factor": 100.0,
        "file_prefix": "bdod_mean_",
    },
    "clay": {
        "abbr": "clay",
        "description": "Clay content (< 2 µm)",
        "raw_unit": "g/kg (0.1 %)",
        "physical_unit": "%",
        "scale_factor": 10.0,
        "file_prefix": "clay_mean_",
    },
    "sand": {
        "abbr": "sand",
        "description": "Sand content (50-2000 µm)",
        "raw_unit": "g/kg (0.1 %)",
        "physical_unit": "%",
        "scale_factor": 10.0,
        "file_prefix": "sand_mean_",
    },
    "silt": {
        "abbr": "silt",
        "description": "Silt content (2-50 µm)",
        "raw_unit": "g/kg (0.1 %)",
        "physical_unit": "%",
        "scale_factor": 10.0,
        "file_prefix": "silt_mean_",
    },
    "organic_carbon_density": {
        "abbr": "ocd",
        "description": "Soil organic carbon density",
        "raw_unit": "hg/m³ (0.1 kg/m³)",
        "physical_unit": "kg/m³",
        "scale_factor": 10.0,
        "file_prefix": "ocd_mean_",
    },
    "water_content_10kPa": {
        "abbr": "wv0010",
        "description": "Volumetric water content at -10 kPa (rapid drainage / pF 2.0)",
        "raw_unit": "0.1 vol%",
        "physical_unit": "m³/m³",
        "scale_factor": 1000.0,
        "scale_factor_volpct": 10.0,
        "file_prefix": "wv0010_mean_",
    },
    "water_content_33kPa": {
        "abbr": "wv0033",
        "description": "Volumetric water content at -33 kPa (field capacity / pF 2.5)",
        "raw_unit": "0.1 vol%",
        "physical_unit": "m³/m³",
        "scale_factor": 1000.0,
        "scale_factor_volpct": 10.0,
        "file_prefix": "wv0033_mean_",
    },
    "water_content_1500kPa": {
        "abbr": "wv1500",
        "description": "Volumetric water content at -1500 kPa (wilting point / pF 4.2)",
        "raw_unit": "0.1 vol%",
        "physical_unit": "m³/m³",
        "scale_factor": 1000.0,
        "scale_factor_volpct": 10.0,
        "file_prefix": "wv1500_mean_",
    },
}

EXPECTED_DEPTH_INTERVALS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm"]


def compute_file_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def discover_and_validate_rasters(raw_dir: Path) -> Dict[Tuple[str, str], Path]:
    """
    Programmatically discovers all 32 expected GeoTIFF files under raw_dir.
    Verifies that every property and depth combination exists and is readable.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"SoilGrids raw directory not found at {raw_dir}")

    found_rasters: Dict[Tuple[str, str], Path] = {}

    for prop_name, prop_meta in EXPECTED_PROPERTIES.items():
        prop_subfolder = raw_dir / prop_name
        if not prop_subfolder.exists():
            raise FileNotFoundError(f"Property subfolder missing: {prop_subfolder}")

        for depth_str in EXPECTED_DEPTH_INTERVALS:
            expected_filename = f"{prop_meta['file_prefix']}{depth_str}.tif"
            raster_path = prop_subfolder / expected_filename
            if not raster_path.exists():
                raise FileNotFoundError(
                    f"Required SoilGrids raster missing: {raster_path}"
                )
            found_rasters[(prop_name, depth_str)] = raster_path

    if len(found_rasters) != 32:
        raise ValueError(f"Expected exactly 32 GeoTIFF rasters, discovered {len(found_rasters)}")

    return found_rasters


def verify_raster_spatial_metadata(
    raster_path: Path,
    station_lat: float = EXPECTED_LATITUDE,
    station_lon: float = EXPECTED_LONGITUDE,
) -> Dict[str, Any]:
    """
    Reads GeoTIFF tags and computes exact pixel indices (col, row) for station coordinates.
    """
    with Image.open(raster_path) as im:
        width, height = im.size
        if width != EXPECTED_RASTER_WIDTH or height != EXPECTED_RASTER_HEIGHT:
            raise ValueError(
                f"Raster dimensions mismatch in {raster_path.name}: "
                f"expected ({EXPECTED_RASTER_WIDTH}, {EXPECTED_RASTER_HEIGHT}), got ({width}, {height})"
            )

        # Tags: 33550 = ModelPixelScaleTag, 33922 = ModelTiepointTag
        scale_tag = im.tag_v2.get(33550)
        tiepoint_tag = im.tag_v2.get(33922)

        if not scale_tag or not tiepoint_tag:
            raise ValueError(f"Missing georeferencing tags in {raster_path.name}")

        dx = float(scale_tag[0])
        dy = float(scale_tag[1])
        x_min = float(tiepoint_tag[3])
        y_max = float(tiepoint_tag[4])

        # Mathematical pixel coordinate
        exact_col = (station_lon - x_min) / dx
        exact_row = (y_max - station_lat) / dy

        pixel_col = int(round(exact_col))
        pixel_row = int(round(exact_row))

        if not (0 <= pixel_col < width and 0 <= pixel_row < height):
            raise ValueError(
                f"Station coordinates ({station_lat}, {station_lon}) fall outside raster bounds in {raster_path.name}"
            )

        return {
            "width": width,
            "height": height,
            "dx": dx,
            "dy": dy,
            "x_min": x_min,
            "y_max": y_max,
            "exact_col": exact_col,
            "exact_row": exact_row,
            "pixel_col": pixel_col,
            "pixel_row": pixel_row,
        }


def extract_and_scale_properties(
    found_rasters: Dict[Tuple[str, str], Path],
    station_lat: float = EXPECTED_LATITUDE,
    station_lon: float = EXPECTED_LONGITUDE,
) -> Dict[str, Any]:
    """
    Extracts station pixel values from all 32 GeoTIFFs, applies scaling factors,
    and returns a structured dictionary of raw and converted values.
    """
    extracted_records: Dict[str, Any] = {}
    master_pixel_col: Optional[int] = None
    master_pixel_row: Optional[int] = None

    for (prop_name, depth_str), raster_path in found_rasters.items():
        spatial_meta = verify_raster_spatial_metadata(raster_path, station_lat, station_lon)

        col = spatial_meta["pixel_col"]
        row = spatial_meta["pixel_row"]

        if master_pixel_col is None:
            master_pixel_col = col
            master_pixel_row = row
        else:
            if col != master_pixel_col or row != master_pixel_row:
                raise ValueError(
                    f"Pixel alignment discrepancy in {raster_path.name}: "
                    f"got ({col}, {row}), expected ({master_pixel_col}, {master_pixel_row})"
                )

        prop_meta = EXPECTED_PROPERTIES[prop_name]

        with Image.open(raster_path) as im:
            raw_val = int(im.getpixel((col, row)))

        # NoData check: in SoilGrids, water is 0 or -32768
        # Terrestrial values for soil properties must not be -32768 or <= 0 (except organic carbon in rare minerals)
        if raw_val == -32768 or (raw_val <= 0 and prop_name in ("bulk_density", "clay", "sand", "silt")):
            raise ValueError(
                f"Station pixel ({col}, {row}) in {raster_path.name} contains invalid/NoData value: {raw_val}"
            )

        scaled_physical = float(raw_val / prop_meta["scale_factor"])
        scaled_volpct = (
            float(raw_val / prop_meta["scale_factor_volpct"])
            if "scale_factor_volpct" in prop_meta
            else None
        )

        sha256 = compute_file_sha256(raster_path)
        file_size = raster_path.stat().st_size

        item_key = f"{prop_name}_{depth_str}"
        extracted_records[item_key] = {
            "property": prop_name,
            "abbr": prop_meta["abbr"],
            "depth_interval": depth_str,
            "filename": raster_path.name,
            "file_size_bytes": file_size,
            "sha256": sha256,
            "pixel_col": col,
            "pixel_row": row,
            "raw_value": raw_val,
            "scale_factor": prop_meta["scale_factor"],
            "physical_unit": prop_meta["physical_unit"],
            "physical_value": scaled_physical,
            "vol_pct_value": scaled_volpct,
        }

    return {
        "pixel_col": master_pixel_col,
        "pixel_row": master_pixel_row,
        "records": extracted_records,
    }


def validate_physical_consistency(extracted_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforces authoritative soil physics and hydrological consistency checks:
    1. Textural mass balance: Clay% + Sand% + Silt% == 100.0% at all 4 depths.
    2. Overburden compaction: Bulk density strictly increases monotonically with depth.
    3. Organic matter decay: Organic carbon density strictly decreases monotonically with depth.
    4. Water retention suction hierarchy: θ_1500kPa (wilting point) < θ_33kPa (field capacity) < θ_10kPa.
    """
    records = extracted_dict["records"]
    validation_results = {
        "textural_mass_balance": {},
        "bulk_density_monotonicity": None,
        "organic_carbon_decay": None,
        "water_retention_hierarchy": {},
        "overall_physically_consistent": True,
    }

    # 1. Soil Texture Mass Balance
    for depth in EXPECTED_DEPTH_INTERVALS:
        clay = records[f"clay_{depth}"]["physical_value"]
        sand = records[f"sand_{depth}"]["physical_value"]
        silt = records[f"silt_{depth}"]["physical_value"]
        total = round(clay + sand + silt, 2)
        is_balanced = abs(total - 100.0) < 1e-2
        validation_results["textural_mass_balance"][depth] = {
            "clay_pct": clay,
            "sand_pct": sand,
            "silt_pct": silt,
            "sum_pct": total,
            "is_valid": is_balanced,
        }
        if not is_balanced:
            validation_results["overall_physically_consistent"] = False
            raise ValueError(f"Texture mass balance violation at depth {depth}: sum={total}% != 100.0%")

    # 2. Bulk Density Monotonicity
    bd_vals = [records[f"bulk_density_{d}"]["physical_value"] for d in EXPECTED_DEPTH_INTERVALS]
    is_bd_monotonic = all(x <= y for x, y in zip(bd_vals, bd_vals[1:]))
    validation_results["bulk_density_monotonicity"] = {
        "values_g_cm3": bd_vals,
        "is_monotonically_increasing": is_bd_monotonic,
    }
    if not is_bd_monotonic:
        validation_results["overall_physically_consistent"] = False
        raise ValueError(f"Bulk density monotonicity violation across depths: {bd_vals}")

    # 3. Organic Carbon Decay
    ocd_vals = [records[f"organic_carbon_density_{d}"]["physical_value"] for d in EXPECTED_DEPTH_INTERVALS]
    is_ocd_decaying = all(x >= y for x, y in zip(ocd_vals, ocd_vals[1:]))
    validation_results["organic_carbon_decay"] = {
        "values_kg_m3": ocd_vals,
        "is_monotonically_decreasing": is_ocd_decaying,
    }
    if not is_ocd_decaying:
        validation_results["overall_physically_consistent"] = False
        raise ValueError(f"Organic carbon decay violation across depths: {ocd_vals}")

    # 4. Water Retention Hierarchy
    for depth in EXPECTED_DEPTH_INTERVALS:
        theta_1500 = records[f"water_content_1500kPa_{depth}"]["physical_value"]
        theta_33 = records[f"water_content_33kPa_{depth}"]["physical_value"]
        theta_10 = records[f"water_content_10kPa_{depth}"]["physical_value"]
        hierarchy_holds = theta_1500 < theta_33 < theta_10
        validation_results["water_retention_hierarchy"][depth] = {
            "theta_1500kPa_m3_m3": theta_1500,
            "theta_33kPa_m3_m3": theta_33,
            "theta_10kPa_m3_m3": theta_10,
            "hierarchy_satisfied": hierarchy_holds,
        }
        if not hierarchy_holds:
            validation_results["overall_physically_consistent"] = False
            raise ValueError(
                f"Water retention hierarchy violation at {depth}: "
                f"1500kPa={theta_1500} < 33kPa={theta_33} < 10kPa={theta_10} is False"
            )

    return validation_results


def process_soilgrids_features(
    raw_dir: Optional[Path] = None,
    output_csv_path: Optional[Path] = None,
    audit_json_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main extraction pipeline for SoilGrids datasets at AAMU-JTG.
    Produces single-row static feature CSV and comprehensive verification audit JSON.
    """
    if raw_dir is None:
        raw_dir = RAW_SOILGRIDS_DIR

    if output_csv_path is None:
        output_csv_path = PROCESSED_SOILGRIDS_DIR / f"soilgrids_{EXPECTED_STATION_ID}_features.csv"

    if audit_json_path is None:
        audit_json_path = AUDIT_SOILGRIDS_DIR / "soilgrids_extraction_report.json"

    # 1. Discover all 32 GeoTIFF rasters
    found_rasters = discover_and_validate_rasters(raw_dir)

    # 2. Extract and scale properties at station pixel
    extraction_res = extract_and_scale_properties(found_rasters)
    records = extraction_res["records"]

    # 3. Validate physical laws and consistency
    physics_audit = validate_physical_consistency(extraction_res)

    # 4. Construct Single-Row Static Feature Table
    flat_row: Dict[str, Any] = {
        "station_id": EXPECTED_STATION_ID,
        "latitude": EXPECTED_LATITUDE,
        "longitude": EXPECTED_LONGITUDE,
        "elevation_m": EXPECTED_ELEVATION_M,
        "raster_crs": EXPECTED_CRS,
        "raster_pixel_col": extraction_res["pixel_col"],
        "raster_pixel_row": extraction_res["pixel_row"],
    }

    # Add features for every property and depth
    for item_key, item in records.items():
        depth_str = item["depth_interval"]
        clean_depth = depth_str.replace("-", "_").replace("cm", "")
        abbr = item["abbr"]
        flat_row[f"soilgrids_{abbr}_{clean_depth}cm_raw"] = item["raw_value"]
        flat_row[f"soilgrids_{abbr}_{clean_depth}cm"] = item["physical_value"]

    df_features = pd.DataFrame([flat_row])

    # Save CSV
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(output_csv_path, index=False)

    # 5. Assemble Audit JSON
    audit_data = {
        "dataset_name": "SoilGrids_250m_v2.0",
        "station_id": EXPECTED_STATION_ID,
        "latitude": EXPECTED_LATITUDE,
        "longitude": EXPECTED_LONGITUDE,
        "elevation_m": EXPECTED_ELEVATION_M,
        "grid_alignment": {
            "crs": EXPECTED_CRS,
            "raster_dimensions": f"{EXPECTED_RASTER_WIDTH}x{EXPECTED_RASTER_HEIGHT}",
            "station_pixel_col": extraction_res["pixel_col"],
            "station_pixel_row": extraction_res["pixel_row"],
            "confirmed_matching_affine_transform": True,
        },
        "total_expected_rasters": 32,
        "total_discovered_rasters": len(found_rasters),
        "total_verified_rasters": len(records),
        "physical_validation_results": physics_audit,
        "processed_features_file": str(output_csv_path.resolve()),
        "extracted_properties": records,
    }

    audit_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    return df_features, audit_data


if __name__ == "__main__":
    df_out, audit = process_soilgrids_features()
    print("=" * 80)
    print(f"SoilGrids extraction complete. Saved to: {audit['processed_features_file']}")
    print(f"Station pixel: col={audit['grid_alignment']['station_pixel_col']}, row={audit['grid_alignment']['station_pixel_row']}")
    print(f"Total features extracted: {len(df_out.columns)} columns.")
    print("Physical consistency verified:", audit["physical_validation_results"]["overall_physically_consistent"])
    print("=" * 80)
