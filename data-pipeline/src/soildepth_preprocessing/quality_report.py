"""Machine-readable JSON and human-readable Markdown quality report generators."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from soildepth_preprocessing.cleaning import CleaningAuditEntry
from soildepth_preprocessing.schema import SchemaDefinition
from soildepth_preprocessing.validation import ValidationResult


@dataclass
class ColumnProfile:
    """Summary statistics and metadata for a single column."""

    name: str
    role: str
    data_type: str
    total_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    outlier_count: int = 0
    unit: str | None = None


@dataclass
class QualityReport:
    """Consolidated report documenting data transformations, schema checks and ML readiness."""

    pipeline_name: str
    pipeline_version: str
    run_timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    execution_duration_seconds: float = 0.0
    input_source: str = ""
    output_destination: str = ""
    initial_row_count: int = 0
    final_row_count: int = 0
    dropped_row_count: int = 0
    dropped_row_reasons: dict[str, int] = field(default_factory=dict)
    schema_status: str = "PASS"  # "PASS", "WARNING", "FAIL"
    schema_errors: list[str] = field(default_factory=list)
    schema_warnings: list[str] = field(default_factory=list)
    model_readiness_errors: list[str] = field(default_factory=list)
    model_readiness_warnings: list[str] = field(default_factory=list)
    column_profiles: dict[str, ColumnProfile] = field(default_factory=dict)
    audit_trail: list[CleaningAuditEntry] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    input_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        data = asdict(self)
        return data

    def save_json(self, file_path: str | Path) -> None:
        """Write report out to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    def to_markdown(self) -> str:
        """Render a readable GitHub-flavored Markdown report."""
        status_badge = (
            "🟢 **PASS**"
            if self.schema_status == "PASS"
            else ("🟡 **WARNINGS PRESENT**" if self.schema_status == "WARNING" else "🔴 **FAILED**")
        )

        md: list[str] = [
            "# SoilDepth-AI Preprocessing Quality Report",
            "",
            f"- **Pipeline:** {self.pipeline_name} (v{self.pipeline_version})",
            f"- **Execution Timestamp:** {self.run_timestamp}",
            f"- **Duration:** {self.execution_duration_seconds:.2f} seconds",
            f"- **Input:** `{self.input_source}`",
        ]
        if self.input_sha256:
            md.append(f"- **Input SHA-256 Provenance:** `{self.input_sha256}`")
        md.extend(
            [
                f"- **Output:** `{self.output_destination}`",
                f"- **Overall Pipeline Status:** {status_badge}",
                "",
                "---",
                "",
                "## 1. Summary Metrics",
                "",
                "| Metric | Value |",
                "| :--- | :--- |",
                f"| Initial Row Count | **{self.initial_row_count:,}** |",
                f"| Final Cleaned Row Count | **{self.final_row_count:,}** |",
                f"| Total Dropped Rows | **{self.dropped_row_count:,}** |",
                f"| Total Columns Processed | **{len(self.column_profiles)}** |",
                f"| Schema Violations (Errors) | **{len(self.schema_errors)}** |",
                f"| Schema Warnings | **{len(self.schema_warnings)}** |",
                f"| Model Readiness Warnings | **{len(self.model_readiness_warnings)}** |",
                "",
            ]
        )

        # Dropped row breakdown
        if self.dropped_row_reasons:
            md.extend(
                [
                    "### Dropped Row Breakdown",
                    "",
                    "| Reason | Dropped Count |",
                    "| :--- | :--- |",
                ]
            )
            for reason, count in self.dropped_row_reasons.items():
                md.append(f"| `{reason}` | {count:,} |")
            md.append("")

        # Column profile table
        md.extend(
            [
                "## 2. Column Profiles & Data Quality",
                "",
                "| Column | Role | Type | Missing Count | Missing % | Uniques | Outliers | Unit |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
            ]
        )
        for col_name, profile in self.column_profiles.items():
            unit_str = profile.unit or "—"
            md.append(
                f"| `{col_name}` | `{profile.role}` | `{profile.data_type}` | "
                f"{profile.missing_count:,} | {profile.missing_percentage:.1%} | "
                f"{profile.unique_count:,} | {profile.outlier_count:,} | {unit_str} |"
            )
        md.append("")

        # Validation & Readiness Issues
        if self.schema_errors or self.model_readiness_errors:
            md.extend(
                [
                    "## 3. Errors (Action Required)",
                    "",
                ]
            )
            for err in self.schema_errors:
                md.append(f"- 🔴 [Schema Error] {err}")
            for err in self.model_readiness_errors:
                md.append(f"- 🔴 [Model Readiness Error] {err}")
            md.append("")

        if self.schema_warnings or self.model_readiness_warnings:
            md.extend(
                [
                    "## 4. Warnings & Review Items",
                    "",
                ]
            )
            for w in self.schema_warnings:
                md.append(f"- 🟡 [Schema Warning] {w}")
            for w in self.model_readiness_warnings:
                md.append(f"- 🟡 [Model Readiness Warning] {w}")
            md.append("")

        # Audit Trail
        if self.audit_trail:
            md.extend(
                [
                    "## 5. Cleaning & Transformation Audit Trail",
                    "",
                    "| Stage | Column | Action | Rows Affected | Details |",
                    "| :--- | :--- | :--- | :--- | :--- |",
                ]
            )
            for entry in self.audit_trail:
                col_txt = f"`{entry.column}`" if entry.column else "—"
                md.append(
                    f"| `{entry.stage}` | {col_txt} | `{entry.action}` | "
                    f"{entry.rows_affected:,} | {entry.details} |"
                )
            md.append("")

        return "\n".join(md)

    def save_markdown(self, file_path: str | Path) -> None:
        """Write report out to Markdown file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(self.to_markdown())


def generate_quality_report(
    pipeline_name: str,
    pipeline_version: str,
    input_source: str,
    output_destination: str,
    initial_rows: int,
    final_rows: int,
    dropped_row_reasons: dict[str, int],
    cleaned_df: Any,
    schema: SchemaDefinition,
    schema_validation: ValidationResult,
    model_validation: ValidationResult,
    audit_trail: list[CleaningAuditEntry],
    duration_seconds: float,
) -> QualityReport:
    """Build a comprehensive QualityReport from pipeline components."""
    # Build column profiles
    col_profiles: dict[str, ColumnProfile] = {}
    for col in cleaned_df.columns:
        spec = schema.find_column_by_source_name(col)
        role = spec.role.value if spec else "unknown"
        dtype = spec.data_type.value if spec else str(cleaned_df[col].dtype)
        unit = spec.unit if spec else None

        missing_count = int(cleaned_df[col].isna().sum())
        total_count = len(cleaned_df)
        missing_pct = missing_count / total_count if total_count > 0 else 0.0
        unique_cnt = int(cleaned_df[col].nunique(dropna=True))

        outlier_col = f"is_outlier_{col}"
        outlier_cnt = int(cleaned_df[outlier_col].sum()) if outlier_col in cleaned_df.columns else 0

        col_profiles[col] = ColumnProfile(
            name=col,
            role=role,
            data_type=dtype,
            total_count=total_count,
            missing_count=missing_count,
            missing_percentage=missing_pct,
            unique_count=unique_cnt,
            outlier_count=outlier_cnt,
            unit=unit,
        )

    # Determine status
    has_errors = (not schema_validation.is_valid) or (not model_validation.is_valid)
    has_warnings = bool(schema_validation.warnings or model_validation.warnings)
    status = "FAIL" if has_errors else ("WARNING" if has_warnings else "PASS")

    total_dropped = initial_rows - final_rows

    sha256_hash: str | None = None
    try:
        p = Path(input_source)
        if p.is_file():
            import hashlib

            sha256_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception:
        sha256_hash = None

    return QualityReport(
        pipeline_name=pipeline_name,
        pipeline_version=pipeline_version,
        execution_duration_seconds=duration_seconds,
        input_source=input_source,
        output_destination=output_destination,
        initial_row_count=initial_rows,
        final_row_count=final_rows,
        dropped_row_count=total_dropped,
        dropped_row_reasons=dropped_row_reasons,
        schema_status=status,
        schema_errors=schema_validation.errors,
        schema_warnings=schema_validation.warnings,
        model_readiness_errors=model_validation.errors,
        model_readiness_warnings=model_validation.warnings,
        column_profiles=col_profiles,
        audit_trail=audit_trail,
        metrics={**schema_validation.metrics, **model_validation.metrics},
        input_sha256=sha256_hash,
    )
