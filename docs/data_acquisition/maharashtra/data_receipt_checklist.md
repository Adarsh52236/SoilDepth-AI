# SoilDepth-AI — Maharashtra Ground-Truth Data Receipt Checklist

**Document ID:** `CHECKLIST-MAHA-GT-RECEIPT-2026`  
**Phase:** Phase 3: Maharashtra Ground-Truth Acquisition  
**Standard:** ISO-19157 (Geographic Information — Data Quality) & SoilDepth-AI QA Gate Protocol  
**Purpose:** Comprehensive quality gate applied to every incoming in-situ soil moisture dataset before ingestion and promotion to the verified repository.

---

## 1. Overview & Verification Gate Flow

When observational files are received from an institutional provider, they must pass **all seven mandatory verification dimensions** below before the request status can transition from `DATA_RECEIVED` to `DATA_VERIFIED`:

```
 Incoming Raw Data
        │
        ▼
 [ Gate 1: Timestamps ] ──> [ Gate 2: Physical Units ] ──> [ Gate 3: Sensor Depth & Anti-Interpolation ]
                                                                             │
                                                                             ▼
 [ Gate 7: Missingness & Training Sufficiency ] <── [ Gate 6: Quality Flags ] <── [ Gate 5: Coordinates ] <── [ Gate 4: Measurement Modality ]
        │
        ▼
 Passed All Gates? ──(YES)──> Status: DATA_VERIFIED (Promote to dataset/Maharashtra/ground_truth/verified/)
        │
      (NO)
        ▼
 Status: DATA_REJECTED / ACTION_REQUIRED (Document specific anomalies in issue log)
```

---

## 2. Seven Mandatory Quality Dimensions

### Dimension 1: Timestamps & Temporal Integrity
| Item | Requirement | Verification Criterion | Status Check |
| :---: | :--- | :--- | :---: |
| **1.1** | **Datetime Formatting** | ISO 8601 string (`YYYY-MM-DDTHH:MM:SSZ`) or standard datetime (`YYYY-MM-DD HH:MM:SS`). | [ ] |
| **1.2** | **Timezone Identification** | Timezone explicitly documented. If Indian Standard Time (IST / UTC+05:30), must convert via: $T_{\text{UTC}} = T_{\text{IST}} - 5.5\text{ h}$. | [ ] |
| **1.3** | **Monotonic Ordering** | Timestamps strictly ascending across time; zero temporal retrogressions. | [ ] |
| **1.4** | **Zero Duplicates** | Zero duplicate timestamps for the same `(station_id, sensor_depth_cm)` pair. | [ ] |
| **1.5** | **Sampling Frequency** | Sampling interval explicitly identified: hourly, 30-minute, or daily average. | [ ] |
| **1.6** | **Environmental Alignment** | Observations fall within study window: 2017-01-01 to 2023-12-31. | [ ] |

---

### Dimension 2: Units & Physical Boundary Integrity
| Item | Requirement | Verification Criterion | Status Check |
| :---: | :--- | :--- | :---: |
| **2.1** | **Canonical Unit** | Normalized to Volumetric Water Content ($\text{m}^3/\text{m}^3$). | [ ] |
| **2.2** | **Percentage Conversion** | If supplied as volume percentage ($\%$), divided by 100 ($0.0 \le \theta_{\%} \le 65.0 \implies 0.00 \le \theta \le 0.65\text{ m}^3/\text{m}^3$). | [ ] |
| **2.3** | **Gravimetric Conversion** | If supplied as dry weight gravimetric moisture ($\text{g}/\text{g}$ or $\text{wt }\%$), **must not be silently converted** without authenticated field bulk density ($\rho_b$). Must be flagged for conversion: $\theta_v = \theta_g \times (\rho_b / \rho_w)$. | [ ] |
| **2.4** | **Physical Bounds Check** | All values strictly within mineral Vertisol bounds: $0.00 \le \theta \le 0.65\text{ m}^3/\text{m}^3$. Zero values $> 0.65$ or $< 0.00$. | [ ] |
| **2.5** | **CRNS Raw Counts** | If CRNS raw pulse counts ($N, N_{\text{corr}}$), must include calibration parameters ($N_0$, bulk density $\rho_b$, lattice water $w_{\text{lat}}$, organic matter $w_{\text{som}}$). | [ ] |

---

### Dimension 3: Sensor Depth & Anti-Interpolation Gate
| Item | Requirement | Verification Criterion | Status Check |
| :---: | :--- | :--- | :---: |
| **3.1** | **Documented Physical Depth** | Sensor depth corresponds to genuine physical instrumentation installed at that horizon. | [ ] |
| **3.2** | **Physical Depth Bounds** | Depth must be positive and within root zone: $0.0\text{ cm} < d \le 200.0\text{ cm}$. | [ ] |
| **3.3** | **Station Depth Match** | Depth matches station installation record within $\pm 1.0\text{ cm}$ (e.g. MPKV 10, 20, 30, 60 cm; NIASM 10, 20, 30, 50 cm). | [ ] |
| **3.4** | **Strict Anti-Interpolation** | **ZERO synthetic depth interpolation.** It is strictly prohibited to mathematically interpolate or extrapolate between sensor depths (e.g. averaging 10 cm and 30 cm to invent a 20 cm observation). | [ ] |
| **3.5** | **Independent Profiles** | Multi-depth probes at the same site logged as distinct sensor streams, not merged into a single bulk variable. | [ ] |

---

