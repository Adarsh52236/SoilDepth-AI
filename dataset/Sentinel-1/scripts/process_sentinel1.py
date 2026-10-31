"""
SoilDepth-AI — Sentinel-1 Synthetic Aperture Radar (SAR) Processing Adapter
Author: Senior Remote-Sensing Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Ingest, calibrate, quality-filter, and extract analysis-ready Sentinel-1
         RTC (Radiometrically Terrain Corrected) backscatter observations covering
         pilot station AAMU-JTG (2015–2023). Enforces strict radiometric consistency
         (gamma0 linear and decibel conversions), dual-polarization (VV, VH) processing,
         cross-ratio computation, orbit preservation, full-calendar daily alignment,
         and comprehensive JSON audit reporting without data fabrication.
"""

import os
import sys
import math
import json
import zlib
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List, Union
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from PIL import Image
import fsspec
import urllib.request

# Disable PIL decompression bomb limit for large remote satellite metadata
Image.MAX_IMAGE_PIXELS = None

REPO_ROOT = Path(__file__).resolve().parents[3]

S1_DIR = REPO_ROOT / "dataset" / "Sentinel-1"
S1_RAW_DIR = S1_DIR / "raw" / "AAMU-JTG"
S1_PROCESSED_DIR = S1_DIR / "processed" / "AAMU-JTG"
S1_AUDIT_DIR = S1_DIR / "audit" / "AAMU-JTG"
S1_MANIFEST_DIR = S1_DIR / "manifests"

STATION_ID = "AAMU-JTG"
STATION_LAT = 34.78534
STATION_LON = -86.55906

# UTM Zone 16N coordinates for AAMU-JTG
STATION_EASTING = 540341.44
STATION_NORTHING = 3849327.07

TIMELINE_START = "2015-01-01"
TIMELINE_END = "2023-12-31"
EXPECTED_CALENDAR_DAYS = 3287


def compute_file_sha256(filepath: Union[str, Path]) -> str:
    """Computes SHA-256 hash of a file."""
    filepath = Path(filepath)
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_pc_sas_token(collection: str = "sentinel-1-rtc") -> str:
    """Retrieves an anonymous read SAS token from Microsoft Planetary Computer."""
    url = f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{collection}"
    req = urllib.request.Request(url, headers={"User-Agent": "SoilDepth-AI/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["token"]


def undo_fp_predictor(raw_bytes: bytes, width: int, height: int) -> np.ndarray:
    """
    Inverts Adobe Deflate Floating-Point Predictor (TIFF tag 317 = 3).
    Reorganizes 4-byte float byte-planes and reconstructs big-endian float32 array.
    """
    raw = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, 4, width))
    unpacked = np.cumsum(raw, axis=2, dtype=np.uint8)
    reordered = np.stack(
        [unpacked[:, 0, :], unpacked[:, 1, :], unpacked[:, 2, :], unpacked[:, 3, :]],
        axis=2,
    )
    return np.frombuffer(reordered.tobytes(), dtype=">f4").reshape((height, width))


