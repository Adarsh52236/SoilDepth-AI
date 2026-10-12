"""Integration and end-to-end pipeline tests with messy datasets and adapters."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from soildepth_preprocessing.adapters import (
    AdapterRegistry,
    DEMAdapter,
    ERA5LandAdapter,
    ISMNAdapter,
    SentinelAdapter,
    SMAPAdapter,
    SoilGridsAdapter,
)
from soildepth_preprocessing.cli import main
from soildepth_preprocessing.config import load_config_from_yaml
from soildepth_preprocessing.pipeline import PreprocessingPipeline


@pytest.fixture
def messy_csv_file(tmp_path: Path) -> Path:
    """Create a synthetic deliberately messy raw dataset.

    Contains:
    - Trailing and leading whitespace in strings
    - Exact duplicate record
    - Sentinel null values (-999, -9999, "NA")
    - Outlier values
    - Invalid latitude coordinate (125.0)
    - Soil moisture in percentage (needs conversion to m3/m3)
    - Temperature in Kelvin (needs conversion to Celsius)
    - Missing target label row
    """
    csv_content = """station,date_time,lat,lon,depth_cm,sm_pct,t2m,precip
  STN_A  ,2026-01-01 00:00:00,45.1,9.2,10.0,25.0,293.15,0.0
