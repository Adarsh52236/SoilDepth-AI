"""
SoilDepth-AI — Baseline Reference Models
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Provide standard reference baselines for soil moisture estimation:
         1. Persistence Baseline (y_hat_t = y_{t-1})
         2. DOY Climatology Baseline (y_hat_t = mean(y_train for day-of-year))
         3. Historical Mean Baseline (y_hat_t = mean(y_train))
"""

from typing import Optional, Dict
import numpy as np
import pandas as pd


class BaseEstimator:
    """Base class for reference baselines."""
    def fit(self, df_train: pd.DataFrame, target_col: str = "target"):
        raise NotImplementedError

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError


class PersistenceBaseline(BaseEstimator):
    """
    Persistence Baseline:
    Predicts yesterday's observed in-situ soil moisture: y_hat_t = y_{t-1}.
    Requires target_lag_1d column (or shifts target column by 1 if absent).
    """
    def __init__(self, lag_col: str = "target_lag_1d"):
        self.lag_col = lag_col

    def fit(self, df_train: pd.DataFrame, target_col: str = "target"):
        # Persistence has no free parameters to fit
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if self.lag_col in df.columns:
            return df[self.lag_col].to_numpy(dtype=float)
        elif "target" in df.columns:
            return df["target"].shift(1).to_numpy(dtype=float)
        else:
            raise KeyError(f"Neither '{self.lag_col}' nor 'target' found in DataFrame")


class ClimatologyBaseline(BaseEstimator):
    """
    DOY Climatology Baseline:
    Calculates the long-term empirical mean target value for each Day-Of-Year (1..366)
    from the training set. Predicts this DOY mean for each test sample.
    """
    def __init__(self, date_col: str = "date_utc"):
        self.date_col = date_col
        self.doy_means: Dict[int, float] = {}
        self.global_mean: float = 0.0

    def fit(self, df_train: pd.DataFrame, target_col: str = "target"):
        df_valid = df_train.dropna(subset=[target_col]).copy()
        if len(df_valid) == 0:
            raise ValueError("Cannot fit ClimatologyBaseline: training target has no valid values")

        dt = pd.to_datetime(df_valid[self.date_col])
        df_valid["doy"] = dt.dt.dayofyear

        self.global_mean = float(df_valid[target_col].mean())
        doy_group = df_valid.groupby("doy")[target_col].mean().to_dict()
        self.doy_means = {int(k): float(v) for k, v in doy_group.items()}
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        dt = pd.to_datetime(df[self.date_col])
        doys = dt.dt.dayofyear.values

        preds = np.empty(len(df), dtype=float)
        for i, doy in enumerate(doys):
            preds[i] = self.doy_means.get(doy, self.global_mean)
        return preds


class HistoricalMeanBaseline(BaseEstimator):
    """
    Historical Mean Baseline:
    Predicts a constant value equal to the mean observed soil moisture in the training set.
    """
    def __init__(self):
        self.mean_value: float = 0.0

    def fit(self, df_train: pd.DataFrame, target_col: str = "target"):
        df_valid = df_train.dropna(subset=[target_col])
        if len(df_valid) == 0:
            raise ValueError("Cannot fit HistoricalMeanBaseline: training target has no valid values")
        self.mean_value = float(df_valid[target_col].mean())
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return np.full(len(df), self.mean_value, dtype=float)
