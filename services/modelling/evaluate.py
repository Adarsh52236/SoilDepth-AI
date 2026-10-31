"""
SoilDepth-AI — Evaluation & Metrics Suite
Author: Senior Data Engineer & Geospatial ML Researcher, SoilDepth-AI
Purpose: Compute rigorous, chronological evaluation metrics for soil moisture
         estimations: MAE, RMSE, R², Mean Bias Error (MBE), and Pearson Correlation (r).
         Handles missing values, edge cases, and outputs structured reports.
"""

from typing import Dict, Any, Optional, Sequence
import numpy as np
import pandas as pd


def compute_metrics(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    dates: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Computes standard hydrological & ML regression metrics on paired observations.
    Filters out any rows where either true or pred is NaN/infinite.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    if len(y_t) != len(y_p):
        raise ValueError(f"Length mismatch: len(y_true)={len(y_t)} vs len(y_pred)={len(y_p)}")

    valid_mask = np.isfinite(y_t) & np.isfinite(y_p)
    n_valid = int(np.sum(valid_mask))
    n_total = len(y_t)
    n_excluded = n_total - n_valid

    if n_valid == 0:
        return {
            "n_samples": 0,
            "n_total": n_total,
            "n_excluded": n_excluded,
            "mae": None,
            "rmse": None,
            "r2": None,
            "bias": None,
            "pearson_r": None,
            "start_date": None,
            "end_date": None,
        }

    yt_val = y_t[valid_mask]
    yp_val = y_p[valid_mask]

    diff = yp_val - yt_val
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    bias = float(np.mean(diff))

    # Variance and R²
    var_true = float(np.var(yt_val, ddof=0))
    if var_true > 1e-12:
        ss_res = np.sum((yt_val - yp_val) ** 2)
        ss_tot = np.sum((yt_val - np.mean(yt_val)) ** 2)
        r2 = float(1.0 - (ss_res / ss_tot))
    else:
        r2 = 0.0

    # Pearson correlation r
    std_t = float(np.std(yt_val))
    std_p = float(np.std(yp_val))
    if std_t > 1e-12 and std_p > 1e-12:
        cov = np.mean((yt_val - np.mean(yt_val)) * (yp_val - np.mean(yp_val)))
        pearson_r = float(cov / (std_t * std_p))
        # Clamp to [-1, 1] to avoid float precision drift
        pearson_r = float(np.clip(pearson_r, -1.0, 1.0))
    else:
        pearson_r = 0.0

    start_date = None
    end_date = None
    if dates is not None:
        valid_dates = [d for d, m in zip(dates, valid_mask) if m]
        if valid_dates:
            start_date = str(min(valid_dates))
            end_date = str(max(valid_dates))

    return {
        "n_samples": n_valid,
        "n_total": n_total,
        "n_excluded": n_excluded,
        "mae": round(mae, 5),
        "rmse": round(rmse, 5),
        "r2": round(r2, 4),
        "bias": round(bias, 5),
        "pearson_r": round(pearson_r, 4),
        "mean_true": round(float(np.mean(yt_val)), 5),
        "mean_pred": round(float(np.mean(yp_val)), 5),
        "std_true": round(std_t, 5),
        "std_pred": round(std_p, 5),
        "start_date": start_date,
        "end_date": end_date,
    }


def compute_residual_diagnostics(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> Dict[str, Any]:
    """
    Computes detailed diagnostic statistics on prediction residuals (e = y_pred - y_true).
    Used for assessing model bias across moisture ranges, skewness, and error spread.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    if len(y_t) != len(y_p):
        raise ValueError(f"Length mismatch: len(y_true)={len(y_t)} vs len(y_pred)={len(y_p)}")

    valid_mask = np.isfinite(y_t) & np.isfinite(y_p)
    if not np.any(valid_mask):
        return {
            "n_samples": 0,
            "residual_mean": None,
            "residual_std": None,
            "residual_median": None,
            "residual_q25": None,
            "residual_q75": None,
            "residual_iqr": None,
            "residual_max_abs": None,
            "residual_skewness": None,
        }

    res = y_p[valid_mask] - y_t[valid_mask]
    n_res = len(res)
    std_r = float(np.std(res))
    mean_r = float(np.mean(res))

    q25 = float(np.percentile(res, 25))
    q75 = float(np.percentile(res, 75))

    if std_r > 1e-12:
        skewness = float(np.mean(((res - mean_r) / std_r) ** 3))
    else:
        skewness = 0.0

    return {
        "n_samples": n_res,
        "residual_mean": round(mean_r, 5),
        "residual_std": round(std_r, 5),
        "residual_median": round(float(np.median(res)), 5),
        "residual_q25": round(q25, 5),
        "residual_q75": round(q75, 5),
        "residual_iqr": round(q75 - q25, 5),
        "residual_max_abs": round(float(np.max(np.abs(res))), 5),
        "residual_skewness": round(skewness, 4),
    }


def format_metrics_markdown_table(results_dict: Dict[str, Dict[str, Any]]) -> str:
    """
    Renders a formatted Markdown table comparing models across depths.
    """
    headers = [
        "Depth",
        "Model Configuration",
        "N (Eval)",
        "MAE (m³/m³)",
        "RMSE (m³/m³)",
        "R²",
        "Bias (m³/m³)",
        "Pearson r",
        "Date Range",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for model_key, m in results_dict.items():
        depth = m.get("depth", "-")
        cfg = m.get("config", model_key)
        n = m.get("n_samples", 0)
        mae = f"{m.get('mae'):.4f}" if m.get("mae") is not None else "N/A"
        rmse = f"{m.get('rmse'):.4f}" if m.get("rmse") is not None else "N/A"
        r2 = f"{m.get('r2'):.4f}" if m.get("r2") is not None else "N/A"
        bias = f"{m.get('bias'):+.4f}" if m.get("bias") is not None else "N/A"
        r = f"{m.get('pearson_r'):.4f}" if m.get("pearson_r") is not None else "N/A"
        date_range = f"{m.get('start_date', '')} to {m.get('end_date', '')}"

        row = [
            depth,
            cfg,
            str(n),
            mae,
            rmse,
            r2,
            bias,
            r,
            date_range,
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)