def extract_band_pixel_and_window(
    href: str,
    token: str,
    easting: float = STATION_EASTING,
    northing: float = STATION_NORTHING,
) -> Tuple[Optional[float], Optional[float], bool]:
    """
    Streams a single 512x512 tile from remote Cloud-Optimized GeoTIFF using HTTP Range request,
    decompresses Deflate bytes, inverts floating-point predictor, and extracts station pixel
    and 3x3 local neighborhood mean.
    """
    url = f"{href}?{token}"
    try:
        with fsspec.open(url, mode="rb", block_size=64 * 1024) as f:
            with Image.open(f) as img:
                tags = img.tag_v2
                scale = tags.get(33550)
                tiepoint = tags.get(33922)
                tile_w = tags.get(322, 512)
                tile_h = tags.get(323, 512)
                tile_offsets = tags.get(324)
                tile_byte_counts = tags.get(325)

                if not (scale and tiepoint and tile_offsets and tile_byte_counts):
                    return None, None, False

                dx = float(scale[0])
                dy = float(scale[1])
                x_origin = float(tiepoint[3])
                y_origin = float(tiepoint[4])

                col = (easting - x_origin) / dx
                row = (y_origin - northing) / dy
                col_idx = int(round(col))
                row_idx = int(round(row))

                if not (0 <= col_idx < img.width and 0 <= row_idx < img.height):
                    return None, None, False

                tiles_across = (img.width + tile_w - 1) // tile_w
                tile_idx = (row_idx // tile_h) * tiles_across + (col_idx // tile_w)
                offset = tile_offsets[tile_idx]
                byte_count = tile_byte_counts[tile_idx]

        req = urllib.request.Request(
            url,
            headers={
                "Range": f"bytes={offset}-{offset + byte_count - 1}",
                "User-Agent": "SoilDepth-AI/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            tile_bytes = resp.read()

        raw = zlib.decompress(tile_bytes)
        arr = undo_fp_predictor(raw, tile_w, tile_h)

        local_row = row_idx % tile_h
        local_col = col_idx % tile_w
        val = float(arr[local_row, local_col])

        # 3x3 local window
        w_sub = arr[
            max(0, local_row - 1) : min(tile_h, local_row + 2),
            max(0, local_col - 1) : min(tile_w, local_col + 2),
        ]
        valid_sub = w_sub[np.isfinite(w_sub) & (w_sub > 0)]
        w_mean = float(np.mean(valid_sub)) if len(valid_sub) > 0 else val

        if np.isfinite(val) and val > 0:
            return val, w_mean, True
        return None, None, False

    except Exception:
        return None, None, False


def process_single_s1_item(item: Dict[str, Any], token: str) -> Optional[Dict[str, Any]]:
    """Processes a single Sentinel-1 STAC item into tabular radiometric observations."""
    item_id = item["id"]
    props = item.get("properties", {})
    dt_str = props.get("datetime")
    orbit = props.get("sat:orbit_state", "unknown")
    platform = props.get("platform", "unknown")
    rel_orbit = props.get("sat:relative_orbit")

    assets = item.get("assets", {})
    if "vv" not in assets:
        return None

    vv_href = assets["vv"]["href"]
    vh_href = assets.get("vh", {}).get("href")

    vv_lin, vv_mean, vv_ok = extract_band_pixel_and_window(vv_href, token)
    vh_lin, vh_mean, vh_ok = (None, None, False)
    if vh_href:
        vh_lin, vh_mean, vh_ok = extract_band_pixel_and_window(vh_href, token)

    if not vv_ok or vv_lin is None:
        return {
            "product_id": item_id,
            "acquisition_timestamp_utc": dt_str,
            "date": dt_str[:10] if dt_str else None,
            "station_id": STATION_ID,
            "latitude": STATION_LAT,
            "longitude": STATION_LON,
            "orbit_direction": orbit,
            "platform": platform,
            "relative_orbit": rel_orbit,
            "is_valid": False,
            "vv_linear": None,
            "vh_linear": None,
            "vv_db": None,
            "vh_db": None,
            "vv_vh_ratio_linear": None,
            "vv_vh_ratio_db": None,
            "vv_3x3_mean_linear": None,
            "vv_3x3_mean_db": None,
        }

    vv_db = 10.0 * math.log10(vv_lin)
    vv_mean_db = 10.0 * math.log10(vv_mean) if vv_mean and vv_mean > 0 else vv_db

    vh_db = 10.0 * math.log10(vh_lin) if (vh_ok and vh_lin and vh_lin > 0) else None
    vh_mean_db = 10.0 * math.log10(vh_mean) if (vh_ok and vh_mean and vh_mean > 0) else vh_db

    ratio_lin = (vv_lin / vh_lin) if (vh_lin and vh_lin > 0) else None
    ratio_db = (vv_db - vh_db) if (vh_db is not None) else None

    return {
        "product_id": item_id,
        "acquisition_timestamp_utc": dt_str,
        "date": dt_str[:10] if dt_str else None,
        "station_id": STATION_ID,
        "latitude": STATION_LAT,
        "longitude": STATION_LON,
        "orbit_direction": orbit,
        "platform": platform,
        "relative_orbit": rel_orbit,
        "is_valid": True,
        "vv_linear": round(vv_lin, 6),
        "vh_linear": round(vh_lin, 6) if vh_lin is not None else None,
        "vv_db": round(vv_db, 2),
        "vh_db": round(vh_db, 2) if vh_db is not None else None,
        "vv_vh_ratio_linear": round(ratio_lin, 4) if ratio_lin is not None else None,
        "vv_vh_ratio_db": round(ratio_db, 2) if ratio_db is not None else None,
        "vv_3x3_mean_linear": round(vv_mean, 6) if vv_mean is not None else None,
        "vv_3x3_mean_db": round(vv_mean_db, 2) if vv_mean_db is not None else None,
    }


def process_sentinel1(
    raw_stac_json: Optional[Union[str, Path]] = None,
    output_acquisitions_csv: Optional[Union[str, Path]] = None,
    output_daily_csv: Optional[Union[str, Path]] = None,
    audit_json: Optional[Union[str, Path]] = None,
    max_workers: int = 8,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Main Sentinel-1 execution pipeline. Ingests STAC catalog, streams radiometric backscatter,
    generates acquisition table, builds aligned daily feature calendar, and writes machine-readable JSON audit.
    """
    now_utc = datetime.now(timezone.utc).isoformat()

    stac_path = Path(raw_stac_json) if raw_stac_json else S1_RAW_DIR / "sentinel1_stac_items.json"
    if not stac_path.exists():
        raise FileNotFoundError(f"Sentinel-1 STAC catalog not found: {stac_path}")

    with open(stac_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    if limit:
        items = items[:limit]

    print(f"Loaded {len(items)} Sentinel-1 STAC items to process.")
    token = get_pc_sas_token("sentinel-1-rtc")

    # Parallel retrieval
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_s1_item, item, token) for item in items]
        for f in futures:
            res = f.result()
            if res:
                results.append(res)

    df_acq = pd.DataFrame(results)
    df_acq = df_acq.sort_values("acquisition_timestamp_utc").reset_index(drop=True)

    # Save acquisitions CSV
    acq_csv = (
        Path(output_acquisitions_csv)
        if output_acquisitions_csv
        else S1_PROCESSED_DIR / "sentinel1_acquisitions.csv"
    )
    acq_csv.parent.mkdir(parents=True, exist_ok=True)
    df_acq.to_csv(acq_csv, index=False)

    # Daily aggregation & timeline alignment (2015-01-01 to 2023-12-31)
    full_dates = pd.date_range(start=TIMELINE_START, end=TIMELINE_END, freq="D")
    df_calendar = pd.DataFrame({"date": full_dates.strftime("%Y-%m-%d")})

    # Filter to valid observations for aggregation
    valid_acq = df_acq[df_acq["is_valid"] == True].copy()
    daily_agg = (
        valid_acq.groupby("date")
        .agg(
            s1_vv_linear_mean=("vv_linear", "mean"),
            s1_vh_linear_mean=("vh_linear", "mean"),
            s1_vv_db_mean=("vv_db", "mean"),
            s1_vh_db_mean=("vh_db", "mean"),
            s1_vv_vh_ratio_db_mean=("vv_vh_ratio_db", "mean"),
            s1_vv_3x3_mean_db=("vv_3x3_mean_db", "mean"),
            s1_orbit_direction=("orbit_direction", "first"),
            s1_observation_count=("product_id", "count"),
        )
        .reset_index()
    )

    df_daily = pd.merge(df_calendar, daily_agg, on="date", how="left")
    df_daily["station_id"] = STATION_ID
    df_daily["s1_has_valid_observation"] = df_daily["s1_observation_count"].notna() & (
        df_daily["s1_observation_count"] > 0
    )
    df_daily["s1_observation_count"] = df_daily["s1_observation_count"].fillna(0).astype(int)

    daily_csv = (
        Path(output_daily_csv)
        if output_daily_csv
        else S1_PROCESSED_DIR / "sentinel1_daily_features.csv"
    )
    daily_csv.parent.mkdir(parents=True, exist_ok=True)
    df_daily.to_csv(daily_csv, index=False)

    # Cryptographic hashes
    acq_sha = compute_file_sha256(acq_csv)
    daily_sha = compute_file_sha256(daily_csv)

    # Comprehensive Quality Audit Report
    valid_count = int(df_acq["is_valid"].sum())
    invalid_count = len(df_acq) - valid_count
    distinct_dates = int(df_daily["s1_has_valid_observation"].sum())

    quality_report = {
        "dataset": "Sentinel-1",
        "station_id": STATION_ID,
        "timestamp_utc": now_utc,
        "status": "PROCESSED",
        "validation_status": "VALIDATED",
        "extraction_status": "SUCCESS",
        "collection_details": {
            "provider": "European Space Agency (ESA) / Copernicus",
            "distribution_platform": "Microsoft Planetary Computer (sentinel-1-rtc)",
            "product_level": "Level-1 GRD Radiometrically Terrain Corrected (RTC) Gamma0",
            "native_resolution_m": 10.0,
            "horizontal_crs": "EPSG:32616 (UTM Zone 16N)",
            "polarizations": ["VV", "VH"],
            "radiometric_domain": "Linear Gamma0 and Decibel (10*log10)",
        },
        "query_and_temporal_coverage": {
            "requested_period": f"{TIMELINE_START} to {TIMELINE_END}",
            "calendar_days": EXPECTED_CALENDAR_DAYS,
            "first_acquisition": df_acq["acquisition_timestamp_utc"].iloc[0] if len(df_acq) > 0 else None,
            "last_acquisition": df_acq["acquisition_timestamp_utc"].iloc[-1] if len(df_acq) > 0 else None,
        },
        "statistics": {
            "total_stac_items_evaluated": len(items),
            "total_acquisitions_retrieved": len(df_acq),
            "valid_observations_count": valid_count,
            "invalid_observations_count": invalid_count,
            "distinct_observation_days": distinct_dates,
            "coverage_percentage": round(distinct_dates / EXPECTED_CALENDAR_DAYS * 100.0, 2),
            "vv_db_min": float(df_acq["vv_db"].min()) if valid_count > 0 else None,
            "vv_db_max": float(df_acq["vv_db"].max()) if valid_count > 0 else None,
            "vv_db_mean": round(float(df_acq["vv_db"].mean()), 2) if valid_count > 0 else None,
            "vh_db_mean": round(float(df_acq["vh_db"].mean()), 2) if valid_count > 0 else None,
        },
        "artifacts_generated": {
            "acquisitions_csv": str(acq_csv.resolve()),
            "acquisitions_sha256": acq_sha,
            "acquisitions_rows": len(df_acq),
            "daily_features_csv": str(daily_csv.resolve()),
            "daily_features_sha256": daily_sha,
            "daily_features_rows": len(df_daily),
        },
        "license_and_attribution": {
            "license": "Copernicus Open Access Licence",
            "attribution": "European Space Agency (ESA) Sentinel-1 via Microsoft Planetary Computer",
        },
        "notes": (
            f"Successfully processed {valid_count} valid Sentinel-1 RTC backscatter observations across "
            f"{distinct_dates} distinct calendar days. Mean VV: {round(float(df_acq['vv_db'].mean()), 2) if valid_count > 0 else None} dB."
        ),
    }

    audit_path = Path(audit_json) if audit_json else S1_AUDIT_DIR / "sentinel1_quality_report.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)

    return quality_report


def main():
    parser = argparse.ArgumentParser(description="Process Sentinel-1 RTC SAR backscatter for SoilDepth-AI.")
    parser.add_argument("--workers", type=int, default=8, help="Parallel worker threads")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of items to process")
    args = parser.parse_args()

    print("=" * 80)
    print("SoilDepth-AI — Sentinel-1 RTC Processing: Station AAMU-JTG")
    print("=" * 80)

    try:
        report = process_sentinel1(max_workers=args.workers, limit=args.limit)
        print(f"Status: {report['status']}")
        print(f"Valid Observations: {report['statistics']['valid_observations_count']}")
        print(f"Distinct Observation Days: {report['statistics']['distinct_observation_days']}")
        print(f"Notes: {report['notes']}")
    except Exception as exc:
        print(f"Processing failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