STN_A,2026-01-01 00:00:00,45.1,9.2,10.0,25.0,293.15,0.0
STN_A,2026-01-02 00:00:00,45.1,9.2,10.0,30.0,295.15,5.2
STN_B,2026-01-01 00:00:00,125.0,9.2,10.0,20.0,290.15,0.0
STN_C,2026-01-01 00:00:00,45.5,9.8,10.0,-999,291.15,0.0
STN_D,2026-01-01 00:00:00,45.6,9.9,10.0,28.0,-9999,NA
"""
    file_path = tmp_path / "raw_messy_dataset.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    return file_path


def test_end_to_end_pipeline_execution(tmp_path: Path, messy_csv_file: Path) -> None:
    output_parquet = tmp_path / "cleaned_data.parquet"
    report_json = tmp_path / "report.json"
    report_md = tmp_path / "report.md"

    # Store raw content before running
    raw_content_before = messy_csv_file.read_bytes()

    # Load example config
    config_path = Path("data-pipeline/config/example.yaml")
    config = load_config_from_yaml(config_path)

    pipeline = PreprocessingPipeline(config)
    result = pipeline.run(
        input_path=messy_csv_file,
        output_path=output_parquet,
        report_json_path=report_json,
        report_md_path=report_md,
    )

    # 1. Raw input file must remain 100% UNCHANGED (immutability)
    assert messy_csv_file.read_bytes() == raw_content_before

    # 2. Files generated successfully
    assert output_parquet.is_file()
    assert report_json.is_file()
    assert report_md.is_file()

    # 3. Validation checks
    assert result.success is True
    # Initial rows: 6
    # - 1 duplicate dropped
    # - 1 invalid coordinate dropped (STN_B: lat 125.0)
    # - 1 missing target dropped (STN_C: -999)
    # Remaining: 3 rows (STN_A row 1, STN_A row 2, STN_D)
    assert result.report.initial_row_count == 6
    assert result.report.final_row_count == 3
    assert result.report.dropped_row_count == 3

    # Check that unit conversion applied: 25.0% -> 0.25 m3/m3
    df_clean = pd.read_parquet(output_parquet)
    assert df_clean["soil_moisture"].iloc[0] == pytest.approx(0.25)
    # Kelvin to Celsius: 293.15 -> 20.0 C
    assert df_clean["air_temperature_c"].iloc[0] == pytest.approx(20.0)


def test_pipeline_reproducibility(tmp_path: Path, messy_csv_file: Path) -> None:
    config = load_config_from_yaml("data-pipeline/config/example.yaml")
    pipeline = PreprocessingPipeline(config)

    out1 = tmp_path / "run1.parquet"
    out2 = tmp_path / "run2.parquet"

    res1 = pipeline.run(messy_csv_file, out1)
    res2 = pipeline.run(messy_csv_file, out2)

    df1 = pd.read_parquet(out1)
    df2 = pd.read_parquet(out2)

    pd.testing.assert_frame_equal(df1, df2)
    assert res1.report.final_row_count == res2.report.final_row_count


def test_cli_execution(tmp_path: Path, messy_csv_file: Path) -> None:
    runner = CliRunner()
    output_p = tmp_path / "cli_clean.parquet"
    rep_json = tmp_path / "cli_report.json"
    rep_md = tmp_path / "cli_report.md"

    res = runner.invoke(
        main,
        [
            "--input",
            str(messy_csv_file),
            "--output",
            str(output_p),
            "--config",
            "data-pipeline/config/example.yaml",
            "--report-json",
            str(rep_json),
            "--report-md",
            str(rep_md),
        ],
    )

    assert res.exit_code == 0
    assert "SoilDepth-AI Data Preprocessing Pipeline" in res.output
    assert output_p.is_file()
    assert rep_json.is_file()
    assert rep_md.is_file()


def test_source_adapters_registry() -> None:
    expected_adapters = {
        "generic_tabular",
        "ismn",
        "era5",
        "sentinel",
        "smap",
        "soilgrids",
        "dem",
    }
    registered = set(AdapterRegistry.list_adapters())
    assert expected_adapters.issubset(registered)


def test_source_adapter_schemas_and_adaptations() -> None:
    # 1. ISMN
    ismn = ISMNAdapter()
    assert ismn.is_ground_truth is True
    df_ismn = ismn.adapt(
        pd.DataFrame(
            {
                "station": ["STN_1"],
                "date_time": ["2026-01-01"],
                "lat": [45.0],
                "lon": [10.0],
                "sm": [0.25],
                "depth_from": [10.0],  # cm -> m
                "depth_to": [15.0],
            }
        )
    )
    assert "station_id" in df_ismn.columns
    assert df_ismn["depth_from_m"].iloc[0] == pytest.approx(0.10)

    # 2. ERA5
    era5 = ERA5LandAdapter()
    assert era5.is_ground_truth is False
    df_era5 = era5.adapt(
        pd.DataFrame(
            {
                "time": ["2026-01-01"],
                "lat": [45.0],
                "lon": [10.0],
                "t2m": [293.15],
                "tp": [0.005],  # meters -> mm
            }
        )
    )
    assert df_era5["air_temperature_c"].iloc[0] == pytest.approx(20.0)
    assert df_era5["precipitation_mm"].iloc[0] == pytest.approx(5.0)

    # 3. Sentinel
    sentinel = SentinelAdapter()
    df_s = sentinel.adapt(
        pd.DataFrame(
            {
                "datetime": ["2026-01-01"],
                "lat": [45.0],
                "lon": [10.0],
                "vv": [-12.0],
                "vh": [-18.0],
            }
        )
    )
    assert "s1_vv_db" in df_s.columns
    assert "s1_vh_vv_ratio_db" in df_s.columns
    assert df_s["s1_vh_vv_ratio_db"].iloc[0] == pytest.approx(-6.0)

    # 4. SMAP
    smap = SMAPAdapter()
    assert smap.is_ground_truth is False
    df_smap = smap.adapt(
        pd.DataFrame(
            {
                "datetime": ["2026-01-01"],
                "lat": [45.0],
                "lon": [10.0],
                "surface_sm": [0.24],
            }
        )
    )
    assert "smap_surface_sm_m3m3" in df_smap.columns

    # 5. SoilGrids
    soilgrids = SoilGridsAdapter()
    df_sg = soilgrids.adapt(
        pd.DataFrame(
            {
                "lat": [45.0],
                "lon": [10.0],
                "clay": [25.0],
                "bdod": [135.0],  # cg/cm3 -> 1.35 g/cm3
            }
        )
    )
    assert "clay_pct" in df_sg.columns
    assert df_sg["bulk_density_g_cm3"].iloc[0] == pytest.approx(1.35)

    # 6. DEM
    dem = DEMAdapter()
    df_dem = dem.adapt(
        pd.DataFrame(
            {
                "lat": [45.0],
                "lon": [10.0],
                "elevation": [450.0],
            }
        )
    )
    assert "elevation_m" in df_dem.columns
