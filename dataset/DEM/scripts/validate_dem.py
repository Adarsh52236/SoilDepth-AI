#!/usr/bin/env python3
"""
SoilDepth-AI — Digital Elevation Model (DEM) Validation Tool
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Standalone verification script for manually downloaded DEM rasters.
         Inspects raster dimensions, data types, physical elevation bounds,
         computes SHA-256 checksums, and updates manifests/download_manifest.csv.
"""

import os
import sys
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image

# Benchmark elevation for station AAMU-JTG
STATION_METADATA = {
    "AAMU-JTG": {
        "latitude": 34.78534,
        "longitude": -86.55906,
        "elevation_benchmark_m": 241.0,
        "expected_elevation_min_m": 150.0,
        "expected_elevation_max_m": 450.0,
    }
}


def compute_sha256(filepath: Path) -> str:
    """Calculates SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024 * 8), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def inspect_dem_raster(filepath: Path, station_id: str) -> dict:
    """
    Inspects a DEM GeoTIFF or raster file using PIL / numpy,
    extracting image dimensions, channels, data ranges, and checking physical bounds.
    """
    file_size = filepath.stat().st_size
    sha256_hash = compute_sha256(filepath)
    station_info = STATION_METADATA.get(station_id, {})

    profile = {
        "file_name": filepath.name,
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
        "has_geotiff_tags": False,
    }

    try:
        # Open with PIL (handles standard TIFF and BigTIFF)
        with Image.open(filepath) as img:
            profile["width"] = img.width
            profile["height"] = img.height
            profile["mode"] = img.mode

            # Check for standard GeoTIFF tags
            # 33550: ModelPixelScaleTag, 33922: ModelTiepointTag, 34735: GeoKeyDirectoryTag
            if hasattr(img, "tag_v2"):
                geotiff_tags = [33550, 33922, 34735]
                has_geo = any(tag in img.tag_v2 for tag in geotiff_tags)
                profile["has_geotiff_tags"] = has_geo

            # Read sample or full array depending on file size
            # If raster <= 200 MB, read array directly
            if file_size <= 200 * 1024 * 1024:
                arr = np.array(img, dtype=float)
                profile["data_type"] = str(arr.dtype)

                # Filter out standard NoData markers (-9999, -32767, -3.4e38, etc.)
                valid_mask = np.isfinite(arr) & (arr > -1000.0) & (arr < 10000.0)
                if np.any(valid_mask):
                    valid_elev = arr[valid_mask]
                    min_val = float(np.min(valid_elev))
                    max_val = float(np.max(valid_elev))
                    mean_val = float(np.mean(valid_elev))

                    profile["min_elevation"] = round(min_val, 2)
                    profile["max_elevation"] = round(max_val, 2)
                    profile["mean_elevation"] = round(mean_val, 2)

                    # Physical check against station context
                    if station_info:
                        exp_min = station_info.get("expected_elevation_min_m", 0.0)
                        exp_max = station_info.get("expected_elevation_max_m", 5000.0)
                        if min_val < exp_min or max_val > exp_max:
                            profile["warnings"].append(
                                f"Elevation range [{min_val:.1f}, {max_val:.1f}] m extends beyond "
                                f"typical station local terrain [{exp_min}, {exp_max}] m."
                            )

                profile["is_valid"] = True
            else:
                profile["warnings"].append("Large raster file (>200 MB); full array statistics skipped.")
                profile["is_valid"] = True

    except Exception as e:
        profile["error_message"] = str(e)
        profile["is_valid"] = False

    return profile


def update_download_manifest(manifest_path: Path, profile: dict, station_id: str):
    """Updates or appends file entry in download_manifest.csv."""
    if not manifest_path.exists():
        return

    import pandas as pd
    df = pd.read_csv(manifest_path)

    # Check if station entry exists
    mask = (df["station_id"] == station_id) & (df["dataset"] == "DEM")
    if mask.any():
        idx = df[mask].index[0]
        df.loc[idx, "actual_filename"] = profile["file_name"]
        df.loc[idx, "file_size_bytes"] = profile["file_size_bytes"]
        df.loc[idx, "sha256"] = profile["sha256"]
        df.loc[idx, "status"] = "RAW_DOWNLOAD"
        df.loc[idx, "download_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        df.loc[idx, "validation_status"] = "VALIDATED" if profile["is_valid"] else "FAILED"
        notes = (
            f"Dimensions: {profile.get('width')}x{profile.get('height')}. "
            f"Elev range: [{profile.get('min_elevation')}, {profile.get('max_elevation')}] m."
        )
        df.loc[idx, "notes"] = notes
    else:
        new_row = {
            "dataset": "DEM",
            "station_id": station_id,
            "latitude": STATION_METADATA.get(station_id, {}).get("latitude"),
            "longitude": STATION_METADATA.get(station_id, {}).get("longitude"),
            "bounding_box": "PENDING",
            "source_agency": "PENDING",
            "product_name": "PENDING",
            "resolution_m": 30.0,
            "vertical_datum": "PENDING",
            "crs": "PENDING",
            "format": "GeoTIFF",
            "expected_filename": f"DEM_{station_id}_raw.tif",
            "actual_filename": profile["file_name"],
            "status": "RAW_DOWNLOAD",
            "download_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "file_size_bytes": profile["file_size_bytes"],
            "sha256": profile["sha256"],
            "validation_status": "VALIDATED" if profile["is_valid"] else "FAILED",
            "notes": f"Dimensions: {profile.get('width')}x{profile.get('height')}.",
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_csv(manifest_path, index=False)


def main():
    parser = argparse.ArgumentParser(description="Validate manually downloaded DEM rasters.")
    parser.add_argument("--station", type=str, default="AAMU-JTG", help="Station ID (default: AAMU-JTG)")
    parser.add_argument("--file", type=str, default=None, help="Specific DEM raster file path")
    args = parser.parse_args()

    dem_dir = Path(__file__).resolve().parent.parent
    raw_station_dir = dem_dir / "raw" / args.station
    audit_dir = dem_dir / "audit"
    manifest_path = dem_dir / "manifests" / "download_manifest.csv"

    print("=" * 80)
    print(f"SoilDepth-AI — DEM Raster Validation Tool: Station {args.station}")
    print("=" * 80)

    if args.file:
        target_files = [Path(args.file).resolve()]
    else:
        if not raw_station_dir.exists():
            print(f"Raw directory not found: {raw_station_dir}")
            sys.exit(1)
        exts = ["*.tif", "*.tiff", "*.geotiff", "*.dem", "*.hgt", "*.asc"]
        target_files = []
        for ext in exts:
            target_files.extend(list(raw_station_dir.glob(ext)))
        target_files = sorted(target_files)

    if not target_files:
        print(f"No DEM raster files found in: {raw_station_dir}")
        print("Awaiting manual raster download placement.")
        print(f"Expected path: {raw_station_dir / f'DEM_{args.station}_raw.tif'}")
        return

    print(f"Found {len(target_files)} raster file(s) to inspect:\n")
    all_profiles = []
    for f in target_files:
        print(f"-> Inspecting: {f.name}")
        prof = inspect_dem_raster(f, args.station)
        all_profiles.append(prof)
        print(f"   Size: {prof['file_size_mb']} MB | Dimensions: {prof['width']} x {prof['height']}")
        print(f"   Elevation Range: [{prof['min_elevation']}, {prof['max_elevation']}] m")
        print(f"   GeoTIFF Tags: {prof['has_geotiff_tags']} | Valid: {prof['is_valid']}")
        if prof["warnings"]:
            for w in prof["warnings"]:
                print(f"   Warning: {w}")
        if prof["error_message"]:
            print(f"   Error: {prof['error_message']}")

        # Update manifest
        update_download_manifest(manifest_path, prof, args.station)

    # Write audit report
    audit_file = audit_dir / f"{args.station}_dem_inspection.md"
    report_lines = [
        f"# SoilDepth-AI — DEM Inspection Report: Station `{args.station}`",
        f"**Audit Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Inspected Rasters:** {len(all_profiles)}",
        "",
        "## Raster Profiles",
        "",
    ]
    for p in all_profiles:
        report_lines.append(f"### File: `{p['file_name']}`")
        report_lines.append(f"- **File Size:** {p['file_size_bytes']} bytes ({p['file_size_mb']} MB)")
        report_lines.append(f"- **SHA-256:** `{p['sha256']}`")
        report_lines.append(f"- **Dimensions:** {p['width']} columns $\\times$ {p['height']} rows")
        report_lines.append(f"- **Mode / Datatype:** `{p['mode']}` / `{p['data_type']}`")
        report_lines.append(f"- **Elevation Bounds:** Min `{p['min_elevation']} m`, Max `{p['max_elevation']} m`, Mean `{p['mean_elevation']} m`")
        report_lines.append(f"- **GeoTIFF Spatial Tags:** `{p['has_geotiff_tags']}`")
        report_lines.append(f"- **Validation Status:** `{'VALIDATED' if p['is_valid'] else 'FAILED'}`")
        if p["warnings"]:
            for w in p["warnings"]:
                report_lines.append(f"- **Warning:** {w}")
        report_lines.append("")

    audit_file.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nAudit report saved to: {audit_file}")


if __name__ == "__main__":
    main()
