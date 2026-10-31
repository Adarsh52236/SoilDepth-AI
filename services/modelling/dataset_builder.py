"""
SoilDepth-AI — In-Situ & ERA5-Land Dataset Builder
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Ingest and align processed ERA5-Land daily weather data and ground-truth
         ISMN SCAN point-sensor observations for pilot station AAMU-JTG.
         Enforces station coordinate verification, strict quality filtering (G, V/E),
         minimum diurnal completeness threshold (>=18h/day), and stores intermediate
         aligned datasets in data/modelling/interim/.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

from services.modelling.config import (
    REPO_ROOT,
    ERA5_DAILY_CSV,
    SCAN_EXTRACTED_DIR,
    SMAP_DAILY_CSV,
    SOILGRIDS_STATIC_CSV,
    DEM_STATIC_CSV,
    SENTINEL1_DAILY_CSV,
    SENTINEL2_DAILY_CSV,
    INTERIM_DATA_DIR,
    STATION_ID,
    STATION_LAT,
    STATION_LON,
    STATION_ELEV_M,
    MAX_COORD_TOLERANCE_DEG,
    SENSOR_DEPTHS,
    MIN_VALID_HOURS_PER_DAY,
    ACCEPTED_QFLAGS,
    ACCEPTED_PFLAGS,
    PHYSICAL_SM_MIN,
    PHYSICAL_SM_MAX,
    SensorDepthConfig,
)


def parse_static_soil_properties(static_file: Path) -> Dict[str, Dict[str, float]]:
    """
    Parses HWSD static soil properties from SCAN static_variables.csv.
    Returns:
        dict: {
            '0.00-0.30': {
                'clay_fraction_pct': 25.0,
                'sand_fraction_pct': 53.0,
                'silt_fraction_pct': 22.0,
                'organic_carbon_pct': 0.98,
                'saturation_m3_m3': 0.43
            },
            '0.30-1.00': {
                'clay_fraction_pct': 39.0,
                ...
            }
        }
    """
    if not static_file.exists():
        raise FileNotFoundError(f"Static variables file not found at {static_file}")

    df = pd.read_csv(static_file, sep=";")
    hwsd_df = df[df["quantity_source_name"] == "HWSD"].copy()

    property_map = {
        "clay fraction": "clay_fraction_pct",
        "sand fraction": "sand_fraction_pct",
        "silt fraction": "silt_fraction_pct",
        "organic carbon": "organic_carbon_pct",
        "saturation": "saturation_m3_m3",
    }

    results: Dict[str, Dict[str, float]] = {
        "0.00-0.30": {},
        "0.30-1.00": {},
    }

    for _, row in hwsd_df.iterrows():
        q_name = str(row["quantity_name"]).strip()
        if q_name in property_map:
            key = property_map[q_name]
            d_from = float(row["depth_from[m]"])
            d_to = float(row["depth_to[m]"])
            layer_tag = f"{d_from:.2f}-{d_to:.2f}"
            val = float(row["value"])
            if layer_tag in results:
                results[layer_tag][key] = val

    return results


def parse_soilgrids_static_properties(
    soilgrids_csv: Optional[Path] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Parses extracted SoilGrids 250m static physical and hydraulic properties from
    soilgrids_AAMU-JTG_features.csv.
    Returns:
        dict: {
            '0_5cm': {'soilgrids_clay_pct': 24.7, ...},
            '5_15cm': ...,
            '15_30cm': ...,
            '30_60cm': ...
        }
    """
    if soilgrids_csv is None:
        soilgrids_csv = SOILGRIDS_STATIC_CSV

    if not soilgrids_csv.exists():
        return {}

    df = pd.read_csv(soilgrids_csv)
    if df.empty:
        return {}

    row = df.iloc[0]
    layer_tags = ["0_5cm", "5_15cm", "15_30cm", "30_60cm"]
    prop_names = ["clay", "sand", "silt", "bdod", "ocd", "wv0010", "wv0033", "wv1500"]

    results: Dict[str, Dict[str, float]] = {}
    for tag in layer_tags:
        layer_dict: Dict[str, float] = {}
        for p in prop_names:
            col_name = f"soilgrids_{p}_{tag}"
            if col_name in df.columns:
                val = float(row[col_name])
                if p in ("clay", "sand", "silt"):
                    layer_dict[f"soilgrids_{p}_pct"] = val
                elif p == "bdod":
                    layer_dict["soilgrids_bdod_g_cm3"] = val
                elif p == "ocd":
                    layer_dict["soilgrids_ocd_kg_m3"] = val
                elif p.startswith("wv"):
                    layer_dict[f"soilgrids_{p}_m3_m3"] = val
        results[tag] = layer_dict

    return results


