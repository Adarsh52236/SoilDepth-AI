"""
SoilDepth-AI — SMAP L3 (SPL3SMP_E.006) Preprocessing Adapter
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Ingest, validate, quality-filter, and standardize NASA AppEEARS SMAP L3
         enhanced 9 km daily soil moisture point extracts for station AAMU-JTG.
         Enforces schema validation, strict flag interpretation (retrieval attempted
         AND successful), fill-value conversion (-9999 -> NaN), preservation of AM/PM
         observations, derivation of daily features without future leakage or fabrication,
         and generates comprehensive machine-readable quality audits.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

RAW_SMAP_CSV = (
    REPO_ROOT
    / "dataset"
    / "SMAP"
    / "raw"
    / "SoilDepth-AAMU-JTG-SMAP-SPL3SMP-E-006-results.csv"
)
PROCESSED_SMAP_DIR = REPO_ROOT / "dataset" / "SMAP" / "processed" / "AAMU-JTG"
AUDIT_SMAP_DIR = REPO_ROOT / "dataset" / "SMAP" / "audit"

EXPECTED_STATION_ID = "AAMU-JTG"
EXPECTED_LATITUDE = 34.78534
EXPECTED_LONGITUDE = -86.55906
COORD_TOLERANCE_DEG = 0.001

EXPECTED_RAW_ROWS = 3115
RAW_DATE_MIN = "2015-03-31"
RAW_DATE_MAX = "2023-12-31"

STUDY_TIMELINE_START = "2015-01-01"
STUDY_TIMELINE_END = "2023-12-31"
EXPECTED_CALENDAR_DAYS = 3287

FILL_VALUE = -9999.0
VALID_RETRIEVAL_FLAG = 9.0  # Attempted AND Successful retrieval
PHYSICAL_SM_MIN = 0.0       # m³/m³
PHYSICAL_SM_MAX = 0.60      # m³/m³

# Exact column names in raw AppEEARS results CSV
COL_CATEGORY = "Category"
COL_ID = "ID"
COL_LAT = "Latitude"
COL_LON = "Longitude"
COL_DATE = "Date"
COL_TILE = "SMAP_Tile"
COL_LINE_Y = "SPL3SMP_E_006_Line_Y_9.00805km"
COL_SAMPLE_X = "SPL3SMP_E_006_Sample_X_9.00805km"
COL_AM_SM = "SPL3SMP_E_006_Soil_Moisture_Retrieval_Data_AM_soil_moisture"
COL_PM_SM = "SPL3SMP_E_006_Soil_Moisture_Retrieval_Data_PM_soil_moisture_pm"
COL_AM_QF = "SPL3SMP_E_006_Soil_Moisture_Retrieval_Data_AM_retrieval_qual_flag"
COL_PM_QF = "SPL3SMP_E_006_Soil_Moisture_Retrieval_Data_PM_retrieval_qual_flag_pm"


def compute_file_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_smap_raw_schema(df_raw: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates schema, station identity, geographic coordinates, and date uniqueness
    of the raw AppEEARS SMAP CSV.
    """
    required_cols = [
        COL_ID, COL_LAT, COL_LON, COL_DATE,
        COL_AM_SM, COL_PM_SM, COL_AM_QF, COL_PM_QF
    ]
    missing_cols = [c for c in required_cols if c not in df_raw.columns]
    if missing_cols:
        raise ValueError(f"Raw SMAP CSV missing expected columns: {missing_cols}")

    # Station ID verification
    unique_ids = df_raw[COL_ID].dropna().unique()
    if len(unique_ids) != 1 or unique_ids[0] != EXPECTED_STATION_ID:
        raise ValueError(f"Expected station ID '{EXPECTED_STATION_ID}', got: {unique_ids}")

    # Coordinate verification
    lat_unique = df_raw[COL_LAT].unique()
    lon_unique = df_raw[COL_LON].unique()
    if len(lat_unique) != 1 or abs(lat_unique[0] - EXPECTED_LATITUDE) > COORD_TOLERANCE_DEG:
        raise ValueError(f"Latitude mismatch in SMAP raw CSV: expected {EXPECTED_LATITUDE}, got {lat_unique}")
    if len(lon_unique) != 1 or abs(lon_unique[0] - EXPECTED_LONGITUDE) > COORD_TOLERANCE_DEG:
        raise ValueError(f"Longitude mismatch in SMAP raw CSV: expected {EXPECTED_LONGITUDE}, got {lon_unique}")

    # Row count verification
    if len(df_raw) != EXPECTED_RAW_ROWS:
        raise ValueError(f"Expected {EXPECTED_RAW_ROWS} raw rows, found {len(df_raw)}")

    # Date range and uniqueness
    date_series = pd.to_datetime(df_raw[COL_DATE])
    min_date = date_series.min().strftime("%Y-%m-%d")
    max_date = date_series.max().strftime("%Y-%m-%d")

    if min_date != RAW_DATE_MIN or max_date != RAW_DATE_MAX:
        raise ValueError(
            f"Date range mismatch in SMAP CSV: expected {RAW_DATE_MIN}..{RAW_DATE_MAX}, "
            f"got {min_date}..{max_date}"
        )

    duplicate_dates = date_series.duplicated().sum()
    if duplicate_dates != 0:
        raise ValueError(f"Found {duplicate_dates} duplicate dates in SMAP CSV!")

    return {
        "station_id": str(unique_ids[0]),
        "latitude": float(lat_unique[0]),
        "longitude": float(lon_unique[0]),
        "row_count": len(df_raw),
        "min_date": min_date,
        "max_date": max_date,
        "duplicate_dates": int(duplicate_dates),
    }


