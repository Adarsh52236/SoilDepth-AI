# SoilDepth-AI — Maharashtra Multi-Crop Agronomic Registry & Metadata Architecture

**Version:** 1.0.0  
**Status:** Approved Agronomic Baseline  
**Geographic Domain:** Maharashtra State, India  
**Standard Reference:** FAO Irrigation and Drainage Paper No. 56 (Allen et al., 1998) & ICAR Agronomic Compendia  

---

## 1. Architectural Purpose and Principles

SoilDepth-AI's root-zone soil moisture (RZSM) reconstruction framework requires rigorous agronomic characterization across Maharashtra's agro-ecological zones (Konkan coastal, Western Ghats / Sahyadri transition, Western Maharashtra plateau, Marathwada semi-arid plateau, and Vidarbha heavy Vertisol plains).

### Core Architectural Principles:
1. **Target Separation:** Crop metadata (phenology, root development, crop coefficients) are strictly maintained as exogenous agronomic contextual priors. They are never conflated with observed physical soil moisture targets ($\text{m}^3/\text{m}^3$).
2. **Ground-Sensor Independence:** Crop metadata inform root depth thresholds ($Z_r$) and depletion fractions ($p$), enabling root-zone water-stress modeling without requiring in-situ telemetry at ungauged candidate fields.
3. **Evidence-Based Assignment:** Crops are never assigned to a station or pilot catchment without empirical documentation from regional State Agricultural Universities (SAUs: MPKV Rahuri, PDKV Akola, VNMKV Parbhani, BSKKV Dapoli) or ICAR commodity institutes.
4. **Soil-Plant-Atmosphere Continuum (SPAC):** Root growth dynamics directly dictate the depth interval over which transpirational suction depletes soil water from field capacity ($\theta_{FC}$) toward the permanent wilting point ($\theta_{WP}$).

---

## 2. Maharashtra Crop Registry

The registry covers the ten dominant commercial, foodgrain, and pulse crops of Maharashtra state, representing >85% of gross cropped area.

| Crop ID | Common Name | Botanical Name | Season | Sowing Window | Growing Period | Effective Root Depth ($Z_{r,\text{eff}}$) | Max Root Depth ($Z_{r,\text{max}}$) | FAO $K_{c,\text{ini}}$ | FAO $K_{c,\text{mid}}$ | FAO $K_{c,\text{end}}$ | Depletion $p$ | Dominant Soil |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `CROP-SOYBEAN` | Soybean | *Glycine max* | Kharif | Jun 15 – Jul 15 | 95–110 d | 30–50 cm | 60–100 cm | 0.40 | 1.15 | 0.50 | 0.50 | Clay loam / Deep Vertisol |
| `CROP-COTTON` | Cotton | *Gossypium spp.* | Kharif / Semi-perennial | Jun 15 – Jul 10 | 150–180 d | 50–90 cm | 120–180 cm | 0.35 | 1.20 | 0.65 | 0.65 | Deep black Vertisol |
| `CROP-RICE` | Lowland Rice | *Oryza sativa* | Kharif | Jun 05 – Jul 20 | 110–135 d | 20–40 cm | 50–60 cm | 1.05 | 1.20 | 0.90 | 0.20 | Clay / Lateritic valley |
| `CROP-WHEAT` | Wheat | *Triticum aestivum* | Rabi | Nov 01 – Nov 25 | 105–120 d | 40–70 cm | 90–120 cm | 0.40 | 1.15 | 0.40 | 0.55 | Medium to deep Vertisol |
| `CROP-SUGARCANE` | Sugarcane | *Saccharum officinarum* | Perennial (Adsali/Suru) | Jul–Aug / Jan–Feb | 360–450 d | 50–80 cm | 120–150 cm | 0.40 | 1.25 | 0.75 | 0.65 | Heavy clay loam |
| `CROP-MAIZE` | Maize | *Zea mays* | Kharif & Rabi | Jun 15 / Oct 15 | 95–115 d | 40–60 cm | 80–120 cm | 0.40 | 1.20 | 0.60 | 0.55 | Well-drained sandy/clay loam |
| `CROP-CHICKPEA` | Chickpea | *Cicer arietinum* | Rabi | Oct 10 – Nov 10 | 90–105 d | 40–60 cm | 90–120 cm | 0.40 | 1.00 | 0.35 | 0.65 | Deep Vertisol (residual) |
| `CROP-PIGEONPEA` | Pigeon pea (Tur) | *Cajanus cajan* | Kharif / Residual | Jun 15 – Jul 10 | 150–180 d | 60–100 cm | 150–200 cm | 0.35 | 1.15 | 0.40 | 0.70 | Medium to deep Vertisol |
| `CROP-GROUNDNUT` | Groundnut | *Arachis hypogaea* | Kharif & Summer | Jun 20 / Jan 15 | 100–120 d | 30–50 cm | 60–90 cm | 0.40 | 1.15 | 0.60 | 0.50 | Sandy loam / Light Vertisol |
| `CROP-SORGHUM` | Grain Sorghum | *Sorghum bicolor* | Kharif & Rabi | Jun 20 / Sep 15 | 105–125 d | 50–80 cm | 120–150 cm | 0.35 | 1.10 | 0.55 | 0.65 | Medium to deep Vertisol |