def parse_dem_static_features(dem_csv: Optional[Path] = None) -> Dict[str, float]:
    """
    Parses USGS 3DEP 1-arc-second 30m DEM terrain attributes from dem_AAMU-JTG_features.csv.
    Returns:
        dict: {
            'dem_elevation_m': 245.47,
            'dem_slope_deg': 4.9156,
            'dem_aspect_sin': -0.1622,
            'dem_aspect_cos': -0.9868
        }
    """
    if dem_csv is None:
        dem_csv = DEM_STATIC_CSV

    if not dem_csv.exists():
        return {}

    df = pd.read_csv(dem_csv)
    if df.empty:
        return {}

    row = df.iloc[0]
    return {
        "dem_elevation_m": float(row["elevation_m"]),
        "dem_slope_deg": float(row["slope_deg"]),
        "dem_aspect_sin": float(row["aspect_sin"]),
        "dem_aspect_cos": float(row["aspect_cos"]),
    }


def parse_scan_stm_file(
    stm_file: Path,
    depth_cfg: SensorDepthConfig,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Reads an ISMN STM file, verifies station identity, coordinates, and depth metadata in header,
    filters by quality flags ('G') and provider flags ('V', 'E'), and aggregates to daily means.

    Returns:
        daily_df: DataFrame indexed by date string (YYYY-MM-DD) with columns:
                  ['target_sm_<depth>', 'valid_hours_<depth>']
        audit: metadata dictionary of counts and exclusions.
    """
    if not stm_file.exists():
        raise FileNotFoundError(f"STM file not found at {stm_file}")

    with open(stm_file, "r") as f:
        header_line = f.readline().strip()

    header_parts = header_line.split()
    # Header format: SCAN SCAN AAMU-JTG 34.78534 -86.55906 241.0 0.0508 0.0508 'Stevens-Hydraprobe-Analog'
    if len(header_parts) < 8:
        raise ValueError(f"Invalid STM header in {stm_file}: {header_line}")

    hdr_net1 = header_parts[0]
    hdr_net2 = header_parts[1]
    hdr_station = header_parts[2]
    hdr_lat = float(header_parts[3])
    hdr_lon = float(header_parts[4])
    hdr_elev = float(header_parts[5])
    hdr_d_from = float(header_parts[6])
    hdr_d_to = float(header_parts[7])

    # 1. Metadata verification
    if hdr_station != STATION_ID:
        raise ValueError(f"Station ID mismatch in {stm_file}: expected {STATION_ID}, got {hdr_station}")
    if abs(hdr_lat - STATION_LAT) > MAX_COORD_TOLERANCE_DEG:
        raise ValueError(f"Latitude mismatch in {stm_file}: expected {STATION_LAT}, got {hdr_lat}")
    if abs(hdr_lon - STATION_LON) > MAX_COORD_TOLERANCE_DEG:
        raise ValueError(f"Longitude mismatch in {stm_file}: expected {STATION_LON}, got {hdr_lon}")
    if abs(hdr_d_from - depth_cfg.depth_m) > 1e-3 or abs(hdr_d_to - depth_cfg.depth_m) > 1e-3:
        raise ValueError(
            f"Sensor depth mismatch in {stm_file}: expected {depth_cfg.depth_m}m, "
            f"got {hdr_d_from}m - {hdr_d_to}m"
        )

    # 2. Read observations (skip header line 0)
    # File format: YYYY/MM/DD HH:MM <value> <qflag> <pflag>
    df_raw = pd.read_csv(
        stm_file,
        skiprows=1,
        sep=r"\s+",
        header=None,
        names=["obs_date", "obs_time", "sm_val", "qflag", "pflag"],
        dtype={"obs_date": str, "obs_time": str, "sm_val": float, "qflag": str, "pflag": str},
    )

    total_hourly_records = len(df_raw)

    # 3. Quality flag filtering
    q_mask = df_raw["qflag"].isin(ACCEPTED_QFLAGS)
    p_mask = df_raw["pflag"].isin(ACCEPTED_PFLAGS)
    phys_mask = (df_raw["sm_val"] >= PHYSICAL_SM_MIN) & (df_raw["sm_val"] <= PHYSICAL_SM_MAX)

    valid_mask = q_mask & p_mask & phys_mask
    df_valid = df_raw[valid_mask].copy()

    excluded_hourly_records = total_hourly_records - len(df_valid)

    # Format date: 'YYYY/MM/DD' -> 'YYYY-MM-DD'
    df_valid["date_utc"] = df_valid["obs_date"].str.replace("/", "-", regex=False)

    # 4. Daily aggregation
    daily_stats = df_valid.groupby("date_utc").agg(
        sm_mean=("sm_val", "mean"),
        valid_hours=("sm_val", "count"),
    ).reset_index()

    # Apply diurnal completeness threshold: >= MIN_VALID_HOURS_PER_DAY
    under_represented_days = (daily_stats["valid_hours"] < MIN_VALID_HOURS_PER_DAY).sum()
    daily_stats.loc[daily_stats["valid_hours"] < MIN_VALID_HOURS_PER_DAY, "sm_mean"] = np.nan

    target_col = f"target_{depth_cfg.depth_key}"
    hours_col = f"obs_hours_{depth_cfg.depth_key}"

    daily_stats = daily_stats.rename(
        columns={"sm_mean": target_col, "valid_hours": hours_col}
    )

    audit = {
        "depth_key": depth_cfg.depth_key,
        "nominal_depth_cm": depth_cfg.nominal_depth_cm,
        "depth_m": depth_cfg.depth_m,
        "file_name": stm_file.name,
        "header_lat": hdr_lat,
        "header_lon": hdr_lon,
        "header_elev": hdr_elev,
        "total_hourly_records": int(total_hourly_records),
        "valid_hourly_records": int(len(df_valid)),
        "excluded_hourly_records": int(excluded_hourly_records),
        "calendar_days_with_data": int(len(daily_stats)),
        "days_meeting_diurnal_threshold": int((daily_stats[hours_col] >= MIN_VALID_HOURS_PER_DAY).sum()),
        "days_excluded_diurnal_threshold": int(under_represented_days),
        "sm_mean": float(daily_stats[target_col].mean()) if not daily_stats[target_col].dropna().empty else None,
        "sm_std": float(daily_stats[target_col].std()) if not daily_stats[target_col].dropna().empty else None,
        "sm_min": float(daily_stats[target_col].min()) if not daily_stats[target_col].dropna().empty else None,
        "sm_max": float(daily_stats[target_col].max()) if not daily_stats[target_col].dropna().empty else None,
    }

    return daily_stats, audit


def build_aligned_pilot_dataset(
    output_path: Optional[Path] = None,
    include_smap: bool = True,
    include_soilgrids: bool = True,
    include_dem: bool = True,
    include_sentinel1: bool = True,
    include_sentinel2: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Builds the aligned daily dataset by joining ERA5-Land daily weather observations
    with the 4 discrete SCAN depth sensor observations, SMAP L3 daily surface moisture,
    SoilGrids static properties, USGS 3DEP DEM terrain features, Sentinel-1 SAR backscatter,
    and Sentinel-2 multispectral surface reflectance for AAMU-JTG.
    """
    if output_path is None:
        output_path = INTERIM_DATA_DIR / f"{STATION_ID}_aligned_raw.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load and verify ERA5-Land Daily Weather
    if not ERA5_DAILY_CSV.exists():
        raise FileNotFoundError(f"ERA5-Land daily processed file not found at {ERA5_DAILY_CSV}")

    df_weather = pd.read_csv(ERA5_DAILY_CSV)

    # Verify weather station ID & coordinates
    if (df_weather["station_id"] != STATION_ID).any():
        raise ValueError(f"Weather data contains station IDs other than {STATION_ID}")

    if not np.allclose(df_weather["latitude_station"], STATION_LAT, atol=MAX_COORD_TOLERANCE_DEG):
        raise ValueError("Weather station latitude does not match expected AAMU-JTG coordinates")

    if not np.allclose(df_weather["longitude_station"], STATION_LON, atol=MAX_COORD_TOLERANCE_DEG):
        raise ValueError("Weather station longitude does not match expected AAMU-JTG coordinates")

    total_weather_days = len(df_weather)
    weather_start_date = df_weather["date_utc"].min()
    weather_end_date = df_weather["date_utc"].max()

    # 2. Ingest Static Soil Properties (HWSD from ISMN, SoilGrids, and DEM terrain)
    static_file = (
        SCAN_EXTRACTED_DIR
        / "surface_0-10cm"
        / "SCAN"
        / STATION_ID
        / f"SCAN_SCAN_{STATION_ID}_static_variables.csv"
    )
    static_props = parse_static_soil_properties(static_file)

    soilgrids_props = {}
    if include_soilgrids and SOILGRIDS_STATIC_CSV.exists():
        soilgrids_props = parse_soilgrids_static_properties(SOILGRIDS_STATIC_CSV)

    dem_props = {}
    if include_dem and DEM_STATIC_CSV.exists():
        dem_props = parse_dem_static_features(DEM_STATIC_CSV)

    # 3. Ingest and Align SCAN Sensor Observations for each depth
    aligned_df = df_weather.copy()
    depth_audits = {}

    for depth_key, depth_cfg in SENSOR_DEPTHS.items():
        station_dir = SCAN_EXTRACTED_DIR / depth_cfg.extracted_subdir / "SCAN" / STATION_ID
        matched_files = list(station_dir.glob(depth_cfg.file_pattern))

        if not matched_files:
            raise FileNotFoundError(
                f"No STM file found matching {depth_cfg.file_pattern} in {station_dir}"
            )

        stm_file = matched_files[0]
        daily_sensor_df, audit = parse_scan_stm_file(stm_file, depth_cfg)
        depth_audits[depth_key] = audit

        # Left join onto master date timeline
        aligned_df = aligned_df.merge(
            daily_sensor_df,
            on="date_utc",
            how="left",
        )

        # Fill missing counts with 0
        hours_col = f"obs_hours_{depth_cfg.depth_key}"
        aligned_df[hours_col] = aligned_df[hours_col].fillna(0).astype(int)

    # 4. Ingest and Align SMAP L3 Features
    smap_audit = None
    if include_smap and SMAP_DAILY_CSV.exists():
        df_smap = pd.read_csv(SMAP_DAILY_CSV)
        smap_cols = [
            "date_utc",
            "smap_sm_daily_mean_m3_m3",
            "smap_sm_am_m3_m3",
            "smap_sm_pm_m3_m3",
            "smap_has_valid_retrieval",
            "smap_valid_passes_count",
            "smap_retrieval_status",
        ]
        cols_to_merge = [c for c in smap_cols if c in df_smap.columns]
        aligned_df = aligned_df.merge(df_smap[cols_to_merge], on="date_utc", how="left")
        smap_audit = {
            "smap_source_csv": str(SMAP_DAILY_CSV.resolve()),
            "smap_valid_days_count": int((aligned_df["smap_has_valid_retrieval"] == True).sum()),
            "smap_missing_days_count": int((aligned_df["smap_has_valid_retrieval"] != True).sum()),
        }

    # 5. Ingest and Align Sentinel-1 SAR Daily Backscatter
    s1_audit = None
    if include_sentinel1 and SENTINEL1_DAILY_CSV.exists():
        df_s1 = pd.read_csv(SENTINEL1_DAILY_CSV)
        if "date" in df_s1.columns and "date_utc" not in df_s1.columns:
            df_s1 = df_s1.rename(columns={"date": "date_utc"})
        s1_cols = [
            "date_utc",
            "s1_vv_linear_mean",
            "s1_vh_linear_mean",
            "s1_vv_db_mean",
            "s1_vh_db_mean",
            "s1_vv_vh_ratio_db_mean",
            "s1_vv_3x3_mean_db",
            "s1_orbit_direction",
            "s1_observation_count",
            "s1_has_valid_observation",
        ]
        cols_to_merge = [c for c in s1_cols if c in df_s1.columns]
        aligned_df = aligned_df.merge(df_s1[cols_to_merge], on="date_utc", how="left")
        aligned_df["s1_has_valid_observation"] = aligned_df["s1_has_valid_observation"].fillna(False).astype(bool)
        s1_audit = {
            "s1_source_csv": str(SENTINEL1_DAILY_CSV.resolve()),
            "s1_valid_days_count": int(aligned_df["s1_has_valid_observation"].sum()),
            "s1_missing_days_count": int((~aligned_df["s1_has_valid_observation"]).sum()),
        }

    # 6. Ingest and Align Sentinel-2 Optical Daily Reflectance & Indices
    s2_audit = None
    if include_sentinel2 and SENTINEL2_DAILY_CSV.exists():
        df_s2 = pd.read_csv(SENTINEL2_DAILY_CSV)
        if "date" in df_s2.columns and "date_utc" not in df_s2.columns:
            df_s2 = df_s2.rename(columns={"date": "date_utc"})
        s2_cols = [
            "date_utc",
            "s2_b02_blue_mean",
            "s2_b03_green_mean",
            "s2_b04_red_mean",
            "s2_b08_nir_mean",
            "s2_b11_swir1_mean",
            "s2_b12_swir2_mean",
            "s2_ndvi_mean",
            "s2_evi_mean",
            "s2_scl_code",
            "s2_observation_count",
            "s2_has_valid_observation",
        ]
        cols_to_merge = [c for c in s2_cols if c in df_s2.columns]
        aligned_df = aligned_df.merge(df_s2[cols_to_merge], on="date_utc", how="left")
        aligned_df["s2_has_valid_observation"] = aligned_df["s2_has_valid_observation"].fillna(False).astype(bool)
        s2_audit = {
            "s2_source_csv": str(SENTINEL2_DAILY_CSV.resolve()),
            "s2_valid_days_count": int(aligned_df["s2_has_valid_observation"].sum()),
            "s2_missing_days_count": int((~aligned_df["s2_has_valid_observation"]).sum()),
        }

    # Sort chronologically and reset index
    aligned_df = aligned_df.sort_values("date_utc").reset_index(drop=True)

    # Save intermediate aligned dataset
    aligned_df.to_csv(output_path, index=False)

    overall_audit = {
        "station_id": STATION_ID,
        "station_latitude": STATION_LAT,
        "station_longitude": STATION_LON,
        "station_elevation_m": STATION_ELEV_M,
        "era5_grid_latitude": float(df_weather["latitude_era5_grid"].iloc[0]),
        "era5_grid_longitude": float(df_weather["longitude_era5_grid"].iloc[0]),
        "total_calendar_days": int(total_weather_days),
        "start_date": weather_start_date,
        "end_date": weather_end_date,
        "sensor_depths_audited": depth_audits,
        "static_soil_properties": static_props,
        "soilgrids_static_properties": soilgrids_props,
        "dem_static_properties": dem_props,
        "smap_alignment_audit": smap_audit,
        "sentinel1_alignment_audit": s1_audit,
        "sentinel2_alignment_audit": s2_audit,
        "interim_output_file": str(output_path.resolve()),
        "output_row_count": int(len(aligned_df)),
    }

    audit_json_path = INTERIM_DATA_DIR / f"{STATION_ID}_alignment_audit.json"
    with open(audit_json_path, "w") as f:
        json.dump(overall_audit, f, indent=2)

    return aligned_df, overall_audit

    audit_json_path = INTERIM_DATA_DIR / f"{STATION_ID}_alignment_audit.json"
    with open(audit_json_path, "w") as f:
        json.dump(overall_audit, f, indent=2)

    return aligned_df, overall_audit


if __name__ == "__main__":
    df, audit = build_aligned_pilot_dataset()
    print("=" * 80)
    print(f"Alignment complete: {len(df)} rows generated.")
    print(f"Date range: {audit['start_date']} to {audit['end_date']}")
    for k, v in audit["sensor_depths_audited"].items():
        print(f"  [{k}] Valid days meeting >=18h threshold: {v['days_meeting_diurnal_threshold']} / {v['calendar_days_with_data']}")
    print("=" * 80)