### Dimension 4: Measurement Modality & Footprint Classification
| Item | Requirement | Verification Criterion | Status Check |
| :---: | :--- | :--- | :---: |
| **4.1** | **Modality Explicitly Labeled** | Labeled as `Point Measurement`, `Layer-Average`, or `CRNS Area-Integrated`. | [ ] |
| **4.2** | **Point Sensor Footprint** | FDR / TDR / Capacitive probes: point measurement ($\sim 5\text{--}10\text{ cm}$ cylinder). Compatible with Model 1 point models. | [ ] |
| **4.3** | **CRNS Footprint Isolation** | Cosmic-ray neutron probes: $\sim 200\text{ m}$ radius footprint with vertically weighted dynamic depth. **Must NOT be evaluated as a discrete point sensor without a forward neutron moderation operator.** | [ ] |
| **4.4** | **Sensor Make & Model** | Instrument make, model, and measurement physics documented (e.g., Campbell CS655, Stevens HydraProbe, Decagon 5TE, CRS-2000B). | [ ] |

---

### Dimension 5: Station Coordinates & Spatial Verification
| Item | Requirement | Verification Criterion | Status Check |
| :---: | :--- | :--- | :---: |
| **5.1** | **Geodetic Datum** | WGS-84 (EPSG:4326) coordinate reference system. | [ ] |
| **5.2** | **Spatial Tolerance Check** | Latitude and longitude match the SoilDepth-AI station registry within $\le 0.05^\circ$ ($\sim 5\text{ km}$). | [ ] |
| **5.3** | **Elevation Consistency** | Station benchmark elevation matches within physical topography bounds ($\pm 35\text{ m}$ vs Copernicus DEM 30m). | [ ] |
| **5.4** | **Fixed Location** | Probes are stationary; coordinates do not drift across observation timestamps. | [ ] |

---

### Dimension 6: Quality Flags & Anomaly Screening
| Item | Requirement | Verification Criterion | Status Check |
| :---: | :--- | :--- | :---: |
| **6.1** | **Standard Quality Codes** | Flags map to: `GOOD`, `SUSPECT`, `CALIBRATION_PERIOD`, `OUT_OF_BOUNDS`, `SENSOR_MALFUNCTION`, `FROZEN_SOIL`, `MISSING`. | [ ] |
| **6.2** | **Anti-Fabrication Check** | **ZERO records flagged `SYNTHETIC`, `INTERPOLATED`, `SIMULATED`, or `MODELLED`.** | [ ] |
| **6.3** | **Spike Detection** | Sudden hourly jumps $|\Delta \theta| > 0.15\text{ m}^3/\text{m}^3$ without accompanying precipitation flagged `SUSPECT`. | [ ] |
| **6.4** | **Flatline Detection** | Unvarying constant reading for $> 14$ consecutive days during active drying cycles flagged `SENSOR_MALFUNCTION`. | [ ] |
| **6.5** | **Voltage / Diagnostic Flags** | Low sensor battery voltage ($< 3.2\text{ V}$) or open-circuit telemetry flagged `SUSPECT`. | [ ] |

---

### Dimension 7: Missingness & Training Sufficiency Benchmark
| Item | Requirement | Verification Criterion | Status Check |
| :---: | :--- | :--- | :---: |
| **7.1** | **Explicit Null Decoding** | Null values (`NaN`, `-9999`, `-999.0`, empty strings) decoded cleanly to IEEE NaN. | [ ] |
| **7.2** | **Coverage Proportion** | Overall temporal completeness percentage calculated per sensor depth. | [ ] |
| **7.3** | **Consecutive Gap Analysis** | Longest continuous missing streak identified and documented. | [ ] |
| **7.4** | **Training Sufficiency Gate** | **$\ge 180$ valid daily observations per depth.** If unique valid observation days $< 180$, depth model training is blocked. | [ ] |
| **7.5** | **Cryptographic Fingerprint** | Raw dataset hashed with SHA-256 and registered in the acquisition manifest. | [ ] |

---

## 3. Data Receipt Audit Sign-Off Form

```
================================================================================
SOILDEPTH-AI IN-SITU DATA RECEIPT & VERIFICATION AUDIT FORM
================================================================================
Request ID:              [ e.g. SOILDEPTH-REQ-2026-003 ]
Institution:             [ e.g. MPKV Rahuri / CAAST-CSAWM ]
Station ID:              [ e.g. MPKV-RAHURI-CAAST ]
Raw Data File(s):        [ e.g. Rahuri_PSMISS_2017_2023.csv ]
Raw File SHA-256:        [ 64-character hex hash ]
Date Received:           [ YYYY-MM-DD ]
Auditor Name / Role:     [ Senior Geospatial Data Engineer ]

QUALITY GATE VERDICTS:
  Gate 1 (Timestamps):        [ PASS / FAIL / PENDING ]
  Gate 2 (Units & Bounds):    [ PASS / FAIL / PENDING ]
  Gate 3 (Sensor Depths):     [ PASS / FAIL / PENDING ]
  Gate 4 (Modality):          [ PASS / FAIL / PENDING ]
  Gate 5 (Coordinates):       [ PASS / FAIL / PENDING ]
  Gate 6 (Quality Flags):     [ PASS / FAIL / PENDING ]
  Gate 7 (Sufficiency >=180d):[ PASS / FAIL / PENDING ]

OVERALL VERIFICATION VERDICT:
  [  ] ACCEPTED & VERIFIED  -> Promote to dataset/Maharashtra/ground_truth/verified/
  [  ] CONDITIONAL ACCEPT   -> Minor format remapping required (No data altered)
  [  ] REJECTED             -> Violates physical integrity / synthetic data detected

Auditor Signature: _______________________ Date: ______________
================================================================================
```
