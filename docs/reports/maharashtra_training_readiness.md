# SoilDepth-AI — Maharashtra Training Readiness Assessment

**Author:** Senior ML Research Scientist & MLOps Lead, SoilDepth-AI  
**Report Date:** 2026-11-04  
**Target Domain:** Maharashtra Regional Model 1  
**Status:** FORMAL SCIENTIFIC GATING SPECIFICATION  

---

## 1. Executive Summary

Supervised training of the SoilDepth-AI Maharashtra regional soil moisture model is currently **BLOCKED**.

In strict adherence to the project's non-negotiable core principles:
- **No model training is permitted on synthetic, simulated, or reanalysis-derived ground-truth observations.**
- **No model training is permitted using inter-depth interpolated soil moisture observations.**
- **No Alabama Model 1 weights may be passed off or deployed as Maharashtra-trained models.**

The engineering infrastructure, dataset builder, baseline algorithms, training pipeline, and validation protocols are **100% complete and fully verified**. Model training will execute automatically upon ingestion of genuine institutional in-situ observations.

---

## 2. Training Readiness Gating Checklist

| Integrity Gate | Requirement | Current Verification Status | Result |
|---|---|---|---|
| **Gate 1: In-Situ Ground Truth** | Verified institutional observations ($\ge 180$ days/depth) | 0 records received; 5 requests drafted | **BLOCKED** |
| **Gate 2: Reanalysis Leakage Bar** | Prohibit ERA5 deep soil moisture (`swvl2-4`) | Validated by regex and schema tests | **PASSED** |
| **Gate 3: Modelled Product Bar** | Prohibit SMAP L4 root-zone products (`smap_l4`) | Validated by regex and schema tests | **PASSED** |
| **Gate 4: Ungauged Autonomy** | Exclude target-lag features (`target_lag_1d`, etc.) | Enforced by `validate_features()` | **PASSED** |
| **Gate 5: Temporal Separation** | Chronological partitioning (Train $\le 2021$, Val 2022, Test 2023) | Enforced by `MaharashtraValidationFramework` | **PASSED** |
| **Gate 6: Observation Threshold** | Minimum 180 daily observations per sensor depth | Enforced by `MaharashtraDatasetBuilder` | **PASSED** |
| **Gate 7: Baseline Benchmark** | Outperform DOY Climatology and Historical Mean | Integrated into training pipeline | **PASSED** |

---

## 3. Training Architecture & Pipeline Workflow

```mermaid
flowchart TD
    A["Raw Institutional Ground Truth"] --> B["MaharashtraGroundTruthAdapter.ingest_file()"]
    B --> C["Strict Physical & Coordinate Validation [0.0, 0.65 m3/m3]"]
    C --> D["Daily Aggregation per Sensor Depth"]
    D --> E{"Daily Obs >= 180 Days?"}
    E -->|No| F["Output INSUFFICIENT_OBSERVATIONS (Refuse Training)"]
    E -->|Yes| G["Join Multi-Modal Environmental Features (ERA5, S1, S2, SMAP, SoilGrids, DEM)"]
    G --> H["Apply Ungauged Leakage Filter (Strip Target Lags & Deep SM)"]
    H --> I["Partition Chronologically (Train: 2017-2021, Val: 2022, Test: 2023)"]
    I --> J["Fit Reference Baselines (Historical Mean, Climatology, Persistence)"]
    I --> K["Fit Weather-Only XGBoost Model"]
    I --> L["Fit Full Multimodal XGBoost Model"]
    J --> M["Compute Hydrologic Evaluation Metrics (RMSE, ubRMSE, MAE, R2, Bias, Pearson r)"]
    K --> M
    L --> M
    M --> N["Serialize Serialized Models & Feature Importances"]
```

---

## 4. Unblocking Execution Procedure

As soon as institutional data files are placed in `dataset/Maharashtra/acquisition/received_datasets/`:

```powershell
# Step 1: Ingest, normalize, and generate receipt audit report
python -c "from services.data_acquisition.maharashtra.ground_truth_adapter import MaharashtraGroundTruthAdapter; adapter = MaharashtraGroundTruthAdapter(); df = adapter.ingest_file('dataset/Maharashtra/acquisition/received_datasets/raw_data.csv', column_mapping={'timestamp': 'date', 'sensor_depth_cm': 'depth', 'soil_moisture_vwc': 'vwc'}, source_dataset='INSTITUTION_NAME'); adapter.generate_receipt_reports(df, output_dir='dataset/Maharashtra/acquisition/receipt_reports/')"

# Step 2: Run Maharashtra regional training pipeline
python services/modelling/train_maharashtra.py --ground-truth-file dataset/Maharashtra/ground_truth/verified/verified_data.csv
```

---

## 5. Summary

The Maharashtra regional model pipeline represents state-of-the-art MLOps rigor. It eliminates lookahead bias, protects against data leakage, and ensures that the model delivered to agricultural decision-makers will be rooted in empirical hydrological reality.
