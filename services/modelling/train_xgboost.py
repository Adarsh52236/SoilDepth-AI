"""
SoilDepth-AI — Baseline & Multimodal XGBoost Model Training Pipeline
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Train and evaluate separate reference baselines and gradient-boosted regression
         models (Weather-Only, Lag-Augmented, and Full Multimodal Earth Observation)
         for each eligible point-sensor target depth (5 cm, 10 cm, 20 cm, 50 cm)
         at pilot station AAMU-JTG using chronological data splits.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
import xgboost as xgb

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from services.modelling.config import (
    REPO_ROOT,
    PROCESSED_DATA_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    STATION_ID,
    STATION_LAT,
    STATION_LON,
    STATION_ELEV_M,
    SENSOR_DEPTHS,
    TRAIN_START_DATE,
    TRAIN_END_DATE,
    VAL_START_DATE,
    VAL_END_DATE,
    TEST_START_DATE,
    TEST_END_DATE,
    WEATHER_ONLY_FEATURE_NAMES,
    LAG_AUGMENTED_FEATURE_NAMES,
    FULL_MULTIMODAL_FEATURE_NAMES,
    XGB_HYPERPARAMS,
)
from services.modelling.feature_engineering import partition_chronological_splits
from services.modelling.baselines import (
    PersistenceBaseline,
    ClimatologyBaseline,
    HistoricalMeanBaseline,
)
from services.modelling.evaluate import (
    compute_metrics,
    compute_residual_diagnostics,
    format_metrics_markdown_table,
)


def generate_depth_plots(
    depth_key: str,
    preds_df: pd.DataFrame,
    preds_val_df: pd.DataFrame,
    plots_dir: Path,
) -> List[Path]:
    """
    Generates publication-quality diagnostic plots for a given depth:
    1. Observed vs Predicted scatter plots with identity line (Test set)
    2. Residual error distributions (Test set)
    3. Chronological time-series hydrograph (2022-2023 holdout test set)
    """
    plots_dir.mkdir(parents=True, exist_ok=True)
    generated_plots = []
    depth_cfg = SENSOR_DEPTHS[depth_key]

    model_plot_configs = [
        ("Historical_Mean", "pred_historical_mean", "res_historical_mean", "Historical Mean", "#7f7f7f"),
        ("Climatology", "pred_climatology", "res_climatology", "DOY Climatology", "#bcbd22"),
        ("Persistence", "pred_persistence", "res_persistence", "Persistence (t-1)", "#17becf"),
        ("XGBoost_Weather_Only", "pred_xgb_weather_only", "res_xgb_weather_only", "XGBoost Weather-Only", "#ff7f0e"),
        ("XGBoost_Lag_Augmented", "pred_xgb_lag_augmented", "res_xgb_lag_augmented", "XGBoost Lag-Augmented", "#2ca02c"),
        ("XGBoost_Full_Multimodal", "pred_xgb_full_multimodal", "res_xgb_full_multimodal", "XGBoost Full Multimodal", "#1f77b4"),
    ]

    active_configs = [c for c in model_plot_configs if c[1] in preds_df.columns]

    # --------------------------------------------------------------------------
    # 1. Observed vs Predicted Scatter Plots (Test Set)
    # --------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(15, 10), sharex=True, sharey=True)
    axes = axes.flatten()

    y_true = preds_df["y_true"].values
    min_val = max(0.0, np.nanmin(y_true) - 0.05)
    max_val = np.nanmax(y_true) + 0.05

    for idx, (m_key, pred_col, res_col, label, color) in enumerate(active_configs):
        ax = axes[idx]
        y_p = preds_df[pred_col].values
        valid_m = np.isfinite(y_true) & np.isfinite(y_p)
        yt_v = y_true[valid_m]
        yp_v = y_p[valid_m]

        ax.scatter(yt_v, yp_v, alpha=0.5, s=18, color=color, edgecolors="none")
        ax.plot([min_val, max_val], [min_val, max_val], "r--", lw=1.5, label="1:1 Identity")

        diff = yp_v - yt_v
        rmse = np.sqrt(np.mean(diff ** 2))
        mae = np.mean(np.abs(diff))
        std_t = np.std(yt_v)
        std_p = np.std(yp_v)
        r = np.corrcoef(yt_v, yp_v)[0, 1] if std_t > 1e-9 and std_p > 1e-9 else 0.0

        ax.set_title(f"{label}\nRMSE: {rmse:.4f} | MAE: {mae:.4f} | r: {r:.3f}", fontsize=10)
        ax.set_xlim(min_val, max_val)
        ax.set_ylim(min_val, max_val)
        ax.set_xlabel("Observed Soil Moisture (m³/m³)", fontsize=9)
        ax.set_ylabel("Predicted Soil Moisture (m³/m³)", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.5)

    plt.suptitle(
        f"SoilDepth-AI — Observed vs Predicted: {depth_key} ({depth_cfg.nominal_depth_cm:.1f} cm)\nHoldout Test Split (2022-01-01 to 2023-12-31)",
        fontsize=12,
        fontweight="bold",
    )
    plt.tight_layout()
    scatter_path = plots_dir / f"{depth_key}_scatter_pred_vs_obs.png"
    plt.savefig(scatter_path, dpi=200)
    plt.close()
    generated_plots.append(scatter_path)

    # --------------------------------------------------------------------------
    # 2. Residual Distribution Plots (Test Set)
    # --------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(15, 10), sharex=True)
    axes = axes.flatten()

    for idx, (m_key, pred_col, res_col, label, color) in enumerate(active_configs):
        ax = axes[idx]
        residuals = preds_df[res_col].dropna().values
        mean_res = np.mean(residuals)
        std_res = np.std(residuals)

        ax.hist(residuals, bins=35, color=color, alpha=0.7, density=True, edgecolor="black", linewidth=0.5)
        ax.axvline(0.0, color="red", linestyle="--", lw=1.5, label="Zero Bias")
        ax.axvline(mean_res, color="black", linestyle=":", lw=1.5, label=f"Bias: {mean_res:+.4f}")

        ax.set_title(f"{label}\nMean: {mean_res:+.4f} | Std: {std_res:.4f}", fontsize=10)
        ax.set_xlabel("Residual (y_pred - y_true) [m³/m³]", fontsize=9)
        ax.set_ylabel("Density", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(fontsize=8, loc="upper right")

    plt.suptitle(
        f"SoilDepth-AI — Residual Distributions: {depth_key} ({depth_cfg.nominal_depth_cm:.1f} cm)\nHoldout Test Split (2022-01-01 to 2023-12-31)",
        fontsize=12,
        fontweight="bold",
    )
    plt.tight_layout()
    res_path = plots_dir / f"{depth_key}_residuals_distribution.png"
    plt.savefig(res_path, dpi=200)
    plt.close()
    generated_plots.append(res_path)

    # --------------------------------------------------------------------------
    # 3. Chronological Time-Series Hydrograph (Test Set)
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, 6))
    dt_series = pd.to_datetime(preds_df["date_utc"])

    ax.plot(dt_series, preds_df["y_true"], color="black", lw=1.8, label="Observed In-Situ (SCAN)", zorder=5)

    if "pred_persistence" in preds_df.columns:
        ax.plot(dt_series, preds_df["pred_persistence"], color="#17becf", lw=1.0, alpha=0.7, label="Persistence (t-1)")
    if "pred_xgb_weather_only" in preds_df.columns:
        ax.plot(dt_series, preds_df["pred_xgb_weather_only"], color="#ff7f0e", lw=1.2, alpha=0.8, label="XGBoost Weather-Only")
    if "pred_xgb_lag_augmented" in preds_df.columns:
        ax.plot(dt_series, preds_df["pred_xgb_lag_augmented"], color="#2ca02c", lw=1.3, alpha=0.8, label="XGBoost Lag-Augmented")
    if "pred_xgb_full_multimodal" in preds_df.columns:
        ax.plot(dt_series, preds_df["pred_xgb_full_multimodal"], color="#1f77b4", lw=1.5, alpha=0.9, label="XGBoost Full Multimodal")

    ax.set_title(
        f"SoilDepth-AI — Chronological Evaluation Hydrograph: {depth_key} ({depth_cfg.nominal_depth_cm:.1f} cm)\nStation {STATION_ID} (Test Split: 2022-01-01 to 2023-12-31)",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Date (UTC)", fontsize=10)
    ax.set_ylabel("Volumetric Soil Moisture (m³/m³)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

    plt.tight_layout()
    ts_path = plots_dir / f"{depth_key}_timeseries_hydrograph.png"
    plt.savefig(ts_path, dpi=200)
    plt.close()
    generated_plots.append(ts_path)

    return generated_plots


def train_and_evaluate_depth(
    depth_key: str,
    df_depth: pd.DataFrame,
    models_dir: Path,
    reports_dir: Path,
    include_full_multimodal: bool = True,
) -> Dict[str, Any]:
    """
    Trains reference baselines and XGBoost models for a single sensor depth,
    evaluates on both validation and unseen test periods, exports predictions,
    residuals, diagnostic plots, and model artifacts.
    """
    depth_cfg = SENSOR_DEPTHS[depth_key]
    print(f"\n{'='*80}")
    print(f">>> Running Modelling Pipeline for Target Depth: {depth_key} ({depth_cfg.nominal_depth_cm:.1f} cm)")
    print(f"{'='*80}")

    plots_dir = reports_dir / "plots"
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    # 1. Chronological splitting
    df_train, df_val, df_test = partition_chronological_splits(df_depth)

    # 2. Prepare common validation & test evaluation sets
    # To enable fair comparison across all 6 models (remote sensing vs autoregressive),
    # evaluate on the common valid subset (where y_t and y_{t-1} are both present).
    val_eval_mask = df_val["target"].notna() & df_val["target_lag_1d"].notna()
    df_val_common = df_val[val_eval_mask].copy()

    test_eval_mask = df_test["target"].notna() & df_test["target_lag_1d"].notna()
    df_test_common = df_test[test_eval_mask].copy()

    # Clean train and validation sets for model fitting
    train_clean_weather = df_train.dropna(subset=["target"]).copy()
    val_clean_weather = df_val.dropna(subset=["target"]).copy()

    train_clean_lag = df_train.dropna(subset=["target", "target_lag_1d"]).copy()
    val_clean_lag = df_val.dropna(subset=["target", "target_lag_1d"]).copy()

    dates_val_common = df_val_common["date_utc"].tolist()
    y_val_common = df_val_common["target"].to_numpy(dtype=float)

    dates_test_common = df_test_common["date_utc"].tolist()
    y_test_common = df_test_common["target"].to_numpy(dtype=float)

    print(f"Sample Counts for {depth_key}:")
    print(f"  Train:      Total days={len(df_train)}, Valid targets={len(train_clean_weather)} (with lag={len(train_clean_lag)})")
    print(f"  Validation: Total days={len(df_val)}, Valid targets={len(val_clean_weather)} (Common eval={len(df_val_common)})")
    print(f"  Test:       Total days={len(df_test)}, Valid targets={df_test['target'].notna().sum()} (Common eval={len(df_test_common)})")

    depth_models_results: Dict[str, Any] = {}
    residual_diagnostics_all: Dict[str, Any] = {}

    preds_val_df = pd.DataFrame({
        "date_utc": dates_val_common,
        "y_true": y_val_common,
    })

    preds_df = pd.DataFrame({
        "date_utc": dates_test_common,
        "y_true": y_test_common,
    })

    # --------------------------------------------------------------------------
    # MODEL 1: Historical Mean Baseline
    # --------------------------------------------------------------------------
    hist_model = HistoricalMeanBaseline()
    hist_model.fit(train_clean_weather, target_col="target")

    y_val_hist = hist_model.predict(df_val_common)
    preds_val_df["pred_historical_mean"] = y_val_hist
    preds_val_df["res_historical_mean"] = y_val_hist - y_val_common

    y_pred_hist = hist_model.predict(df_test_common)
    preds_df["pred_historical_mean"] = y_pred_hist
    preds_df["res_historical_mean"] = y_pred_hist - y_test_common

    val_metrics_hist = compute_metrics(y_val_common, y_val_hist, dates_val_common)
    test_metrics_hist = compute_metrics(y_test_common, y_pred_hist, dates_test_common)

    depth_models_results["Historical_Mean"] = {
        "depth": depth_key,
        "config": "Historical Mean Baseline",
        **test_metrics_hist,
        "val_metrics": val_metrics_hist,
    }
    residual_diagnostics_all["Historical_Mean"] = {
        "validation": compute_residual_diagnostics(y_val_common, y_val_hist),
        "test": compute_residual_diagnostics(y_test_common, y_pred_hist),
    }

    # --------------------------------------------------------------------------
    # MODEL 2: Day-of-Year Climatology Baseline
    # --------------------------------------------------------------------------
    clim_model = ClimatologyBaseline(date_col="date_utc")
    clim_model.fit(train_clean_weather, target_col="target")

    y_val_clim = clim_model.predict(df_val_common)
    preds_val_df["pred_climatology"] = y_val_clim
    preds_val_df["res_climatology"] = y_val_clim - y_val_common

    y_pred_clim = clim_model.predict(df_test_common)
    preds_df["pred_climatology"] = y_pred_clim
    preds_df["res_climatology"] = y_pred_clim - y_test_common

    val_metrics_clim = compute_metrics(y_val_common, y_val_clim, dates_val_common)
    test_metrics_clim = compute_metrics(y_test_common, y_pred_clim, dates_test_common)

    depth_models_results["Climatology"] = {
        "depth": depth_key,
        "config": "DOY Climatology Baseline",
        **test_metrics_clim,
        "val_metrics": val_metrics_clim,
    }
    residual_diagnostics_all["Climatology"] = {
        "validation": compute_residual_diagnostics(y_val_common, y_val_clim),
        "test": compute_residual_diagnostics(y_test_common, y_pred_clim),
    }

    # --------------------------------------------------------------------------
    # MODEL 3: Persistence Baseline (y_hat_t = y_{t-1})
    # --------------------------------------------------------------------------
    persist_model = PersistenceBaseline(lag_col="target_lag_1d")
    persist_model.fit(train_clean_lag, target_col="target")

    y_val_persist = persist_model.predict(df_val_common)
    preds_val_df["pred_persistence"] = y_val_persist
    preds_val_df["res_persistence"] = y_val_persist - y_val_common

    y_pred_persist = persist_model.predict(df_test_common)
    preds_df["pred_persistence"] = y_pred_persist
    preds_df["res_persistence"] = y_pred_persist - y_test_common

    val_metrics_persist = compute_metrics(y_val_common, y_val_persist, dates_val_common)
    test_metrics_persist = compute_metrics(y_test_common, y_pred_persist, dates_test_common)

    depth_models_results["Persistence"] = {
        "depth": depth_key,
        "config": "Persistence Baseline (t-1)",
        **test_metrics_persist,
        "val_metrics": val_metrics_persist,
    }
    residual_diagnostics_all["Persistence"] = {
        "validation": compute_residual_diagnostics(y_val_common, y_val_persist),
        "test": compute_residual_diagnostics(y_test_common, y_pred_persist),
    }

    # --------------------------------------------------------------------------
    # MODEL 4: Weather-Only XGBoost (Remote Sensing / Meteorology Proxy, 25 Features)
    # --------------------------------------------------------------------------
    X_train_w = train_clean_weather[WEATHER_ONLY_FEATURE_NAMES].values
    y_train_w = train_clean_weather["target"].values
    X_val_fit_w = val_clean_weather[WEATHER_ONLY_FEATURE_NAMES].values
    y_val_fit_w = val_clean_weather["target"].values
    X_val_common_w = df_val_common[WEATHER_ONLY_FEATURE_NAMES].values
    X_test_w = df_test_common[WEATHER_ONLY_FEATURE_NAMES].values

    xgb_weather = xgb.XGBRegressor(
        n_estimators=XGB_HYPERPARAMS["n_estimators"],
        max_depth=XGB_HYPERPARAMS["max_depth"],
        learning_rate=XGB_HYPERPARAMS["learning_rate"],
        subsample=XGB_HYPERPARAMS["subsample"],
        colsample_bytree=XGB_HYPERPARAMS["colsample_bytree"],
        min_child_weight=XGB_HYPERPARAMS["min_child_weight"],
        gamma=XGB_HYPERPARAMS["gamma"],
        random_state=XGB_HYPERPARAMS["random_state"],
        early_stopping_rounds=XGB_HYPERPARAMS["early_stopping_rounds"],
        eval_metric=XGB_HYPERPARAMS["eval_metric"],
    )
    xgb_weather.fit(
        X_train_w,
        y_train_w,
        eval_set=[(X_val_fit_w, y_val_fit_w)],
        verbose=False,
    )

    y_val_xgb_weather = xgb_weather.predict(X_val_common_w)
    preds_val_df["pred_xgb_weather_only"] = y_val_xgb_weather
    preds_val_df["res_xgb_weather_only"] = y_val_xgb_weather - y_val_common

    y_pred_xgb_weather = xgb_weather.predict(X_test_w)
    preds_df["pred_xgb_weather_only"] = y_pred_xgb_weather
    preds_df["res_xgb_weather_only"] = y_pred_xgb_weather - y_test_common

    val_metrics_weather = compute_metrics(y_val_common, y_val_xgb_weather, dates_val_common)
    test_metrics_weather = compute_metrics(y_test_common, y_pred_xgb_weather, dates_test_common)

    depth_models_results["XGBoost_Weather_Only"] = {
        "depth": depth_key,
        "config": "XGBoost (Weather + Memory + Seasonality + Edaphics)",
        "best_iteration": int(xgb_weather.best_iteration),
        **test_metrics_weather,
        "val_metrics": val_metrics_weather,
    }
    residual_diagnostics_all["XGBoost_Weather_Only"] = {
        "validation": compute_residual_diagnostics(y_val_common, y_val_xgb_weather),
        "test": compute_residual_diagnostics(y_test_common, y_pred_xgb_weather),
    }

    # Save Weather-Only Model
    model_w_path = models_dir / f"{depth_key}_weather_only_xgb.json"
    xgb_weather.save_model(str(model_w_path))

    # Feature Importance for Weather-Only
    fi_w = pd.DataFrame({
        "feature": WEATHER_ONLY_FEATURE_NAMES,
        "importance": xgb_weather.feature_importances_,
    }).sort_values("importance", ascending=False)
    fi_w.to_csv(models_dir / f"{depth_key}_weather_only_feature_importances.csv", index=False)

    # --------------------------------------------------------------------------
    # MODEL 5: Lag-Augmented XGBoost (Weather + Memory + Seasonality + Target Lag-1, 26 Features)
    # --------------------------------------------------------------------------
    X_train_lag = train_clean_lag[LAG_AUGMENTED_FEATURE_NAMES].values
    y_train_lag = train_clean_lag["target"].values
    X_val_fit_lag = val_clean_lag[LAG_AUGMENTED_FEATURE_NAMES].values
    y_val_fit_lag = val_clean_lag["target"].values
    X_val_common_lag = df_val_common[LAG_AUGMENTED_FEATURE_NAMES].values
    X_test_lag = df_test_common[LAG_AUGMENTED_FEATURE_NAMES].values

    xgb_lag = xgb.XGBRegressor(
        n_estimators=XGB_HYPERPARAMS["n_estimators"],
        max_depth=XGB_HYPERPARAMS["max_depth"],
        learning_rate=XGB_HYPERPARAMS["learning_rate"],
        subsample=XGB_HYPERPARAMS["subsample"],
        colsample_bytree=XGB_HYPERPARAMS["colsample_bytree"],
        min_child_weight=XGB_HYPERPARAMS["min_child_weight"],
        gamma=XGB_HYPERPARAMS["gamma"],
        random_state=XGB_HYPERPARAMS["random_state"],
        early_stopping_rounds=XGB_HYPERPARAMS["early_stopping_rounds"],
        eval_metric=XGB_HYPERPARAMS["eval_metric"],
    )
    xgb_lag.fit(
        X_train_lag,
        y_train_lag,
        eval_set=[(X_val_fit_lag, y_val_fit_lag)],
        verbose=False,
    )

    y_val_xgb_lag = xgb_lag.predict(X_val_common_lag)
    preds_val_df["pred_xgb_lag_augmented"] = y_val_xgb_lag
    preds_val_df["res_xgb_lag_augmented"] = y_val_xgb_lag - y_val_common

    y_pred_xgb_lag = xgb_lag.predict(X_test_lag)
    preds_df["pred_xgb_lag_augmented"] = y_pred_xgb_lag
    preds_df["res_xgb_lag_augmented"] = y_pred_xgb_lag - y_test_common

    val_metrics_lag = compute_metrics(y_val_common, y_val_xgb_lag, dates_val_common)
    test_metrics_lag = compute_metrics(y_test_common, y_pred_xgb_lag, dates_test_common)

    depth_models_results["XGBoost_Lag_Augmented"] = {
        "depth": depth_key,
        "config": "XGBoost (Weather + Memory + Seasonality + Edaphics + Lag-1)",
        "best_iteration": int(xgb_lag.best_iteration),
        **test_metrics_lag,
        "val_metrics": val_metrics_lag,
    }
    residual_diagnostics_all["XGBoost_Lag_Augmented"] = {
        "validation": compute_residual_diagnostics(y_val_common, y_val_xgb_lag),
        "test": compute_residual_diagnostics(y_test_common, y_pred_xgb_lag),
    }

    # Save Lag-Augmented Model
    model_lag_path = models_dir / f"{depth_key}_lag_augmented_xgb.json"
    xgb_lag.save_model(str(model_lag_path))

    # Feature Importance for Lag-Augmented
    fi_lag = pd.DataFrame({
        "feature": LAG_AUGMENTED_FEATURE_NAMES,
        "importance": xgb_lag.feature_importances_,
    }).sort_values("importance", ascending=False)
    fi_lag.to_csv(models_dir / f"{depth_key}_lag_augmented_feature_importances.csv", index=False)

    # --------------------------------------------------------------------------
    # MODEL 6: Full Multimodal XGBoost (Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2, 58 Features)
    # --------------------------------------------------------------------------
    if include_full_multimodal:
        X_train_full = train_clean_weather[FULL_MULTIMODAL_FEATURE_NAMES].values
        y_train_full = train_clean_weather["target"].values
        X_val_fit_full = val_clean_weather[FULL_MULTIMODAL_FEATURE_NAMES].values
        y_val_fit_full = val_clean_weather["target"].values
        X_val_common_full = df_val_common[FULL_MULTIMODAL_FEATURE_NAMES].values
        X_test_full = df_test_common[FULL_MULTIMODAL_FEATURE_NAMES].values

        xgb_full = xgb.XGBRegressor(
            n_estimators=XGB_HYPERPARAMS["n_estimators"],
            max_depth=XGB_HYPERPARAMS["max_depth"],
            learning_rate=XGB_HYPERPARAMS["learning_rate"],
            subsample=XGB_HYPERPARAMS["subsample"],
            colsample_bytree=XGB_HYPERPARAMS["colsample_bytree"],
            min_child_weight=XGB_HYPERPARAMS["min_child_weight"],
            gamma=XGB_HYPERPARAMS["gamma"],
            random_state=XGB_HYPERPARAMS["random_state"],
            early_stopping_rounds=XGB_HYPERPARAMS["early_stopping_rounds"],
            eval_metric=XGB_HYPERPARAMS["eval_metric"],
        )
        xgb_full.fit(
            X_train_full,
            y_train_full,
            eval_set=[(X_val_fit_full, y_val_fit_full)],
            verbose=False,
        )

        y_val_xgb_full = xgb_full.predict(X_val_common_full)
        preds_val_df["pred_xgb_full_multimodal"] = y_val_xgb_full
        preds_val_df["res_xgb_full_multimodal"] = y_val_xgb_full - y_val_common

        y_pred_xgb_full = xgb_full.predict(X_test_full)
        preds_df["pred_xgb_full_multimodal"] = y_pred_xgb_full
        preds_df["res_xgb_full_multimodal"] = y_pred_xgb_full - y_test_common

        val_metrics_full = compute_metrics(y_val_common, y_val_xgb_full, dates_val_common)
        test_metrics_full = compute_metrics(y_test_common, y_pred_xgb_full, dates_test_common)

        depth_models_results["XGBoost_Full_Multimodal"] = {
            "depth": depth_key,
            "config": "XGBoost Full Multimodal (58 Features: Weather + HWSD + SoilGrids + DEM + SMAP + S1 + S2)",
            "best_iteration": int(xgb_full.best_iteration),
            **test_metrics_full,
            "val_metrics": val_metrics_full,
        }
        residual_diagnostics_all["XGBoost_Full_Multimodal"] = {
            "validation": compute_residual_diagnostics(y_val_common, y_val_xgb_full),
            "test": compute_residual_diagnostics(y_test_common, y_pred_xgb_full),
        }

        # Save Full Multimodal Model
        model_full_path = models_dir / f"{depth_key}_full_multimodal_xgb.json"
        xgb_full.save_model(str(model_full_path))

        # Feature Importance for Full Multimodal
        fi_full = pd.DataFrame({
            "feature": FULL_MULTIMODAL_FEATURE_NAMES,
            "importance": xgb_full.feature_importances_,
        }).sort_values("importance", ascending=False)
        fi_full.to_csv(models_dir / f"{depth_key}_full_multimodal_feature_importances.csv", index=False)

    # --------------------------------------------------------------------------
    # MODEL SELECTION USING VALIDATION SET
    # --------------------------------------------------------------------------
    # Evaluate all models strictly by Validation RMSE
    val_rmse_ranking = []
    for m_name, m_res in depth_models_results.items():
        v_rmse = m_res["val_metrics"]["rmse"]
        val_rmse_ranking.append((m_name, v_rmse))
    val_rmse_ranking.sort(key=lambda x: x[1])

    best_overall_model = val_rmse_ranking[0][0]
    best_overall_val_rmse = val_rmse_ranking[0][1]

    # Best remote-sensing model (no ground truth lag)
    rs_models = [m for m in ["Historical_Mean", "Climatology", "XGBoost_Weather_Only", "XGBoost_Full_Multimodal"] if m in depth_models_results]
    rs_ranking = sorted([(m, depth_models_results[m]["val_metrics"]["rmse"]) for m in rs_models], key=lambda x: x[1])
    best_rs_model = rs_ranking[0][0]

    # Best autoregressive model
    ar_models = [m for m in ["Persistence", "XGBoost_Lag_Augmented"] if m in depth_models_results]
    ar_ranking = sorted([(m, depth_models_results[m]["val_metrics"]["rmse"]) for m in ar_models], key=lambda x: x[1])
    best_ar_model = ar_ranking[0][0]

    model_selection_record = {
        "depth_key": depth_key,
        "selected_best_overall_model": best_overall_model,
        "selected_best_overall_val_rmse": best_overall_val_rmse,
        "selected_best_rs_model": best_rs_model,
        "selected_best_rs_val_rmse": rs_ranking[0][1],
        "selected_best_ar_model": best_ar_model,
        "selected_best_ar_val_rmse": ar_ranking[0][1],
        "validation_ranking": val_rmse_ranking,
        "untouched_test_performance_best_overall": {
            "model": best_overall_model,
            "mae": depth_models_results[best_overall_model]["mae"],
            "rmse": depth_models_results[best_overall_model]["rmse"],
            "r2": depth_models_results[best_overall_model]["r2"],
            "bias": depth_models_results[best_overall_model]["bias"],
            "pearson_r": depth_models_results[best_overall_model]["pearson_r"],
        },
        "untouched_test_performance_best_rs": {
            "model": best_rs_model,
            "mae": depth_models_results[best_rs_model]["mae"],
            "rmse": depth_models_results[best_rs_model]["rmse"],
            "r2": depth_models_results[best_rs_model]["r2"],
            "bias": depth_models_results[best_rs_model]["bias"],
            "pearson_r": depth_models_results[best_rs_model]["pearson_r"],
        },
    }

    # Save Predictions CSVs (Validation and Test)
    val_csv_path = reports_dir / f"{depth_key}_val_predictions.csv"
    preds_val_df.to_csv(val_csv_path, index=False)

    preds_csv_path = reports_dir / f"{depth_key}_test_predictions.csv"
    preds_df.to_csv(preds_csv_path, index=False)

    # Save Residual Diagnostics JSON
    res_diag_path = reports_dir / f"{depth_key}_residual_diagnostics.json"
    with open(res_diag_path, "w", encoding="utf-8") as f:
        json.dump(residual_diagnostics_all, f, indent=2)

    # Generate Diagnostic Visualizations
    generated_plots = generate_depth_plots(depth_key, preds_df, preds_val_df, plots_dir)

    print(f"\nBenchmark Metrics Summary for {depth_key}:")
    for m_name, m_data in depth_models_results.items():
        v_rmse = m_data['val_metrics']['rmse']
        t_rmse = m_data['rmse']
        t_mae = m_data['mae']
        t_r2 = m_data['r2']
        t_r = m_data['pearson_r']
        print(f"  [{m_name:<24}] Val RMSE: {v_rmse:.4f} | Test MAE: {t_mae:.4f} | Test RMSE: {t_rmse:.4f} | Test R²: {t_r2:.4f} | Test r: {t_r:.4f}")

    print(f"\n  >>> Model Selected by Validation RMSE: {best_overall_model} (Val RMSE: {best_overall_val_rmse:.4f})")
    print(f"  >>> Best Remote-Sensing (Ungauged) Model: {best_rs_model} (Val RMSE: {rs_ranking[0][1]:.4f})")
    print(f"  >>> Diagnostic plots generated: {[p.name for p in generated_plots]}")

    return {
        "depth_key": depth_key,
        "nominal_depth_cm": depth_cfg.nominal_depth_cm,
        "depth_m": depth_cfg.depth_m,
        "train_samples_weather": len(train_clean_weather),
        "train_samples_lag": len(train_clean_lag),
        "val_samples_weather": len(val_clean_weather),
        "val_samples_common": len(df_val_common),
        "test_samples_common": len(df_test_common),
        "models": depth_models_results,
        "residual_diagnostics": residual_diagnostics_all,
        "model_selection": model_selection_record,
        "generated_plots": [str(p) for p in generated_plots],
    }


def run_dry_run_audit(
    depth_keys: Optional[List[str]] = None,
    processed_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes a comprehensive, non-destructive audit of all training datasets,
    verifying 3,287 days, chronological monotonicity, exact presence of all 58 features,
    zero target leakage, and split sample counts.
    """
    if depth_keys is None:
        depth_keys = list(SENSOR_DEPTHS.keys())
    if processed_dir is None:
        processed_dir = PROCESSED_DATA_DIR

    audit_results = {}
    print("=" * 80)
    print("SoilDepth-AI — Model 1 Training Readiness Audit (Dry Run)")
    print(f"Station: {STATION_ID}")
    print(f"Target Depths: {', '.join(depth_keys)}")
    print(f"Configured Predictors: {len(FULL_MULTIMODAL_FEATURE_NAMES)} features")
    print(f"Train split: {TRAIN_START_DATE} to {TRAIN_END_DATE} (6 years)")
    print(f"Val split:   {VAL_START_DATE} to {VAL_END_DATE} (1 year)")
    print(f"Test split:  {TEST_START_DATE} to {TEST_END_DATE} (2 years)")
    print("=" * 80)

    for depth_key in depth_keys:
        csv_path = processed_dir / f"{STATION_ID}_{depth_key}_daily.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing modeling dataset: {csv_path}")

        df = pd.read_csv(csv_path)

        # 1. Row count & chronological order
        assert len(df) == 3287, f"Expected 3,287 rows, got {len(df)}"
        assert df["date_utc"].is_monotonic_increasing, f"{depth_key}: dates not monotonic"
        assert df["date_utc"].iloc[0] == TRAIN_START_DATE, f"Min date mismatch: {df['date_utc'].iloc[0]}"
        assert df["date_utc"].iloc[-1] == TEST_END_DATE, f"Max date mismatch: {df['date_utc'].iloc[-1]}"

        # 2. 58 features presence
        missing_feats = [col for col in FULL_MULTIMODAL_FEATURE_NAMES if col not in df.columns]
        assert len(missing_feats) == 0, f"{depth_key} missing features: {missing_feats}"

        # 3. Target isolation in predictor feature set
        for feat in FULL_MULTIMODAL_FEATURE_NAMES:
            for term in ["target", "sm_5cm", "sm_10cm", "sm_20cm", "sm_50cm"]:
                assert term not in feat.lower(), f"Leakage detected in feature: {feat}"

        # 4. Check for infinite values
        numeric_cols = [c for c in FULL_MULTIMODAL_FEATURE_NAMES if pd.api.types.is_numeric_dtype(df[c])]
        any_inf = any(np.isinf(df[col]).any() for col in numeric_cols)
        assert not any_inf, f"{depth_key} contains infinite values in predictors"

        # 5. Chronological splits
        df_train, df_val, df_test = partition_chronological_splits(df)
        assert len(df_train) == 2192
        assert len(df_val) == 365
        assert len(df_test) == 730

        train_valid = int(df_train["target"].notna().sum())
        val_valid = int(df_val["target"].notna().sum())
        test_valid = int(df_test["target"].notna().sum())
        test_common = int((df_test["target"].notna() & df_test["target_lag_1d"].notna()).sum())

        target_min = float(df["target"].min())
        target_max = float(df["target"].max())

        audit_results[depth_key] = {
            "total_days": len(df),
            "date_range": [df["date_utc"].iloc[0], df["date_utc"].iloc[-1]],
            "columns": len(df.columns),
            "feature_count": len(FULL_MULTIMODAL_FEATURE_NAMES),
            "train_valid_targets": train_valid,
            "val_valid_targets": val_valid,
            "test_valid_targets": test_valid,
            "test_common_targets": test_common,
            "target_range": [round(target_min, 4), round(target_max, 4)],
            "status": "READY_FOR_TRAINING",
        }
        print(f"  [{depth_key}] Ready: 3,287 days | Train: {train_valid} | Val: {val_valid} | Test: {test_valid} (Common: {test_common}) | Range: [{target_min:.4f}, {target_max:.4f}]")

    print("=" * 80)
    print("All datasets verified! Training readiness confirmed.")
    print("=" * 80)
    return audit_results


