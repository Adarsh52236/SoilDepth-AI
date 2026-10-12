# SoilDepth-AI: Data Quality & Scientific Integrity Standards

SoilDepth-AI adheres to rigorous data-engineering and scientific integrity principles. This document outlines why specific cleaning policies are enforced and why simplistic or universal rules are strictly prohibited.

---

## 1. Core Principles

### Principle 1: Raw Data Immutability
Raw datasets must never be overwritten, modified in-place, or destructively edited. The preprocessing pipeline operates purely out-of-place: raw files are read in read-only mode, and cleaned datasets are persisted to dedicated destination directories (`data/processed/`).

### Principle 2: Auditability Over Magic
Every modification, row drop, imputation, or unit conversion must leave a traceable entry in the **Cleaning Audit Trail**. A dataset cannot be considered "production-ready" without its accompanying audit report.

### Principle 3: Preprocessing Improves Consistency, Not Magic Accuracy
A clean dataset improves reproducibility and prevents avoidable pipeline errors, but it does **not** automatically guarantee improved model accuracy. ML model metrics must always be evaluated separately on held-out test splits.

---

## 2. Prohibition of Universal Cleaning Rules

In real-world environmental data, blunt automated heuristics often discard genuine physical signals:

| Universal Rule | Why It Is Prohibited in SoilDepth-AI | Enforced Policy in Pipeline |
| :--- | :--- | :--- |
| **"Drop all rows with any null value"** | Sensor nodes often drop auxiliary temperature channels during maintenance while soil moisture continues logging. Dropping entire rows causes severe sample loss and temporal gaps. | Configurable per-column missingness policies. Only essential keys or target labels trigger row drops when configured. |
| **"Automatically clip all outliers"** | Soil moisture spikes after extreme rainfall events look like statistical outliers (high z-score) but are physically genuine saturation events. Blind clipping truncates peak signals. | Outliers are flagged by default (`flag_only`) rather than destructively clipped or deleted, preserving genuine hydrologic events. |
| **"Universal normalizer on all numbers"** | Physical units have explicit physical meanings ($m^3/m^3$, $^\circ C$, $mm$). Blindly scaling everything to $[0, 1]$ before splitting causes test leakage and obscures physical interpretability. | Explicit unit conversions ($K \to ^\circ C$, $\% \to m^3/m^3$) based on schema declarations. Normalization is learned exclusively on training splits. |

---

## 3. Strict Prevention of Data Leakage

Data leakage occurs when information from outside the training dataset is inadvertently used to create the model, leading to overly optimistic evaluation metrics that collapse in production.

### A. Target Imputation Prohibition
Under supervised machine learning, imputing missing ground-truth target values (`soil_moisture`) using mean, median, linear interpolation, or ML regressors creates artificial targets that train the model on its own assumptions.
> **Rule:** If a target label is missing, the record is either dropped from the training set or preserved unlabelled for inference. Automatic imputation of target columns is strictly prohibited.

### B. Temporal Data Leakage
Time-series environmental data has strong temporal autocorrelation.
- **Lag Feature Rule:** Any lagged feature $x_{t - k}$ must strictly have $k \ge 1$. $k \le 0$ or negative shifts peer into future time steps and will immediately raise a `ValueError`.
- **Rolling Window Rule:** Rolling aggregations must use `closed='left'` so the window strictly contains observations prior to time $t$.
- **Temporal Splitting Rule:** Time-series datasets must use chronological partitioning (e.g. 2020–2022 Train, 2023 Validation, 2024 Test), never random shuffle splitting.

### C. Spatial / Entity Leakage
Sensor stations deployed in identical soil zones have correlated readings. Random splitting across time allows the model to memorize station-specific idiosyncrasies in training and test on the exact same station at different times.
> **Rule:** When spatial independence is required, group splitting (`group` split method by `station_id`) ensures distinct sensor locations are separated across train and test partitions.

---

## 4. Ground Truth vs. Model Estimates

SoilDepth-AI makes an explicit scientific distinction between:
- **Primary Ground Truth (`is_ground_truth: True`):** Calibrated in-situ soil moisture sensors (e.g., ISMN gravimetric, TDR, or FDR sensors). Only these observations may serve as direct supervised target labels.
- **Model Reanalysis & Satellite Baselines (`is_ground_truth: False`):**
  - ECMWF ERA5-Land `swvl1-4` (land surface model output).
  - NASA SMAP Level 4 (assimilated ensemble Kalman filter output).
  - *These products are covariates or benchmark baselines, never ground truth.*
