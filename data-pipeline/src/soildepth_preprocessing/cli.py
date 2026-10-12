"""Command Line Interface for SoilDepth-AI preprocessing pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from soildepth_preprocessing.config import PipelineConfig, load_config_from_yaml
from soildepth_preprocessing.pipeline import PreprocessingPipeline


@click.command(name="preprocess")
@click.option(
    "--input",
    "-i",
    "input_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the raw input dataset (CSV, Parquet, JSON, Excel, etc.).",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    required=False,
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Destination path for cleaned output dataset (e.g. data/processed/clean.parquet).",
)
@click.option(
    "--config",
    "-c",
    "config_path",
    required=False,
    default=None,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to pipeline YAML configuration file.",
)
@click.option(
    "--adapter",
    "-a",
    "adapter_name",
    required=False,
    default=None,
    help="Override adapter name (e.g. generic_tabular, ismn, era5, sentinel, smap, soilgrids, dem).",
)
@click.option(
    "--report-json",
    "report_json_path",
    required=False,
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Destination path to export machine-readable JSON quality report.",
)
@click.option(
    "--report-md",
    "report_md_path",
    required=False,
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Destination path to export human-readable Markdown quality report.",
)
def main(
    input_path: Path,
    output_path: Path | None,
    config_path: Path | None,
    adapter_name: str | None,
    report_json_path: Path | None,
    report_md_path: Path | None,
) -> None:
    """Execute the SoilDepth-AI data preprocessing pipeline."""
    click.echo("=" * 60)
    click.echo(" SoilDepth-AI Data Preprocessing Pipeline ")
    click.echo("=" * 60)
    click.echo(f"Input Dataset:  {input_path}")

    # Load configuration
    if config_path:
        click.echo(f"Configuration:  {config_path}")
        config = load_config_from_yaml(config_path)
    else:
        click.echo("Configuration:  Default In-Memory Configuration")
        config = PipelineConfig()

    if adapter_name:
        click.echo(f"Adapter Override: {adapter_name}")
        config.adapter = adapter_name

    # Set default output destinations if not provided
    if output_path is None:
        default_out_dir = Path("data/processed")
        default_out_dir.mkdir(parents=True, exist_ok=True)
        output_path = default_out_dir / f"{input_path.stem}_cleaned.parquet"
    click.echo(f"Output Dataset: {output_path}")

    if report_json_path is None:
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_json_path = reports_dir / f"{input_path.stem}_quality_report.json"

    if report_md_path is None:
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_md_path = reports_dir / f"{input_path.stem}_quality_report.md"

    try:
        pipeline = PreprocessingPipeline(config)
        result = pipeline.run(
            input_path=input_path,
            output_path=output_path,
            report_json_path=report_json_path,
            report_md_path=report_md_path,
        )

        click.echo("-" * 60)
        click.echo(f"Initial Rows:   {result.report.initial_row_count:,}")
        click.echo(f"Cleaned Rows:   {result.report.final_row_count:,}")
        click.echo(f"Dropped Rows:   {result.report.dropped_row_count:,}")
        click.echo(f"Status:         {result.report.schema_status}")
        click.echo(f"Duration:       {result.report.execution_duration_seconds:.2f}s")
        click.echo("-" * 60)
        click.echo(f"Saved Dataset:  {result.saved_paths.get('data')}")
        click.echo(f"Saved Report:   {result.saved_paths.get('report_md')}")
        click.echo(f"Saved JSON:     {result.saved_paths.get('report_json')}")
        click.echo("=" * 60)

        if not result.success:
            click.secho("Pipeline finished with errors. Review reports.", fg="red", err=True)
            sys.exit(1)
        elif result.report.schema_status == "WARNING":
            click.secho("Pipeline succeeded with warnings. Review reports.", fg="yellow")
            sys.exit(0)
        else:
            click.secho("Pipeline completed successfully! Dataset is model-ready.", fg="green")
            sys.exit(0)

    except Exception as err:
        click.secho(f"\n[FATAL ERROR] Preprocessing failed: {err}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
