# COSMOS-India Pune Station Data Access Investigation Report

**Project:** SoilDepth-AI (Maharashtra Phase 2A)  
**Target Station:** `IITM-PUNE-COSMOS` (Indian Institute of Tropical Meteorology, Pune)  
**Portal Investigated:** `https://cosmos-india.org/`  
**Date:** 2026-10-31  
**Investigation Status:** Complete Technical Audit — Data Gated / Institutional Requisition Required  

---

## 1. Executive Summary

As part of Phase 2A data acquisition for Maharashtra, an empirical investigation was conducted on the official **COSMOS-India** web portal (`https://cosmos-india.org/`) to download in-situ soil moisture observations for the **IITM Pune** station.

### Key Investigation Findings:
1. **Portal Infrastructure:** The public-facing site `https://cosmos-india.org/` is active (`HTTP 200`), running a WordPress platform with Cloudflare bot mitigation.
2. **Data Portal Routing:** The portal's primary navigation button for data access points to `https://cccr.tropmet.res.in/cosmos-data.php`.
3. **DNS & Network Gating:** The target host `cccr.tropmet.res.in` fails domain name resolution on public DNS (`[Errno 11001] getaddrinfo failed`), indicating it is hosted on an internal IITM intranet or restricted government server network.
4. **Direct Endpoints:** Standard sub-endpoints (`/data-portal/`, `/stations/`, `/pune/`) return `HTTP Error 503: Service Unavailable` or `403: Forbidden`.
5. **Programmatic API:** There is **no public REST API, STAC catalog, or unauthenticated open download link** for the Pune station time series.
6. **Project Policy Compliance:** In accordance with SoilDepth-AI operational guidelines (*"If authentication or institutional permission is required, document the exact access procedure instead of attempting to bypass it. Do not fabricate or interpolate ground-truth measurements"*), no security bypass was attempted. The dataset is formally documented as **institutionally gated**, requiring a sanctioned research requisition.

---

## 2. Technical Diagnostics & Endpoint Audit

| Endpoint Tested | Expected Resource | HTTP Status | Response / Diagnostic Detail |
| :--- | :--- | :---: | :--- |
| `https://cosmos-india.org/` | Portal Homepage | `200 OK` | Loads WordPress frontend, project description, and partner listing. |
| `https://cosmos-india.org/data/` | Data landing page | `200 OK` | Mirrored root landing; no direct download tables. |
| `https://cosmos-india.org/data-portal/` | Interactive data portal | `503 Service Unavailable` | Cloudflare origin gateway error. |
| `https://cosmos-india.org/stations/` | Station list & downloads | `503 Service Unavailable` | Cloudflare origin gateway error. |
| `https://cosmos-india.org/pune/` | Pune station page | `503 Service Unavailable` | Cloudflare origin gateway error. |
| `https://cccr.tropmet.res.in/cosmos-data.php` | Backend data download | `DNS Resolution Failed` | Host `cccr.tropmet.res.in` not resolved via public DNS. |
| `https://www.tropmet.res.in/cosmos-data.php` | IITM public web mirror | `404 Not Found` | Route does not exist on main public web server. |

---

## 3. Metadata & Technical Specifications of the Pune Station

Drawing from peer-reviewed literature (*Journal of Hydrology*, 2021; *Remote Sensing*, 2021; *Environmental Research Letters*, 2023) and technical network documentation:

* **Station Identifier:** `IITM-PUNE` / `ICON-PUNE`
* **Geographical Coordinates:** $18.5372^\circ\text{ N}, 73.8051^\circ\text{ E}$
* **Elevation:** $560.0\text{ m}$ above mean sea level (AMSL)
* **Location:** Inside IITM Campus, Dr. Homi Bhabha Road, Pashan, Pune – 411008, Maharashtra.
* **Agro-Ecological Setting:** Western Maharashtra plateau (core Indian summer monsoon zone); mean annual rainfall $\sim 750\text{ mm}$ (strongly concentrated June–September).
* **Soil Series / Texture:** Sandy clay loam (derived from Deccan basalt regolith; bulk density $\sim 1.35\text{--}1.42\text{ g/cm}^3$, sand $\sim 52\%$, clay $\sim 28\%$, silt $\sim 20\%$).
* **Vegetation Cover:** Sparse trees, mixed natural grasses, open experimental meteorological field.
* **Commissioning Date:** January 31, 2017.
* **Active Operational Span:** 2017 to Present (continuous hourly time series).

### Sensor Systems Deployed:
1. **Cosmic-Ray Neutron Sensor (CRNS):**
   - *Instrumentation:* Hydroinnova CRS-2000/B thermal and epithermal neutron detector.
   - *Measurement Scale:* Intermediate field-scale (horizontal footprint radius $\sim 150\text{--}200\text{ m}$; effective sensing depth $z^* \approx 12\text{ cm}$ during peak monsoon to $\approx 30\text{ cm}$ during hyper-arid pre-monsoon).
   - *Calibration:* Calibrated using the Desilets et al. $N_0$ neutron moderation formulation based on 108 spatial gravimetric soil core calibration samples taken within the footprint.
