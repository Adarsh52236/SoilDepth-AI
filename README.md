# SoilDepth-AI

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Architecture: Clean Pipeline](https://img.shields.io/badge/pipeline-reusable%20%26%20auditable-green.svg)]()

> **AI-based root-zone soil-moisture estimation and irrigation decision-support system.**

---

## 1. Project Overview

SoilDepth-AI is designed to accurately estimate root-zone soil moisture ($0-100\text{ cm}$) by fusing multiple geospatial and remote sensing inputs (ISMN in-situ ground sensors, ERA5-Land atmospheric reanalysis, Sentinel-1/2 satellite imagery, SMAP radiometry, SoilGrids physical properties, and Digital Elevation Models).

### Current Development Phase: Data Preprocessing Pipeline First
To guarantee scientific reliability and prevent downstream model failures, development begins with a robust, production-grade **data preprocessing and quality assurance pipeline**. Downstream modules (`services/`, `models/`, `dashboard/`) are intentionally stubbed and will be developed once data ingestion and validation are fully established.

---

## 2. Repository Structure

```text
SoilDepth-AI/
├── README.md
├── .gitignore
├── .editorconfig
├── pyproject.toml
├── uv.lock
├── .pre-commit-config.yaml
├── docs/
│   ├── architecture.md
│   ├── preprocessing-guide.md
│   └── data-quality.md
├── data-pipeline/
│   ├── README.md
│   ├── config/
│   │   └── example.yaml
│   ├── src/
│   │   └── soildepth_preprocessing/
│   │       ├── __init__.py
│   │       ├── cli.py
│   │       ├── config.py
│   │       ├── readers.py
│   │       ├── schema.py
│   │       ├── validation.py
│   │       ├── cleaning.py
│   │       ├── transformations.py
│   │       ├── quality_report.py
│   │       ├── pipeline.py
│   │       └── adapters/
│   │           ├── __init__.py
│   │           ├── generic_tabular.py
│   │           ├── ismn.py
│   │           ├── era5.py
│   │           ├── sentinel.py
│   │           ├── smap.py
│   │           ├── soilgrids.py
│   │           └── dem.py
│   └── tests/
│       ├── test_readers.py
│       ├── test_cleaning.py
│       ├── test_validation.py
│       ├── test_transformations.py
│       ├── test_quality_report.py
│       └── test_pipeline.py
├── services/               # Future microservices (empty / stubbed)
├── models/                 # Future ML model artifacts (empty / stubbed)
├── dashboard/              # Future user interface (empty / stubbed)
└── data/                   # Data directory (raw, processed, reports)
```

---

## 3. Quickstart

### Prerequisites
- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

Clone the repository and install all dependencies in a virtual environment:

```bash
# Install dependencies including dev tools
uv sync --extra dev
```

### Running the Preprocessing CLI

```bash
# Execute preprocessing on a dataset
uv run python -m soildepth_preprocessing.cli \
  --input data/raw/sample_soil_moisture.csv \
  --output data/processed/cleaned_soil_moisture.parquet \
  --config data-pipeline/config/example.yaml \
  --report-json data/reports/quality_report.json \
  --report-md data/reports/quality_report.md
```

Or using the installed console script:

```bash
uv run soildepth-preprocess \
  --input data/raw/sample_soil_moisture.csv \
  --output data/processed/cleaned_soil_moisture.parquet \
  --config data-pipeline/config/example.yaml
```

---

## 4. Documentation Links

- [System Architecture](docs/architecture.md)
- [Preprocessing Pipeline Guide](docs/preprocessing-guide.md)
- [Data Quality & Integrity Policy](docs/data-quality.md)
- [Data Pipeline Package Readme](data-pipeline/README.md)

---

## 5. Testing & Code Quality

Run tests:
```bash
uv run pytest
```

Run linter & formatting check:
```bash
uv run ruff check .
uv run ruff format --check .
```
