"""
SoilDepth-AI — Unit Tests for Maharashtra Ground-Truth Adapter
Author: Senior Geospatial Data Engineer & ML Pipeline Developer, SoilDepth-AI
Purpose: Tests schema normalization, physical bounds validation, synthetic data rejection,
         incompatible depth detection, file ingestion (CSV/TSV), temporal alignment,
         and coverage summary generation.
"""

import json
from pathlib import Path
import tempfile
import pandas as pd
import pytest

from services.data_acquisition.maharashtra.ground_truth_adapter import (
    MaharashtraGroundTruthAdapter,
    GroundTruthValidationError,
    NORMALIZED_COLUMNS,
    ALLOWED_QUALITY_FLAGS,
)


@pytest.fixture
def adapter():
    return MaharashtraGroundTruthAdapter()


def test_adapter_initialization(adapter):
    """Verifies that the adapter loads station metadata and depth compatibility matrix."""
    assert len(adapter.known_stations) >= 16
    assert "IITM-PUNE-COSMOS" in adapter.known_stations
    assert "MPKV-RAHURI-CAAST" in adapter.known_stations
    assert len(adapter.depth_matrix) >= 16


def test_normalize_valid_dataframe(adapter):
    """Verifies that a valid arbitrary telemetry dataframe is correctly normalized."""
    df_raw = pd.DataFrame({
        "obs_time": ["2020-06-01 10:00:00", "2020-06-01 11:00:00"],
        "depth": [10.0, 10.0],
        "moisture": [0.245, 0.260],
        "flag": ["GOOD", "GOOD"],
    })
    mapping = {
        "timestamp": "obs_time",
        "sensor_depth_cm": "depth",
        "soil_moisture_vwc": "moisture",
        "quality_flag": "flag",
    }
    df_norm = adapter.normalize(
        df=df_raw,
        column_mapping=mapping,
        source_dataset="TEST_SOURCE",
        default_station_id="MPKV-RAHURI-CAAST",
        input_vwc_unit="m3/m3",
        input_timezone="UTC",
    )

    assert list(df_norm.columns) == NORMALIZED_COLUMNS
    assert len(df_norm) == 2
    assert (df_norm["station_id"] == "MPKV-RAHURI-CAAST").all()
    assert (df_norm["measurement_unit"] == "m3/m3").all()
    assert df_norm["soil_moisture_vwc"].iloc[0] == 0.245


def test_normalize_vwc_percentage_conversion(adapter):
    """Verifies that VWC expressed as percentage is correctly converted to m3/m3."""
    df_raw = pd.DataFrame({
        "timestamp": ["2020-06-01T00:00:00Z"],
        "sensor_depth_cm": [10.0],
        "vwc_pct": [32.5],
    })
    mapping = {
        "timestamp": "timestamp",
        "sensor_depth_cm": "sensor_depth_cm",
        "soil_moisture_vwc": "vwc_pct",
    }
    df_norm = adapter.normalize(
        df=df_raw,
        column_mapping=mapping,
        source_dataset="TEST_PCT",
        default_station_id="MPKV-RAHURI-CAAST",
        input_vwc_unit="%",
    )
    assert abs(df_norm["soil_moisture_vwc"].iloc[0] - 0.325) < 1e-4


def test_normalize_ist_timezone_conversion(adapter):
    """Verifies that IST timestamps are converted to ISO 8601 UTC."""
    df_raw = pd.DataFrame({
        "time_ist": ["2020-06-01 05:30:00"],
        "depth": [10.0],
        "vwc": [0.22],
    })
    mapping = {
        "timestamp": "time_ist",
        "sensor_depth_cm": "depth",
        "soil_moisture_vwc": "vwc",
    }
    df_norm = adapter.normalize(
        df=df_raw,
        column_mapping=mapping,
        source_dataset="TEST_IST",
        default_station_id="MPKV-RAHURI-CAAST",
        input_timezone="Asia/Kolkata",
    )
    # 05:30 IST is 00:00 UTC
    assert df_norm["timestamp"].iloc[0] == "2020-06-01T00:00:00Z"


def test_normalize_rejects_synthetic_column_markers(adapter):
    """Verifies that presence of synthetic/interpolated columns triggers GroundTruthValidationError."""
    df_raw = pd.DataFrame({
        "timestamp": ["2020-06-01T00:00:00Z"],
        "depth": [10.0],
        "vwc": [0.22],
        "is_interpolated": [True],
    })
    mapping = {
        "timestamp": "timestamp",
        "sensor_depth_cm": "depth",
        "soil_moisture_vwc": "vwc",
    }
    with pytest.raises(GroundTruthValidationError, match="Interpolated sensor observations detected"):
        adapter.normalize(
            df=df_raw,
            column_mapping=mapping,
            source_dataset="TEST_INTERP",
            default_station_id="MPKV-RAHURI-CAAST",
        )


