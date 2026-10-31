"""
SoilDepth-AI — Maharashtra Phase 2C Independent Scientific & Data Integrity Audit Tests
Pilot Station: IITM-PUNE-COSMOS
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Validates DEM coordinate and pixel extraction, coordinate transformations,
         satellite staleness thresholds, absence of future observation leakage,
         raw vs processed missingness, SoilGrids scaling and texture mass balance,
         ERA5-Land temporal alignment and zero deep soil moisture leakage, and
         SMAP unpopulated state handling.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAHARASHTRA_PROCESSED_DIR = REPO_ROOT / "dataset" / "Maharashtra" / "COSMOS" / "processed" / "IITM-PUNE"
DAILY_FEATURES_CSV = MAHARASHTRA_PROCESSED_DIR / "daily_environmental_features.csv"
STATIC_FEATURES_CSV = MAHARASHTRA_PROCESSED_DIR / "static_environmental_features.csv"
MANIFEST_JSON = MAHARASHTRA_PROCESSED_DIR / "acquisition_manifest.json"
QUALITY_REPORT_JSON = MAHARASHTRA_PROCESSED_DIR / "quality_report.json"


@pytest.fixture(scope="module")
def daily_features():
    assert DAILY_FEATURES_CSV.exists(), f"Missing {DAILY_FEATURES_CSV}"
    return pd.read_csv(DAILY_FEATURES_CSV)


@pytest.fixture(scope="module")
def static_features():
    assert STATIC_FEATURES_CSV.exists(), f"Missing {STATIC_FEATURES_CSV}"
    return pd.read_csv(STATIC_FEATURES_CSV)


@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST_JSON.exists(), f"Missing {MANIFEST_JSON}"
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def quality_report():
    assert QUALITY_REPORT_JSON.exists(), f"Missing {QUALITY_REPORT_JSON}"
    with open(QUALITY_REPORT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# 1. DEM PIXEL EXTRACTION & ELEVATION AUDIT
# ==============================================================================
def test_dem_pixel_extraction_and_elevation_discrepancy(static_features):
    """
    Verifies Copernicus DEM 30m pixel indexing, elevation decoding,
    subpixel bilinear interpolation, and independent SRTM comparison.
    """
    row = static_features.iloc[0]
    
    # 1. Coordinate and grid geometry
    assert row["station_id"] == "IITM-PUNE-COSMOS"
    assert round(float(row["latitude"]), 4) == 18.5372
    assert round(float(row["longitude"]), 4) == 73.8051
    assert row["raster_column_idx"] == 2898
    assert row["raster_row_idx"] == 1666
    assert abs(float(row["continuous_column_idx"]) - 2898.36) < 0.01
    assert abs(float(row["continuous_row_idx"]) - 1666.08) < 0.01
    assert row["dem_pixel_type"] == "RasterPixelIsPoint"

    # 2. Extracted vs Subpixel vs Benchmark vs SRTM
    dem_elev = float(row["elevation_m"])
    subpixel_elev = float(row["subpixel_bilinear_elevation_m"])
    benchmark_elev = float(row["benchmark_elevation_m"])
    srtm_elev = float(row["independent_srtm_elevation_m"])

    # Copernicus DEM elevation must be within [590, 593] m (591.58 m)
    assert 590.0 <= dem_elev <= 593.0, f"Unexpected DEM elevation: {dem_elev}"
    assert 589.5 <= subpixel_elev <= 592.0, f"Unexpected subpixel elevation: {subpixel_elev}"
    assert benchmark_elev == 560.0
    assert srtm_elev == 590.0

    # DEM must NOT have been artificially forced to 560.0 m
    assert dem_elev != 560.0, "Copernicus DEM must not be forced to 560.0 m"
    
    # Discrepancy against independent SRTM must be small (< 3.0 m)
    assert abs(dem_elev - srtm_elev) <= 3.0, f"Copernicus DEM diverges >3m from SRTM: {dem_elev} vs {srtm_elev}"

    # Documentation explanation present
    assert "Pashan" in str(row["elevation_discrepancy_explanation"])


# ==============================================================================
# 2. COORDINATE TRANSFORMATION & SPATIAL BOUNDS
# ==============================================================================
def test_coordinate_transformation_and_spatial_bounds():
    """Verifies WGS84 and UTM Zone 43N coordinate consistency and bounding box containment."""
    from services.data_acquisition.maharashtra.config import (
        STATION_LATITUDE,
        STATION_LONGITUDE,
        STATION_EASTING,
        STATION_NORTHING,
        BBOX_WEST,
        BBOX_SOUTH,
        BBOX_EAST,
        BBOX_NORTH,
        UTM_EPSG,
    )

    # Station coordinates must fall strictly within the ~3 km bounding box
    assert BBOX_WEST < STATION_LONGITUDE < BBOX_EAST
    assert BBOX_SOUTH < STATION_LATITUDE < BBOX_NORTH

    # UTM Zone 43N Easting and Northing sanity check for Pune
    assert 370000.0 < STATION_EASTING < 380000.0
    assert 2045000.0 < STATION_NORTHING < 2055000.0
    assert UTM_EPSG == "EPSG:32643"


# ==============================================================================
# 3. SATELLITE STALENESS THRESHOLDS
# ==============================================================================
def test_satellite_staleness_thresholds(daily_features):
    """
    Verifies that S1 (>30d) and S2 (>45d) staleness flags are rigorously evaluated
    and distinguishable from fresh observations.
    """
    df = daily_features

    # S1 staleness check
    s1_days = df["s1_days_since_last_valid_observation"]
    s1_stale = df["s1_is_stale"]
    assert s1_stale.dtype == bool

    # For days where days_since > 30, is_stale must be True
    stale_mask_s1 = s1_days > 30.0
    assert (s1_stale[stale_mask_s1] == True).all(), "S1 observations > 30 days old must be flagged is_stale=True"

    # For days where days_since <= 30 and not NaN, is_stale must be False
    fresh_mask_s1 = (s1_days <= 30.0) & (s1_days.notna())
    assert (s1_stale[fresh_mask_s1] == False).all(), "S1 observations <= 30 days old must not be flagged stale"

    # S2 staleness check
    s2_days = df["s2_days_since_last_valid_observation"]
    s2_stale = df["s2_is_stale"]
    assert s2_stale.dtype == bool

    # For days where days_since > 45, is_stale must be True
    stale_mask_s2 = s2_days > 45.0
    assert (s2_stale[stale_mask_s2] == True).all(), "S2 observations > 45 days old must be flagged is_stale=True"

    # For days where days_since <= 45 and not NaN, is_stale must be False
    fresh_mask_s2 = (s2_days <= 45.0) & (s2_days.notna())
    assert (s2_stale[fresh_mask_s2] == False).all(), "S2 observations <= 45 days old must not be flagged stale"


# ==============================================================================
# 4. NO FUTURE OBSERVATION LEAKAGE
# ==============================================================================
def test_no_future_observation_leakage(daily_features):
    """
    Verifies that observation_source_date is strictly prior to current date D (causal shift(1)),
    preventing any future or same-day lookahead.
    """
    df = daily_features
    cur_dates = pd.to_datetime(df["date"])

    # 1. Sentinel-1 causal check
    s1_src_dates = pd.to_datetime(df["s1_observation_source_date"])
    valid_s1_src = s1_src_dates.notna()
    diff_s1 = (cur_dates[valid_s1_src] - s1_src_dates[valid_s1_src]).dt.days
    assert (diff_s1 >= 1).all(), "Sentinel-1 source observation date must be at least 1 day prior to prediction date"

    # 2. Sentinel-2 causal check
    s2_src_dates = pd.to_datetime(df["s2_observation_source_date"])
    valid_s2_src = s2_src_dates.notna()
    diff_s2 = (cur_dates[valid_s2_src] - s2_src_dates[valid_s2_src]).dt.days
    assert (diff_s2 >= 1).all(), "Sentinel-2 source observation date must be at least 1 day prior to prediction date"

    # 3. Weather causal check: precip_lag_1d on day D must equal precipitation_total_mm on day D-1
    assert np.allclose(df["precip_lag_1d"].iloc[1:].values, df["precipitation_total_mm"].iloc[:-1].values, atol=1e-4)


# ==============================================================================
# 5. RAW VERSUS PROCESSED MISSINGNESS
# ==============================================================================
def test_raw_versus_processed_missingness(daily_features, quality_report):
    """
    Verifies that raw observation missingness (sparse satellite revisit) is strictly
    distinguished from imputed/LOCF feature coverage.
    """
    df = daily_features
    total_days = len(df)

    # S1 raw observations: 175 days
    s1_raw_count = int(df["s1_raw_observation_available"].sum())
    assert s1_raw_count == 175, f"Expected 175 raw S1 observations, got {s1_raw_count}"
    s1_raw_miss_pct = 100.0 * (1.0 - s1_raw_count / total_days)
    assert 93.0 <= s1_raw_miss_pct <= 94.0, f"Expected S1 raw missingness ~93.15%, got {s1_raw_miss_pct}%"

    # S1 LOCF features coverage: > 99%
    s1_locf_count = int(df["s1_has_past_obs"].sum())
    assert s1_locf_count > 2500

    # S2 raw clear observations: 299 days
    s2_raw_count = int(df["s2_raw_observation_available"].sum())
    assert s2_raw_count == 299, f"Expected 299 raw S2 clear observations, got {s2_raw_count}"
    s2_raw_miss_pct = 100.0 * (1.0 - s2_raw_count / total_days)
    assert 88.0 <= s2_raw_miss_pct <= 89.0, f"Expected S2 raw missingness ~88.30%, got {s2_raw_miss_pct}%"

    # S2 LOCF features coverage: > 98%
    s2_locf_count = int(df["s2_has_past_obs"].sum())
    assert s2_locf_count > 2500

    # Quality report must report raw missingness separately from imputed coverage
    q_s1 = quality_report["datasets_summary"]["sentinel1_sar"]
    assert "raw_missingness_pct" in q_s1
    assert "imputed_locf_coverage_pct" in q_s1
    assert q_s1["raw_missingness_pct"] > 90.0

    q_s2 = quality_report["datasets_summary"]["sentinel2_optical"]
    assert "raw_missingness_pct" in q_s2
    assert "imputed_locf_coverage_pct" in q_s2
    assert q_s2["raw_missingness_pct"] > 85.0


# ==============================================================================
# 6. SOILGRIDS UNIT CONVERSIONS & SCALING
# ==============================================================================
def test_soilgrids_unit_conversion(static_features):
    """
    Verifies raw integer DN to physical scale factor conversions for all 8 SoilGrids properties.
    """
    row = static_features.iloc[0]
    for depth in ["0_5cm", "5_15cm", "15_30cm", "30_60cm"]:
        # bdod: raw cg/cm3 / 100 -> g/cm3
        raw_bdod = row[f"soilgrids_bdod_{depth}_raw"]
        scaled_bdod = row[f"soilgrids_bdod_{depth}"]
        assert abs(scaled_bdod - round(raw_bdod / 100.0, 3)) < 1e-4

        # clay, sand, silt: raw g/kg / 10 -> %
        for tex in ["clay", "sand", "silt"]:
            raw_tex = row[f"soilgrids_{tex}_{depth}_raw"]
            scaled_tex = row[f"soilgrids_{tex}_{depth}"]
            assert abs(scaled_tex - round(raw_tex / 10.0, 2)) < 1e-4

        # ocd: raw hg/m3 / 10 -> kg/m3
        raw_ocd = row[f"soilgrids_ocd_{depth}_raw"]
        scaled_ocd = row[f"soilgrids_ocd_{depth}"]
        assert abs(scaled_ocd - round(raw_ocd / 10.0, 2)) < 1e-4

        # wv*: raw (10*cm3/dm3) / 1000 -> m3/m3
        for wv in ["wv0010", "wv0033", "wv1500"]:
            raw_wv = row[f"soilgrids_{wv}_{depth}_raw"]
            scaled_wv = row[f"soilgrids_{wv}_{depth}"]
            assert abs(scaled_wv - round(raw_wv / 1000.0, 4)) < 1e-4


# ==============================================================================
# 7. SOIL TEXTURE MASS BALANCE & HYDRAULIC CONSISTENCY
# ==============================================================================
def test_soil_texture_mass_balance_and_hydraulics(static_features):
    """
    Verifies clay + sand + silt = 100.00% mass balance closure across all 4 depths,
    water retention suction hierarchy (PWP < FC < saturation), and positive AWC.
    """
    row = static_features.iloc[0]
    for depth in ["0_5cm", "5_15cm", "15_30cm", "30_60cm"]:
        c = float(row[f"soilgrids_clay_{depth}"])
        s = float(row[f"soilgrids_sand_{depth}"])
        si = float(row[f"soilgrids_silt_{depth}"])
        tex_sum = float(row[f"soilgrids_texture_sum_{depth}"])

        # Texture closure must be exactly 100.00%
        assert abs(tex_sum - 100.0) < 0.1, f"Texture mass balance violated at {depth}: {tex_sum}%"
        assert abs((c + s + si) - 100.0) < 0.1

        # Suction hierarchy: wv1500 (1500 kPa) < wv0033 (33 kPa) < wv0010 (10 kPa)
        wv10 = float(row[f"soilgrids_wv0010_{depth}"])
        wv33 = float(row[f"soilgrids_wv0033_{depth}"])
        wv15 = float(row[f"soilgrids_wv1500_{depth}"])
        assert wv15 < wv33 < wv10, f"Suction hierarchy violated at {depth}: {wv15} < {wv33} < {wv10}"

        # Derived properties: AWC = FC - PWP
        fc = float(row[f"derived_field_capacity_{depth}"])
        pwp = float(row[f"derived_wilting_point_{depth}"])
        awc = float(row[f"derived_awc_{depth}"])
        assert fc == wv33
        assert pwp == wv15
        assert abs(awc - (fc - pwp)) < 1e-4
        assert 0.05 <= awc <= 0.25, f"Derived AWC out of agronomic range at {depth}: {awc}"


# ==============================================================================
# 8. ERA5-LAND TEMPORAL ALIGNMENT & ZERO DEEP SOIL MOISTURE
# ==============================================================================
def test_era5_land_temporal_alignment_and_no_deep_sm(daily_features):
    """
    Verifies 2,556 continuous daily rows, zero missing hours,
    and strict absence of ERA5 deep soil moisture variables (swvl1-4).
    """
    df = daily_features
    assert len(df) == 2556
    assert (df["era5_hourly_count"] == 24).all(), "Every day must have exactly 24 hourly timesteps"
    assert (df["is_complete"] == True).all()

    # Zero ERA5 soil moisture variables allowed in feature set
    forbidden_sm = ["swvl1", "swvl2", "swvl3", "swvl4", "era5_sm", "deep_soil_moisture"]
    for col in df.columns:
        for f in forbidden_sm:
            assert f not in col.lower(), f"Forbidden ERA5 soil moisture column detected: {col}"


# ==============================================================================
# 9. SMAP UNAVAILABLE-STATE HANDLING
# ==============================================================================
def test_smap_unavailable_state_handling(daily_features, quality_report):
    """
    Verifies SMAP L3 is explicitly flagged AWAITING_AUTH and preserved as NaN
    without synthetic data fabrication or replacement with SMAP L4.
    """
    df = daily_features

    # SMAP retrievals must be False
    assert (df["smap_has_valid_retrieval"] == False).all()
    assert (df["smap_raw_observation_available"] == False).all()
    assert (df["smap_is_stale"] == True).all()

    # Daily mean and rolling features must be completely NaN
    assert df["smap_sm_daily_mean_m3_m3"].isna().all(), "SMAP daily mean must be NaN"
    assert df["smap_sm_lag_1d"].isna().all(), "SMAP lag must be NaN"
    assert df["smap_sm_roll_mean_3d"].isna().all(), "SMAP roll mean must be NaN"

    # Quality report status
    q_smap = quality_report["datasets_summary"]["smap_l3"]
    assert q_smap["status"] == "AWAITING_AUTH"
    assert q_smap["zero_synthetic_data_verified"] == True
    assert q_smap["imputed_coverage_pct"] == 0.0

