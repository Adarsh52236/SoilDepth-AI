# IIT Kanpur ISMN In Situ Dataset (`IIT_KANPUR`)

This directory houses the in situ soil moisture observational data downloaded from the International Soil Moisture Network (ISMN) for the **IIT_KANPUR** network in India.

---

## 1. Directory Structure

```text
IIT_KANPUR/
├── README.md
├── raw/                               # Unprocessed downloaded ZIP archives
├── extracted/                         # Extracted ISMN station datasets by depth query
│   ├── surface_0-10cm/                # Extracted from ISMN depth query 0.0–10.0 cm
│   │   └── IIT_KANPUR/
│   │       └── IITK-Airstrip/
│   │           ├── ..._sm_0.100000_0.100000_...stm  (10 cm sensor)
│   │           └── ..._static_variables.csv
│   ├── middle_10-30cm/                # Extracted from ISMN depth query 10.0–30.0 cm
│   │   └── IIT_KANPUR/
│   │       └── IITK-Airstrip/
│   │           ├── ..._sm_0.100000_0.100000_...stm  (10 cm sensor)
│   │           ├── ..._sm_0.250000_0.250000_...stm  (25 cm sensor)
│   │           └── ..._static_variables.csv
│   └── deep_30-60cm/                  # Extracted from ISMN depth query 30.0–60.0 cm
│       └── IIT_KANPUR/
│           └── IITK-Airstrip/
│               ├── ..._sm_0.500000_0.500000_...stm  (50 cm sensor)
│               └── ..._static_variables.csv
└── audit/                             # Audit artifacts and inspection logs for IIT_KANPUR
```

---

## 2. Station and Sensor Metadata

- **Network ID:** `IIT_KANPUR`
- **Station ID / Name:** `IITK_Airstrip` (`IITK-Airstrip`)
- **Country / State:** India / Uttar Pradesh (Indo-Gangetic Plain)
- **Geographic Coordinates:**
  - Latitude: `26.51881° N`
  - Longitude: `80.23303° E`
  - Elevation: `123.444 m`
- **Regional Note:** Located ~750+ km north of Maharashtra. Zero stations exist in Maharashtra.
- **Sensor Hardware:** `Spectrum-WaterScoutSM100` (capacitance-based point sensors).
- **Measurement Support:** Point sensor (`point_sensor`).
- **Physical Soil Parameters (HWSD v1.1):**
  - Soil Type: Loam (0–30 cm: 42% Sand, 36% Silt, 22% Clay; 30–100 cm: 40% Sand, 35% Silt, 25% Clay).
  - Saturation Capacity ($VWC_{sat}$): $0.44\text{ m}^3/\text{m}^3$.

---

## 3. Observation Summary & Audit Findings

| Depth | Nominal Depth ($cm$) | Total Observations | Observation Period (UTC) | Quality Flag | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0.10 m** | 10.0 cm | 11,280 | 2011-06-16 13:00 to 2012-11-22 05:00 | 100% `G` (Good) | Duplicated in both `surface_0-10cm/` and `middle_10-30cm/` |
| **0.25 m** | 25.0 cm | 11,282 | 2011-06-16 13:00 to 2012-11-22 05:00 | 100% `G` (Good) | Unique to `middle_10-30cm/` |
| **0.50 m** | 50.0 cm | 10,175 | 2011-06-16 13:00 to 2012-11-22 05:00 | 100% `G` (Good) | Unique to `deep_30-60cm/` |

### Key Model-Readiness Constraints:
1. **No 5 cm Surface Proxy:** The `surface_0-10cm/` folder contains only a 10 cm sensor. There is no 5 cm sensor installed at this station.
2. **Cross-Folder Redundancy:** The 10 cm file in `surface_0-10cm/` is 100% identical to the 10 cm file in `middle_10-30cm/`.
3. **Temporal Scope vs. Satellites:** Active period is June 2011 – November 2012, completely preceding Sentinel-1 (2014), Sentinel-2 (2015), and SMAP (2015). Overlap is **0.0%**.
4. **Historical Reanalysis:** Suitable for ERA5-Land reanalysis weather-driven water-balance baselines (1950–present).
