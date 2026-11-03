# Formal Academic Data Requisition: Maharashtra PoCRA PMU

**Document Reference:** `SOILDEPTH-REQ-2026-005`  
**Date of Drafting:** November 3, 2026  
**Status:** `DRAFTED_NOT_SENT` (Pending Institutional Submission)  
**Target Institution:**  
Project Management Unit (PMU), Project on Climate Resilient Agriculture (PoCRA)  
Department of Agriculture, Government of Maharashtra  
(World Bank Assisted Project)  
Makarand Sahakari Gruhanirman Sanstha, Senapati Bapat Marg, Dadar (West), Mumbai – 400028, Maharashtra, India  

**Recipient Designation:**  
State Project Director, PoCRA  
Department of Agriculture, Government of Maharashtra  
*Attention:* IT & Geoinformatics Specialist / Agronomy and Climate Resilient Technologies Cell  

---

### Subject: Request for Micro-Watershed Soil Moisture Monitoring Sensor Data for Academic Research on Drought Resilience and Protective Irrigation (SoilDepth-AI Project)

Respected Sir/Madam,

We write to respectfully request access to automated soil moisture telemetry records collected under the World Bank-assisted **Project on Climate Resilient Agriculture (PoCRA - Nanaji Deshmukh Krishi Sanjivani Prakalp)**, implemented by the Department of Agriculture, Government of Maharashtra.

#### 1. Context and Academic Motivation
The **SoilDepth-AI** project is an academic research initiative developing artificial intelligence models to predict vertical root-zone soil moisture ($0\text{--}60\text{ cm}$) across drought-vulnerable smallholder farming regions of Maharashtra. The project aims to provide high-resolution hydrological intelligence to optimize protective irrigation scheduling and mitigate agricultural drought.

The PoCRA project has established automated soil moisture and weather monitoring networks across drought-prone micro-watersheds in Marathwada and Vidarbha. Access to IoT soil moisture data from representative agrarian clusters will enable rigorous cross-validation of satellite-derived soil moisture algorithms in real-world farmer fields cultivating cotton, soybean, pigeon pea, and maize.

#### 2. Target Observation Clusters Requested
We specifically request time-series data from automated IoT monitoring clusters in two prominent rain-shadow districts:
1. **Cluster A: Amravati District (`POCRA-AMRAVATI-DARYAPUR`)**
   - Location: Daryapur / Bhatkuli micro-watershed cluster (Cotton & Soybean Vertisol plain)
   - Coordinates: Approximately $20.9254^\circ\text{ N}$, $77.3142^\circ\text{ E}$ (elevation $\sim 288\text{ m}$ AMSL)
2. **Cluster B: Jalna District (`POCRA-JALNA-BADNAPUR`)**
   - Location: Badnapur / Ambad micro-watershed cluster (Marathwada dryland plateau)
   - Coordinates: Approximately $19.8651^\circ\text{ N}$, $75.8824^\circ\text{ E}$ (elevation $\sim 512\text{ m}$ AMSL)

#### 3. Requested Historical Observation Period
- **Start Date:** January 1, 2019 (`2019-01-01T00:00:00Z`)
- **End Date:** December 31, 2023 (`2023-12-31T23:59:59Z`)
- **Duration:** 5 continuous operational years (or available duration of project telemetry)

#### 4. Specific Parameters Requested
1. **Multi-Depth Soil Moisture Observations:**
   - Volumetric soil water content ($\text{m}^3/\text{m}^3$ or % VWC) at installed probe depths:
     - Shallow root zone: $10\text{ cm}$
     - Mid root zone: $20\text{ cm}$
     - Deep root zone: $40\text{ cm}$ (or actual probe array depths).
   - Frequency: Daily average or hourly time series.
2. **Auxiliary Automatic Weather Station (AWS) Measurements:**
   - Daily accumulated rainfall (mm), minimum and maximum temperature ($^\circ\text{C}$), relative humidity (%), and wind speed.
3. **Cluster Metadata:**
   - Sensor type and make (capacitance / frequency domain reflectometry probe specifications).
   - Soil series and texture classification of the sensor installation plots.
   - Sensor quality flags (e.g. data transmission errors, battery dropouts, or probe recalibration periods).

#### 5. Preferred Format & Access Route
- Structured tabular data (CSV, Microsoft Excel `.xlsx`), JSON export, or secure read-only REST API access to the PoCRA database gateway.
- Explicit UTC or Indian Standard Time (IST) timestamps.

#### 6. Academic Licensing, Attribution & Compliance Terms
We affirm that:
1. The requested data will be utilized **strictly for non-commercial academic research, open algorithmic benchmarking, and scientific dissertation work**.
2. No data will be shared with commercial or private third parties.
3. The Government of Maharashtra, the PoCRA Project Management Unit, and the World Bank initiative will be **prominently acknowledged and cited** in all publications, technical reports, and public research documentation.
4. We are fully prepared to enter into a formal **Academic Research Undertaking / Data Use Agreement** with the PoCRA PMU.
5. All research findings, predictive models, and validation benchmarks will be shared openly with the PoCRA PMU to support state-level agricultural resilience planning.

We respectfully request your approval to provide the requested telemetry extracts.

Sincerely,

**SoilDepth-AI Research Team**  
*Project Lead & Senior Geospatial ML Engineering Group*  
Academic Machine Learning & Hydrological Remote Sensing Initiative  
Contact: `project@soildepth-ai.org`
