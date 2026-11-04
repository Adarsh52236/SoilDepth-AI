"""
SoilDepth-AI — Maharashtra Scientific Validation Framework
Author: Senior ML Research Scientist & Hydrological Modeling Lead, SoilDepth-AI
Purpose: Implements rigorous chronological and spatial Leave-One-Station-Out (LOSO)
         cross-validation protocols, standard hydrological error metrics (RMSE, ubRMSE,
         MAE, R², Bias, Pearson r), and baseline hierarchy benchmarking for Maharashtra.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Sequence, Union
import numpy as np
import pandas as pd

from services.modelling.evaluate import compute_metrics, compute_residual_diagnostics
from services.modelling.baselines import HistoricalMeanBaseline, ClimatologyBaseline, PersistenceBaseline

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REPORTS_DIR = REPO_ROOT / "docs" / "reports"


class MaharashtraValidationFramework:
    """
    Standardized validation framework for Maharashtra regional soil moisture models.
    """

    def __init__(self, reports_dir: Optional[Path] = None):
        self.reports_dir = reports_dir or DEFAULT_REPORTS_DIR

    def compute_validation_metrics(
        self,
        y_true: Sequence[float],
        y_pred: Sequence[float],
        dates: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """
        Computes standard hydrological metrics: MAE, RMSE, ubRMSE, R², Bias, Pearson r.
        """
        base_metrics = compute_metrics(y_true, y_pred, dates=dates)
        if base_metrics["n_samples"] == 0:
            base_metrics["ubrmse"] = None
            return base_metrics

        rmse = base_metrics["rmse"]
        bias = base_metrics["bias"]
        # ubRMSE = sqrt(max(0, RMSE^2 - Bias^2))
        ubrmse = float(np.sqrt(max(0.0, (rmse ** 2) - (bias ** 2))))
        base_metrics["ubrmse"] = round(ubrmse, 5)
        return base_metrics

    def create_chronological_splits(
        self,
        df: pd.DataFrame,
        date_col: str = "date_utc",
        train_end: str = "2021-12-31",
        val_end: str = "2022-12-31",
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Creates strictly chronological splits:
        - Train: date <= train_end (e.g. 2017-01-01 to 2021-12-31, 5 years)
        - Val:   train_end < date <= val_end (e.g. 2022-01-01 to 2022-12-31, 1 year)
        - Test:  date > val_end (e.g. 2023-01-01 to 2023-12-31, 1 year)
        """
        if date_col not in df.columns:
            raise KeyError(f"Date column '{date_col}' not found in DataFrame")

        train_mask = df[date_col] <= train_end
        val_mask = (df[date_col] > train_end) & (df[date_col] <= val_end)
        test_mask = df[date_col] > val_end

        return df[train_mask].copy(), df[val_mask].copy(), df[test_mask].copy()

    def create_loso_splits(
        self,
        df: pd.DataFrame,
        station_col: str = "station_id",
    ) -> List[Tuple[str, pd.DataFrame, pd.DataFrame]]:
        """
        Creates spatial Leave-One-Station-Out (LOSO) splits.
        Yields (held_out_station_id, df_train_other_stations, df_test_held_out_station).
        """
        if station_col not in df.columns:
            raise KeyError(f"Station column '{station_col}' not found in DataFrame")

        unique_stations = df[station_col].unique()
        splits = []
        for sid in unique_stations:
            df_test = df[df[station_col] == sid].copy()
            df_train = df[df[station_col] != sid].copy()
            splits.append((str(sid), df_train, df_test))

        return splits

    def evaluate_model_hierarchy(
        self,
        y_train: pd.Series,
        y_test: pd.Series,
        dates_train: pd.Series,
        dates_test: pd.Series,
        weather_preds: Optional[np.ndarray] = None,
        multimodal_preds: Optional[np.ndarray] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluates full model hierarchy against ground truth:
        1. Historical Mean
        2. DOY Climatology
        3. Persistence
        4. Weather-Only ML
        5. Full Multimodal ML
        """
        results = {}

        # 1. Historical Mean
        hm_val = float(y_train.mean())
        hm_preds = np.full(len(y_test), hm_val)
        results["historical_mean"] = self.compute_validation_metrics(y_test, hm_preds, dates=dates_test)

        # 2. DOY Climatology
        df_tr = pd.DataFrame({"date_utc": dates_train, "target": y_train})
        df_te = pd.DataFrame({"date_utc": dates_test, "target": y_test})
        clim = ClimatologyBaseline(date_col="date_utc")
        clim.fit(df_tr, target_col="target")
        clim_preds = clim.predict(df_te)
        results["climatology"] = self.compute_validation_metrics(y_test, clim_preds, dates=dates_test)

        # 3. Persistence (sequential lag within test set)
        if len(y_test) > 1:
            pers_preds = y_test.shift(1).bfill().to_numpy()
            results["persistence"] = self.compute_validation_metrics(y_test, pers_preds, dates=dates_test)

        # 4. Weather-Only ML
        if weather_preds is not None:
            results["weather_only_xgb"] = self.compute_validation_metrics(y_test, weather_preds, dates=dates_test)

        # 5. Full Multimodal ML
        if multimodal_preds is not None:
            results["full_multimodal_xgb"] = self.compute_validation_metrics(y_test, multimodal_preds, dates=dates_test)

        return results

    def generate_validation_protocol_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generates formal markdown documentation of the Maharashtra validation protocol.
        """
        out_p = output_path or (self.reports_dir / "maharashtra_validation_protocol.md")
        out_p.parent.mkdir(parents=True, exist_ok=True)

        md_text = """# SoilDepth-AI — Maharashtra Scientific Validation Protocol

**Author:** Senior ML Research Scientist & Hydrological Modeling Lead, SoilDepth-AI  
**Framework Version:** 1.0.0 (Freeze Commit Baseline)  
**Status:** ACTIVE SPECIFICATION  

---

## 1. Objective & Scope

This protocol establishes the rigorous, peer-review defensible validation criteria for all Maharashtra regional soil moisture estimation models developed within SoilDepth-AI.

The protocol enforces:
1. Complete temporal separation (zero future leakage).
2. Spatial cross-validation for ungauged transferability.
3. Strict hydrological performance baselines.
4. Absolute prohibition of synthetic ground-truth data for validation.

---

## 2. Temporal Partitioning (Chronological Split)

To ensure realistic operational evaluation and eliminate temporal autocorrelation leakage, data must be partitioned chronologically:

| Split Phase | Calendar Window | Duration | Role |
|---|---|---|---|
| **Training** | 2017-01-01 to 2021-12-31 | 5 Years (1,826 days) | Hyperparameter tuning & model fitting |
| **Validation** | 2022-01-01 to 2022-12-31 | 1 Year (365 days) | Early stopping & feature selection |
| **Testing** | 2023-01-01 to 2023-12-31 | 1 Year (365 days) | Final unbiased holdout evaluation |

> [!IMPORTANT]
> Random k-fold cross-validation across time is strictly prohibited because soil moisture has high temporal autocorrelation (persistence), which causes severe optimistic bias.

---

## 3. Spatial Cross-Validation: Leave-One-Station-Out (LOSO)

When multiple stations have verified in-situ data:
- Each station $S_k$ is held out as the test set.
- The model is trained strictly on observations from stations $S_{j \ne k}$.
- Evaluates spatial generalizability to ungauged agricultural talukas.

---

## 4. Evaluation Metrics & Formulation

For observed in-situ series $y_t$ and predicted series $\hat{y}_t$ over $N$ valid timesteps:

1. **Root Mean Squared Error (RMSE):**
   $$\\text{RMSE} = \\sqrt{\\frac{1}{N} \\sum_{t=1}^N (\\hat{y}_t - y_t)^2}$$

2. **Unbiased RMSE (ubRMSE):**
   $$\\text{ubRMSE} = \\sqrt{\\max(0, \\text{RMSE}^2 - \\text{Bias}^2)}$$

3. **Mean Absolute Error (MAE):**
   $$\\text{MAE} = \\frac{1}{N} \\sum_{t=1}^N |\\hat{y}_t - y_t|$$

4. **Coefficient of Determination ($R^2$):**
   $$R^2 = 1 - \\frac{\\sum_{t=1}^N (y_t - \\hat{y}_t)^2}{\\sum_{t=1}^N (y_t - \\bar{y})^2}$$

5. **Mean Bias Error (Bias):**
   $$\\text{Bias} = \\frac{1}{N} \\sum_{t=1}^N (\\hat{y}_t - y_t)$$

6. **Pearson Correlation Coefficient ($r$):**
   $$r = \\frac{\\sum_{t=1}^N (y_t - \\bar{y})(\\hat{y}_t - \\bar{\\hat{y}})}{\\sqrt{\\sum_{t=1}^N (y_t - \\bar{y})^2} \\sqrt{\\sum_{t=1}^N (\\hat{y}_t - \\bar{\\hat{y}})^2}}$$

---

## 5. Baseline Hierarchy & Minimum Acceptance Criteria

Any proposed Maharashtra ML model must beat standard hydrologic baselines to be considered scientifically valid:

| Model Tier | Description | Minimum Threshold |
|---|---|---|
| **Tier 1: Historical Mean** | Constant prediction $\\hat{y} = \\bar{y}_{\\text{train}}$ | Baseline reference |
| **Tier 2: DOY Climatology** | Empirical mean for each Day-Of-Year | $\\text{RMSE}_{\\text{ML}} < \\text{RMSE}_{\\text{Clim}}$ |
| **Tier 3: Persistence** | $\\hat{y}_t = y_{t-1}$ (Gauged benchmark only) | Reference |
| **Tier 4: Weather-Only XGB** | Trained strictly on meteorological variables | Baseline ML |
| **Tier 5: Full Multimodal XGB** | Weather + S1 SAR + S2 Optical + SMAP L3 + SoilGrids + DEM | $\\ge 10\\%$ improvement over Tier 4 |

### Target Performance Benchmarks:
- **Topsoil (0–10 cm):** $\\text{ubRMSE} \\le 0.050 \\text{ m}^3/\\text{m}^3$, Pearson $r \\ge 0.70$.
- **Subsoil (10–30 cm):** $\\text{ubRMSE} \\le 0.055 \\text{ m}^3/\\text{m}^3$, Pearson $r \\ge 0.60$.
- **Deep Root-Zone (30–60 cm):** $\\text{ubRMSE} \\le 0.060 \\text{ m}^3/\\text{m}^3$, Pearson $r \\ge 0.50$.

---

## 6. Prohibited Practices

1. **No Synthetic Validation:** Under no circumstances may synthetic, simulated, reanalysis, or interpolated data be used to validate models.
2. **No Target Lags in Ungauged Testing:** Operational inference must rely strictly on remote sensing and weather.
3. **No Silenced Layer-Averaging:** Point measurements must not be equated to layer averages without documented calibration.
"""
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(md_text)

        return md_text