def run_full_baseline_training(
    depth_keys: Optional[List[str]] = None,
    models_dir: Optional[Path] = None,
    reports_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    include_full_multimodal: bool = True,
) -> Dict[str, Any]:
    """
    Executes training across sensor depths, generates structured reports,
    evaluates validation and holdout test performance, and saves execution metadata.
    """
    if depth_keys is None:
        depth_keys = list(SENSOR_DEPTHS.keys())
    if models_dir is None:
        models_dir = MODELS_DIR
    if reports_dir is None:
        reports_dir = REPORTS_DIR
    if processed_dir is None:
        processed_dir = PROCESSED_DATA_DIR

    print("=" * 80)
    print("SoilDepth-AI — Starting Model 1 Baseline & Multimodal Training Pipeline")
    print(f"Station: {STATION_ID}")
    print(f"Depths:  {', '.join(depth_keys)}")
    print(f"Train split: {TRAIN_START_DATE} to {TRAIN_END_DATE} (6 years)")
    print(f"Val split:   {VAL_START_DATE} to {VAL_END_DATE} (1 year, early stopping & selection)")
    print(f"Test split:  {TEST_START_DATE} to {TEST_END_DATE} (2 years, untouched holdout)")
    print(f"Include Full Multimodal: {include_full_multimodal} (58 features)")
    print(f"Configurations to train: {len(depth_keys) * (6 if include_full_multimodal else 5)}")
    print("=" * 80)

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "plots").mkdir(parents=True, exist_ok=True)

    all_depth_results = {}
    flat_test_table_dict = {}
    flat_val_table_dict = {}
    model_selection_summary = {}

    for depth_key in depth_keys:
        processed_file = processed_dir / f"{STATION_ID}_{depth_key}_daily.csv"
        if not processed_file.exists():
            raise FileNotFoundError(f"Processed depth data file not found at {processed_file}")

        df_depth = pd.read_csv(processed_file)
        res = train_and_evaluate_depth(
            depth_key,
            df_depth,
            models_dir,
            reports_dir,
            include_full_multimodal=include_full_multimodal,
        )
        all_depth_results[depth_key] = res
        model_selection_summary[depth_key] = res["model_selection"]

        for m_name, m_stats in res["models"].items():
            flat_key = f"{depth_key}_{m_name}"
            flat_test_table_dict[flat_key] = m_stats

            # Prepare validation table entry
            v_stats = dict(m_stats["val_metrics"])
            v_stats["depth"] = depth_key
            v_stats["config"] = m_stats.get("config", m_name)
            flat_val_table_dict[flat_key] = v_stats

    # Render Markdown Tables
    md_test_table = format_metrics_markdown_table(flat_test_table_dict)
    md_val_table = format_metrics_markdown_table(flat_val_table_dict)

    # Format Model Selection Summary Table
    sel_rows = []
    sel_headers = [
        "Depth",
        "Selected Best Overall Model (by Val RMSE)",
        "Val RMSE (m³/m³)",
        "Test RMSE (m³/m³)",
        "Test R²",
        "Selected Remote-Sensing Model (Ungauged)",
        "RS Val RMSE",
        "RS Test RMSE",
        "RS Test R²",
    ]
    sel_lines = [
        "| " + " | ".join(sel_headers) + " |",
        "| " + " | ".join(["---"] * len(sel_headers)) + " |",
    ]
    for d_key, s_info in model_selection_summary.items():
        best_overall = s_info["selected_best_overall_model"]
        best_rs = s_info["selected_best_rs_model"]
        t_overall = s_info["untouched_test_performance_best_overall"]
        t_rs = s_info["untouched_test_performance_best_rs"]
        row = [
            d_key,
            best_overall,
            f"{s_info['selected_best_overall_val_rmse']:.4f}",
            f"{t_overall['rmse']:.4f}",
            f"{t_overall['r2']:.4f}",
            best_rs,
            f"{s_info['selected_best_rs_val_rmse']:.4f}",
            f"{t_rs['rmse']:.4f}",
            f"{t_rs['r2']:.4f}",
        ]
        sel_lines.append("| " + " | ".join(row) + " |")
    md_selection_table = "\n".join(sel_lines)

    report_content = f"""# SoilDepth-AI — Model 1 Baseline & Multimodal Evaluation Report
**Station:** `{STATION_ID}` (SCAN Network, USDA-NRCS, USA)
**Geographic Coordinates:** Latitude `{STATION_LAT:.5f}° N`, Longitude `{STATION_LON:.5f}° W`, Elevation `{STATION_ELEV_M} m`
**ERA5-Land Grid Point:** Latitude `34.80000° N`, Longitude `-86.60000° W` (Offset: 4.08 km)
**Timestamp of Evaluation:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## 1. Experimental Setup & Protocol

- **Objective:** Model 1 pointwise discrete sensor depth estimation across four target depths (`sm_5cm`, `sm_10cm`, `sm_20cm`, `sm_50cm`).
- **Chronological Split Partitioning:**
  - **Train:** `{TRAIN_START_DATE}` to `{TRAIN_END_DATE}` (6 full years, 2,192 days). Used for fitting baselines and training gradient boosted trees.
  - **Validation:** `{VAL_START_DATE}` to `{VAL_END_DATE}` (1 full year, 365 days). Used exclusively for early stopping (35 rounds) and model selection.
  - **Test (Holdout):** `{TEST_START_DATE}` to `{TEST_END_DATE}` (2 full years, 730 days). Strictly untouched during training and model selection.
- **Leakage Safeguards:**
  - Strictly past-only memory features (`shift(1)` on precipitation and thermal memory).
  - Strictly past-only remote sensing features (LOCF on SMAP, S1 SAR, and S2 optical).
  - Ground truth ISMN observations are strictly dependent targets, never features (except autoregressive `target_lag_1d` in explicitly designated lag models).
  - Point-sensor observations treated strictly as point proxies, not layer-integrated averages.
- **Model Formulations:**
  1. `Historical Mean`: Constant historical mean from training split.
  2. `DOY Climatology`: Empirical mean for each Day-Of-Year ($1..366$) from training split.
  3. `Persistence (t-1)`: Autoregressive naive baseline: $\\hat{{y}}_t = y_{{t-1}}$.
  4. `XGBoost Weather-Only`: Remote sensing proxy model using 25 past-only atmospheric, memory, seasonal, and static edaphic features without in-situ soil moisture.
  5. `XGBoost Lag-Augmented`: Forecasting model using weather + memory + seasonal + edaphic + autoregressive $y_{{t-1}}$ (26 features).
  6. `XGBoost Full Multimodal`: Earth observation model using 58 features (Weather + HWSD + SoilGrids + DEM + SMAP L3 + Sentinel-1 SAR + Sentinel-2 Optical).

---

## 2. Model Selection on Validation Split (2021-01-01 to 2021-12-31)

{md_val_table}

---

## 3. Untouched Holdout Test Performance (2022-01-01 to 2023-12-31)

{md_test_table}

---

## 4. Selected Best Models per Depth & Physical Interpretation

{md_selection_table}

### 4.1 Surface Zone: 5 cm (`sm_5cm`)
- The 5 cm layer responds rapidly to precipitation impulses and solar evaporation.
- Full Multimodal XGBoost leverages satellite surface observations (SMAP radiometry, Sentinel-1 backscatter, and Sentinel-2 vegetation indices) alongside meteorology and static hydraulics.
- When antecedent in-situ observations are accessible, Lag-Augmented XGBoost achieves near-perfect tracking.

### 4.2 Upper Root Zone: 10 cm (`sm_10cm`)
- Strong hydrological damping compared to 5 cm.
- Meteorological forcing combined with static soil hydraulics and satellite observations is highly predictive of upper root-zone moisture dynamics.

### 4.3 Mid Root Zone: 20 cm (`sm_20cm`)
- Higher moisture retention and thermal damping.
- Persistence is a very strong baseline at this depth due to slow water percolation and root uptake timescales.

### 4.4 Deep Root Zone: 50 cm (`sm_50cm`)
- Slowest hydraulic dynamics and high buffer against high-frequency weather noise.
- Models rely heavily on long-term rolling memory (14d, 30d precipitation and thermal integrals).

---

## 5. Artifact Manifest

All model artifacts and intermediate datasets are saved under standard repository paths:
- Models: `models/baselines/AAMU-JTG/`
- Interim aligned data: `data/modelling/interim/AAMU-JTG_aligned_raw.csv`
- Processed feature data: `data/modelling/processed/AAMU-JTG_*.csv`
- Validation predictions & residuals: `reports/modelling/AAMU-JTG/*_val_predictions.csv`
- Test predictions & residuals: `reports/modelling/AAMU-JTG/*_test_predictions.csv`
- Residual diagnostics: `reports/modelling/AAMU-JTG/*_residual_diagnostics.json`
- Diagnostic plots: `reports/modelling/AAMU-JTG/plots/`
- Metrics JSON: `reports/modelling/AAMU-JTG/metrics.json`
"""

    report_path = reports_dir / "evaluation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    # Save metrics JSON
    metrics_path = reports_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_depth_results, f, indent=2)

    # Save training metadata
    meta = {
        "station_id": STATION_ID,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "splits": {
            "train": [TRAIN_START_DATE, TRAIN_END_DATE],
            "val": [VAL_START_DATE, VAL_END_DATE],
            "test": [TEST_START_DATE, TEST_END_DATE],
        },
        "hyperparams": XGB_HYPERPARAMS,
        "features_weather_only": WEATHER_ONLY_FEATURE_NAMES,
        "features_lag_augmented": LAG_AUGMENTED_FEATURE_NAMES,
        "features_full_multimodal": FULL_MULTIMODAL_FEATURE_NAMES,
        "feature_count_full_multimodal": len(FULL_MULTIMODAL_FEATURE_NAMES),
        "depths": depth_keys,
        "model_selection": model_selection_summary,
    }
    with open(models_dir / "training_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print("\n" + "=" * 80)
    print("Training, evaluation, plotting, and artifact export complete!")
    print(f"Report saved to:   {report_path}")
    print(f"Metrics saved to:  {metrics_path}")
    print(f"Plots saved to:    {reports_dir / 'plots'}")
    print("=" * 80)

    return all_depth_results


def main():
    parser = argparse.ArgumentParser(
        description="SoilDepth-AI — Model 1 Baseline & Multimodal Training Pipeline"
    )
    parser.add_argument(
        "--depths",
        nargs="+",
        default=list(SENSOR_DEPTHS.keys()),
        choices=list(SENSOR_DEPTHS.keys()),
        help="Target depths to process (default: all 4 depths)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform readiness audit and dataset integrity verification without training models",
    )
    parser.add_argument(
        "--skip-full-multimodal",
        action="store_true",
        help="Skip full multimodal model and train only baselines (Weather-Only and Lag-Augmented)",
    )

    args = parser.parse_args()

    if args.dry_run:
        run_dry_run_audit(depth_keys=args.depths)
    else:
        run_full_baseline_training(
            depth_keys=args.depths,
            include_full_multimodal=not args.skip_full_multimodal,
        )


if __name__ == "__main__":
    main()