def process_smap_daily_features(
    raw_csv_path: Optional[Path] = None,
    output_csv_path: Optional[Path] = None,
    audit_json_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Processes the raw SMAP L3 CSV into a standardized, complete daily feature table.
    
    Processing Steps:
    1. Schema and coordinate validation.
    2. Fill value conversion (-9999.0 -> NaN).
    3. Rigorous quality flag interpretation:
       - Flag 9.0: Retrieval attempted AND successful -> Valid.
       - Flag 13.0: Retrieval attempted but NOT successful (constant fallback value 0.4276806) -> Invalid.
       - Flag 7.0: Retrieval skipped and not successful -> Invalid.
       - Flag 15.0: Retrieval skipped and not successful -> Invalid.
       - Physical plausibility check: 0.0 <= VWC <= 0.60 m³/m³.
    4. Daily aggregation:
       - If both AM and PM are valid: arithmetic mean (AM + PM) / 2.0.
       - If only one pass is valid: single valid pass value.
       - If neither pass is valid (or missing date): NaN.
    5. Reindexing to complete study timeline (2015-01-01 to 2023-12-31, 3,287 days):
       - 89 pre-mission days (2015-01-01 to 2015-03-30) marked as 'PRE_MISSION'.
       - 83 missing granule days marked as 'NO_GRANULE'.
       - No synthetic data fabrication or forward-leakage imputation.
    6. Serialization of processed CSV and audit JSON.
    """
    if raw_csv_path is None:
        raw_csv_path = RAW_SMAP_CSV

    if output_csv_path is None:
        output_csv_path = PROCESSED_SMAP_DIR / "smap_daily_features.csv"

    if audit_json_path is None:
        audit_json_path = AUDIT_SMAP_DIR / "smap_quality_report.json"

    if not raw_csv_path.exists():
        raise FileNotFoundError(f"Raw SMAP CSV not found at {raw_csv_path}")

    raw_sha256 = compute_file_sha256(raw_csv_path)
    raw_size_bytes = raw_csv_path.stat().st_size

    df_raw = pd.read_csv(raw_csv_path)
    schema_info = validate_smap_raw_schema(df_raw)

    # Convert fill value -9999.0 to NaN
    df_work = df_raw.copy()
    df_work["date_utc"] = pd.to_datetime(df_work[COL_DATE]).dt.strftime("%Y-%m-%d")

    am_sm_clean = df_work[COL_AM_SM].replace(FILL_VALUE, np.nan)
    pm_sm_clean = df_work[COL_PM_SM].replace(FILL_VALUE, np.nan)

    # Flag interpretation: only flag 9.0 represents attempted AND successful retrieval
    am_qf = df_work[COL_AM_QF]
    pm_qf = df_work[COL_PM_QF]

    is_valid_am = (
        (am_qf == VALID_RETRIEVAL_FLAG)
        & am_sm_clean.notna()
        & (am_sm_clean >= PHYSICAL_SM_MIN)
        & (am_sm_clean <= PHYSICAL_SM_MAX)
    )

    is_valid_pm = (
        (pm_qf == VALID_RETRIEVAL_FLAG)
        & pm_sm_clean.notna()
        & (pm_sm_clean >= PHYSICAL_SM_MIN)
        & (pm_sm_clean <= PHYSICAL_SM_MAX)
    )

    df_work["smap_sm_am_m3_m3"] = np.where(is_valid_am, am_sm_clean, np.nan)
    df_work["smap_sm_pm_m3_m3"] = np.where(is_valid_pm, pm_sm_clean, np.nan)
    df_work["smap_is_valid_am"] = is_valid_am
    df_work["smap_is_valid_pm"] = is_valid_pm
    df_work["smap_qual_flag_am"] = am_qf
    df_work["smap_qual_flag_pm"] = pm_qf

    # Create master chronological calendar timeline (2015-01-01 to 2023-12-31)
    full_dates = pd.date_range(STUDY_TIMELINE_START, STUDY_TIMELINE_END, freq="D").strftime("%Y-%m-%d")
    df_master = pd.DataFrame({"date_utc": full_dates})

    df_merged = df_master.merge(
        df_work[[
            "date_utc",
            "smap_sm_am_m3_m3",
            "smap_sm_pm_m3_m3",
            "smap_qual_flag_am",
            "smap_qual_flag_pm",
            "smap_is_valid_am",
            "smap_is_valid_pm",
        ]],
        on="date_utc",
        how="left",
    )

    # Coordinate and station metadata
    df_merged["station_id"] = EXPECTED_STATION_ID
    df_merged["latitude"] = EXPECTED_LATITUDE
    df_merged["longitude"] = EXPECTED_LONGITUDE

    # Handle boolean masks after left join
    df_merged["smap_is_valid_am"] = df_merged["smap_is_valid_am"] == True
    df_merged["smap_is_valid_pm"] = df_merged["smap_is_valid_pm"] == True

    # Valid pass count and indicator
    df_merged["smap_valid_passes_count"] = (
        df_merged["smap_is_valid_am"].astype(int) + df_merged["smap_is_valid_pm"].astype(int)
    )
    df_merged["smap_has_valid_retrieval"] = df_merged["smap_valid_passes_count"] > 0

    # Derive daily mean with explicit rule
    am_vals = df_merged["smap_sm_am_m3_m3"].values
    pm_vals = df_merged["smap_sm_pm_m3_m3"].values
    pass_counts = df_merged["smap_valid_passes_count"].values

    daily_means = np.full(len(df_merged), np.nan)
    for i in range(len(df_merged)):
        n = pass_counts[i]
        if n == 2:
            daily_means[i] = (am_vals[i] + pm_vals[i]) / 2.0
        elif n == 1:
            daily_means[i] = am_vals[i] if not np.isnan(am_vals[i]) else pm_vals[i]
        else:
            daily_means[i] = np.nan

    df_merged["smap_sm_daily_mean_m3_m3"] = daily_means

    # Categorical retrieval status for provenance and filtering
    status_list = []
    for _, row in df_merged.iterrows():
        d = row["date_utc"]
        if d < RAW_DATE_MIN:
            status_list.append("PRE_MISSION")
        elif row["smap_valid_passes_count"] == 2:
            status_list.append("VALID_AM_PM")
        elif row["smap_is_valid_am"]:
            status_list.append("VALID_AM_ONLY")
        elif row["smap_is_valid_pm"]:
            status_list.append("VALID_PM_ONLY")
        elif pd.isna(row["smap_qual_flag_am"]) and pd.isna(row["smap_qual_flag_pm"]):
            status_list.append("NO_GRANULE")
        else:
            status_list.append("FAILED_RETRIEVAL")

    df_merged["smap_retrieval_status"] = status_list

    final_columns = [
        "date_utc",
        "station_id",
        "latitude",
        "longitude",
        "smap_sm_daily_mean_m3_m3",
        "smap_sm_am_m3_m3",
        "smap_sm_pm_m3_m3",
        "smap_qual_flag_am",
        "smap_qual_flag_pm",
        "smap_is_valid_am",
        "smap_is_valid_pm",
        "smap_valid_passes_count",
        "smap_has_valid_retrieval",
        "smap_retrieval_status",
    ]
    df_output = df_merged[final_columns].copy()

    # Serialization
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_output.to_csv(output_csv_path, index=False)

    # Compute descriptive statistics
    valid_sm = df_output["smap_sm_daily_mean_m3_m3"].dropna()
    status_counts = df_output["smap_retrieval_status"].value_counts().to_dict()

    audit_report = {
        "dataset_name": "SMAP_L3_SPL3SMP_E_006",
        "product_description": "SMAP Enhanced L3 Radiometer Global Daily 9 km EASE-Grid Soil Moisture",
        "source_raw_file": str(raw_csv_path.resolve()),
        "source_sha256": raw_sha256,
        "source_size_bytes": raw_size_bytes,
        "processed_file": str(output_csv_path.resolve()),
        "station_id": EXPECTED_STATION_ID,
        "station_latitude": EXPECTED_LATITUDE,
        "station_longitude": EXPECTED_LONGITUDE,
        "study_period": {
            "start_date": STUDY_TIMELINE_START,
            "end_date": STUDY_TIMELINE_END,
            "total_calendar_days": len(df_output),
        },
        "raw_data_coverage": {
            "start_date": schema_info["min_date"],
            "end_date": schema_info["max_date"],
            "raw_rows_count": schema_info["row_count"],
            "pre_mission_days": status_counts.get("PRE_MISSION", 0),
            "no_granule_gap_days": status_counts.get("NO_GRANULE", 0),
            "duplicate_dates_count": schema_info["duplicate_dates"],
        },
        "quality_flag_interpretation": {
            "valid_flag": VALID_RETRIEVAL_FLAG,
            "valid_flag_definition": "Bit 1=0 (attempted) and Bit 2=0 (successful retrieval)",
            "invalid_flags_observed": {
                "7.0": "Retrieval skipped, retrieval not successful (fill value -9999.0)",
                "13.0": "Retrieval attempted, retrieval not successful (constant fill 0.4276806 excluded)",
                "15.0": "Retrieval skipped, retrieval not successful (fill value -9999.0)",
            },
            "recommended_quality_note": (
                "Bit 0 (recommended quality) is set to 1 (not recommended) across all days at this site "
                "due to standard land-cover/vegetation density thresholds. Retrieval was attempted and "
                "successful (Bit 2=0, Flag 9.0), providing valid physical measurements in the 0.09-0.43 range."
            ),
        },
        "retrieval_counts": {
            "valid_am_retrievals": int(df_output["smap_is_valid_am"].sum()),
            "valid_pm_retrievals": int(df_output["smap_is_valid_pm"].sum()),
            "days_with_both_am_pm_valid": int((df_output["smap_is_valid_am"] & df_output["smap_is_valid_pm"]).sum()),
            "days_with_at_least_one_valid": int(df_output["smap_has_valid_retrieval"].sum()),
            "status_breakdown": status_counts,
        },
        "daily_mean_statistics_m3_m3": {
            "count": int(valid_sm.count()),
            "mean": float(valid_sm.mean()) if not valid_sm.empty else None,
            "std": float(valid_sm.std()) if not valid_sm.empty else None,
            "min": float(valid_sm.min()) if not valid_sm.empty else None,
            "max": float(valid_sm.max()) if not valid_sm.empty else None,
            "p25": float(valid_sm.quantile(0.25)) if not valid_sm.empty else None,
            "p50": float(valid_sm.median()) if not valid_sm.empty else None,
            "p75": float(valid_sm.quantile(0.75)) if not valid_sm.empty else None,
        },
        "missingness_policy": (
            "Missing satellite observations are preserved as NaN. No synthetic values or future "
            "observations were interpolated into target or predictor columns."
        ),
        "limitations": [
            "AppEEARS JSON request metadata, XML metadata, and granule lists were not retained in dataset/SMAP/raw/.",
            "Covers single point extraction at AAMU-JTG; does not provide spatial raster grid.",
            "SMAP L3 measures top 0-5 cm soil moisture only; it is an input feature, not root-zone ground truth."
        ],
    }

    audit_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    return df_output, audit_report


if __name__ == "__main__":
    df_out, audit = process_smap_daily_features()
    print("=" * 80)
    print(f"SMAP processing complete. Output saved to: {audit['processed_file']}")
    print(f"Total rows: {len(df_out)}, Calendar days: {audit['study_period']['total_calendar_days']}")
    print(f"Valid days with SMAP: {audit['retrieval_counts']['days_with_at_least_one_valid']}")
    print("Retrieval Status Breakdown:", audit["retrieval_counts"]["status_breakdown"])
    print("Daily SM Mean Stats:", audit["daily_mean_statistics_m3_m3"])
    print("=" * 80)
