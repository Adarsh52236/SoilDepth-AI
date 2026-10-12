# SoilDepth-AI: Preprocessing User Guide

This guide walks you through installing, configuring, running, and extending the data preprocessing pipeline.

---

## 1. Installation

SoilDepth-AI uses [`uv`](https://docs.astral.sh/uv/) for high-performance dependency management.

```bash
# Clone the repository
git checkout feature/preprocessing-pipeline

# Synchronize virtual environment with all runtime and development tools
uv sync --extra dev
```

---

## 2. Command Line Interface (CLI)

The preprocessing pipeline can be invoked using `uv run python -m soildepth_preprocessing.cli` or using the registered `soildepth-preprocess` command.

### Basic Execution

```bash
uv run python -m soildepth_preprocessing.cli \
  --input data/raw/field_station_data.csv \
  --output data/processed/field_station_clean.parquet \
  --config data-pipeline/config/example.yaml
```

### Full Options Flag Matrix

| Flag | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--input` | `-i` | Path to raw input dataset (CSV, TSV, Parquet, JSON, Excel). | *Required* |
| `--output` | `-o` | Destination path for cleaned output dataset. | `data/processed/<name>_cleaned.parquet` |
| `--config` | `-c` | Path to YAML configuration file. | In-memory default config |
| `--adapter`| `-a` | Name of registered adapter to use. | `generic_tabular` |
| `--report-json` | — | Path to save machine-readable JSON quality report. | `data/reports/<name>_quality_report.json` |
| `--report-md` | — | Path to save human-readable Markdown quality report. | `data/reports/<name>_quality_report.md` |

---

## 3. Configuring Column Mappings & Rules

The pipeline uses YAML configuration files to define schema expectations, unit conversions, and cleaning rules.

```yaml
# data-pipeline/config/my_dataset.yaml
pipeline_name: "Station-Cleaning-Pipeline"
adapter: "generic_tabular"

schema:
  columns:
    station_id:
      canonical_name: "station_id"
      source_names: ["station_code", "site_id"]
      role: "id"
      data_type: "string"
      required: true

    timestamp_utc:
      canonical_name: "timestamp_utc"
      source_names: ["date_time", "observed_at"]
      role: "timestamp"
      data_type: "datetime"
      required: true

    soil_moisture:
      canonical_name: "soil_moisture"
      source_names: ["vwc", "sm_pct"]
      role: "target"
      data_type: "float"
      required: true
      min_value: 0.0
      max_value: 1.0
      unit: "%"
      target_unit: "m3/m3" # Pipeline will automatically divide by 100

cleaning:
  deduplicate: true
  dedup_keys: ["station_id", "timestamp_utc"]
  missing_target_policy: "drop_row" # Never impute targets
  outlier_method: "bounds"
  outlier_action: "flag_only"
```

---

## 4. Processing Large Files Safely (Chunked Processing)

For datasets exceeding available RAM (e.g., millions of multi-station records), specify `chunk_size` in the `ingestion` configuration block:

```yaml
ingestion:
  format: "csv"
  chunk_size: 100000 # Read in batches of 100,000 rows
```

In Python code, stream batches using `read_tabular_chunks`:

```python
from soildepth_preprocessing.readers import read_tabular_chunks

for chunk in read_tabular_chunks("large_dataset.csv", chunk_size=50000):
    # Process each chunk iteratively
    pass
```

---

## 5. Interpreting the Quality Report

Each pipeline run generates both a Markdown and a JSON quality report.

1. **Overall Status**:
   - `PASS`: All required columns present, types matched, no critical errors.
   - `WARNING`: Non-fatal issues detected (e.g. outlier flags created, high missingness in an optional feature, unit conversion applied).
   - `FAIL`: Unrecoverable errors (e.g. required column missing, target column 100% null, corrupted file).
2. **Dropped Row Breakdown**: Explicit counts of rows dropped due to duplicates, missing targets, or invalid coordinates.
3. **Column Profile Table**: Shows missing percentages, outlier counts, and detected data types.
4. **Audit Trail**: Step-by-step record of transformations performed on specific columns.

---

## 6. Programmatic Python Execution

```python
from soildepth_preprocessing import PreprocessingPipeline, load_config_from_yaml

# 1. Load configuration
config = load_config_from_yaml("data-pipeline/config/example.yaml")

# 2. Instantiate pipeline
pipeline = PreprocessingPipeline(config)

# 3. Execute
result = pipeline.run(
    input_path="data/raw/sensor_data.csv",
    output_path="data/processed/clean_sensor_data.parquet",
    report_json_path="data/reports/report.json",
    report_md_path="data/reports/report.md",
)

if result.success:
    print(f"Success! Final row count: {result.report.final_row_count}")
else:
    print(f"Failed with errors: {result.report.schema_errors}")
```
