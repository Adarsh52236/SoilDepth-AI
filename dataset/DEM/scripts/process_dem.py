"""
SoilDepth-AI — Digital Elevation Model (DEM) Processing & Extraction Adapter
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Ingest, validate, extract, and derive topographic predictors for ground stations
         (pilot: AAMU-JTG). Enforces rigorous raster integrity checks, GeoTIFF spatial
         tag parsing, station spatial coverage verification, elevation extraction against
         ground-truth benchmarks (241.0 m +/- 15 m), conditional Horn (1981) 3x3 slope
         derivation with boundary/NoData guards, processed tabular dataset export, and
         machine-readable JSON quality audits. Gracefully handles unpopulated raw states.
"""

import os
import sys
import math
import json
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List, Union
import numpy as np
import pandas as pd
from PIL import Image

# Repository Root & Standard Directory Paths
REPO_ROOT = Path(__file__).resolve().parents[3]

DEM_DIR = REPO_ROOT / "dataset" / "DEM"
DEM_RAW_DIR = DEM_DIR / "raw"
DEM_PROCESSED_DIR = DEM_DIR / "processed"
DEM_AUDIT_DIR = DEM_DIR / "audit"
DEM_MANIFEST_DIR = DEM_DIR / "manifests"

# Station Topographic Reference Registry
STATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "AAMU-JTG": {
        "network": "SCAN",
        "site_name": "Alabama A&M University - Winfred Thomas Agricultural Research Station",
        "latitude": 34.78534,
        "longitude": -86.55906,
        "benchmark_elevation_m": 241.0,
        "elevation_tolerance_m": 15.0,
        "expected_elevation_min_m": 150.0,
        "expected_elevation_max_m": 450.0,
        "recommended_bbox": {
            "min_latitude": 34.68,
            "max_latitude": 34.88,
            "min_longitude": -86.66,
            "max_longitude": -86.46,
            "standard_1deg_tile_id": "n34_w087",
        },
    }
}

# Standard NoData Sentinels in Geoscientific Rasters
STANDARD_NODATA_VALUES = {-9999.0, -32767.0, -32768.0, -3.4028235e38, 9999.0, 32767.0}
EARTH_EQUATORIAL_RADIUS_M = 6378137.0


def compute_file_sha256(filepath: Union[str, Path]) -> str:
    """Computes SHA-256 hash of a file for immutable audit tracking."""
    filepath = Path(filepath)
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_geotiff_spatial_metadata(img: Image.Image) -> Dict[str, Any]:
    """
    Extracts GeoTIFF georeferencing metadata from TIFF tags (ModelPixelScaleTag,
    ModelTiepointTag, GeoKeyDirectoryTag, GDAL_NODATA) without third-party dependencies.
    """
    meta: Dict[str, Any] = {
        "has_geotiff_tags": False,
        "pixel_scale": None,
        "tiepoint": None,
        "dx": None,
        "dy": None,
        "x_origin": None,
        "y_origin": None,
        "x_min": None,
        "x_max": None,
        "y_min": None,
        "y_max": None,
        "crs_estimated": "EPSG:4326 (WGS84)",
        "horizontal_units": "degrees",
        "nodata_tag_value": None,
    }

    if not hasattr(img, "tag_v2"):
        return meta

    # GeoTIFF Tag IDs:
    # 33550: ModelPixelScaleTag (dx, dy, dz)
    # 33922: ModelTiepointTag (I, J, K, X, Y, Z)
    # 34735: GeoKeyDirectoryTag
    # 42113: GDAL_NODATA (ASCII)
    tags = img.tag_v2

    scale_tag = tags.get(33550)
    tiepoint_tag = tags.get(33922)
    nodata_tag = tags.get(42113)

    if nodata_tag:
        try:
            if isinstance(nodata_tag, bytes):
                nodata_str = nodata_tag.decode("utf-8", errors="ignore").strip("\x00 \r\n")
            else:
                nodata_str = str(nodata_tag).strip("\x00 \r\n")
            meta["nodata_tag_value"] = float(nodata_str)
        except (ValueError, TypeError):
            pass

    if scale_tag and tiepoint_tag:
        meta["has_geotiff_tags"] = True
        try:
            dx = float(scale_tag[0])
            dy = float(scale_tag[1])
            x_origin = float(tiepoint_tag[3])
            y_origin = float(tiepoint_tag[4])

            meta["pixel_scale"] = tuple(float(x) for x in scale_tag)
            meta["tiepoint"] = tuple(float(x) for x in tiepoint_tag)
            meta["dx"] = dx
            meta["dy"] = dy
            meta["x_origin"] = x_origin
            meta["y_origin"] = y_origin

            # Bounds computation (assuming raster north-up orientation)
            width = img.width
            height = img.height
            meta["x_min"] = round(x_origin, 7)
            meta["x_max"] = round(x_origin + (width * dx), 7)
            meta["y_min"] = round(y_origin - (height * dy), 7)
            meta["y_max"] = round(y_origin, 7)

            if dx > 1.0:
                meta["horizontal_units"] = "meters"
                meta["crs_estimated"] = "Projected CRS (e.g., UTM)"
            else:
                meta["horizontal_units"] = "degrees"
                meta["crs_estimated"] = "EPSG:4326 (WGS84) or EPSG:4269 (NAD83)"
        except (IndexError, TypeError, ValueError) as err:
            meta["has_geotiff_tags"] = False
            meta["error"] = str(err)

    return meta


