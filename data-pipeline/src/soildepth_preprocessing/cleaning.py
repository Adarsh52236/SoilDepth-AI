"""Data sanitization, deduplication, outlier handling, and unit normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from soildepth_preprocessing.config import CleaningConfig
from soildepth_preprocessing.schema import ColumnRole, DataType, SchemaDefinition


@dataclass
class CleaningAuditEntry:
    """Audit record capturing an individual transformation or sanitization step."""

    stage: str
    column: str | None
    action: str
    rows_affected: int
    details: str


@dataclass
class CleaningResult:
    """Container holding cleaned DataFrame and associated audit trail."""

    data: pd.DataFrame
    audit_trail: list[CleaningAuditEntry]
    initial_rows: int
    final_rows: int
    dropped_row_reasons: dict[str, int]


def strip_text_and_replace_sentinels(
    df: pd.DataFrame, config: CleaningConfig
) -> tuple[pd.DataFrame, list[CleaningAuditEntry]]:
    """Clean whitespace-only strings and normalize sentinel missing values to NaN."""
    audit_entries: list[CleaningAuditEntry] = []
    df = df.copy()

    # 1. Strip whitespace on string/object columns
    if config.strip_whitespace:
        text_cols = df.select_dtypes(include=["object", "string"]).columns
        for col in text_cols:
            # Replace whitespace-only strings with empty string
            is_str_mask = df[col].apply(lambda x: isinstance(x, str))
            if is_str_mask.any():
                df.loc[is_str_mask, col] = df.loc[is_str_mask, col].str.strip()

    # 2. Replace sentinel nulls
    sentinels = set(config.sentinel_null_values)
    # Also add string representations of numbers in sentinels
    for s in config.sentinel_null_values:
        sentinels.add(str(s))

    total_sentinel_replaced = 0
    for col in df.columns:
        # Check matching sentinel values
        mask = df[col].isin(sentinels)
        # Also check whitespace-only or empty strings
        if df[col].dtype == object or str(df[col].dtype) == "string":
            mask = mask | (df[col] == "")

        count = int(mask.sum())
        if count > 0:
            df.loc[mask, col] = np.nan
            total_sentinel_replaced += count
            audit_entries.append(
                CleaningAuditEntry(
                    stage="sentinel_replacement",
                    column=col,
                    action="replace_with_nan",
                    rows_affected=count,
                    details=f"Normalized {count} sentinel/empty values to NaN",
                )
            )

    return df, audit_entries


def deduplicate_dataframe(
    df: pd.DataFrame, config: CleaningConfig
) -> tuple[pd.DataFrame, list[CleaningAuditEntry], int]:
    """Execute exact and key-based deduplication per configuration."""
    audit_entries: list[CleaningAuditEntry] = []
    if not config.deduplicate or df.empty:
        return df, audit_entries, 0

    initial_len = len(df)
    df = df.copy()

    # Determine subset for deduplication
    subset = None
    if config.dedup_keys:
        # Only use keys that exist in current DataFrame
        existing_keys = [k for k in config.dedup_keys if k in df.columns]
        if existing_keys:
            subset = existing_keys

    keep_arg: Any = "first"
    if config.dedup_keep == "drop_all":
        keep_arg = False
    elif config.dedup_keep == "last":
        keep_arg = "last"

    dups_mask = df.duplicated(subset=subset, keep=keep_arg)
    dup_count = int(dups_mask.sum())

    if dup_count > 0:
        df = df[~dups_mask].reset_index(drop=True)
        keys_desc = f"keys={subset}" if subset else "all columns"
        audit_entries.append(
            CleaningAuditEntry(
                stage="deduplication",
                column=None,
                action=f"drop_duplicates(keep={config.dedup_keep})",
                rows_affected=dup_count,
                details=f"Removed {dup_count} duplicate records based on {keys_desc}",
            )
        )

    return df, audit_entries, initial_len - len(df)


def validate_and_clean_coordinates(
    df: pd.DataFrame,
    schema: SchemaDefinition,
    config: CleaningConfig,
) -> tuple[pd.DataFrame, list[CleaningAuditEntry], int]:
    """Validate physical latitude and longitude coordinates."""
    audit_entries: list[CleaningAuditEntry] = []
    if not config.validate_coordinates or df.empty:
        return df, audit_entries, 0

    lat_cols = [
        c.canonical_name
        for c in schema.get_columns_by_role(ColumnRole.LATITUDE)
        if c.canonical_name in df.columns
    ]
    lon_cols = [
        c.canonical_name
        for c in schema.get_columns_by_role(ColumnRole.LONGITUDE)
        if c.canonical_name in df.columns
    ]

    invalid_mask = pd.Series(False, index=df.index)

    for col in lat_cols:
        col_numeric = pd.to_numeric(df[col], errors="coerce")
        col_invalid = (col_numeric < -90.0) | (col_numeric > 90.0)
        invalid_count = int(col_invalid.sum())
        if invalid_count > 0:
            invalid_mask |= col_invalid
            audit_entries.append(
                CleaningAuditEntry(
                    stage="coordinate_validation",
                    column=col,
                    action=config.invalid_coordinate_action,
                    rows_affected=invalid_count,
                    details=f"Detected {invalid_count} latitude values outside [-90, +90]",
                )
            )

    for col in lon_cols:
        col_numeric = pd.to_numeric(df[col], errors="coerce")
        col_invalid = (col_numeric < -180.0) | (col_numeric > 180.0)
        invalid_count = int(col_invalid.sum())
        if invalid_count > 0:
            invalid_mask |= col_invalid
            audit_entries.append(
                CleaningAuditEntry(
                    stage="coordinate_validation",
                    column=col,
                    action=config.invalid_coordinate_action,
                    rows_affected=invalid_count,
                    details=f"Detected {invalid_count} longitude values outside [-180, +180]",
                )
            )

    total_invalid = int(invalid_mask.sum())
    dropped_count = 0
    if total_invalid > 0:
        if config.invalid_coordinate_action == "drop_row":
            df = df[~invalid_mask].reset_index(drop=True)
            dropped_count = total_invalid
        elif config.invalid_coordinate_action == "nullify":
            for col in lat_cols + lon_cols:
                df.loc[invalid_mask, col] = np.nan

    return df, audit_entries, dropped_count


def convert_units(
    df: pd.DataFrame,
    schema: SchemaDefinition,
) -> tuple[pd.DataFrame, list[CleaningAuditEntry]]:
    """Convert columns between units according to schema specifications."""
    audit_entries: list[CleaningAuditEntry] = []
    df = df.copy()

    for col_name, spec in schema.columns.items():
        if col_name not in df.columns or not spec.unit or not spec.target_unit:
            continue
        if spec.unit.lower() == spec.target_unit.lower():
            continue

        src_u = spec.unit.lower()
        dst_u = spec.target_unit.lower()
        series_num = pd.to_numeric(df[col_name], errors="coerce")

        converted = False
        action_note = ""

        # Soil moisture percentage to volumetric water content (m3/m3)
        if src_u in ("%", "percentage") and dst_u in ("m3/m3", "m3m3", "volumetric"):
            df[col_name] = series_num / 100.0
            converted = True
            action_note = "Divided percentage by 100 to yield m3/m3"

        # Volumetric water content (m3/m3) to percentage
        elif src_u in ("m3/m3", "m3m3", "volumetric") and dst_u in ("%", "percentage"):
            df[col_name] = series_num * 100.0
            converted = True
            action_note = "Multiplied m3/m3 by 100 to yield percentage"

        # Temperature Kelvin to Celsius
        elif src_u in ("k", "kelvin") and dst_u in ("degc", "c", "celsius"):
            df[col_name] = series_num - 273.15
            converted = True
            action_note = "Subtracted 273.15 to convert Kelvin to Celsius"

        # Depth cm to m
        elif src_u in ("cm", "centimeter", "centimeters") and dst_u in ("m", "meter", "meters"):
            df[col_name] = series_num / 100.0
            converted = True
            action_note = "Divided cm by 100 to yield meters"

        # Depth mm to m
        elif src_u in ("mm", "millimeter", "millimeters") and dst_u in ("m", "meter", "meters"):
            df[col_name] = series_num / 1000.0
            converted = True
            action_note = "Divided mm by 1000 to yield meters"

        # Precipitation meters to mm
        elif src_u in ("m", "meter", "meters") and dst_u in ("mm", "millimeter", "millimeters"):
            df[col_name] = series_num * 1000.0
            converted = True
            action_note = "Multiplied meters by 1000 to yield mm"

        if converted:
            audit_entries.append(
                CleaningAuditEntry(
                    stage="unit_conversion",
                    column=col_name,
                    action=f"convert_{src_u}_to_{dst_u}",
                    rows_affected=len(df),
                    details=f"Unit converted from {spec.unit} to {spec.target_unit}: {action_note}",
                )
            )

    return df, audit_entries


def detect_and_handle_outliers(
    df: pd.DataFrame,
    schema: SchemaDefinition,
    config: CleaningConfig,
) -> tuple[pd.DataFrame, list[CleaningAuditEntry], int]:
    """Detect scientific and statistical outliers; apply configured policy."""
    audit_entries: list[CleaningAuditEntry] = []
    if config.outlier_method == "none" or df.empty:
        return df, audit_entries, 0

    df = df.copy()
    rows_to_drop = pd.Series(False, index=df.index)

    for col_name, spec in schema.columns.items():
        if col_name not in df.columns:
            continue
        if spec.data_type not in (DataType.FLOAT, DataType.INT):
            continue

        series = pd.to_numeric(df[col_name], errors="coerce")
        outlier_mask = pd.Series(False, index=df.index)

        # 1. Scientific physical bounds
        if config.outlier_method in ("bounds", "iqr", "zscore"):
            if spec.min_value is not None:
                outlier_mask |= series < spec.min_value
            if spec.max_value is not None:
                outlier_mask |= series > spec.max_value

        # 2. Statistical IQR
        if config.outlier_method == "iqr":
            q25 = series.quantile(0.25)
            q75 = series.quantile(0.75)
            iqr = q75 - q25
            if iqr > 0:
                lower = q25 - config.outlier_iqr_multiplier * iqr
                upper = q75 + config.outlier_iqr_multiplier * iqr
                outlier_mask |= (series < lower) | (series > upper)

        # 3. Statistical Z-Score
        if config.outlier_method == "zscore":
            mean = series.mean()
            std = series.std()
            if std > 0:
                z = (series - mean).abs() / std
                outlier_mask |= z > config.outlier_zscore_threshold

        count = int(outlier_mask.sum())
        if count == 0:
            continue

        if config.outlier_action == "flag_only":
            flag_col = f"is_outlier_{col_name}"
            df[flag_col] = outlier_mask
            audit_entries.append(
                CleaningAuditEntry(
                    stage="outlier_detection",
                    column=col_name,
                    action="flag_only",
                    rows_affected=count,
                    details=f"Created {flag_col} marking {count} outliers",
                )
            )

        elif config.outlier_action == "clip":
            if spec.min_value is not None or spec.max_value is not None:
                df[col_name] = series.clip(lower=spec.min_value, upper=spec.max_value)
                audit_entries.append(
                    CleaningAuditEntry(
                        stage="outlier_detection",
                        column=col_name,
                        action="clip",
                        rows_affected=count,
                        details=f"Clipped {count} values to scientific bounds [{spec.min_value}, {spec.max_value}]",
                    )
                )

        elif config.outlier_action == "nullify":
            df.loc[outlier_mask, col_name] = np.nan
            audit_entries.append(
                CleaningAuditEntry(
                    stage="outlier_detection",
                    column=col_name,
                    action="nullify",
                    rows_affected=count,
                    details=f"Set {count} outlier values to NaN",
                )
            )

        elif config.outlier_action == "drop_row":
            rows_to_drop |= outlier_mask
            audit_entries.append(
                CleaningAuditEntry(
                    stage="outlier_detection",
                    column=col_name,
                    action="drop_row",
                    rows_affected=count,
                    details=f"Marked {count} outlier rows for deletion",
                )
            )

    dropped_count = 0
    if rows_to_drop.any():
        dropped_count = int(rows_to_drop.sum())
        df = df[~rows_to_drop].reset_index(drop=True)

    return df, audit_entries, dropped_count


def handle_missing_values(
    df: pd.DataFrame,
    schema: SchemaDefinition,
    config: CleaningConfig,
) -> tuple[pd.DataFrame, list[CleaningAuditEntry], dict[str, int]]:
    """Enforce missingness policies. Targets are NEVER imputed automatically."""
    audit_entries: list[CleaningAuditEntry] = []
    dropped_reasons: dict[str, int] = {}
    df = df.copy()

    # 1. Target column missingness handling
    target_cols = [
        c.canonical_name
        for c in schema.get_columns_by_role(ColumnRole.TARGET)
        if c.canonical_name in df.columns
    ]

    for col in target_cols:
        target_null_mask = df[col].isna()
        null_count = int(target_null_mask.sum())
        if null_count == 0:
            continue

        if config.missing_target_policy == "drop_row":
            df = df[~target_null_mask].reset_index(drop=True)
            dropped_reasons[f"missing_target_{col}"] = null_count
            audit_entries.append(
                CleaningAuditEntry(
                    stage="missing_target_handling",
                    column=col,
                    action="drop_row",
                    rows_affected=null_count,
                    details=(
                        f"Dropped {null_count} rows with missing target '{col}'. "
                        "Target imputation for ML training is strictly prohibited."
                    ),
                )
            )
        else:
            audit_entries.append(
                CleaningAuditEntry(
                    stage="missing_target_handling",
                    column=col,
                    action="preserved_unlabelled",
                    rows_affected=null_count,
                    details=f"Preserved {null_count} unlabelled target records as NaN without imputation.",
                )
            )

    # 2. Non-target feature and metadata column handling
    feature_cols = [
        col
        for col in df.columns
        if col not in target_cols and (schema.find_column_by_source_name(col) is not None)
    ]

    for col in feature_cols:
        spec = schema.find_column_by_source_name(col)
        if not spec:
            continue

        null_mask = df[col].isna()
        null_count = int(null_mask.sum())
        if null_count == 0:
            continue

        # Numeric policies
        if spec.data_type in (DataType.FLOAT, DataType.INT):
            if config.missing_numeric_policy == "drop_row":
                df = df[~null_mask].reset_index(drop=True)
                dropped_reasons[f"missing_feature_{col}"] = null_count
                audit_entries.append(
                    CleaningAuditEntry(
                        stage="missing_numeric_handling",
                        column=col,
                        action="drop_row",
                        rows_affected=null_count,
                        details=f"Dropped {null_count} rows due to missing value in '{col}'",
                    )
                )
            elif config.missing_numeric_policy == "fill_value":
                fill_val = (
                    config.missing_numeric_fill_value
                    if config.missing_numeric_fill_value is not None
                    else 0.0
                )
                df[col] = df[col].fillna(fill_val)
                audit_entries.append(
                    CleaningAuditEntry(
                        stage="missing_numeric_handling",
                        column=col,
                        action="fill_value",
                        rows_affected=null_count,
                        details=f"Filled {null_count} missing values in '{col}' with {fill_val}",
                    )
                )
            elif config.missing_numeric_policy == "interpolate":
                df[col] = (
                    pd.to_numeric(df[col], errors="coerce").interpolate(method="linear").bfill()
                )
                audit_entries.append(
                    CleaningAuditEntry(
                        stage="missing_numeric_handling",
                        column=col,
                        action="interpolate",
                        rows_affected=null_count,
                        details=f"Interpolated {null_count} values linearly in '{col}'",
                    )
                )

        # Categorical / String policies
        elif spec.data_type in (DataType.STRING, DataType.CATEGORY):
            if config.missing_categorical_policy == "drop_row":
                df = df[~null_mask].reset_index(drop=True)
                dropped_reasons[f"missing_categorical_{col}"] = null_count
                audit_entries.append(
                    CleaningAuditEntry(
                        stage="missing_categorical_handling",
                        column=col,
                        action="drop_row",
                        rows_affected=null_count,
                        details=f"Dropped {null_count} rows due to missing category in '{col}'",
                    )
                )
            elif config.missing_categorical_policy == "fill_value":
                fill_val = config.missing_categorical_fill_value
                df[col] = df[col].fillna(fill_val)
                audit_entries.append(
                    CleaningAuditEntry(
                        stage="missing_categorical_handling",
                        column=col,
                        action="fill_value",
                        rows_affected=null_count,
                        details=f"Filled {null_count} missing values in '{col}' with '{fill_val}'",
                    )
                )

    return df, audit_entries, dropped_reasons


def clean_dataset(
    df: pd.DataFrame,
    schema: SchemaDefinition,
    config: CleaningConfig,
) -> CleaningResult:
    """Execute the full data cleaning lifecycle on a DataFrame."""
    initial_rows = len(df)
    audit_trail: list[CleaningAuditEntry] = []
    dropped_reasons: dict[str, int] = {}

    # Step 1: Strip text & sentinel null normalization
    df_clean, sentinels_audit = strip_text_and_replace_sentinels(df, config)
    audit_trail.extend(sentinels_audit)

    # Step 2: Deduplication
    df_clean, dedup_audit, dropped_dups = deduplicate_dataframe(df_clean, config)
    audit_trail.extend(dedup_audit)
    if dropped_dups > 0:
        dropped_reasons["duplicate_rows"] = dropped_dups

    # Step 3: Coordinate validation
    df_clean, coord_audit, dropped_coords = validate_and_clean_coordinates(df_clean, schema, config)
    audit_trail.extend(coord_audit)
    if dropped_coords > 0:
        dropped_reasons["invalid_coordinates"] = dropped_coords

    # Step 4: Unit conversions
    df_clean, units_audit = convert_units(df_clean, schema)
    audit_trail.extend(units_audit)

    # Step 5: Outliers & bounds
    df_clean, outlier_audit, dropped_outliers = detect_and_handle_outliers(df_clean, schema, config)
    audit_trail.extend(outlier_audit)
    if dropped_outliers > 0:
        dropped_reasons["outliers"] = dropped_outliers

    # Step 6: Missing values & target protection
    df_clean, missing_audit, dropped_missing = handle_missing_values(df_clean, schema, config)
    audit_trail.extend(missing_audit)
    dropped_reasons.update(dropped_missing)

    final_rows = len(df_clean)

    return CleaningResult(
        data=df_clean,
        audit_trail=audit_trail,
        initial_rows=initial_rows,
        final_rows=final_rows,
        dropped_row_reasons=dropped_reasons,
    )
