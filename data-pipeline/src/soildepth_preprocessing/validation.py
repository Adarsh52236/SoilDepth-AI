"""Schema validation and downstream ML model-readiness verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from soildepth_preprocessing.config import ModelReadinessConfig
from soildepth_preprocessing.schema import ColumnRole, DataType, SchemaDefinition


@dataclass
class ValidationIssue:
    """Represents a specific validation finding."""

    category: str
    column: str | None
    message: str
    severity: str  # "ERROR" or "WARNING"


@dataclass
class ValidationResult:
    """Aggregated outcome of schema and model-readiness checks."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def add_error(self, category: str, column: str | None, message: str) -> None:
        self.is_valid = False
        self.errors.append(f"[{category}] {f'{column}: ' if column else ''}{message}")
        self.issues.append(
            ValidationIssue(
                category=category,
                column=column,
                message=message,
                severity="ERROR",
            )
        )

    def add_warning(self, category: str, column: str | None, message: str) -> None:
        self.warnings.append(f"[{category}] {f'{column}: ' if column else ''}{message}")
        self.issues.append(
            ValidationIssue(
                category=category,
                column=column,
                message=message,
                severity="WARNING",
            )
        )


def validate_schema(
    df: pd.DataFrame,
    schema: SchemaDefinition,
) -> ValidationResult:
    """Validate DataFrame against structural requirements of the schema."""
    result = ValidationResult(is_valid=True)

    # 1. Check required canonical columns
    for col_name, spec in schema.columns.items():
        if spec.required and col_name not in df.columns:
            # Check if an alias exists in the raw data
            alias_found = any(alias in df.columns for alias in spec.source_names)
            if not alias_found:
                result.add_error(
                    category="schema_missing_column",
                    column=col_name,
                    message=f"Required canonical column '{col_name}' (role={spec.role.value}) is missing from dataset.",
                )

    # 2. Check scientific physical constraints for present columns
    for col_name, spec in schema.columns.items():
        if col_name not in df.columns:
            continue

        series = df[col_name]
        non_null = series.dropna()

        if non_null.empty:
            if spec.required:
                result.add_warning(
                    category="schema_all_null",
                    column=col_name,
                    message=f"Required column '{col_name}' contains 100% null values.",
                )
            continue

        # Physical numeric bounds
        if spec.data_type in (DataType.FLOAT, DataType.INT):
            numeric_series = pd.to_numeric(non_null, errors="coerce")
            num_coerced = numeric_series.isna().sum()
            if num_coerced > 0:
                result.add_warning(
                    category="schema_type_mismatch",
                    column=col_name,
                    message=f"{num_coerced} values could not be parsed as numeric.",
                )

            valid_nums = numeric_series.dropna()
            if not valid_nums.empty:
                if spec.min_value is not None:
                    min_violations = (valid_nums < spec.min_value).sum()
                    if min_violations > 0:
                        result.add_warning(
                            category="schema_bound_violation",
                            column=col_name,
                            message=f"{min_violations} values fall below scientific minimum {spec.min_value}.",
                        )
                if spec.max_value is not None:
                    max_violations = (valid_nums > spec.max_value).sum()
                    if max_violations > 0:
                        result.add_warning(
                            category="schema_bound_violation",
                            column=col_name,
                            message=f"{max_violations} values exceed scientific maximum {spec.max_value}.",
                        )

    return result