def inspect_dem_raster(
    filepath: Union[str, Path],
    station_id: str = "AAMU-JTG",
) -> Dict[str, Any]:
    """
    Validates a DEM raster file: file integrity, dimensions, data type,
    georeferencing tags, and valid elevation range.
    """
    filepath = Path(filepath)
    if not filepath.exists() or not filepath.is_file():
        raise FileNotFoundError(f"DEM raster file does not exist: {filepath}")

    file_size = filepath.stat().st_size
    sha256_hash = compute_file_sha256(filepath)
    station_info = STATION_REGISTRY.get(station_id, {})

    profile: Dict[str, Any] = {
        "file_name": filepath.name,
        "file_path": str(filepath.resolve()),
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "sha256": sha256_hash,
        "is_valid": False,
        "error_message": None,
        "warnings": [],
        "width": None,
        "height": None,
        "mode": None,
        "data_type": None,
        "min_elevation": None,
        "max_elevation": None,
        "mean_elevation": None,
        "spatial_metadata": {},
    }

    try:
        with Image.open(filepath) as img:
            profile["width"] = img.width
            profile["height"] = img.height
            profile["mode"] = img.mode

            spatial_meta = extract_geotiff_spatial_metadata(img)
            profile["spatial_metadata"] = spatial_meta

            # Read raster array (for validation and statistics)
            arr = np.array(img, dtype=float)
            profile["data_type"] = str(arr.dtype)

            # Mask out identified NoData
            nodata_val = spatial_meta.get("nodata_tag_value")
            valid_mask = np.isfinite(arr)
            if nodata_val is not None:
                valid_mask &= ~np.isclose(arr, nodata_val)
            for sentinel in STANDARD_NODATA_VALUES:
                valid_mask &= ~np.isclose(arr, sentinel)
            # Mask out obvious unphysical elevation limits (< -500m or > 9000m)
            valid_mask &= (arr >= -500.0) & (arr <= 9000.0)

            if np.any(valid_mask):
                valid_elev = arr[valid_mask]
                profile["min_elevation"] = round(float(np.min(valid_elev)), 2)
                profile["max_elevation"] = round(float(np.max(valid_elev)), 2)
                profile["mean_elevation"] = round(float(np.mean(valid_elev)), 2)

                if station_info:
                    exp_min = station_info.get("expected_elevation_min_m", 0.0)
                    exp_max = station_info.get("expected_elevation_max_m", 5000.0)
                    if (
                        profile["min_elevation"] < exp_min
                        or profile["max_elevation"] > exp_max
                    ):
                        profile["warnings"].append(
                            f"Elevation range [{profile['min_elevation']}, {profile['max_elevation']}] m "
                            f"extends beyond station local terrain bounds [{exp_min}, {exp_max}] m."
                        )
            else:
                profile["warnings"].append("Raster contains no valid finite elevation cells.")

            profile["is_valid"] = True

    except Exception as exc:
        profile["error_message"] = str(exc)
        profile["is_valid"] = False

    return profile


