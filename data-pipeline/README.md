# SoilDepth-AI Data Pipeline (`soildepth_preprocessing`)

The `soildepth_preprocessing` package provides an auditable, schema-driven, and scientifically validated data preprocessing pipeline. It transforms raw or messy environmental and remote-sensing datasets into clean, model-ready datasets for downstream ML training.

---

## 1. Core Modules

| Module | Purpose |
| :--- | :--- |
| [`schema.py`](src/soildepth_preprocessing/schema.py) | Declarative schema models, column role specifications (`ID`, `TIMESTAMP`, `TARGET`, `FEATURE`), and physical constraints. |
| [`config.py`](src/soildepth_preprocessing/config.py) | Pydantic configuration models for ingestion, cleaning, transformation, and model readiness. |
| [`readers.py`](src/soildepth_preprocessing/readers.py) | Multi-format tabular ingestion (CSV, TSV, Parquet, JSON/JSONL, Excel) with auto-detection and chunked streaming. |
| [`cleaning.py`](src/soildepth_preprocessing/cleaning.py) | Deduplication, whitespace stripping, sentinel null normalization, coordinate sanitization, unit conversion, and outlier handling. |
| [`transformations.py`](src/soildepth_preprocessing/transformations.py) | Temporal alignment, past-only lag and rolling features, leakage-aware temporal/group splitting, and learned scaler. |
| [`validation.py`](src/soildepth_preprocessing/validation.py) | Structural schema validation and downstream ML model-readiness verification (preventing target imputation & data leakage). |
| [`quality_report.py`](src/soildepth_preprocessing/quality_report.py) | Machine-readable JSON and human-readable Markdown quality reports with complete audit trails. |
| [`adapters/`](src/soildepth_preprocessing/adapters/) | Source-specific adapters: `generic_tabular`, `ismn`, `era5`, `sentinel`, `smap`, `soilgrids`, `dem`. |
| [`pipeline.py`](src/soildepth_preprocessing/pipeline.py) | Orchestration engine connecting all stages into an end-to-end pipeline. |
| [`cli.py`](src/soildepth_preprocessing/cli.py) | Command-line interface with informative output and status flags. |

---

## 2. CLI Usage

Run preprocessing from the command line:

```bash
uv run python -m soildepth_preprocessing.cli \
  --input data/raw/sample.csv \
  --output data/processed/sample_cleaned.parquet \
  --config data-pipeline/config/example.yaml \
  --report-json data/reports/quality_report.json \
  --report-md data/reports/quality_report.md
```

### CLI Arguments
- `--input` / `-i`: Path to the raw input data file (required).
- `--output` / `-o`: Output file destination (defaults to `data/processed/<name>_cleaned.parquet`).
- `--config` / `-c`: Path to custom YAML configuration.
- `--adapter` / `-a`: Specific adapter override (e.g. `ismn`, `era5`, `generic_tabular`).
- `--report-json`: File path to output the JSON quality report.
- `--report-md`: File path to output the Markdown quality report.

---

## 3. Programmatic Python Usage

```python
from pathlib import Path
from soildepth_preprocessing import PreprocessingPipeline, PipelineConfig

# 1. Initialize from YAML configuration
pipeline = PreprocessingPipeline.from_config_file("data-pipeline/config/example.yaml")

# 2. Execute on raw dataset
result = pipeline.run(
    input_path="data/raw/sensor_data.csv",
    output_path="data/processed/clean_sensor_data.parquet",
    report_json_path="data/reports/report.json",
    report_md_path="data/reports/report.md",
)

# 3. Access cleaned DataFrame and quality metrics
df_cleaned = result.data
print(f"Processed {len(df_cleaned)} rows with status {result.report.schema_status}")
```

---

## 4. Scientific Integrity & Leakage Prevention Rules

1. **Target Imputation is Strictly Forbidden**: The pipeline will never impute missing target labels (`soil_moisture`) using mean, median, interpolation, or ML estimators for supervised datasets. Rows with missing targets are dropped or preserved unlabelled.
2. **Lagged Features Peering Prohibited**: All lag operations strictly require `lag > 0`. Any non-positive lag raises a `ValueError`.
3. **Past-Only Rolling Windows**: Rolling windows use `closed='left'` to ensure observations at time $t$ do not incorporate current or future values.
4. **Chronological Splitting**: Train/Val/Test partitioning uses chronological cutoffs so that the training set strictly precedes validation and test sets in time.
5. **Learned Scaling Separation**: `LearnedStandardScaler` fits parameters solely on training data and transforms validation/test partitions without distribution leakage.

---

## 5. Adding a New Adapter

To add an adapter for a new source:

1. Create a new module in `src/soildepth_preprocessing/adapters/your_source.py`.
2. Subclass `BaseDataAdapter` and decorate with `@AdapterRegistry.register`:
```python
from typing import ClassVar
import pandas as pd
from soildepth_preprocessing.adapters import BaseDataAdapter, AdapterRegistry
from soildepth_preprocessing.schema import SchemaDefinition


@AdapterRegistry.register
class MySourceAdapter(BaseDataAdapter):
    name: ClassVar[str] = "mysource"
    description: ClassVar[str] = "My source description"
    is_ground_truth: ClassVar[bool] = False

    def get_default_schema(self) -> SchemaDefinition:
        return SchemaDefinition(name="mysource_schema", columns={...})

    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        # Map source column names and perform raw source-specific conversions
        return raw_df
```
3. Import the adapter in `src/soildepth_preprocessing/adapters/__init__.py`.
