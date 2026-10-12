"""End-to-end preprocessing pipeline orchestrator."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from soildepth_preprocessing.adapters import AdapterRegistry, BaseDataAdapter
from soildepth_preprocessing.cleaning import clean_dataset
from soildepth_preprocessing.config import PipelineConfig, load_config_from_yaml
from soildepth_preprocessing.quality_report import QualityReport, generate_quality_report
from soildepth_preprocessing.readers import read_tabular
from soildepth_preprocessing.schema import ColumnRole
from soildepth_preprocessing.transformations import apply_transformations
from soildepth_preprocessing.validation import validate_model_readiness, validate_schema


@dataclass
class PipelineResult:
    """Encapsulates the output dataset, quality report, and execution status."""

    data: pd.DataFrame
    report: QualityReport
    success: bool
    saved_paths: dict[str, str] = field(default_factory=dict)


class PreprocessingPipeline:
    """Auditable, scientifically sound preprocessing pipeline for SoilDepth-AI."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.adapter: BaseDataAdapter = self._init_adapter()

    def _init_adapter(self) -> BaseDataAdapter:
        """Instantiate configured data adapter."""
        adapter_cls = AdapterRegistry.get(self.config.adapter)
        # Pass schema definition if columns are specified, otherwise let adapter use default
        schema = self.config.schema_def if self.config.schema_def.columns else None
        return adapter_cls(schema=schema)

    @classmethod
    def from_config_file(cls, config_path: str | Path) -> PreprocessingPipeline:
        """Initialize pipeline directly from a YAML configuration file."""
        config = load_config_from_yaml(config_path)
        return cls(config)

    def process_dataframe(
        self,
        raw_df: pd.DataFrame,
        source_name: str = "in_memory",
        destination_name: str = "in_memory",
    ) -> tuple[pd.DataFrame, QualityReport]:
        """Execute full cleaning, transformation, and validation lifecycle on a DataFrame."""
        start_time = time.perf_counter()
        initial_row_count = len(raw_df)

        # 1. Adapt raw columns and formats to canonical representation
        adapted_df = self.adapter.adapt(raw_df)
        active_schema = self.adapter.schema

        # 2. Structural schema validation
        schema_validation = validate_schema(adapted_df, active_schema, is_cleaned=False)

        # 3. Data sanitization, deduplication, and outlier handling
        cleaning_result = clean_dataset(
            df=adapted_df,
            schema=active_schema,
            config=self.config.cleaning,
        )

        # Post-cleaning scientific physical bounds check
        post_validation = validate_schema(cleaning_result.data, active_schema, is_cleaned=True)
        for w in post_validation.warnings:
            if w not in schema_validation.warnings:
                schema_validation.warnings.append(w)
        for err in post_validation.errors:
            if err not in schema_validation.errors:
                schema_validation.errors.append(err)

        # 4. Feature engineering and temporal transformations
        ts_cols = [
            c.canonical_name for c in active_schema.get_columns_by_role(ColumnRole.TIMESTAMP)
        ]
        group_cols = [c.canonical_name for c in active_schema.get_columns_by_role(ColumnRole.ID)]

        ts_col = ts_cols[0] if ts_cols and ts_cols[0] in cleaning_result.data.columns else None
        grp_col = (
            group_cols[0] if group_cols and group_cols[0] in cleaning_result.data.columns else None
        )

        transformed_df = apply_transformations(
            df=cleaning_result.data,
            config=self.config.transformations,
            timestamp_col=ts_col,
            group_col=grp_col,
        )

        # 5. Downstream ML readiness & data leakage validation
        model_validation = validate_model_readiness(
            df=transformed_df,
            schema=active_schema,
            config=self.config.readiness,
        )

        duration = time.perf_counter() - start_time

        # 6. Build consolidated Quality Report
        report = generate_quality_report(
            pipeline_name=self.config.pipeline_name,
            pipeline_version=self.config.pipeline_version,
            input_source=source_name,
            output_destination=destination_name,
            initial_rows=initial_row_count,
            final_rows=len(transformed_df),
            dropped_row_reasons=cleaning_result.dropped_row_reasons,
            cleaned_df=transformed_df,
            schema=active_schema,
            schema_validation=schema_validation,
            model_validation=model_validation,
            audit_trail=cleaning_result.audit_trail,
            duration_seconds=duration,
        )

        return transformed_df, report

    def run(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        report_json_path: str | Path | None = None,
        report_md_path: str | Path | None = None,
    ) -> PipelineResult:
        """Ingest raw dataset, execute preprocessing, generate reports and persist outputs."""
        input_p = Path(input_path)
        output_dest = str(output_path) if output_path else "stdout"

        # Ingest raw dataset (preserves raw input file completely unchanged)
        raw_df = read_tabular(
            file_path=input_p,
            config=self.config.ingestion,
            schema=self.adapter.schema,
        )

        cleaned_df, report = self.process_dataframe(
            raw_df=raw_df,
            source_name=str(input_p),
            destination_name=output_dest,
        )

        saved_paths: dict[str, str] = {}

        # Save processed dataset
        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            if out_p.suffix.lower() == ".parquet":
                cleaned_df.to_parquet(out_p, index=False)
            elif out_p.suffix.lower() in (".csv", ".txt"):
                cleaned_df.to_csv(out_p, index=False)
            elif out_p.suffix.lower() == ".tsv":
                cleaned_df.to_csv(out_p, sep="\t", index=False)
            elif out_p.suffix.lower() in (".xlsx", ".xls"):
                cleaned_df.to_excel(out_p, index=False)
            else:
                # Default to parquet if extension not specified or unrecognized
                target = out_p.with_suffix(".parquet") if not out_p.suffix else out_p
                cleaned_df.to_parquet(target, index=False)
                out_p = target

            saved_paths["data"] = str(out_p)

        # Save JSON Quality Report
        if report_json_path:
            json_p = Path(report_json_path)
            report.save_json(json_p)
            saved_paths["report_json"] = str(json_p)

        # Save Markdown Quality Report
        if report_md_path:
            md_p = Path(report_md_path)
            report.save_markdown(md_p)
            saved_paths["report_md"] = str(md_p)

        success = report.schema_status != "FAIL"

        return PipelineResult(
            data=cleaned_df,
            report=report,
            success=success,
            saved_paths=saved_paths,
        )