def check_station_coverage(
    spatial_meta: Dict[str, Any],
    lat: float,
    lon: float,
) -> Tuple[bool, Optional[int], Optional[int], Optional[str]]:
    """
    Checks whether station (lat, lon) falls completely within raster bounds
    and calculates 0-indexed column and row indices.
    """
    if not spatial_meta.get("has_geotiff_tags"):
        return False, None, None, "Raster lacks required GeoTIFF spatial georeferencing tags."

    x_min = spatial_meta["x_min"]
    x_max = spatial_meta["x_max"]
    y_min = spatial_meta["y_min"]
    y_max = spatial_meta["y_max"]
    dx = spatial_meta["dx"]
    dy = spatial_meta["dy"]

    if not (x_min <= lon <= x_max and y_min <= lat <= y_max):
        return (
            False,
            None,
            None,
            f"Station coordinate ({lat}, {lon}) falls outside raster bounds "
            f"[Lon: {x_min} to {x_max}, Lat: {y_min} to {y_max}].",
        )

    # Column: distance from west edge / dx
    # Row: distance from north edge / dy
    col_idx = int(round((lon - x_min) / dx))
    row_idx = int(round((y_max - lat) / dy))

    return True, col_idx, row_idx, "Station is covered by raster extent."


def extract_station_elevation(
    arr: np.ndarray,
    col_idx: int,
    row_idx: int,
    nodata_value: Optional[float] = None,
) -> Tuple[Optional[float], bool, str]:
    """
    Extracts elevation value at (row_idx, col_idx) and verifies against NoData sentinels.
    """
    height, width = arr.shape[:2]
    if not (0 <= row_idx < height and 0 <= col_idx < width):
        return None, False, f"Pixel ({col_idx}, {row_idx}) out of array bounds ({width}x{height})."

    val = float(arr[row_idx, col_idx])

    if not np.isfinite(val):
        return None, False, "Station pixel contains non-finite value (NaN/Inf)."

    if nodata_value is not None and np.isclose(val, nodata_value):
        return None, False, f"Station pixel matches raster NoData sentinel ({nodata_value})."

    for sentinel in STANDARD_NODATA_VALUES:
        if np.isclose(val, sentinel):
            return None, False, f"Station pixel matches standard NoData sentinel ({sentinel})."

    return round(val, 2), True, "Valid elevation extraction."