---

## 3. Crop Profiles & Root-Zone Hydrology

### 3.1 Soybean (*Glycine max*)
- **Ecology & Distribution:** Primary oilseed of Marathwada and Vidarbha (Latur, Nanded, Akola, Amravati, Yavatmal).
- **Phenology & Growth Stages:**
  1. *Emergence and Early Vegetative (VE–V3):* 0–20 Days After Sowing (DAS), $Z_r \approx 10\text{--}20\text{ cm}$.
  2. *Rapid Vegetative (V4–R1):* 20–40 DAS, root expansion to $35\text{ cm}$.
  3. *Flowering & Pod Initiation (R1–R3):* 40–65 DAS, critical moisture sensitivity stage; peak transpirational suction ($K_c = 1.15$).
  4. *Pod Filling & Seed Development (R4–R6):* 65–85 DAS, $Z_r \approx 40\text{--}50\text{ cm}$.
  5. *Maturity & Senescence (R7–R8):* 85–105 DAS, leaf abscission, water uptake plummets ($K_c = 0.50$).
- **Rooting Profile & Soil Moisture Interaction:**
  - 80% of active root biomass resides in the top $0\text{--}40\text{ cm}$.
  - Highly susceptible to transient waterlogging in heavy smectitic Vertisols during high-intensity monsoon events. Aeration stress ($\text{air filled porosity} < 0.10\text{ cm}^3/\text{cm}^3$) halts symbiotic nitrogen fixation.
  - Severe drought during pod initiation ($R3$) triggers irreversible flower and pod abortion, dropping final yields by up to 60%.

### 3.2 Cotton (*Gossypium hirsutum / arboreum*)
- **Ecology & Distribution:** Keystone cash crop of Vidarbha and Marathwada (Yavatmal, Wardha, Jalgaon, Aurangabad).
- **Phenology & Growth Stages:**
  1. *Germination to Seedling:* 0–25 DAS, taproot elongates rapidly ($1.5\text{--}2.5\text{ cm/day}$), exceeding vegetative shoot height.
  2. *Squaring (Square formation):* 40–60 DAS, root depth $Z_r \approx 60\text{ cm}$.
  3. *Flowering and Boll Development:* 60–120 DAS, maximum canopy coverage ($K_c = 1.20$), peak root expansion ($Z_r \approx 90\text{--}150\text{ cm}$).
  4. *Boll Opening and Harvesting:* 120–180 DAS, declining transpirational demand ($K_c = 0.65$).
- **Rooting Profile & Soil Moisture Interaction:**
  - Possesses a deeply penetrating taproot capable of descending beyond $1.5\text{ m}$ in unconstrained deep Vertisols.
  - Scavenges subsoil moisture stored in the $60\text{--}120\text{ cm}$ profile during post-monsoon dry spells.
  - Moisture stress at peak flowering induces square and boll shedding through ethylene synthesis; excessive moisture causes vegetative rank growth and delays boll maturation.

### 3.3 Lowland Rice (*Oryza sativa*)
- **Ecology & Distribution:** Dominant crop in the high-rainfall Konkan coastal belt (Thane, Raigad, Ratnagiri, Sindhudurg) and eastern Vidarbha lake basin (Bhandara, Gondia).
- **Phenology & Growth Stages:**
  1. *Nursery Stage:* 0–25 DAS.
  2. *Transplanting to Tillering:* 25–55 DAT, root depth $Z_r \approx 15\text{--}25\text{ cm}$.
  3. *Panicle Initiation to Heading:* 55–85 DAT, critical moisture stage ($K_c = 1.20$).
  4. *Flowering to Milk/Dough Stage:* 85–110 DAT.
  5. *Maturity:* 110–130 DAT, drainage prior to harvest ($K_c = 0.90$).
- **Rooting Profile & Soil Moisture Interaction:**
  - Shallow, adventitious fibrous root system restricted to $0\text{--}30\text{ cm}$ due to mechanical resistance of the puddled hardpan (plow sole).
  - Maintained under saturated to shallow flooded hydrologic regimes ($1200\text{--}1400\text{ mm}$ total requirement); depletion fraction $p = 0.20$ reflects zero tolerance to soil water matric suction beyond $-20\text{ kPa}$.

