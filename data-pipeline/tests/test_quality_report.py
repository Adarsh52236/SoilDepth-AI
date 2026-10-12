"""Unit tests for JSON and Markdown quality report generation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from soildepth_preprocessing.cleaning import CleaningAuditEntry
from soildepth_preprocessing.quality_report import (
    generate_quality_report,
)
from soildepth_preprocessing.schema import (
    ColumnRole,
    ColumnSpec,
    DataType,
    SchemaDefinition,
)
from soildepth_preprocessing.validation import ValidationResult


def test_quality_report_json_and_markdown(tmp_path: Path) -> None:
    schema = SchemaDefinition(
        name="test_schema",
        columns={
            "station_id": ColumnSpec(
                canonical_name="station_id",
                role=ColumnRole.ID,
                data_type=DataType.STRING,
            ),
            "soil_moisture": ColumnSpec(
                canonical_name="soil_moisture",
                role=ColumnRole.TARGET,
                data_type=DataType.FLOAT,
                unit="m3/m3",
            ),
        },
    )

    df_cleaned = pd.DataFrame(
        {
            "station_id": ["S1", "S2"],
            "soil_moisture": [0.25, 0.30],
        }
    )

    schema_val = ValidationResult(is_valid=True)
    model_val = ValidationResult(is_valid=True)
    audit = [
        CleaningAuditEntry(
            stage="deduplication",
            column=None,
            action="drop_duplicates",
            rows_affected=1,
            details="Removed 1 duplicate row",
        )
    ]

    report = generate_quality_report(
        pipeline_name="Test-Pipeline",
        pipeline_version="0.1.0",
        input_source="test.csv",
        output_destination="clean.parquet",
        initial_rows=3,
        final_rows=2,
        dropped_row_reasons={"duplicates": 1},
        cleaned_df=df_cleaned,
        schema=schema,
        schema_validation=schema_val,
        model_validation=model_val,
        audit_trail=audit,
        duration_seconds=0.15,
    )

    # 1. Test JSON Serialization
    json_path = tmp_path / "report.json"
    report.save_json(json_path)
    assert json_path.is_file()

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["pipeline_name"] == "Test-Pipeline"
    assert data["initial_row_count"] == 3
    assert data["final_row_count"] == 2
    assert data["dropped_row_count"] == 1
    assert data["schema_status"] == "PASS"
    assert "station_id" in data["column_profiles"]

    # 2. Test Markdown Generation
    md_path = tmp_path / "report.md"
    report.save_markdown(md_path)
    assert md_path.is_file()

    md_content = md_path.read_text(encoding="utf-8")
    assert "# SoilDepth-AI Preprocessing Quality Report" in md_content
    assert "Initial Row Count | **3**" in md_content
    assert "Final Cleaned Row Count | **2**" in md_content
    assert "🟢 **PASS**" in md_content
    assert "Cleaning & Transformation Audit Trail" in md_content
