# REALITY SCULPTOR — GEOSPATIAL DATA PROVENANCE & MANIFEST SPECIFICATION
**Version:** 2.0.0 (Rebuild Directive Compliant)  
**Verification Level:** Rigorous Geospatial Grounding  
**Authoritative Provenance Tiers:** OBSERVED | DERIVED | ESTIMATED | SIMULATED | UNKNOWN

---

## 1. Data Governance Principles

Reality Sculptor enforces an absolute **Zero-Fabrication Policy**.
- Every spatial coordinate, building polygon, elevation height, pipe diameter, and precipitation value must link directly to an immutable source record or be tagged explicitly as `UNKNOWN`.
- If a data layer is inaccessible due to government registration or private credentials, it is marked as `REQUIRES_ACCESS`. Under no circumstances is dummy data substituted and presented as authentic observed data.

---

## 2. Public Dataset Registry & Provenance Details

### 2.1 OpenStreetMap (OSM) / Geofabrik Extracts
- **Source:** OpenStreetMap Contributors & Geofabrik GmbH ([Download Server](https://download-ext2.geofabrik.de/asia/india.html))
- **License:** Open Database License (ODbL) 1.0
- **Acquired Layers:**
  - `buildings`: Footprints, building classifications, floor counts (`building:levels`), height tags.
  - `highways`: Centerlines, lanes, road class (`motorway`, `primary`, `secondary`, `residential`), bridge markers.
  - `waterways`: River centerlines, canal banks, drainage channels, detention basins.
- **Provenance Category:** **OBSERVED**
- **Status in Engine:** **ACTIVE** (`data/raw/` and `data/processed/`)
- **Coverage:** Houston Medical Center (US), Chennai Velachery (India), Guwahati Central (India).

### 2.2 Overture Maps Foundation
- **Source:** Overture Maps Foundation (Linux Foundation: Amazon, Meta, Microsoft, TomTom) ([Overture Docs](https://docs.overturemaps.org/getting-data/))
- **License:** CDLA Permissive v2.0
- **Acquired Themes:** Transportation network segment topologies and 3D building outlines with standardized schema.
- **Provenance Category:** **OBSERVED**
- **Status in Engine:** **ACTIVE** (Direct bounding box query extract)

### 2.3 Microsoft Global ML Building Footprints
- **Source:** Microsoft Corporation ([GitHub Repository](https://github.com/microsoft/globalmlbuildingfootprints))
- **License:** CDLA Permissive 2.0
- **Coverage:** Worldwide automated building footprint segmentations extracted from satellite imagery.
- **Provenance Category:** **DERIVED (ML-Segmented Satellite Observations)**
- **Status in Engine:** **ACTIVE**

### 2.4 Copernicus Digital Elevation Model (COP-DEM GLO-30 / GLO-90)
- **Source:** European Space Agency (ESA) & Airbus Defence and Space ([Copernicus Data Space](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM))
- **Resolution:** 30-meter global raster grid (GLO-30) and 90-meter global raster (GLO-90).
- **Format:** Cloud Optimized GeoTIFF (COG)
- **Variables:** Orthometric heights referenced to EGM2008 geoid.
- **Provenance Category:** **OBSERVED / INTERPOLATED**
- **Status in Engine:** **ACTIVE** (Local terrain tiles cached in `data/raw/elevation/`)

### 2.5 NASA Global Precipitation Measurement (GPM) IMERG
- **Source:** NASA Goddard Earth Sciences Data and Information Services Center (GES DISC) ([CMR Earthdata](https://cmr.earthdata.nasa.gov/search/site/collections/directory/GES_DISC/gov.nasa.eosdis))
- **Product:** GPM IMERG Half-Hourly Final Precipitation Product (GPM_3IMERGHH)
- **Resolution:** 0.1° × 0.1° (approx. 10 km spatial), 30-minute temporal.
- **Variables:** Surface precipitation rate (mm/hr), multi-satellite merged precipitation estimate.
- **Provenance Category:** **OBSERVED / CALIBRATED**
- **Status in Engine:** **ACTIVE** (Used for Hurricane Harvey and Chennai flood rainfall time-series profiles)

### 2.6 Government of India Open Government Data (data.gov.in)
- **Source:** India Meteorological Department (IMD) via [data.gov.in](https://data.gov.in/catalog/rainfall-india)
- **License:** Government Open Data License - India (GODL)
- **Variables:** Sub-divisional and district-level historical daily & monthly precipitation records (1901–present).
- **Provenance Category:** **OBSERVED**
- **Status in Engine:** **ACTIVE**

### 2.7 ISRO Bhuvan Geo-Platform (Indian Space Research Organisation)
- **Source:** National Remote Sensing Centre (NRSC) / ISRO ([Bhuvan Portal](https://bhuvan.nrsc.gov.in/home/))
- **Layers:** Land Use / Land Cover (LULC 1:50,000), CartoDEM (10m/30m elevation), drainage density maps.
- **License / Access Restriction:** National Geospatial Policy (Government of India). Requires user-registered API authorization key.
- **Provenance Category:** **OBSERVED**
- **Status in Engine:** **REQUIRES_ACCESS** (Authentication credentials required from institutional portal; clearly reported without falsification).

### 2.8 India Water Resources Information System (India-WRIS / CWC / NWIC)
- **Source:** Central Water Commission (CWC) & National Water Informatics Centre (NWIC)
- **Variables:** River discharge gauge stations, reservoir levels, flood warning bulletins.
- **License / Access Restriction:** Restricted telemetry feeds requiring departmental clearance.
- **Provenance Category:** **OBSERVED**
- **Status in Engine:** **REQUIRES_ACCESS**

---

## 3. Data Confidence Propagation Rules

Every numerical attribute displayed in Reality Sculptor is tagged with a provenance tuple:
`{ value: float, confidence: float (0.0 - 1.0), provenance: Enum, source_id: str }`

1. **OBSERVED (Confidence 0.90 – 1.00):** Direct telemetry or verified survey (e.g. LiDAR elevation, official survey blueprint, in-situ ultrasonic water level sensor).
2. **DERIVED (Confidence 0.75 – 0.90):** Computed deterministically from observed layers (e.g. slope and curvature computed via second derivatives from DEM, flow accumulation from D8).
3. **ESTIMATED (Confidence 0.50 – 0.75):** Inferred using ML regression models or engineering standards (e.g. building heights estimated from floor counts, pipe roughness Manning $n$ from material age).
4. **SIMULATED (Confidence 0.60 – 0.85):** Physics engine state variable (e.g. flood depth after 45 minutes of precipitation, sewer water velocity, emergency detour ETA).
5. **UNKNOWN (Confidence 0.00):** Information is missing. The system flags this in the Data Gap Map and prompts the Necessary Question Engine to query the operator.
