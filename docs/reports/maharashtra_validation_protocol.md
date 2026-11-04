# SoilDepth-AI — Maharashtra Scientific Validation Protocol

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
- The model is trained strictly on observations from stations $S_{j 
e k}$.
- Evaluates spatial generalizability to ungauged agricultural talukas.

---

## 4. Evaluation Metrics & Formulation

For observed in-situ series $y_t$ and predicted series $\hat{y}_t$ over $N$ valid timesteps:

1. **Root Mean Squared Error (RMSE):**
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{t=1}^N (\hat{y}_t - y_t)^2}$$

2. **Unbiased RMSE (ubRMSE):**
   $$\text{ubRMSE} = \sqrt{\max(0, \text{RMSE}^2 - \text{Bias}^2)}$$

3. **Mean Absolute Error (MAE):**
   $$\text{MAE} = \frac{1}{N} \sum_{t=1}^N |\hat{y}_t - y_t|$$

4. **Coefficient of Determination ($R^2$):**
   $$R^2 = 1 - \frac{\sum_{t=1}^N (y_t - \hat{y}_t)^2}{\sum_{t=1}^N (y_t - \bar{y})^2}$$

5. **Mean Bias Error (Bias):**
   $$\text{Bias} = \frac{1}{N} \sum_{t=1}^N (\hat{y}_t - y_t)$$

6. **Pearson Correlation Coefficient ($r$):**
   $$r = \frac{\sum_{t=1}^N (y_t - \bar{y})(\hat{y}_t - \bar{\hat{y}})}{\sqrt{\sum_{t=1}^N (y_t - \bar{y})^2} \sqrt{\sum_{t=1}^N (\hat{y}_t - \bar{\hat{y}})^2}}$$

---

## 5. Baseline Hierarchy & Minimum Acceptance Criteria

Any proposed Maharashtra ML model must beat standard hydrologic baselines to be considered scientifically valid:

| Model Tier | Description | Minimum Threshold |
|---|---|---|
| **Tier 1: Historical Mean** | Constant prediction $\hat{y} = \bar{y}_{\text{train}}$ | Baseline reference |
| **Tier 2: DOY Climatology** | Empirical mean for each Day-Of-Year | $\text{RMSE}_{\text{ML}} < \text{RMSE}_{\text{Clim}}$ |
| **Tier 3: Persistence** | $\hat{y}_t = y_{t-1}$ (Gauged benchmark only) | Reference |
| **Tier 4: Weather-Only XGB** | Trained strictly on meteorological variables | Baseline ML |
| **Tier 5: Full Multimodal XGB** | Weather + S1 SAR + S2 Optical + SMAP L3 + SoilGrids + DEM | $\ge 10\%$ improvement over Tier 4 |

### Target Performance Benchmarks:
- **Topsoil (0–10 cm):** $\text{ubRMSE} \le 0.050 \text{ m}^3/\text{m}^3$, Pearson $r \ge 0.70$.
- **Subsoil (10–30 cm):** $\text{ubRMSE} \le 0.055 \text{ m}^3/\text{m}^3$, Pearson $r \ge 0.60$.
- **Deep Root-Zone (30–60 cm):** $\text{ubRMSE} \le 0.060 \text{ m}^3/\text{m}^3$, Pearson $r \ge 0.50$.

---

## 6. Prohibited Practices

1. **No Synthetic Validation:** Under no circumstances may synthetic, simulated, reanalysis, or interpolated data be used to validate models.
2. **No Target Lags in Ungauged Testing:** Operational inference must rely strictly on remote sensing and weather.
3. **No Silenced Layer-Averaging:** Point measurements must not be equated to layer averages without documented calibration.