def test_normalize_rejects_synthetic_quality_flags(adapter):
    """Verifies that synthetic quality flags trigger GroundTruthValidationError."""
    df_raw = pd.DataFrame({
        "timestamp": ["2020-06-01T00:00:00Z"],
        "depth": [10.0],
        "vwc": [0.22],
        "qflag": ["SYNTHETIC"],
    })
    mapping = {
        "timestamp": "timestamp",
        "sensor_depth_cm": "depth",
        "soil_moisture_vwc": "vwc",
        "quality_flag": "qflag",
    }
    with pytest.raises(GroundTruthValidationError, match="Synthetic or interpolated observation flag detected"):
        adapter.normalize(
            df=df_raw,
            column_mapping=mapping,
            source_dataset="TEST_SYNTH",
            default_station_id="MPKV-RAHURI-CAAST",
        )


def test_validate_catches_out_of_bounds_vwc(adapter):
    """Verifies that VWC outside [0.00, 0.65] is caught by validation."""
    df_bad = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST"],
        "timestamp": ["2020-06-01T00:00:00Z"],
        "latitude": [19.3333],
        "longitude": [74.6500],
        "sensor_depth_cm": [10.0],
        "soil_moisture_vwc": [0.85],  # Out of bounds (> 0.65)
        "measurement_unit": ["m3/m3"],
        "quality_flag": ["GOOD"],
        "source_dataset": ["TEST"],
        "source_record_id": ["REC_01"],
    })
    report = adapter.validate(df_bad)
    assert not report["is_valid"]
    assert report["out_of_bounds_count"] == 1


def test_validate_catches_invalid_sensor_depth(adapter):
    """Verifies that non-physical depths (<= 0 or > 200 cm) are flagged."""
    df_bad = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST"],
        "timestamp": ["2020-06-01T00:00:00Z"],
        "latitude": [19.3333],
        "longitude": [74.6500],
        "sensor_depth_cm": [-5.0],  # Invalid negative depth
        "soil_moisture_vwc": [0.25],
        "measurement_unit": ["m3/m3"],
        "quality_flag": ["GOOD"],
        "source_dataset": ["TEST"],
        "source_record_id": ["REC_01"],
    })
    report = adapter.validate(df_bad)
    assert not report["is_valid"]
    assert report["invalid_depth_count"] == 1


def test_validate_catches_unmatched_station_depth(adapter):
    """Verifies that depths unaligned with documented station sensor depths are flagged."""
    # MPKV Rahuri has sensors at 10, 20, 30, 40, 50, 60 cm. 95 cm is undocumented.
    df_unmatched = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST"],
        "timestamp": ["2020-06-01T00:00:00Z"],
        "latitude": [19.3333],
        "longitude": [74.6500],
        "sensor_depth_cm": [95.0],
        "soil_moisture_vwc": [0.25],
        "measurement_unit": ["m3/m3"],
        "quality_flag": ["GOOD"],
        "source_dataset": ["TEST"],
        "source_record_id": ["REC_01"],
    })
    report = adapter.validate(df_unmatched)
    assert not report["is_valid"]
    assert any("not matching documented sensor depths" in iss for iss in report["issues"])


def test_validate_strict_mode_raises(adapter):
    """Verifies that strict=True raises GroundTruthValidationError on issues."""
    df_bad = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST"],
        "timestamp": ["2020-06-01T00:00:00Z"],
        "latitude": [19.3932],
        "longitude": [74.6525],
        "sensor_depth_cm": [10.0],
        "soil_moisture_vwc": [0.99],
        "measurement_unit": ["m3/m3"],
        "quality_flag": ["GOOD"],
        "source_dataset": ["TEST"],
        "source_record_id": ["REC_01"],
    })
    with pytest.raises(GroundTruthValidationError, match="validation failed with 1 issues"):
        adapter.validate(df_bad, strict=True)


def test_ingest_file_csv(adapter):
    """Verifies end-to-end ingestion from a real CSV file."""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False, newline="") as f:
        f.write("date_time,depth_cm,vwc_val\n")
        f.write("2021-03-15 12:00:00,10.0,0.225\n")
        f.write("2021-03-16 12:00:00,10.0,0.218\n")
        temp_csv = Path(f.name)

    try:
        mapping = {
            "timestamp": "date_time",
            "sensor_depth_cm": "depth_cm",
            "soil_moisture_vwc": "vwc_val",
        }
        df_ingested = adapter.ingest_file(
            file_path=temp_csv,
            column_mapping=mapping,
            source_dataset="CSV_TEST",
            default_station_id="MPKV-RAHURI-CAAST",
            strict=True,
        )
        assert len(df_ingested) == 2
        assert df_ingested["soil_moisture_vwc"].iloc[0] == 0.225
    finally:
        if temp_csv.exists():
            temp_csv.unlink()


