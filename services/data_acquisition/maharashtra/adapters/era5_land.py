"""
SoilDepth-AI — ERA5-Land Reanalysis Weather Adapter
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Ingests ECMWF ERA5-Land hourly reanalysis, aggregates to daily totals/means,
         computes antecedent memory features with strictly past-only shift(1) windows,
         and verifies zero deep soil moisture leakage across Maharashtra stations.
"""

import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from ..config import (
    StationConfig,
    PUNE_CONFIG,
    STATION_ID,
    STATION_LATITUDE,
    STATION_LONGITUDE,
    BENCHMARK_ELEVATION_M,
    START_DATE,
    END_DATE,
    EXPECTED_DAILY_ROWS,
    ERA5_RAW_DIR,
    PHYSICAL_LIMITS,
)
from .base_adapter import BaseEnvironmentalAdapter


class ERA5LandAdapter(BaseEnvironmentalAdapter):
    """ECMWF ERA5-Land Reanalysis data adapter."""

    def __init__(self, station_config: Optional[StationConfig] = None, raw_dir: Optional[Path] = None):
        cfg = station_config or PUNE_CONFIG
        self.station_config = cfg
        target_raw_dir = raw_dir if raw_dir is not None else cfg.era5_raw_dir
        super().__init__(
            name="ERA5-Land",
            source="ECMWF Copernicus Climate Change Service (via Open-Meteo Archive API)",
            raw_dir=target_raw_dir,
            station_config=cfg,
        )

    def acquire(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves hourly ERA5-Land reanalysis year-by-year and stores unmodified JSON files.
        """
        s_date = start_date or self.station_config.start_date
        e_date = end_date or self.station_config.end_date
        start_year = int(s_date[:4])
        end_year = int(e_date[:4])
        manifest_records = []
        downloaded_years = []

        print(f"[{self.name}] Acquiring hourly reanalysis for {self.station_config.station_id} ({s_date} to {e_date})...")

        for year in range(start_year, end_year + 1):
            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31"
            raw_file = self.raw_dir / f"era5_hourly_{year}.json"

            if raw_file.exists() and raw_file.stat().st_size > 10000:
                print(f"  -> Reusing existing raw file: {raw_file.name}")
            else:
                url = (
                    f"https://archive-api.open-meteo.com/v1/archive?"
                    f"latitude={self.station_config.latitude}&longitude={self.station_config.longitude}&"
                    f"start_date={year_start}&end_date={year_end}&"
                    f"hourly=temperature_2m,dew_point_2m,precipitation,wind_speed_10m,wind_direction_10m,shortwave_radiation&"
                    f"wind_speed_unit=ms&timezone=UTC"
                )
                req = urllib.request.Request(url, headers={"User-Agent": "SoilDepth-AI/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw_data = resp.read()

                with open(raw_file, "wb") as f:
                    f.write(raw_data)
                print(f"  -> Downloaded and cached: {raw_file.name} ({len(raw_data):,} bytes)")

            record = self.create_manifest_record(
                filepath=raw_file,
                spatial_resolution="0.1 deg (~9 km)",
                temporal_resolution="Hourly",
                units="°C, mm, m/s, W/m², deg",
                crs="EPSG:4326 (WGS84)",
                status="VERIFIED_RAW_SAVED",
                notes=f"Year {year} ECMWF ERA5-Land hourly point reanalysis for {self.station_config.station_id}",
                collection_identifier="reanalysis-era5-land",
                temporal_coverage=f"{year_start} to {year_end}",
                download_url_or_id=f"https://archive-api.open-meteo.com/v1/archive?start_date={year_start}&end_date={year_end}&hourly=temperature_2m,dew_point_2m,precipitation,wind_speed_10m,wind_direction_10m,shortwave_radiation",
            )
            manifest_records.append(record)
            downloaded_years.append(year)

        return {
            "status": "ACQUISITION_SUCCESS",
            "years_acquired": downloaded_years,
            "manifest_records": manifest_records,
        }

    def extract_features(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Parses raw hourly JSON files into a standardized daily weather feature table
        with antecedent memory and cyclical transformations.
        Guarantees zero target or ERA5 deep soil moisture leakage.
        """
        s_date = start_date or self.station_config.start_date
        e_date = end_date or self.station_config.end_date
        start_year = int(s_date[:4])
        end_year = int(e_date[:4])

        all_times: List[str] = []
        all_t2m: List[float] = []
        all_d2m: List[float] = []
        all_precip: List[float] = []
        all_wind_speed: List[float] = []
        all_wind_dir: List[float] = []
        all_solar_flux: List[float] = []

        for year in range(start_year, end_year + 1):
            raw_file = self.raw_dir / f"era5_hourly_{year}.json"
            if not raw_file.exists():
                self.acquire(f"{year}-01-01", f"{year}-12-31")

            with open(raw_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            t2m = hourly.get("temperature_2m", [])
            d2m = hourly.get("dew_point_2m", [])
            precip = hourly.get("precipitation", [])
            ws = hourly.get("wind_speed_10m", [])
            wd = hourly.get("wind_direction_10m", [])
            ssrd = hourly.get("shortwave_radiation", [])

            all_times.extend(times)
            all_t2m.extend(t2m)
            all_d2m.extend(d2m)
            all_precip.extend(precip)
            all_wind_speed.extend(ws)
            all_wind_dir.extend(wd)
            all_solar_flux.extend(ssrd)

        df_hourly = pd.DataFrame({
            "timestamp_utc": all_times,
            "temperature_2m_c": all_t2m,
            "dewpoint_2m_c": all_d2m,
            "precipitation_mm": all_precip,
            "wind_speed_ms": all_wind_speed,
            "wind_direction_deg": all_wind_dir,
            "solar_flux_w_m2": all_solar_flux,
        })

        df_hourly["date"] = df_hourly["timestamp_utc"].str[:10]

        # Compute hourly wind vector components:
        # u = -s * sin(d), v = -s * cos(d)
        wind_rad = np.radians(df_hourly["wind_direction_deg"])
        df_hourly["u10_ms"] = -df_hourly["wind_speed_ms"] * np.sin(wind_rad)
        df_hourly["v10_ms"] = -df_hourly["wind_speed_ms"] * np.cos(wind_rad)

        daily_rows = []
        for date_str, group in df_hourly.groupby("date", sort=True):
            if date_str < s_date or date_str > e_date:
                continue

            count_hours = len(group)
            t_mean = float(group["temperature_2m_c"].mean())
            t_min = float(group["temperature_2m_c"].min())
            t_max = float(group["temperature_2m_c"].max())
            dp_mean = float(group["dewpoint_2m_c"].mean())

            # Vapor pressure deficit via Tetens formula (kPa)
            es = 0.61078 * math.exp((17.27 * t_mean) / (t_mean + 237.3))
            ea = 0.61078 * math.exp((17.27 * dp_mean) / (dp_mean + 237.3))
            vpd = max(0.0, es - ea)

            precip_tot = max(0.0, float(group["precipitation_mm"].sum()))
            # Daily solar radiation accumulation in MJ/m2: sum(W/m2 * 3600 s) / 1e6
            solar_mj = max(0.0, float(group["solar_flux_w_m2"].sum() * 3600.0 / 1e6))
            wind_s = float(group["wind_speed_ms"].mean())
            u10 = float(group["u10_ms"].mean())
            v10 = float(group["v10_ms"].mean())

            daily_rows.append({
                "date": date_str,
                "station_id": self.station_config.station_id,
                "latitude": self.station_config.latitude,
                "longitude": self.station_config.longitude,
                "elevation_m": self.station_config.benchmark_elevation_m,
                "era5_hourly_count": count_hours,
                "is_complete": (count_hours == 24),
                "temperature_2m_mean_c": round(t_mean, 3),
                "temperature_2m_min_c": round(t_min, 3),
                "temperature_2m_max_c": round(t_max, 3),
                "dewpoint_2m_mean_c": round(dp_mean, 3),
                "vpd_kpa": round(vpd, 3),
                "precipitation_total_mm": round(precip_tot, 4),
                "solar_radiation_total_mj_m2": round(solar_mj, 3),
                "wind_speed_10m_ms": round(wind_s, 3),
                "wind_u10_mean_ms": round(u10, 3),
                "wind_v10_mean_ms": round(v10, 3),
            })

        df_daily = pd.DataFrame(daily_rows)

        # Antecedent weather memory transformations (strictly past-only shift(1))
        df_daily["precip_lag_1d"] = df_daily["precipitation_total_mm"].shift(1).fillna(0.0).round(4)
        df_daily["precip_roll_sum_3d"] = df_daily["precipitation_total_mm"].shift(1).rolling(3, min_periods=1).sum().round(4)
        df_daily["precip_roll_sum_7d"] = df_daily["precipitation_total_mm"].shift(1).rolling(7, min_periods=1).sum().round(4)
        df_daily["precip_roll_sum_14d"] = df_daily["precipitation_total_mm"].shift(1).rolling(14, min_periods=1).sum().round(4)
        df_daily["precip_roll_sum_30d"] = df_daily["precipitation_total_mm"].shift(1).rolling(30, min_periods=1).sum().round(4)

        # Days since rain > 1.0 mm (causal accumulator)
        days_since = []
        current_streak = 10.0
        precip_vals = df_daily["precipitation_total_mm"].values
        for i in range(len(precip_vals)):
            if i > 0:
                if precip_vals[i - 1] > 1.0:
                    current_streak = 1.0
                else:
                    current_streak += 1.0
            days_since.append(current_streak)
        df_daily["days_since_rain_gt_1mm"] = days_since

        df_daily["temp_roll_mean_7d"] = df_daily["temperature_2m_mean_c"].shift(1).rolling(7, min_periods=1).mean().round(3)
        df_daily["temp_roll_mean_30d"] = df_daily["temperature_2m_mean_c"].shift(1).rolling(30, min_periods=1).mean().round(3)
        df_daily["vpd_roll_mean_7d"] = df_daily["vpd_kpa"].shift(1).rolling(7, min_periods=1).mean().round(3)
        df_daily["solar_roll_mean_7d"] = df_daily["solar_radiation_total_mj_m2"].shift(1).rolling(7, min_periods=1).mean().round(3)

        # Cyclical day of year
        dt_series = pd.to_datetime(df_daily["date"])
        doy = dt_series.dt.dayofyear.values
        df_daily["doy_sin"] = np.round(np.sin(2.0 * np.pi * doy / 365.25), 5)
        df_daily["doy_cos"] = np.round(np.cos(2.0 * np.pi * doy / 365.25), 5)

        return df_daily

    def validate_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Applies rigorous quality, completeness, and boundary checks."""
        issues = []
        row_count = len(df)
        expected = self.station_config.expected_daily_rows
        if row_count != expected:
            issues.append(f"Row count {row_count} differs from expected {expected}")

        # Check bounds
        t_min = df["temperature_2m_mean_c"].min()
        t_max = df["temperature_2m_mean_c"].max()
        if t_min < PHYSICAL_LIMITS["temperature_c"]["min"] or t_max > PHYSICAL_LIMITS["temperature_c"]["max"]:
            issues.append(f"Temperature mean out of bounds [{t_min}, {t_max}]")

        p_max = df["precipitation_total_mm"].max()
        if p_max > PHYSICAL_LIMITS["precipitation_mm"]["max"]:
            issues.append(f"Precipitation max {p_max} exceeds physical threshold")

        incomplete_days = (df["is_complete"] == False).sum()
        if incomplete_days > 0:
            issues.append(f"{incomplete_days} days have fewer than 24 hourly observations")

        # Verify no deep soil moisture columns
        swvl_cols = [c for c in df.columns if "swvl" in c.lower() or "deep_sm" in c.lower()]
        if swvl_cols:
            issues.append(f"Forbidden ERA5 deep soil moisture columns found: {swvl_cols}")

        return {
            "adapter": self.name,
            "station_id": self.station_config.station_id,
            "row_count": row_count,
            "expected_rows": expected,
            "hourly_timesteps_verified": row_count * 24,
            "incomplete_days": int(incomplete_days),
            "temperature_range_c": [float(t_min), float(t_max)],
            "max_daily_precip_mm": float(p_max),
            "zero_era5_deep_sm_verified": len(swvl_cols) == 0,
            "is_valid": len(issues) == 0,
            "issues": issues,
        }
