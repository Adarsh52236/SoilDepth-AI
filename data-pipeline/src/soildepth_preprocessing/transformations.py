"""Feature engineering, time-series operations, and leakage-aware dataset partitioning."""

from __future__ import annotations

import numpy as np
import pandas as pd

from soildepth_preprocessing.config import RollingConfig, SplitConfig, TransformationConfig


def normalize_datetimes(
    df: pd.DataFrame,
    timestamp_column: str,
    target_tz: str = "UTC",
    date_format: str | None = None,
) -> pd.DataFrame:
    """Parse timestamps safely and normalize to ISO-8601 UTC timezone."""
    if timestamp_column not in df.columns:
        return df

    df = df.copy()
    ts_series = pd.to_datetime(df[timestamp_column], format=date_format, errors="coerce")

    # If timezone naive, localize to target timezone; if aware, convert to target timezone
    if ts_series.dt.tz is None:
        ts_series = ts_series.dt.tz_localize(target_tz, ambiguous="NaT", nonexistent="NaT")
    else:
        ts_series = ts_series.dt.tz_convert(target_tz)

    df[timestamp_column] = ts_series
    return df


def generate_lag_features(
    df: pd.DataFrame,
    lags_config: dict[str, list[int]],
    time_col: str | None = None,
    group_col: str | None = None,
) -> pd.DataFrame:
    """Generate lagged features strictly from past observations.

    Raises ValueError if any requested lag is <= 0 (future peering prohibited).
    """
    df = df.copy()

    # Ensure chronological sorting if time column exists
    if time_col and time_col in df.columns:
        if group_col and group_col in df.columns:
            df = df.sort_values(by=[group_col, time_col]).reset_index(drop=True)
        else:
            df = df.sort_values(by=[time_col]).reset_index(drop=True)

    for target_col, lags in lags_config.items():
        if target_col not in df.columns:
            continue

        for lag in lags:
            if lag <= 0:
                raise ValueError(
                    f"Illegal lag value {lag} for column '{target_col}'. "
                    "Lags must strictly be positive integers to prevent future-data leakage."
                )

            new_col_name = f"{target_col}_lag_{lag}"
            if group_col and group_col in df.columns:
                df[new_col_name] = df.groupby(group_col)[target_col].shift(lag)
            else:
                df[new_col_name] = df[target_col].shift(lag)

    return df


def generate_rolling_features(
    df: pd.DataFrame,
    rolling_configs: list[RollingConfig],
    time_col: str | None = None,
    group_col: str | None = None,
) -> pd.DataFrame:
    """Generate rolling window aggregations strictly over past observations."""
    df = df.copy()

    if time_col and time_col in df.columns:
        if group_col and group_col in df.columns:
            df = df.sort_values(by=[group_col, time_col]).reset_index(drop=True)
        else:
            df = df.sort_values(by=[time_col]).reset_index(drop=True)

    for r_cfg in rolling_configs:
        if r_cfg.column not in df.columns:
            continue

        if r_cfg.window <= 0:
            raise ValueError(
                f"Rolling window size must be positive, got {r_cfg.window} for '{r_cfg.column}'."
            )

        new_name = r_cfg.new_column_name or f"{r_cfg.column}_roll_{r_cfg.agg}_{r_cfg.window}"

        def compute_rolling(series: pd.Series, cfg: RollingConfig = r_cfg) -> pd.Series:
            roller = series.rolling(
                window=cfg.window,
                min_periods=cfg.min_periods,
                closed="left",  # closed='left' strictly excludes current/future observation
            )
            if cfg.agg == "mean":
                return roller.mean()
            if cfg.agg == "std":
                return roller.std()
            if cfg.agg == "min":
                return roller.min()
            if cfg.agg == "max":
                return roller.max()
            if cfg.agg == "sum":
                return roller.sum()
            raise ValueError(f"Unsupported aggregation: {cfg.agg}")

        if group_col and group_col in df.columns:
            df[new_name] = df.groupby(group_col)[r_cfg.column].transform(compute_rolling)
        else:
            df[new_name] = compute_rolling(df[r_cfg.column])

    return df