def validate_model_readiness(
    df: pd.DataFrame,
    schema: SchemaDefinition,
    config: ModelReadinessConfig,
) -> ValidationResult:
    """Perform checks for ML suitability, data leakage, and training stability."""
    result = ValidationResult(is_valid=True)
    if df.empty:
        result.add_error(
            category="model_readiness",
            column=None,
            message="Dataset is empty. Cannot be used for machine learning.",
        )
        return result

    # 1. Target column health
    target_specs = schema.get_columns_by_role(ColumnRole.TARGET)
    for spec in target_specs:
        col = spec.canonical_name
        if col not in df.columns:
            result.add_error(
                category="target_missing",
                column=col,
                message=f"Target column '{col}' is missing from the dataset.",
            )
            continue

        missing_ratio = float(df[col].isna().mean())
        result.metrics[f"target_{col}_missing_ratio"] = missing_ratio

        if missing_ratio >= 1.0:
            result.add_error(
                category="target_health",
                column=col,
                message=f"Target column '{col}' is entirely null. Cannot train supervised model.",
            )
        elif missing_ratio > config.max_target_missing_ratio:
            result.add_warning(
                category="target_health",
                column=col,
                message=(
                    f"Target column '{col}' has {missing_ratio:.1%} missing values "
                    f"(exceeds threshold {config.max_target_missing_ratio:.1%})."
                ),
            )

    # 2. Constant or near-constant features (zero/near-zero variance)
    feature_specs = schema.get_columns_by_role(ColumnRole.FEATURE)
    for spec in feature_specs:
        col = spec.canonical_name
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 2:
            continue

        var = float(series.var())
        result.metrics[f"feature_{col}_variance"] = var
        if var <= config.variance_threshold:
            result.add_warning(
                category="constant_feature",
                column=col,
                message=f"Feature '{col}' has near-zero variance ({var:.2e}). May provide no predictive signal.",
            )

    # 3. Identifier leakage check (ensure IDs are not treated as features)
    if config.check_id_leakage:
        id_cols = [c.canonical_name for c in schema.get_columns_by_role(ColumnRole.ID)]
        for id_c in id_cols:
            if id_c in df.columns and any(s.canonical_name == id_c for s in feature_specs):
                result.add_error(
                    category="identifier_leakage",
                    column=id_c,
                    message=f"Column '{id_c}' is assigned both ID and FEATURE roles. Identifier leakage risk.",
                )

    # 4. Partition / split overlap check (entity leakage across splits)
    if config.check_split_overlap and "split" in df.columns:
        splits = df["split"].unique()
        if "train" in splits and "test" in splits:
            group_cols = [c.canonical_name for c in schema.get_columns_by_role(ColumnRole.ID)]
            for grp in group_cols:
                if grp in df.columns:
                    train_groups = set(df[df["split"] == "train"][grp].dropna())
                    test_groups = set(df[df["split"] == "test"][grp].dropna())
                    overlap = train_groups.intersection(test_groups)
                    if overlap:
                        result.add_warning(
                            category="split_entity_overlap",
                            column=grp,
                            message=(
                                f"Found {len(overlap)} entities in '{grp}' shared across 'train' and 'test' splits. "
                                "May cause spatial or group data leakage."
                            ),
                        )

    # 5. Temporal ordering check (future data leakage across splits)
    if config.check_temporal_leakage and "split" in df.columns:
        ts_specs = schema.get_columns_by_role(ColumnRole.TIMESTAMP)
        for ts_s in ts_specs:
            ts_col = ts_s.canonical_name
            if (
                ts_col in df.columns
                and "train" in df["split"].values
                and "test" in df["split"].values
            ):
                train_ts = pd.to_datetime(
                    df[df["split"] == "train"][ts_col], errors="coerce"
                ).dropna()
                test_ts = pd.to_datetime(
                    df[df["split"] == "test"][ts_col], errors="coerce"
                ).dropna()
                if not train_ts.empty and not test_ts.empty and train_ts.max() > test_ts.min():
                    result.add_warning(
                        category="temporal_leakage",
                        column=ts_col,
                        message=(
                            f"Chronological ordering violation: latest train timestamp ({train_ts.max()}) "
                            f"is after earliest test timestamp ({test_ts.min()})."
                        ),
                    )

    # 6. High feature-target correlation check
    if config.check_high_correlation and target_specs:
        for t_spec in target_specs:
            t_col = t_spec.canonical_name
            if t_col not in df.columns:
                continue
            t_series = pd.to_numeric(df[t_col], errors="coerce")
            for f_spec in feature_specs:
                f_col = f_spec.canonical_name
                if f_col not in df.columns or f_col == t_col:
                    continue
                f_series = pd.to_numeric(df[f_col], errors="coerce")
                valid_mask = t_series.notna() & f_series.notna()
                if valid_mask.sum() > 10:
                    corr = float(np.corrcoef(t_series[valid_mask], f_series[valid_mask])[0, 1])
                    if abs(corr) >= config.high_correlation_threshold:
                        result.add_warning(
                            category="suspicious_correlation",
                            column=f_col,
                            message=(
                                f"Feature '{f_col}' has suspiciously high correlation ({corr:.4f}) "
                                f"with target '{t_col}'. Potential label leakage or proxy target."
                            ),
                        )

    return result
