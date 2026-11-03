"""
SoilDepth-AI — Common Ground-Truth Data Adapter Interface for Maharashtra
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Ingests, normalizes, and strictly validates heterogeneous in-situ ground-truth
         soil moisture observations across Maharashtra candidate networks (COSMOS, IMD,
         SAUs, PoCRA, ICAR). Enforces physical range boundaries, sensor-depth integrity,
         and absolute prohibition of inter-depth synthetic interpolation.
"""

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import numpy as np
import pandas as pd

from .config import METADATA_DIR, STATION_CONFIGS, get_station_config

NORMALIZED_COLUMNS = [
    "station_id",
    "timestamp",
    "latitude",
    "longitude",
    "sensor_depth_cm",
    "soil_moisture_vwc",
    "measurement_unit",
    "quality_flag",
    "source_dataset",
    "source_record_id",
]

ALLOWED_QUALITY_FLAGS: Set[str] = {
    "GOOD",
    "SUSPECT",
    "CALIBRATION_PERIOD",
    "OUT_OF_BOUNDS",
    "SENSOR_MALFUNCTION",
    "FROZEN_SOIL",
    "INTERPOLATED_PROHIBITED",
    "MISSING",
}

# Physical bounds for mineral / smectitic Vertisols in Maharashtra
MIN_VWC = 0.00
MAX_VWC = 0.65
MAX_SENSOR_DEPTH_CM = 200.0


class GroundTruthValidationError(ValueError):
    """Raised when ground-truth data violates physical, spatial, or temporal integrity rules."""
    pass