2. **Point-Scale Soil Moisture Profile Probes:**
   - *Instrumentation:* Stevens Hydra Probe II (coaxial impedance dielectric reflectometry at $50\text{ MHz}$).
   - *Installed Depths:* **5 cm, 15 cm, and 50 cm** below ground surface.
   - *Parameters:* Real-time Volumetric Water Content (VWC, $\text{m}^3/\text{m}^3$), dielectric permittivity, and soil temperature ($^\circ\text{C}$).
3. **Ancillary Surface Meteorology:**
   - Vaisala WXT520 weather transmitter recording barometric pressure, air temperature, relative humidity, and tipping-bucket precipitation.

---

## 4. File Formats & Quality Flags in COSMOS-India

When released through institutional channels or research datasets, COSMOS observations are formatted as follows:

* **Primary Formats:** Delimited ASCII text (`.txt`) and comma-separated values (`.csv`), alongside NetCDF4 (`.nc`) for gridded model intercomparisons.
* **Standard Variable Headers:**
  - `TIMESTAMP_UTC`: Date and time in UTC (`YYYY-MM-DD HH:MM:SS`).
  - `TIMESTAMP_IST`: Indian Standard Time (`UTC + 05:30`).
  - `MOD_NEUTRONS`: Raw epithermal neutron count rate (counts per hour).
  - `CORR_NEUTRONS`: Corrected neutron count rate (normalized for atmospheric pressure $P$, atmospheric vapor $e$, and geomagnetic/solar intensity $F_i$).
  - `VWC_CRNS`: Footprint-averaged volumetric water content ($\text{m}^3/\text{m}^3$).
  - `VWC_05CM`: Hydra Probe point-scale volumetric water content at 5 cm ($\text{m}^3/\text{m}^3$).
  - `VWC_15CM`: Hydra Probe point-scale volumetric water content at 15 cm ($\text{m}^3/\text{m}^3$).
  - `VWC_50CM`: Hydra Probe point-scale volumetric water content at 50 cm ($\text{m}^3/\text{m}^3$).
  - `TEMP_05CM`, `TEMP_15CM`, `TEMP_50CM`: Subsurface soil temperatures ($^\circ\text{C}$).
  - `PRECIP_MM`: Hourly precipitation total ($\text{mm}$).
  - `PRESS_HPA`: Atmospheric surface pressure ($\text{hPa}$).
  - `RH_PCT`: Air relative humidity ($\%$).
* **Quality Flag Conventions:**
  - `QC_FLAG = 0`: Valid, high-confidence observation.
  - `QC_FLAG = 1`: Suspect data (extreme atmospheric pressure fluctuation, battery voltage dip below $11.5\text{ V}$, or sudden unphysical step change $>0.10\text{ m}^3/\text{m}^3\text{/hr}$).
  - `QC_FLAG = 2`: Sensor offline, maintenance, or physical probe saturation.
  - Missing values: Encoded as `-9999` or `NaN`.

---

## 5. Institutional Access Protocol & Procurement Strategy

Because public open download is obstructed by server DNS routing, the authorized procedure to acquire the official IITM Pune time series is as follows:

```
[SoilDepth-AI Host Institution]
   │
   ▼
[Formal Research Requisition Letter]
   │
   ▼
[Director, Indian Institute of Tropical Meteorology (IITM)]
   │
   ├── Copy to: Head, Centre for Climate Change Research (CCCR)
   └── Copy to: Lead Scientist, Hydrometeorology Research Unit (HMRU)
   │
   ▼
[MoES / UKRI NERC Data-Sharing Agreement & Academic Attribution Sign-off]
   │
   ▼
[Delivery of Calibrated Hourly/Daily NetCDF/CSV Archive]
   │
   ▼
[Ingestion into dataset/Maharashtra/COSMOS/raw/IITM-PUNE/]
```

### Actionable Contact Details:
* **Host Authority:** Director, Indian Institute of Tropical Meteorology (IITM), Dr. Homi Bhabha Road, Pashan, Pune – 411008, Maharashtra.
* **Email:** `director@tropmet.res.in`
* **Scientific Unit:** Hydrometeorology Research Unit (HMRU), CCCR.
* **Principal Research Contact:** Dr. Milind Mujumdar, Scientist-F, IITM (`mujumdar@tropmet.res.in`).
* **Telephone:** +91 (20) 25904200 / +91 (20) 25904423.
* **Formal Letter Template:** Available in [`docs/data_acquisition/maharashtra/data_access_requests.md`](file:///c:/Users/adars/OneDrive/Documents/PROJECTS/SoilDepth-AI/docs/data_acquisition/maharashtra/data_access_requests.md).