def derive_station_slope(
    arr: np.ndarray,
    col_idx: int,
    row_idx: int,
    dx: float,
    dy: float,
    lat: float,
    horizontal_units: str = "degrees",
    nodata_value: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Derives topographic slope gradient and aspect using Horn's (1981) 3x3 weighted
    finite-difference algorithm.
    Guards against boundary truncation and missing/NoData neighborhood pixels.
    """
    height, width = arr.shape[:2]
    result: Dict[str, Any] = {
        "slope_deg": None,
        "slope_rise_run": None,
        "aspect_deg": None,
        "aspect_sin": None,
        "aspect_cos": None,
        "slope_method": "Horn 3x3 estimator",
        "slope_coverage_valid": False,
        "status": "UNPROCESSED",
    }

    # Boundary check: Requires complete 3x3 neighborhood
    if row_idx - 1 < 0 or row_idx + 1 >= height or col_idx - 1 < 0 or col_idx + 1 >= width:
        result["status"] = "INSUFFICIENT_COVERAGE_BORDER"
        result["notes"] = (
            f"Station pixel ({col_idx}, {row_idx}) is on or adjacent to raster boundary; "
            f"Horn 3x3 estimator requires 1-pixel buffer."
        )
        return result

    # Extract 3x3 neighborhood window
    window = arr[row_idx - 1 : row_idx + 2, col_idx - 1 : col_idx + 2].astype(float)

    # Check for NoData or non-finite values in 3x3 neighborhood
    if not np.all(np.isfinite(window)):
        result["status"] = "INSUFFICIENT_COVERAGE_NONFINITE"
        result["notes"] = "3x3 neighborhood contains non-finite cells."
        return result

    if nodata_value is not None and np.any(np.isclose(window, nodata_value)):
        result["status"] = "INSUFFICIENT_COVERAGE_NODATA"
        result["notes"] = f"3x3 neighborhood contains raster NoData value ({nodata_value})."
        return result

    for sentinel in STANDARD_NODATA_VALUES:
        if np.any(np.isclose(window, sentinel)):
            result["status"] = "INSUFFICIENT_COVERAGE_NODATA"
            result["notes"] = f"3x3 neighborhood contains standard NoData sentinel ({sentinel})."
            return result

    # Convert horizontal cell spacing to meters if in geographic degrees
    if horizontal_units.lower() == "degrees":
        lat_rad = math.radians(lat)
        delta_x = dx * (math.pi / 180.0) * EARTH_EQUATORIAL_RADIUS_M * math.cos(lat_rad)
        delta_y = dy * (math.pi / 180.0) * EARTH_EQUATORIAL_RADIUS_M
    else:
        delta_x = float(dx)
        delta_y = float(dy)

    if delta_x <= 0 or delta_y <= 0:
        result["status"] = "INVALID_GRID_SPACING"
        result["notes"] = f"Grid cell spacing non-positive: dx={delta_x}, dy={delta_y}."
        return result

    # Window cell notation:
    # [z1, z2, z3]
    # [z4, z5, z6]
    # [z7, z8, z9]
    z1, z2, z3 = window[0, 0], window[0, 1], window[0, 2]
    z4, z5, z6 = window[1, 0], window[1, 1], window[1, 2]
    z7, z8, z9 = window[2, 0], window[2, 1], window[2, 2]

    # Horn (1981) partial derivatives
    # Note: row index increases southward (downward), so top row is north, bottom is south
    dz_dx = ((z3 + (2.0 * z6) + z9) - (z1 + (2.0 * z4) + z7)) / (8.0 * delta_x)
    dz_dy = ((z1 + (2.0 * z2) + z3) - (z7 + (2.0 * z8) + z9)) / (8.0 * delta_y)

    rise_run = math.sqrt((dz_dx**2) + (dz_dy**2))
    slope_rad = math.atan(rise_run)
    slope_deg = math.degrees(slope_rad)

    # Aspect calculation (compass azimuth in degrees from North: 0-360)
    aspect_deg: Optional[float] = None
    aspect_sin: Optional[float] = None
    aspect_cos: Optional[float] = None
    if rise_run > 1e-6:
        # Mathematical angle in radians from East
        math_angle = math.atan2(dz_dy, -dz_dx)
        # Convert to navigational compass bearing: 0 = North, 90 = East, 180 = South, 270 = West
        compass_deg = (90.0 - math.degrees(math_angle)) % 360.0
        aspect_deg = round(compass_deg, 2)
        aspect_sin = round(math.sin(math.radians(compass_deg)), 4)
        aspect_cos = round(math.cos(math.radians(compass_deg)), 4)
    else:
        # Flat surface (slope ~ 0)
        aspect_deg = 0.0
        aspect_sin = 0.0
        aspect_cos = 1.0

    result["slope_deg"] = round(slope_deg, 4)
    result["slope_rise_run"] = round(rise_run, 6)
    result["aspect_deg"] = aspect_deg
    result["aspect_sin"] = aspect_sin
    result["aspect_cos"] = aspect_cos
    result["slope_coverage_valid"] = True
    result["status"] = "VALID"
    result["notes"] = f"Horn 3x3 derivative computed: delta_x={delta_x:.2f}m, delta_y={delta_y:.2f}m."

    return result


def process_dem(
    raw_raster_path: Optional[Union[str, Path]] = None,
    station_id: str = "AAMU-JTG",
    output_csv: Optional[Union[str, Path]] = None,
    audit_json: Optional[Union[str, Path]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Main processing entry point.
    Discovers or ingests raw DEM raster, validates integrity and georeferencing,
    verifies station spatial coverage, extracts station elevation, derives slope,
    and produces processed feature CSV and JSON quality audit.
    If no raster is available, returns a compliant 'PENDING_DOWNLOAD' report.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    station_info = STATION_REGISTRY.get(station_id, {})
    if not station_info:
        raise ValueError(f"Station ID '{station_id}' not found in STATION_REGISTRY.")

    station_lat = station_info["latitude"]
    station_lon = station_info["longitude"]
    benchmark_elev = station_info["benchmark_elevation_m"]
    tolerance_m = station_info["elevation_tolerance_m"]

    raw_dir = DEM_RAW_DIR / station_id
    processed_dir = DEM_PROCESSED_DIR / station_id
    audit_dir = DEM_AUDIT_DIR / station_id

    target_csv = Path(output_csv) if output_csv else processed_dir / f"dem_{station_id}_features.csv"
    target_audit = Path(audit_json) if audit_json else audit_dir / "dem_quality_report.json"

    # 1. Discover raw raster file
    if raw_raster_path is not None:
        candidate_files = [Path(raw_raster_path).resolve()]
    else:
        if raw_dir.exists():
            exts = ["*.tif", "*.tiff", "*.geotiff", "*.dem", "*.hgt", "*.asc"]
            candidate_files = []
            for ext in exts:
                candidate_files.extend(list(raw_dir.glob(ext)))
            candidate_files = sorted(candidate_files)
        else:
            candidate_files = []

    # Case A: No raw raster exists -> Report PENDING_DOWNLOAD without errors or fabrications
    if not candidate_files:
        pending_report = {
            "dataset": "DEM",
            "station_id": station_id,
            "timestamp_utc": now_utc,
            "status": "PENDING_DOWNLOAD",
            "validation_status": "PENDING",
            "extraction_status": "PENDING",
            "raw_file_count": 0,
            "raw_directory": str(raw_dir.resolve()) if raw_dir.exists() else str(raw_dir),
            "processed_output_csv": str(target_csv),
            "audit_report_json": str(target_audit),
            "station_target": {
                "station_id": station_id,
                "latitude": station_lat,
                "longitude": station_lon,
                "benchmark_elevation_m": benchmark_elev,
                "elevation_tolerance_m": tolerance_m,
            },
            "features_extracted": None,
            "known_limitations": [
                "No raw DEM raster downloaded yet.",
                "Pilot station AAMU-JTG (SCAN) is in Alabama, USA; does not establish India/Maharashtra coverage.",
                "Slope derivation requires an intact 3x3 surrounding pixel window without NoData cells.",
            ],
            "notes": (
                f"No DEM raster files found in {raw_dir}. Processing interface initialized and ready. "
                "Awaiting manual raster download placement (e.g., USGS 3DEP 1-arcsec, Copernicus GLO-30, or NASADEM)."
            ),
        }
        return pending_report

    # Case B: Raw raster present -> Validate, extract elevation, derive slope, write outputs
    raster_file = candidate_files[0]
    profile = inspect_dem_raster(raster_file, station_id=station_id)

    if not profile["is_valid"]:
        raise ValueError(f"Raster inspection failed for {raster_file}: {profile.get('error_message')}")

    spatial_meta = profile["spatial_metadata"]
    has_cov, col_idx, row_idx, cov_msg = check_station_coverage(
        spatial_meta, station_lat, station_lon
    )

    if not has_cov:
        raise ValueError(
            f"Station {station_id} ({station_lat}, {station_lon}) is not covered by raster: {cov_msg}"
        )

    # Open image array to extract elevation and slope
    with Image.open(raster_file) as img:
        arr = np.array(img, dtype=float)

    nodata_val = spatial_meta.get("nodata_tag_value")
    elev_val, elev_valid, elev_msg = extract_station_elevation(
        arr, col_idx, row_idx, nodata_value=nodata_val
    )

    if not elev_valid or elev_val is None:
        raise ValueError(f"Station pixel elevation extraction failed: {elev_msg}")

    # Benchmark consistency check
    elev_diff = round(abs(elev_val - benchmark_elev), 2)
    is_benchmark_consistent = elev_diff <= tolerance_m

    # Derive slope (Horn 3x3 estimator)
    dx = spatial_meta.get("dx", 0.0)
    dy = spatial_meta.get("dy", 0.0)
    horiz_units = spatial_meta.get("horizontal_units", "degrees")
    slope_info = derive_station_slope(
        arr=arr,
        col_idx=col_idx,
        row_idx=row_idx,
        dx=dx,
        dy=dy,
        lat=station_lat,
        horizontal_units=horiz_units,
        nodata_value=nodata_val,
    )

    # Feature Record
    feature_row = {
        "station_id": station_id,
        "latitude": station_lat,
        "longitude": station_lon,
        "elevation_m": elev_val,
        "benchmark_elevation_m": benchmark_elev,
        "elevation_diff_benchmark_m": elev_diff,
        "is_benchmark_consistent": is_benchmark_consistent,
        "slope_deg": slope_info["slope_deg"],
        "slope_rise_run": slope_info["slope_rise_run"],
        "slope_coverage_valid": slope_info["slope_coverage_valid"],
        "slope_method": slope_info["slope_method"],
        "aspect_deg": slope_info["aspect_deg"],
        "aspect_sin": slope_info["aspect_sin"],
        "aspect_cos": slope_info["aspect_cos"],
        "raster_column_idx": col_idx,
        "raster_row_idx": row_idx,
        "crs": spatial_meta.get("crs_estimated"),
        "horizontal_units": horiz_units,
        "vertical_units": "meters",
        "nodata_value": nodata_val,
        "source_file": raster_file.name,
        "sha256": profile["sha256"],
        "extracted_at_utc": now_utc,
    }

    df_features = pd.DataFrame([feature_row])

    # Comprehensive Quality Audit Report
    quality_report = {
        "dataset": "DEM",
        "station_id": station_id,
        "timestamp_utc": now_utc,
        "status": "PROCESSED",
        "validation_status": "VALIDATED" if is_benchmark_consistent else "WARNING_BENCHMARK_DIVERGENCE",
        "extraction_status": "SUCCESS",
        "raw_source": {
            "filename": raster_file.name,
            "filepath": str(raster_file.resolve()),
            "file_size_bytes": profile["file_size_bytes"],
            "sha256": profile["sha256"],
            "width": profile["width"],
            "height": profile["height"],
            "data_type": profile["data_type"],
            "raster_elevation_min_m": profile["min_elevation"],
            "raster_elevation_max_m": profile["max_elevation"],
            "raster_elevation_mean_m": profile["mean_elevation"],
            "geotiff_spatial_metadata": spatial_meta,
        },
        "station_extraction": {
            "station_id": station_id,
            "latitude": station_lat,
            "longitude": station_lon,
            "pixel_col_idx": col_idx,
            "pixel_row_idx": row_idx,
            "extracted_elevation_m": elev_val,
            "benchmark_elevation_m": benchmark_elev,
            "elevation_diff_m": elev_diff,
            "tolerance_m": tolerance_m,
            "is_benchmark_consistent": is_benchmark_consistent,
            "slope_derivation": slope_info,
        },
        "artifacts_generated": {
            "features_csv": str(target_csv.resolve()),
            "audit_json": str(target_audit.resolve()),
        },
        "known_limitations": [
            "Pilot station AAMU-JTG is a single US SCAN station and does not establish India/Maharashtra ground validation.",
            "Slope derivation requires an intact 3x3 surrounding pixel window without NoData cells.",
        ],
        "notes": (
            f"Successfully processed DEM for {station_id}. Station elevation {elev_val}m "
            f"(benchmark: {benchmark_elev}m, diff: {elev_diff}m). "
            f"Slope: {slope_info['slope_deg']} deg (valid={slope_info['slope_coverage_valid']})."
        ),
    }

    if not dry_run:
        target_csv.parent.mkdir(parents=True, exist_ok=True)
        df_features.to_csv(target_csv, index=False)

        target_audit.parent.mkdir(parents=True, exist_ok=True)
        with open(target_audit, "w", encoding="utf-8") as f:
            json.dump(quality_report, f, indent=2)

    return quality_report


def main():
    parser = argparse.ArgumentParser(description="Process and extract DEM features for SoilDepth-AI.")
    parser.add_argument("--station", type=str, default="AAMU-JTG", help="Station ID (default: AAMU-JTG)")
    parser.add_argument("--file", type=str, default=None, help="Explicit raw DEM raster path")
    parser.add_argument("--output-csv", type=str, default=None, help="Path for processed output CSV")
    parser.add_argument("--audit-json", type=str, default=None, help="Path for output audit JSON")
    parser.add_argument("--dry-run", action="store_true", help="Perform checks without saving files")
    args = parser.parse_args()

    print("=" * 80)
    print(f"SoilDepth-AI — DEM Feature Extraction: Station {args.station}")
    print("=" * 80)

    try:
        report = process_dem(
            raw_raster_path=args.file,
            station_id=args.station,
            output_csv=args.output_csv,
            audit_json=args.audit_json,
            dry_run=args.dry_run,
        )
        print(f"Status: {report['status']}")
        print(f"Validation: {report['validation_status']}")
        print(f"Extraction: {report['extraction_status']}")
        print(f"Notes: {report['notes']}")
        if report.get("station_extraction"):
            ext = report["station_extraction"]
            print(f"Elevation: {ext['extracted_elevation_m']} m (diff: {ext['elevation_diff_m']} m)")
            slp = ext["slope_derivation"]
            print(f"Slope: {slp['slope_deg']} deg (valid={slp['slope_coverage_valid']})")
    except Exception as exc:
        print(f"Processing failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