def test_ingest_file_tsv(adapter):
    """Verifies end-to-end ingestion from a TSV file."""
    with tempfile.NamedTemporaryFile(suffix=".tsv", mode="w", delete=False, newline="") as f:
        f.write("date_time\tdepth_cm\tvwc_val\n")
        f.write("2021-03-15 12:00:00\t10.0\t0.225\n")
        f.write("2021-03-16 12:00:00\t10.0\t0.218\n")
        temp_tsv = Path(f.name)

    try:
        mapping = {
            "timestamp": "date_time",
            "sensor_depth_cm": "depth_cm",
            "soil_moisture_vwc": "vwc_val",
        }
        df_ingested = adapter.ingest_file(
            file_path=temp_tsv,
            column_mapping=mapping,
            source_dataset="TSV_TEST",
            default_station_id="MPKV-RAHURI-CAAST",
            strict=True,
        )
        assert len(df_ingested) == 2
        assert df_ingested["soil_moisture_vwc"].iloc[0] == 0.225
    finally:
        if temp_tsv.exists():
            temp_tsv.unlink()


def test_ingest_file_nonexistent(adapter):
    """Verifies that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        adapter.ingest_file("nonexistent_ground_truth.csv", {}, "SOURCE")


def test_ingest_file_unsupported_extension(adapter):
    """Verifies that unsupported file extension raises ValueError."""
    with tempfile.NamedTemporaryFile(suffix=".h5", mode="wb", delete=False) as f:
        f.write(b"dummy")
        temp_h5 = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Unsupported file format"):
            adapter.ingest_file(temp_h5, {}, "SOURCE")
    finally:
        if temp_h5.exists():
            temp_h5.unlink()


def test_ingest_file_parquet(adapter):
    """Verifies that Parquet files are ingested and normalized properly."""
    df_raw = pd.DataFrame({
        "timestamp": ["2020-07-01T00:00:00Z", "2020-07-02T00:00:00Z"],
        "depth": [10.0, 10.0],
        "vwc": [0.24, 0.28],
    })
    with tempfile.NamedTemporaryFile(suffix=".parquet", mode="wb", delete=False) as f:
        temp_pq = Path(f.name)
    df_raw.to_parquet(temp_pq)

    mapping = {
        "timestamp": "timestamp",
        "sensor_depth_cm": "depth",
        "soil_moisture_vwc": "vwc",
    }
    try:
        df_ingested = adapter.ingest_file(
            file_path=temp_pq,
            column_mapping=mapping,
            source_dataset="PARQUET_TEST",
            default_station_id="MPKV-RAHURI-CAAST",
        )
        assert len(df_ingested) == 2
        assert list(df_ingested.columns) == NORMALIZED_COLUMNS
        assert df_ingested["soil_moisture_vwc"].iloc[0] == 0.24
    finally:
        if temp_pq.exists():
            temp_pq.unlink()


def test_ingest_file_json(adapter):
    """Verifies that JSON files (standard and lines) are ingested properly."""
    df_raw = pd.DataFrame({
        "timestamp": ["2020-07-01T00:00:00Z", "2020-07-02T00:00:00Z"],
        "depth": [10.0, 10.0],
        "vwc": [0.31, 0.33],
    })
    mapping = {
        "timestamp": "timestamp",
        "sensor_depth_cm": "depth",
        "soil_moisture_vwc": "vwc",
    }

    # Standard JSON
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        temp_json = Path(f.name)
    df_raw.to_json(temp_json, orient="records")

    try:
        df_ingested = adapter.ingest_file(
            file_path=temp_json,
            column_mapping=mapping,
            source_dataset="JSON_TEST",
            default_station_id="MPKV-RAHURI-CAAST",
        )
        assert len(df_ingested) == 2
        assert df_ingested["soil_moisture_vwc"].iloc[1] == 0.33
    finally:
        if temp_json.exists():
            temp_json.unlink()


def test_validate_temporal_alignment(adapter):
    """Verifies temporal alignment calculations against the 2017-2023 environmental timeline."""
    df_aligned = pd.DataFrame({
        "timestamp": [
            "2018-05-01T00:00:00Z",
            "2019-06-01T00:00:00Z",
            "2022-07-01T00:00:00Z",
        ]
    })
    align_rep = adapter.validate_temporal_alignment(df_aligned)
    assert align_rep["is_aligned"]
    assert align_rep["coverage_pct"] == 100.0
    assert align_rep["records_in_window"] == 3

    # Dataset with data in 2010 (outside window)
    df_misaligned = pd.DataFrame({
        "timestamp": [
            "2010-05-01T00:00:00Z",
            "2011-06-01T00:00:00Z",
        ]
    })
    align_rep2 = adapter.validate_temporal_alignment(df_misaligned)
    assert not align_rep2["is_aligned"]
    assert align_rep2["records_in_window"] == 0
    assert align_rep2["records_pre_window"] == 2


def test_generate_coverage_summary(adapter):
    """Verifies data coverage summary and the 180-observation training sufficiency check."""
    # 20 observations -> insufficient (< 180)
    dates_20 = pd.date_range("2020-01-01", periods=20, freq="D")
    df_20 = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST"] * 20,
        "timestamp": [d.strftime("%Y-%m-%dT00:00:00Z") for d in dates_20],
        "sensor_depth_cm": [10.0] * 20,
        "soil_moisture_vwc": [0.25] * 20,
        "quality_flag": ["GOOD"] * 20,
    })
    cov_rep = adapter.generate_coverage_summary(df_20, min_obs_for_training=180)
    stat = cov_rep["stations"]["MPKV-RAHURI-CAAST"][10.0]
    assert stat["daily_observation_count"] == 20
    assert not stat["sufficient_for_training"]
    assert "INSUFFICIENT" in stat["verdict"]

    # 200 observations -> sufficient (>= 180)
    dates_200 = pd.date_range("2020-01-01", periods=200, freq="D")
    df_200 = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST"] * 200,
        "timestamp": [d.strftime("%Y-%m-%dT00:00:00Z") for d in dates_200],
        "sensor_depth_cm": [10.0] * 200,
        "soil_moisture_vwc": [0.25] * 200,
        "quality_flag": ["GOOD"] * 200,
    })
    cov_rep2 = adapter.generate_coverage_summary(df_200, min_obs_for_training=180)
    stat2 = cov_rep2["stations"]["MPKV-RAHURI-CAAST"][10.0]
    assert stat2["daily_observation_count"] == 200
    assert stat2["sufficient_for_training"]
    assert stat2["verdict"] == "SUFFICIENT"


def test_generate_receipt_reports(adapter, tmp_path):
    """Verifies generation of complete receipt package: JSON, MD, CSVs, manifest."""
    # Create sample ground truth dataframe
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    df_norm = pd.DataFrame({
        "station_id": ["MPKV-RAHURI-CAAST"] * 10,
        "timestamp": [d.strftime("%Y-%m-%dT00:00:00Z") for d in dates],
        "latitude": [19.3333] * 10,
        "longitude": [74.65] * 10,
        "sensor_depth_cm": [10.0] * 10,
        "soil_moisture_vwc": [0.25] * 10,
        "measurement_unit": ["m3/m3"] * 10,
        "quality_flag": ["GOOD"] * 10,
        "source_dataset": ["TEST_DATASET"] * 10,
        "source_record_id": [f"REC_{i}" for i in range(10)],
    })

    # Create dummy source file
    src_file = tmp_path / "raw_telemetry.csv"
    src_file.write_text("raw,test,data\n1,2,3\n", encoding="utf-8")

    out_dir = tmp_path / "receipt_output"
    rep = adapter.generate_receipt_reports(
        df_norm=df_norm,
        output_dir=out_dir,
        source_files=[src_file],
        rejected_records=[{"timestamp": "2020-01-01", "rejection_reason": "out of bounds"}],
    )

    assert (out_dir / "dataset_receipt_report.json").exists()
    assert (out_dir / "dataset_receipt_report.md").exists()
    assert (out_dir / "station_depth_coverage.csv").exists()
    assert (out_dir / "rejected_records.csv").exists()
    assert (out_dir / "data_hash_manifest.json").exists()

    # Check manifest content
    with open(out_dir / "data_hash_manifest.json", "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    assert manifest_data["total_files"] == 1
    assert manifest_data["files"][0]["filename"] == "raw_telemetry.csv"
    assert len(manifest_data["files"][0]["sha256"]) == 64

    # Check coverage csv
    df_cov = pd.read_csv(out_dir / "station_depth_coverage.csv")
    assert len(df_cov) == 1
    assert df_cov["station_id"].iloc[0] == "MPKV-RAHURI-CAAST"