### 3.4 Wheat (*Triticum aestivum*)
- **Ecology & Distribution:** Premier winter irrigated rabi foodgrain of Western Maharashtra and Marathwada (Pune, Ahmednagar, Nashik, Solapur).
- **Phenology & Growth Stages:**
  1. *Crown Root Initiation (CRI):* 21–25 DAS. **Highest sensitivity stage in life cycle.**
  2. *Tillering:* 25–45 DAS, seminal and nodal roots proliferate to $Z_r \approx 40\text{ cm}$.
  3. *Jointing & Booting:* 45–65 DAS.
  4. *Flowering & Anthesis:* 65–85 DAS, peak water consumption ($K_c = 1.15$).
  5. *Milk, Dough & Ripening:* 85–115 DAS, rapid decline in green leaf area ($K_c = 0.40$).
- **Rooting Profile & Soil Moisture Interaction:**
  - Effective root zone $40\text{--}70\text{ cm}$, with maximum extraction observed in the $0\text{--}60\text{ cm}$ layer.
  - Moisture deficit at CRI irreversibly curtails tiller number and spikelet development; water stress at grain filling accelerates senescence and causes grain shriveling under terminal heat stress ($>32^\circ\text{C}$).

### 3.5 Sugarcane (*Saccharum officinarum*)
- **Ecology & Distribution:** High-value perennial industrial crop across the canal-irrigated Krishna and Godavari basins (Kolhapur, Sangli, Satara, Ahmednagar, Pune).
- **Phenology & Growth Stages:**
  1. *Germination Phase:* 0–45 Days After Planting (DAP).
  2. *Formative / Tillering Phase:* 45–120 DAP. **Most critical stage for moisture deficit.**
  3. *Grand Growth Phase:* 120–270 DAP, rapid internode elongation, canopy closure ($K_c = 1.25$).
  4. *Maturity & Ripening Phase:* 270–360+ DAP, sucrose accumulation in stalk ($K_c = 0.75$).
- **Rooting Profile & Soil Moisture Interaction:**
  - High water requirement ($2000\text{--}2500\text{ mm/year}$).
  - Dense superficial root mat in upper $30\text{ cm}$, with deep anchor and feeder roots descending to $120\text{--}150\text{ cm}$.
  - Moisture deficit during formative phase permanently stunts cane diameter and stalk height; terminal drying (30–45 days before harvest) is standard practice to concentrate sucrose content.

### 3.6 Maize (*Zea mays*)
- **Ecology & Distribution:** Multi-season cereal grown widely in Nashik, Dhule, Jalgaon, and Kolhapur.
- **Phenology & Growth Stages:**
  1. *Early Vegetative (V1–V6):* 0–25 DAS.
  2. *Rapid Stem Elongation (V7–VT):* 25–55 DAS.
  3. *Tasseling & Silking (VT–R1):* 55–70 DAS. **Critical moisture stress window.**
  4. *Blister & Milk Stage (R2–R3):* 70–85 DAS ($K_c = 1.20$).
  5. *Dough, Dent & Maturity (R4–R6):* 85–110 DAS.
- **Rooting Profile & Soil Moisture Interaction:**
  - Fibrous root system concentrating 75% of water uptake in $0\text{--}60\text{ cm}$; maximum roots reach $100\text{--}120\text{ cm}$.
  - Severe water stress at silking delays silk emergence relative to pollen shed (anthesis-silking interval expansion), resulting in barren ears and yield crashes of 50–80%.
  - Extremely intolerant to water stagnation or soil hypoxia.

### 3.7 Chickpea (*Cicer arietinum*)
- **Ecology & Distribution:** Premier post-monsoon rabi pulse grown on residual moisture across the Deccan Plateau (Ahmednagar, Solapur, Beed, Osmanabad).
- **Phenology & Growth Stages:**
  1. *Emergence & Seedling:* 0–20 DAS.
  2. *Branching (Vegetative):* 20–45 DAS, $Z_r \approx 30\text{--}40\text{ cm}$.
  3. *Pre-Flowering & Pod Initiation:* 45–70 DAS, peak moisture consumption ($K_c = 1.00$).
  4. *Pod Development & Maturity:* 70–100 DAS, profile depletion, senescence ($K_c = 0.35$).
- **Rooting Profile & Soil Moisture Interaction:**
  - Deep, well-nodulated taproot system ($90\text{--}120\text{ cm}$) that extracts retreating moisture envelopes in shrinking Vertisols.
  - Grown almost exclusively without canal irrigation; 1–2 protective irrigations at branching and early pod fill optimize seed index.
  - Highly prone to collar rot (*Sclerotium rolfsii*) and dry root rot under excessive surface irrigation or poorly drained micro-depressions.

