"""Data ingestion and multi-format tabular reader module."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

from soildepth_preprocessing.config import IngestionConfig
from soildepth_preprocessing.schema import DataType, SchemaDefinition


class IngestionError(Exception):
    """Base exception for data ingestion failures."""


class UnsupportedFormatError(IngestionError):
    """Raised when an unrecognized or unsupported file format is encountered."""


class CorruptFileError(IngestionError):
    """Raised when a file cannot be parsed or contains corrupted contents."""


class FileNotFoundCustomError(IngestionError):
    """Raised when the specified file path does not exist."""


SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".txt": "csv",
    ".parquet": "parquet",
    ".pq": "parquet",
    ".json": "json",
    ".jsonl": "jsonl",
    ".xlsx": "excel",
    ".xls": "excel",
}


def detect_file_format(file_path: Path, config_format: str = "auto") -> str:
    """Detect file format using configuration override, extension, or content sniffing."""
    if config_format != "auto":
        fmt = config_format.lower()
        valid = {"csv", "tsv", "parquet", "json", "jsonl", "excel"}
        if fmt not in valid:
            raise UnsupportedFormatError(
                f"Requested format '{config_format}' is not supported. Supported: {sorted(valid)}"
            )
        return fmt

    suffix = file_path.suffix.lower()
    if suffix in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[suffix]

    # Content-based magic bytes / sniffing fallback
    try:
        with file_path.open("rb") as f:
            header = f.read(16)
            if header.startswith(b"PAR1"):
                return "parquet"
            if header.startswith(b"PK\x03\x04"):
                return "excel"
            if header.strip().startswith((b"{", b"[")):
                return "json"
    except OSError as err:
        raise CorruptFileError(f"Failed to inspect file contents for '{file_path}': {err}") from err

    raise UnsupportedFormatError(
        f"Unable to determine format for file: '{file_path}'. "
        f"Supported extensions: {sorted(SUPPORTED_EXTENSIONS.keys())}. "
        "Please provide explicit 'format' in ingestion config."
    )


def map_schema_dtypes_to_pandas(schema: SchemaDefinition | None) -> dict[str, Any] | None:
    """Translate schema data types to pandas-compatible dtypes for ingestion."""
    if not schema or not schema.columns:
        return None

    dtype_map: dict[str, Any] = {}
    type_conversion = {
        DataType.FLOAT: "float64",
        DataType.INT: "Int64",
        DataType.STRING: "string",
        DataType.BOOLEAN: "boolean",
        DataType.CATEGORY: "category",
    }

    for col_name, spec in schema.columns.items():
        if spec.data_type in type_conversion:
            dtype_map[col_name] = type_conversion[spec.data_type]
            # Also register raw source aliases so they are parsed with correct types before renaming
            for alias in spec.source_names:
                dtype_map[alias] = type_conversion[spec.data_type]

    return dtype_map if dtype_map else None


def read_tabular(
    file_path: str | Path,
    config: IngestionConfig | None = None,
    schema: SchemaDefinition | None = None,
) -> pd.DataFrame:
    """Ingest a complete tabular dataset into a pandas DataFrame."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundCustomError(f"Target data file not found: {path}")

    config = config or IngestionConfig()
    detected_format = detect_file_format(path, config.format)

    try:
        if detected_format in ("csv", "tsv"):
            sep = config.delimiter or ("\t" if detected_format == "tsv" else ",")
            # Note: We do not pass dtype_map directly into read_csv if sentinel nulls might exist,
            # so malformed types can be cleaned rather than failing read immediately.
            return pd.read_csv(
                path,
                sep=sep,
                encoding=config.encoding,
                low_memory=False,
            )

        if detected_format == "parquet":
            return pd.read_parquet(path)

        if detected_format == "json":
            return pd.read_json(path, encoding=config.encoding)

        if detected_format == "jsonl":
            return pd.read_json(path, lines=True, encoding=config.encoding)

        if detected_format == "excel":
            return pd.read_excel(
                path,
                sheet_name=config.sheet_name if config.sheet_name is not None else 0,
            )

        raise UnsupportedFormatError(f"Unsupported format: {detected_format}")

    except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as err:
        raise CorruptFileError(
            f"Failed to parse file '{path}' as {detected_format}: {err}"
        ) from err
    except Exception as err:
        raise IngestionError(f"Unexpected error ingesting '{path}': {err}") from err


def read_tabular_chunks(
    file_path: str | Path,
    chunk_size: int,
    config: IngestionConfig | None = None,
    schema: SchemaDefinition | None = None,
) -> Generator[pd.DataFrame, None, None]:
    """Stream large datasets in chunks to prevent memory exhaustion."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundCustomError(f"Target data file not found: {path}")

    config = config or IngestionConfig()
    detected_format = detect_file_format(path, config.format)

    try:
        if detected_format in ("csv", "tsv"):
            sep = config.delimiter or ("\t" if detected_format == "tsv" else ",")
            chunk_iterator = pd.read_csv(
                path,
                sep=sep,
                encoding=config.encoding,
                chunksize=chunk_size,
                low_memory=False,
            )
            for chunk in chunk_iterator:
                yield chunk

        elif detected_format == "parquet":
            parquet_file = pq.ParquetFile(str(path))
            for batch in parquet_file.iter_batches(batch_size=chunk_size):
                yield batch.to_pandas()

        elif detected_format == "jsonl":
            chunk_iterator = pd.read_json(
                path,
                lines=True,
                chunksize=chunk_size,
                encoding=config.encoding,
            )
            for chunk in chunk_iterator:
                yield chunk

        else:
            # Fallback for formats that do not natively support chunked streaming (Excel, single JSON)
            df = read_tabular(path, config, schema)
            num_rows = len(df)
            for start in range(0, num_rows, chunk_size):
                yield df.iloc[start : start + chunk_size].copy()

    except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as err:
        raise CorruptFileError(f"Corrupt chunk stream for '{path}': {err}") from err
    except Exception as err:
        raise IngestionError(f"Unexpected error streaming '{path}': {err}") from err
