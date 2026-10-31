"""
SoilDepth-AI — Tests for In-Situ & ERA5-Land Dataset Builder
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from services.modelling.config import (
    REPO_ROOT,
    STATION_ID,
    STATION_LAT,
    STATION_LON,
    SENSOR_DEPTHS,
    MIN_VALID_HOURS_PER_DAY,
    INTERIM_DATA_DIR,
    SensorDepthConfig,
)
from services.modelling.dataset_builder import (
    parse_static_soil_properties,
    parse_scan_stm_file,
    build_aligned_pilot_dataset,
)


def test_parse_static_soil_properties():
    """Verify static HWSD soil texture properties are correctly extracted."""
    static_file = (
        REPO_ROOT
        / "dataset"
        / "ISMN"
        / "SCAN"
        / "extracted"
        / "surface_0-10cm"
        / "SCAN"
        / STATION_ID
        / f"SCAN_SCAN_{STATION_ID}_static_variables.csv"
    )
    assert static_file.exists()
    props = parse_static_soil_properties(static_file)

    assert "0.00-0.30" in props
    assert "0.30-1.00" in props

    top = props["0.00-0.30"]
    assert top["clay_fraction_pct"] == 25.0
    assert top["sand_fraction_pct"] == 53.0
    assert top["silt_fraction_pct"] == 22.0
    assert top["organic_carbon_pct"] == 0.98
    assert top["saturation_m3_m3"] == 0.43

    deep = props["0.30-1.00"]
    assert deep["clay_fraction_pct"] == 39.0
    assert deep["sand_fraction_pct"] == 41.0
    assert deep["silt_fraction_pct"] == 20.0
    assert deep["organic_carbon_pct"] == 0.39
    assert deep["saturation_m3_m3"] == 0.44


def test_station_metadata_mismatch_raises(tmp_path):
    """Verify parser rejects STM file if coordinates or station name deviate."""
    bad_stm = tmp_path / "bad_metadata.stm"
    # Create invalid header with wrong latitude (40.0 instead of 34.78534)
    bad_header = "SCAN SCAN AAMU-JTG 40.00000 -86.55906 241.0 0.0508 0.0508 'Stevens-Hydraprobe-Analog'\n"
    bad_data = "2015/01/01 00:00 0.350 G V\n"
    with open(bad_stm, "w") as f:
        f.write(bad_header + bad_data)

    cfg = SENSOR_DEPTHS["sm_5cm"]
    with pytest.raises(ValueError, match="Latitude mismatch"):
        parse_scan_stm_file(bad_stm, cfg)


def test_diurnal_completeness_threshold(tmp_path):
    """Verify parser enforces >= 18 valid hours/day threshold."""
    stm = tmp_path / "test_diurnal.stm"
    header = f"SCAN SCAN {STATION_ID} {STATION_LAT} {STATION_LON} 241.0 0.0508 0.0508 'Stevens-Hydraprobe-Analog'\n"

    # Day 1: 20 hours (valid >= 18)
    # Day 2: 12 hours (invalid < 18 -> should become NaN)
    lines = [header]
    for h in range(20):
        lines.append(f"2015/01/01 {h:02d}:00 0.350 G V\n")
    for h in range(12):
        lines.append(f"2015/01/02 {h:02d}:00 0.350 G V\n")

    with open(stm, "w") as f:
        f.writelines(lines)

    cfg = SENSOR_DEPTHS["sm_5cm"]
    df_daily, audit = parse_scan_stm_file(stm, cfg)

    assert len(df_daily) == 2
    day1 = df_daily[df_daily["date_utc"] == "2015-01-01"].iloc[0]
    day2 = df_daily[df_daily["date_utc"] == "2015-01-02"].iloc[0]

    assert day1["obs_hours_sm_5cm"] == 20
    assert not np.isnan(day1["target_sm_5cm"])
    assert day1["target_sm_5cm"] == pytest.approx(0.350)

    assert day2["obs_hours_sm_5cm"] == 12
    assert np.isnan(day2["target_sm_5cm"])  # Excluded due to diurnal threshold


def test_interim_aligned_raw_dataset_exists_and_valid():
    """Verify generated interim dataset satisfies all schema constraints."""
    raw_csv = INTERIM_DATA_DIR / f"{STATION_ID}_aligned_raw.csv"
    assert raw_csv.exists(), f"Aligned raw CSV missing at {raw_csv}"

    df = pd.read_csv(raw_csv)
    assert len(df) == 3287
    assert df["station_id"].iloc[0] == STATION_ID

    required_targets = [f"target_{k}" for k in SENSOR_DEPTHS.keys()]
    for t in required_targets:
        assert t in df.columns
        # Volumetric soil moisture must be strictly bounded between 0 and 0.60
        valid_vals = df[t].dropna()
        assert (valid_vals >= 0.0).all()
        assert (valid_vals <= 0.60).all()