def split_dataset(
    df: pd.DataFrame,
    config: SplitConfig,
) -> pd.DataFrame:
    """Partition dataset into train/val/test splits without data leakage.

    Supports 'temporal' (chronological cutoffs) and 'group' (station/site partitioning).
    """
    if config.method == "none" or df.empty:
        return df

    df = df.copy()
    total_ratio = config.train_ratio + config.val_ratio + config.test_ratio
    if not np.isclose(total_ratio, 1.0, atol=1e-3):
        raise ValueError(
            f"Split ratios must sum to 1.0 (train={config.train_ratio}, "
            f"val={config.val_ratio}, test={config.test_ratio})"
        )

    split_col = config.split_column_name
    df[split_col] = "train"

    if config.method == "temporal":
        time_col = config.temporal_column
        if time_col not in df.columns:
            raise ValueError(f"Temporal split requires '{time_col}' in dataset.")

        df = df.sort_values(by=time_col).reset_index(drop=True)
        n = len(df)
        train_end = int(n * config.train_ratio)
        val_end = int(n * (config.train_ratio + config.val_ratio))

        df.loc[: train_end - 1, split_col] = "train"
        df.loc[train_end : val_end - 1, split_col] = "val"
        df.loc[val_end:, split_col] = "test"

    elif config.method == "group":
        grp_col = config.group_column
        if not grp_col or grp_col not in df.columns:
            raise ValueError(f"Group split requires '{grp_col}' in dataset.")

        unique_groups = df[grp_col].unique()
        # Deterministic shuffle by sorting first
        sorted_groups = np.sort(unique_groups)
        rng = np.random.default_rng(seed=42)
        shuffled = rng.permutation(sorted_groups)

        num_groups = len(shuffled)
        train_grp_end = int(num_groups * config.train_ratio)
        val_grp_end = int(num_groups * (config.train_ratio + config.val_ratio))

        train_grps = set(shuffled[:train_grp_end])
        val_grps = set(shuffled[train_grp_end:val_grp_end])
        test_grps = set(shuffled[val_grp_end:])

        df.loc[df[grp_col].isin(train_grps), split_col] = "train"
        df.loc[df[grp_col].isin(val_grps), split_col] = "val"
        df.loc[df[grp_col].isin(test_grps), split_col] = "test"

    return df


class LearnedStandardScaler:
    """Leakage-safe standard scaler.

    Must be fit solely on the training partition and then applied to val/test partitions.
    """

    def __init__(self, columns: list[str]) -> None:
        self.columns = columns
        self.means_: dict[str, float] = {}
        self.stds_: dict[str, float] = {}
        self.is_fitted: bool = False

    def fit(self, train_df: pd.DataFrame) -> LearnedStandardScaler:
        """Calculate statistics exclusively from training data."""
        self.means_.clear()
        self.stds_.clear()
        for col in self.columns:
            if col in train_df.columns:
                series = pd.to_numeric(train_df[col], errors="coerce").dropna()
                self.means_[col] = float(series.mean())
                std = float(series.std())
                self.stds_[col] = std if std > 1e-8 else 1.0
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply learned scaling parameters to evaluation or inference data."""
        if not self.is_fitted:
            raise RuntimeError("Scaler must be fit on training data before transform.")

        df = df.copy()
        for col in self.columns:
            if col in df.columns and col in self.means_:
                df[col] = (pd.to_numeric(df[col], errors="coerce") - self.means_[col]) / self.stds_[
                    col
                ]
        return df


def apply_transformations(
    df: pd.DataFrame,
    config: TransformationConfig,
    timestamp_col: str | None = None,
    group_col: str | None = None,
) -> pd.DataFrame:
    """Orchestrate all configured feature engineering and time transformations."""
    df = df.copy()

    # 1. Normalize timestamp if available
    if timestamp_col and timestamp_col in df.columns:
        df = normalize_datetimes(
            df,
            timestamp_column=timestamp_col,
            target_tz=config.timezone,
            date_format=config.timestamp_format,
        )

    # 2. Lagged features
    if config.lags:
        df = generate_lag_features(
            df,
            lags_config=config.lags,
            time_col=timestamp_col,
            group_col=group_col,
        )

    # 3. Rolling window features
    if config.rolling_windows:
        df = generate_rolling_features(
            df,
            rolling_configs=config.rolling_windows,
            time_col=timestamp_col,
            group_col=group_col,
        )

    # 4. Train / Val / Test splitting
    if config.split.method != "none":
        df = split_dataset(df, config.split)

    return df