class MaharashtraGroundTruthAdapter:
    """
    Standardized adapter and verification harness for future in-situ soil moisture observations.
    """

    def __init__(self, station_registry_path: Optional[Path] = None):
        self.station_registry_path = station_registry_path or (METADATA_DIR / "station_registry.csv")
        self.depth_matrix_path = METADATA_DIR / "depth_compatibility_matrix.csv"
        self._load_registry()

    def _load_registry(self):
        """Loads known station metadata and depth compatibility for coordinate and depth verification."""
        self.known_stations: Dict[str, Dict[str, Any]] = {}
        if self.station_registry_path.exists():
            df_reg = pd.read_csv(self.station_registry_path)
            for _, r in df_reg.iterrows():
                sid = str(r["station_id"])
                depths = []
                for d in str(r.get("sensor_depths_cm", "")).split(","):
                    d_clean = d.strip().replace("cm", "").replace("depth-integrated", "").strip()
                    try:
                        depths.append(float(d_clean))
                    except ValueError:
                        pass

                self.known_stations[sid] = {
                    "station_name": str(r.get("station_name", "")),
                    "latitude": float(r["latitude"]),
                    "longitude": float(r["longitude"]),
                    "sensor_depths_cm": depths,
                    "district": str(r.get("district", "")),
                    "access_status": str(r.get("data_access_classification", "")),
                }

        self.depth_matrix: Dict[str, Dict[str, str]] = {}
        if self.depth_matrix_path.exists():
            df_mat = pd.read_csv(self.depth_matrix_path)
            for _, r in df_mat.iterrows():
                sid = str(r["station_id"])
                self.depth_matrix[sid] = {
                    "sensor_modality": str(r.get("sensor_modality", "")),
                    "model1_5cm": str(r.get("model1_5cm_compatibility", "")),
                    "model1_10cm": str(r.get("model1_10cm_compatibility", "")),
                    "model1_20cm": str(r.get("model1_20cm_compatibility", "")),
                    "model1_50cm": str(r.get("model1_50cm_compatibility", "")),
                    "interpolation_prohibited": str(r.get("prohibited_interpolation_flag", "")),
                }

    def normalize(
        self,
        df: pd.DataFrame,
        column_mapping: Dict[str, str],
        source_dataset: str,
        default_station_id: Optional[str] = None,
        input_vwc_unit: str = "m3/m3",
        input_timezone: str = "UTC",
    ) -> pd.DataFrame:
        """
        Maps arbitrary sensor telemetry schemas into canonical SoilDepth-AI schema.

        column_mapping must map target fields to source fields:
        {
            "timestamp": "Datetime_IST",
            "sensor_depth_cm": "Depth",
            "soil_moisture_vwc": "VWC",
            ...
        }
        """
        df_norm = pd.DataFrame(index=df.index)

        # Station ID
        if "station_id" in column_mapping:
            df_norm["station_id"] = df[column_mapping["station_id"]].astype(str)
        elif default_station_id:
            df_norm["station_id"] = default_station_id
        else:
            raise GroundTruthValidationError("station_id must be provided via mapping or default_station_id")

        # Timestamp normalization to ISO 8601 UTC
        if "timestamp" not in column_mapping:
            raise GroundTruthValidationError("timestamp column mapping is required")

        raw_ts = pd.to_datetime(df[column_mapping["timestamp"]])
        if input_timezone.upper() in ["IST", "ASIA/KOLKATA", "UTC+5:30", "UTC+05:30"]:
            # Local IST -> UTC
            if raw_ts.dt.tz is None:
                ts_utc = raw_ts.dt.tz_localize("Asia/Kolkata").dt.tz_convert("UTC")
            else:
                ts_utc = raw_ts.dt.tz_convert("UTC")
        else:
            if raw_ts.dt.tz is None:
                ts_utc = raw_ts.dt.tz_localize("UTC")
            else:
                ts_utc = raw_ts.dt.tz_convert("UTC")

        df_norm["timestamp"] = ts_utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Latitude & Longitude
        if "latitude" in column_mapping and "longitude" in column_mapping:
            df_norm["latitude"] = pd.to_numeric(df[column_mapping["latitude"]], errors="coerce")
            df_norm["longitude"] = pd.to_numeric(df[column_mapping["longitude"]], errors="coerce")
        elif default_station_id and default_station_id in self.known_stations:
            meta = self.known_stations[default_station_id]
            df_norm["latitude"] = meta["latitude"]
            df_norm["longitude"] = meta["longitude"]
        else:
            raise GroundTruthValidationError("Coordinates must be supplied via mapping or known station registry")

        # Sensor Depth
        if "sensor_depth_cm" not in column_mapping:
            raise GroundTruthValidationError("sensor_depth_cm column mapping is required")
        df_norm["sensor_depth_cm"] = pd.to_numeric(df[column_mapping["sensor_depth_cm"]], errors="coerce")

        # Check for prohibited interpolation markers
        for col in df.columns:
            if "interpolat" in col.lower() or "synthetic" in col.lower() or "estimated" in col.lower():
                # Flag as prohibited if interpolation column indicates true
                is_interp = df[col].astype(str).str.lower().isin(["true", "1", "yes", "interpolated"])
                if is_interp.any():
                    raise GroundTruthValidationError(
                        f"Interpolated sensor observations detected in column '{col}'. "
                        "Strict SoilDepth-AI protocol prohibits interpolating between sensor depths."
                    )

        # Volumetric Water Content
        if "soil_moisture_vwc" not in column_mapping:
            raise GroundTruthValidationError("soil_moisture_vwc column mapping is required")

        vwc_raw = pd.to_numeric(df[column_mapping["soil_moisture_vwc"]], errors="coerce")
        if input_vwc_unit.lower() in ["%", "percent", "percentage"]:
            vwc_norm = vwc_raw / 100.0
        elif input_vwc_unit.lower() in ["m3/m3", "m3_m3", "volumetric"]:
            vwc_norm = vwc_raw
        else:
            raise GroundTruthValidationError(f"Unrecognized input VWC unit: {input_vwc_unit}")

        df_norm["soil_moisture_vwc"] = vwc_norm.round(5)
        df_norm["measurement_unit"] = "m3/m3"

        # Quality flag
        if "quality_flag" in column_mapping:
            flags = df[column_mapping["quality_flag"]].astype(str).str.upper()
            is_synthetic = flags.isin(["SYNTHETIC", "INTERPOLATED", "SIMULATED", "INTERPOLATED_PROHIBITED", "ARTIFICIAL"])
            if is_synthetic.any():
                raise GroundTruthValidationError(
                    "Synthetic or interpolated observation flag detected in ground-truth records. "
                    "Strict SoilDepth-AI protocol prohibits training or validating on synthetic ground-truth data."
                )
            df_norm["quality_flag"] = flags.apply(lambda f: f if f in ALLOWED_QUALITY_FLAGS else "SUSPECT")
        else:
            df_norm["quality_flag"] = "GOOD"

        # Provenance
        df_norm["source_dataset"] = source_dataset
        if "source_record_id" in column_mapping:
            df_norm["source_record_id"] = df[column_mapping["source_record_id"]].astype(str)
        else:
            df_norm["source_record_id"] = [f"{source_dataset}_{i:06d}" for i in range(len(df_norm))]

        return df_norm[NORMALIZED_COLUMNS]

    def validate(self, df: pd.DataFrame, strict: bool = False) -> Dict[str, Any]:
        """
        Applies exhaustive high-assurance data integrity validation to normalized ground truth.
        If strict=True, raises GroundTruthValidationError on any integrity violation.
        """
        issues: List[str] = []
        total_records = len(df)

        if total_records == 0:
            if strict:
                raise GroundTruthValidationError("Dataset is empty")
            return {"is_valid": False, "total_records": 0, "issues": ["Dataset is empty"]}

        # 1. Schema check
        missing_cols = [c for c in NORMALIZED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise GroundTruthValidationError(f"Missing required normalized columns: {missing_cols}")

        # 2. Duplicate timestamps per (station_id, sensor_depth_cm)
        dup_count = int(df.duplicated(subset=["station_id", "sensor_depth_cm", "timestamp"]).sum())
        if dup_count > 0:
            issues.append(f"{dup_count} duplicate timestamp records detected for the same station and depth")

        # 3. Sensor depth validation
        invalid_depths = (df["sensor_depth_cm"] <= 0.0) | (df["sensor_depth_cm"] > MAX_SENSOR_DEPTH_CM) | df["sensor_depth_cm"].isna()
        invalid_depth_count = int(invalid_depths.sum())
        if invalid_depth_count > 0:
            issues.append(f"{invalid_depth_count} records have invalid or out-of-bounds sensor depth (must be 0 < depth <= 200 cm)")

        # Verify against documented station depths if station is in registry
        stations_present = df["station_id"].unique()
        for sid in stations_present:
            if sid in self.known_stations:
                known_depths = self.known_stations[sid]["sensor_depths_cm"]
                if known_depths:
                    observed_depths = df[df["station_id"] == sid]["sensor_depth_cm"].unique()
                    unmatched = [d for d in observed_depths if not any(abs(d - kd) < 1.0 for kd in known_depths)]
                    if unmatched:
                        issues.append(
                            f"Station '{sid}' contains observed depths {unmatched} not matching documented sensor depths {known_depths}"
                        )

        # 4. Physical VWC range checks [0.00, 0.65] m3/m3
        out_of_bounds_vwc = (df["soil_moisture_vwc"] < MIN_VWC) | (df["soil_moisture_vwc"] > MAX_VWC)
        oob_count = int(out_of_bounds_vwc.sum())
        if oob_count > 0:
            issues.append(f"{oob_count} records exceed physical volumetric water content bounds [0.00, 0.65] m3/m3")

        nan_vwc_count = int(df["soil_moisture_vwc"].isna().sum())
        if nan_vwc_count > 0:
            issues.append(f"{nan_vwc_count} records contain NaN soil_moisture_vwc values")

        # 5. Station coordinate consistency check
        for sid in stations_present:
            if sid in self.known_stations:
                expected_lat = self.known_stations[sid]["latitude"]
                expected_lon = self.known_stations[sid]["longitude"]
                sub = df[df["station_id"] == sid]
                max_lat_err = float((sub["latitude"] - expected_lat).abs().max())
                max_lon_err = float((sub["longitude"] - expected_lon).abs().max())
                if max_lat_err > 0.05 or max_lon_err > 0.05:
                    issues.append(
                        f"Station '{sid}' coordinates differ from registry by ({max_lat_err:.4f} lat, {max_lon_err:.4f} lon)"
                    )

        # 6. Quality flag consistency
        unknown_flags = ~df["quality_flag"].isin(ALLOWED_QUALITY_FLAGS)
        unknown_flag_count = int(unknown_flags.sum())
        if unknown_flag_count > 0:
            issues.append(f"{unknown_flag_count} records have unrecognized quality_flag values")

        good_records = int((df["quality_flag"] == "GOOD").sum())
        is_valid = len(issues) == 0

        if strict and not is_valid:
            raise GroundTruthValidationError(
                f"Ground-truth data validation failed with {len(issues)} issues:\n"
                + "\n".join(f"- {iss}" for iss in issues)
            )

        return {
            "adapter": "MaharashtraGroundTruthAdapter",
            "total_records": total_records,
            "good_records": good_records,
            "usable_pct": round(100.0 * good_records / total_records, 2) if total_records > 0 else 0.0,
            "duplicate_count": dup_count,
            "out_of_bounds_count": oob_count,
            "invalid_depth_count": invalid_depth_count,
            "is_valid": is_valid,
            "issues": issues,
        }

    def ingest_file(
        self,
        file_path: Union[str, Path],
        column_mapping: Dict[str, str],
        source_dataset: str,
        default_station_id: Optional[str] = None,
        input_vwc_unit: str = "m3/m3",
        input_timezone: str = "UTC",
        sheet_name: Optional[Union[str, int]] = 0,
        strict: bool = True,
    ) -> pd.DataFrame:
        """
        Ingests ground-truth observations from CSV, TSV, TXT, or Excel files,
        normalizes the schema to SoilDepth-AI standards, and runs strict integrity validation.
        """
        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"Ground-truth file does not exist: {fp}")

        ext = fp.suffix.lower()
        if ext in [".csv", ".txt"]:
            df_raw = pd.read_csv(fp)
        elif ext == ".tsv":
            df_raw = pd.read_csv(fp, sep="\t")
        elif ext in [".xlsx", ".xls"]:
            df_raw = pd.read_excel(fp, sheet_name=sheet_name)
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. Must be CSV (.csv, .txt), TSV (.tsv), or Excel (.xlsx, .xls)."
            )

        # Validate that mapped source columns exist in raw dataframe
        for target_key, raw_col in column_mapping.items():
            if raw_col not in df_raw.columns:
                raise GroundTruthValidationError(
                    f"Mapped source column '{raw_col}' (for '{target_key}') not found in file '{fp.name}'. "
                    f"Available columns: {list(df_raw.columns)}"
                )

        # Normalize schema
        df_norm = self.normalize(
            df=df_raw,
            column_mapping=column_mapping,
            source_dataset=source_dataset,
            default_station_id=default_station_id,
            input_vwc_unit=input_vwc_unit,
            input_timezone=input_timezone,
        )

        # Strict validation
        self.validate(df_norm, strict=strict)

        return df_norm

    def validate_temporal_alignment(
        self,
        df: pd.DataFrame,
        window_start: str = "2017-01-01",
        window_end: str = "2023-12-31",
    ) -> Dict[str, Any]:
        """
        Validates temporal alignment against the environmental feature timeline (2017-01-01 to 2023-12-31).
        Checks coverage, start/end dates, and records within/outside window.
        """
        if "timestamp" not in df.columns:
            raise GroundTruthValidationError("DataFrame must contain 'timestamp' column for temporal alignment")

        ts_series = pd.to_datetime(df["timestamp"], utc=True)
        if ts_series.empty:
            return {
                "window_start": window_start,
                "window_end": window_end,
                "data_start": None,
                "data_end": None,
                "total_records": 0,
                "records_in_window": 0,
                "coverage_pct": 0.0,
                "is_aligned": False,
            }

        t_min = ts_series.min()
        t_max = ts_series.max()

        start_dt = pd.to_datetime(window_start, utc=True)
        end_dt = pd.to_datetime(window_end, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)

        in_window_mask = (ts_series >= start_dt) & (ts_series <= end_dt)
        in_window_count = int(in_window_mask.sum())
        total_records = len(df)
        coverage_pct = round(100.0 * in_window_count / max(total_records, 1), 2)

        pre_window_count = int((ts_series < start_dt).sum())
        post_window_count = int((ts_series > end_dt).sum())

        return {
            "window_start": window_start,
            "window_end": window_end,
            "data_start": t_min.strftime("%Y-%m-%d"),
            "data_end": t_max.strftime("%Y-%m-%d"),
            "total_records": total_records,
            "records_in_window": in_window_count,
            "records_pre_window": pre_window_count,
            "records_post_window": post_window_count,
            "coverage_pct": coverage_pct,
            "is_aligned": (in_window_count > 0) and (coverage_pct >= 90.0),
        }

    def generate_coverage_summary(
        self,
        df: pd.DataFrame,
        min_obs_for_training: int = 180,
    ) -> Dict[str, Any]:
        """
        Produces exhaustive data coverage summary report per station and depth.
        Evaluates against the 180-observation minimum threshold required for depth model training.
        """
        if df.empty:
            return {"total_records": 0, "total_stations": 0, "stations": {}}

        df_copy = df.copy()
        df_copy["date_utc"] = pd.to_datetime(df_copy["timestamp"], utc=True).dt.strftime("%Y-%m-%d")

        stations_summary: Dict[str, Dict[str, Any]] = {}
        for sid, s_group in df_copy.groupby("station_id"):
            depth_summaries: Dict[float, Dict[str, Any]] = {}
            for depth, d_group in s_group.groupby("sensor_depth_cm"):
                n_records = len(d_group)
                unique_dates = int(d_group["date_utc"].nunique())
                min_date = str(d_group["date_utc"].min())
                max_date = str(d_group["date_utc"].max())

                span_days = (pd.to_datetime(max_date) - pd.to_datetime(min_date)).days + 1
                completeness_pct = round(100.0 * unique_dates / max(span_days, 1), 2)

                vwc = d_group["soil_moisture_vwc"].dropna()
                vwc_min = float(vwc.min()) if len(vwc) > 0 else None
                vwc_max = float(vwc.max()) if len(vwc) > 0 else None
                vwc_mean = float(vwc.mean()) if len(vwc) > 0 else None
                vwc_std = float(vwc.std()) if len(vwc) > 1 else 0.0

                flags = {k: int(v) for k, v in d_group["quality_flag"].value_counts().items()}
                sufficient = bool(unique_dates >= min_obs_for_training)

                depth_summaries[float(depth)] = {
                    "record_count": n_records,
                    "daily_observation_count": unique_dates,
                    "start_date": min_date,
                    "end_date": max_date,
                    "span_days": span_days,
                    "temporal_completeness_pct": completeness_pct,
                    "vwc_min": round(vwc_min, 4) if vwc_min is not None else None,
                    "vwc_max": round(vwc_max, 4) if vwc_max is not None else None,
                    "vwc_mean": round(vwc_mean, 4) if vwc_mean is not None else None,
                    "vwc_std": round(vwc_std, 4) if vwc_std is not None else None,
                    "quality_flags": flags,
                    "sufficient_for_training": sufficient,
                    "verdict": "SUFFICIENT" if sufficient else f"INSUFFICIENT_OBSERVATIONS ({unique_dates}/{min_obs_for_training} days)",
                }

            stations_summary[str(sid)] = depth_summaries

        return {
            "total_records": len(df_copy),
            "total_stations": len(stations_summary),
            "stations": stations_summary,
        }