### 3.8 Pigeon pea / Tur (*Cajanus cajan*)
- **Ecology & Distribution:** Long-duration kharif pulse, typically intercropped with cotton or soybean across Vidarbha and Marathwada.
- **Phenology & Growth Stages:**
  1. *Slow Vegetative Phase:* 0–60 DAS, modest shoot development while taproot establishes downward.
  2. *Active Branching & Canopy Expansion:* 60–100 DAS.
  3. *Flower Bud Initiation & Flowering:* 100–135 DAS ($K_c = 1.15$).
  4. *Pod Formation & Maturation:* 135–170 DAS, deep extraction continues after companion kharif crops have been harvested.
- **Rooting Profile & Soil Moisture Interaction:**
  - Extremely hardy, deep taproot penetrating $150\text{--}200\text{ cm}$, breaking through subsoil clay pans.
  - High allowable depletion fraction ($p = 0.70$); capable of sustained extraction at high soil matric suction (down to $-1500\text{ kPa}$).
  - Waterlogging for $>48\text{ hours}$ induces phytophthora blight and wilt mortality.

### 3.9 Groundnut (*Arachis hypogaea*)
- **Ecology & Distribution:** Important oilseed grown in Kharif (Dhule, Nandurbar) and Summer irrigated (Kolhapur, Satara, Solapur).
- **Phenology & Growth Stages:**
  1. *Vegetative Phase:* 0–25 DAS.
  2. *Flowering & Pegging:* 25–50 DAS. **Critical window: pegs must penetrate soil.**
  3. *Pod Formation:* 50–85 DAS, intense underground sink activity ($K_c = 1.15$).
  4. *Pod Maturity:* 85–115 DAS ($K_c = 0.60$).
- **Rooting Profile & Soil Moisture Interaction:**
  - Effective root zone $30\text{--}50\text{ cm}$, maximum $80\text{ cm}$.
  - Requires friable, moist topsoil ($0\text{--}10\text{ cm}$) for gynophore (peg) penetration. If surface soil is dry and hard-crusted, pegs fail to penetrate, forming no pods ("blind nuts").
  - Moisture stress during pod development arrests calcium mobility, producing hollow shells ("pops").

### 3.10 Grain Sorghum / Jowar (*Sorghum bicolor*)
- **Ecology & Distribution:** Traditional drought-hardy cereal of the rain-shadow drought-prone tract (Solapur, Ahmednagar, Sangli, Osmanabad). Both Kharif and Rabi (Maldandi M-35-1).
- **Phenology & Growth Stages:**
  1. *Early Vegetative:* 0–25 DAS.
  2. *Panicle Initiation:* 25–45 DAS.
  3. *Booting & Flowering:* 45–70 DAS ($K_c = 1.10$).
  4. *Grain Filling (Milk to Dough):* 70–95 DAS.
  5. *Physiological Maturity:* 95–120 DAS ($K_c = 0.55$).
- **Rooting Profile & Soil Moisture Interaction:**
  - C4 photosynthetic efficiency and dense lateral root network branching throughout $0\text{--}80\text{ cm}$ and descending to $150\text{ cm}$.
  - Rabi Maldandi is grown entirely on post-monsoon stored soil water in deep Vertisols ($>90\text{ cm}$ depth) without supplemental irrigation.
  - Osmotic adjustment and leaf rolling mechanisms allow the crop to withstand extended dry spells with $p = 0.65$.

---

## 4. FAO-56 Evapotranspiration Integration

SoilDepth-AI utilizes the FAO-56 dual crop coefficient approach to model crop evapotranspiration ($ET_c$) and root-zone water depletion:

$$ET_c = (K_{cb} + K_e) \cdot ET_0$$

Where:
- $K_{cb}$ is the basal crop coefficient representing plant transpiration.
- $K_e$ is the soil surface evaporation coefficient ($0\text{--}10\text{ cm}$ evaporative zone).
- $ET_0$ is the reference evapotranspiration calculated via the FAO Penman-Monteith equation using ERA5-Land surface meteorology.

When root-zone moisture drops below the critical threshold ($RAW = p \cdot TAW$), transpiration is throttled by the stress coefficient $K_s$:

$$K_s = \frac{TAW - D_r}{TAW - RAW} = \frac{TAW - D_r}{(1 - p) \cdot TAW}$$

Where:
- $TAW = 1000 \cdot (\theta_{FC} - \theta_{WP}) \cdot Z_r$ is Total Available Water in the root zone (mm).
- $RAW = p \cdot TAW$ is Readily Available Water (mm).
- $D_r$ is the root-zone moisture depletion (mm).

This framework mathematically couples SoilGrids hydraulic parameters ($\theta_{FC}$, $\theta_{WP}$), ERA5-Land atmospheric evaporative demand ($ET_0$), and the crop registry root profiles ($Z_r$, $p$).
