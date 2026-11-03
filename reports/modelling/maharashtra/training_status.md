# SoilDepth-AI — Maharashtra Regional Training Status Report

**Status:** `BLOCKED_AWAITING_IN_SITU_GROUND_TRUTH`  
**Timestamp:** 2026-11-03T19:00:35.129059+00:00  
**Alabama Baseline Status:** `COMPLETED_AND_INDEPENDENTLY_VALIDATED`  
**Training Permitted:** `False`  

---

## 1. Executive Summary

Supervised training of the Maharashtra regional soil moisture estimation model is currently **BLOCKED**.

Supervised training of Maharashtra regional models is strictly prohibited until verified in-situ soil moisture observations are received from authorized institutions. Training on synthetic, simulated, reanalysis-derived, or inter-depth interpolated observations is strictly prohibited by SoilDepth-AI scientific data integrity protocols.

## 2. In-Situ Ground-Truth Data Availability

- **In-Situ Records Received:** 0
- **In-Situ Stations Received:** 0 / 16
- **Institutional Dispatch Packets Prepared:** 5
- **Awaited Institutions:**
  - IITM/MoES COSMOS Pune
  - ICAR-NIASM Baramati
  - MPKV Rahuri CAAST
  - IMD National Data Centre Pune
  - Maharashtra PoCRA PMU

## 3. Environmental Predictor Readiness

- **Configured Stations Extracted:** 2 (IITM-PUNE, MPKV-RAHURI-CAAST)
- **Temporal Window:** 2017-01-01 to 2023-12-31 (2,556 daily timesteps)
- **Data Leakage Audit:** `PASSED (Zero ERA5 deep SM swvl2-4, zero SMAP L4, past-only lags)`

## 4. Unblocking Execution Procedure

As soon as institutional ground-truth data is received:
Step 1: Receive authorized in-situ observation files from institutional providers.
Step 2: Ingest and normalize files via MaharashtraGroundTruthAdapter.ingest_file().
Step 3: Validate physical VWC bounds [0.00, 0.65] m3/m3, documented sensor depths, and coordinate matching.
Step 4: Align chronologically with daily environmental timelines (2017-2023).
Step 5: Partition chronological splits (Train: 2017-2021, Val: 2022, Test: 2023) and Leave-One-Station-Out CV.
Step 6: Train separate XGBoost depth regressors for depths with >= 180 valid daily observations.
Step 7: Compute independent evaluation metrics (RMSE, MAE, R², Bias, ubRMSE) and residual diagnostics.

---
*Report generated automatically by `services/modelling/train_maharashtra.py`.*
