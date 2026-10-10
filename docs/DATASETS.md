# Reality Sculptor — DATASETS.md
> Comprehensive data sources for ML model training on geospatial flood risk,
> heat mapping, traffic simulation, and urban infrastructure analysis.

---

## 1. Elevation / Terrain

### Copernicus DEM (GLO-30)
| Field | Value |
|---|---|
| **Source** | ESA / Copernicus |
| **URL** | https://dataspace.copernicus.eu/ |
| **Download** | Copernicus Data Space Ecosystem or OpenTopography API (https://opentopography.org/) |
| **Coverage** | Global |
| **Resolution** | 30 m |
| **Format** | GeoTIFF |
| **License** | Free and open (Copernicus) |
| **Variables** | Digital Surface Model (DSM) elevation |
| **Use in RS** | Base terrain for global flood physics and flow routing |
| **Limitations** | Surface model includes trees/buildings; less accurate than bare-earth LiDAR |

### USGS 3DEP (3D Elevation Program)
| Field | Value |
|---|---|
| **Source** | US Geological Survey |
| **URL** | https://www.usgs.gov/3d-elevation-program |
| **Download** | National Map Downloader (https://apps.nationalmap.gov/downloader/) or AWS Open Data |
| **Coverage** | United States |
| **Resolution** | 1 m (LiDAR) |
| **Format** | GeoTIFF, LAZ |
| **License** | Public Domain |
| **Variables** | Bare-earth DEM, DSM, Point Clouds |
| **Use in RS** | High-fidelity urban hydrodynamic simulation for US regions (Houston MVP) |
| **Limitations** | US-only |

### SRTM & ALOS World 3D (AW3D30)
| Field | Value |
|---|---|
| **Source** | NASA / JAXA |
| **URL** | https://earthexplorer.usgs.gov/ (SRTM), https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/aw3d30_e.htm (ALOS) |
| **Coverage** | Global |
| **Resolution** | 30 m |
| **Format** | GeoTIFF |
| **License** | Public Domain / Free for research |
| **Use in RS** | Fallback terrain models for non-US regions |
| **Limitations** | SRTM data is from 2000; aging |

---

## 2. Roads / Buildings

### OpenStreetMap (Geofabrik)
| Field | Value |
|---|---|
| **Source** | OpenStreetMap Contributors / Geofabrik |
| **URL** | https://download.geofabrik.de/ |
| **Download** | Direct download by continent/country/subregion |
| **Coverage** | Global |
| **Resolution** | Vector |
| **Format** | PBF, Shapefile |
| **License** | ODbL |
| **Variables** | Roads, buildings, land use, waterways, infrastructure tags |
| **Use in RS** | Primary road networks, building footprints, drainage features |
| **Limitations** | Completeness varies by region |

### Google Open Buildings
| Field | Value |
|---|---|
| **Source** | Google Research |
| **URL** | https://sites.research.google/open-buildings/ |
| **Download** | Direct via S2 cell links or Google Earth Engine (`GOOGLE_Research_open-buildings_v3_polygons`) |
| **Coverage** | Global (focus on Global South / Africa / South Asia) |
| **Resolution** | Building footprints (Vector) |
| **Format** | GeoJSON, CSV, Earth Engine |
| **License** | CC BY-4.0 |
| **Use in RS** | Urban obstacle modeling for flood blocking and heat mass modeling |
| **Limitations** | Variable accuracy in extremely dense informal settlements |

### Microsoft Global Building Footprints
| Field | Value |
|---|---|
| **Source** | Microsoft |
| **URL** | https://github.com/microsoft/GlobalMLBuildingFootprints |
| **Download** | GitHub links → Azure Blob Storage |
| **Coverage** | Global |
| **Format** | GeoJSON, GeoParquet |
| **License** | ODbL |
| **Use in RS** | Supplementing OSM/Google data for building density analysis |

---

## 3. Satellite Imagery

### Sentinel-2 (Copernicus)
| Field | Value |
|---|---|
| **Source** | ESA |
| **URL** | https://dataspace.copernicus.eu/ |
| **Download** | Copernicus Browser or Google Earth Engine (`COPERNICUS/S2_SR_HARMONIZED`) |
| **Coverage** | Global |
| **Resolution** | 10 m (RGB, NIR) |
| **Format** | JPEG2000, GeoTIFF via API |
| **License** | Free and Open |
| **Variables** | 13 spectral bands |
| **Use in RS** | Land cover classification, post-flood extent validation (NDWI) |
| **Limitations** | Blocked by cloud cover during active storms |

### Landsat 8/9
| Field | Value |
|---|---|
| **Source** | USGS / NASA |
| **URL** | https://earthexplorer.usgs.gov/ |
| **Download** | USGS EarthExplorer or Google Earth Engine |
| **Coverage** | Global |
| **Resolution** | 30 m (Multispectral), 15 m (Pan), 100 m (Thermal) |
| **Format** | GeoTIFF |
| **License** | Public Domain |
| **Variables** | Optical + Thermal (TIRS) |
| **Use in RS** | Thermal mapping for Urban Heat Islands |
| **Limitations** | 16-day revisit time |

---

## 4. Weather / Rainfall

### NASA GPM IMERG
| Field | Value |
|---|---|
| **Source** | NASA |
| **URL** | https://gpm.nasa.gov/data/imerg |
| **Download** | NASA Earthdata Search (https://search.earthdata.nasa.gov/) |
| **Coverage** | Global |
| **Resolution** | 0.1° × 0.1° (~10 km), half-hourly |
| **Format** | NetCDF, HDF5 |
| **License** | Open |
| **Variables** | Precipitation rate (mm/hr) |
| **Use in RS** | Real-time and historical rainfall for flood simulation |
| **Limitations** | Coarse for street-level micro-simulations |

### NOAA GHCN-Daily
| Field | Value |
|---|---|
| **Source** | NOAA |
| **URL** | https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily |
| **Download** | NCEI portal or AWS Registry of Open Data |
| **Coverage** | Global (station-based) |
| **Format** | CSV |
| **License** | Open |
| **Variables** | Precipitation, Max/Min Temperature |
| **Use in RS** | Calibrating remote sensing rainfall and heat with ground truth |

---

## 5. Flood Data

### Global Flood Database (v3)
| Field | Value |
|---|---|
| **Source** | Cloud to Street / DFO |
| **URL** | http://global-flood-database.cloudtostreet.info/ |
| **Download** | `gsutil -m cp gs://gfd_v3 ./` or Google Earth Engine |
| **Coverage** | Global (2000–2018 events) |
| **Resolution** | 250 m |
| **Format** | GeoTIFF |
| **License** | CC BY 4.0 |
| **Variables** | Flood extent, recurrence |
| **Use in RS** | Ground truth for training ML inundation models |
| **Limitations** | MODIS-based; misses cloud-obscured or urban-canopy floods |

### JRC Global Surface Water
| Field | Value |
|---|---|
| **Source** | EC Joint Research Centre |
| **URL** | https://global-surface-water.appspot.com/ |
| **Download** | Portal download or GEE (`JRC/GSW1_4/GlobalSurfaceWater`) |
| **Coverage** | Global |
| **Resolution** | 30 m |
| **Format** | GeoTIFF |
| **License** | Free (Copernicus) |
| **Variables** | Water occurrence, seasonality, transitions |
| **Use in RS** | Permanent vs. ephemeral water body identification |

### GloFAS (Global Flood Awareness System)
| Field | Value |
|---|---|
| **Source** | Copernicus Emergency Management Service |
| **URL** | https://www.globalfloods.eu/ |
| **Use in RS** | Daily riverine flood forecasting inputs |

### Dartmouth Flood Observatory
| Field | Value |
|---|---|
| **Source** | University of Colorado |
| **URL** | https://floodobservatory.colorado.edu/ |
| **Use in RS** | Historical flood event polygons and river discharge |

---

## 6. Land Cover

### ESA WorldCover
| Field | Value |
|---|---|
| **Source** | ESA |
| **URL** | https://esa-worldcover.org/en |
| **Download** | Direct via viewer, GEE, or AWS |
| **Coverage** | Global |
| **Resolution** | 10 m |
| **Format** | GeoTIFF |
| **License** | CC BY 4.0 |
| **Variables** | 11 land cover classes (Tree, Shrubland, Grassland, Built-up, Water, etc.) |
| **Use in RS** | Surface roughness (Manning's n), runoff infiltration rates |

---

## 7. Heat / Urban

### MODIS LST (Land Surface Temperature)
| Field | Value |
|---|---|
| **Source** | NASA |
| **URL** | https://modis.gsfc.nasa.gov/data/dataprod/mod11.php |
| **Download** | Earthdata or GEE (`MODIS/061/MOD11A1`) |
| **Coverage** | Global |
| **Resolution** | 1 km |
| **Format** | HDF, GEE ImageCollection |
| **License** | Open |
| **Variables** | Daytime/Nighttime LST |
| **Use in RS** | Macro-level Urban Heat Island mapping |
| **Limitations** | 1 km too coarse for block-level; use Landsat TIRS for 30–100 m |

---

## 8. India-Specific Data

### ISRO Bhuvan (NOEDA)
| Field | Value |
|---|---|
| **Source** | NRSC / ISRO |
| **URL** | https://bhuvan.nrsc.gov.in/ |
| **Download** | Register at Bhuvan Open Data Archive (NOEDA) and download tiles |
| **Coverage** | India |
| **Resolution** | Variable (up to 23 m LISS-III, CartoDEM 30 m) |
| **Format** | GeoTIFF |
| **License** | Free for research (registration required) |
| **Variables** | LULC, DEM, geomorphology |
| **Use in RS** | Regional terrain/land cover for Assam, Odisha |
| **Limitations** | Strict daily download limits; platform can be slow |

### India-WRIS
| Field | Value |
|---|---|
| **Source** | Ministry of Jal Shakti |
| **URL** | https://indiawris.gov.in/ |
| **Download** | Portal (requires login) |
| **Coverage** | India |
| **Variables** | River basins, reservoir levels, groundwater |
| **Use in RS** | Boundary conditions for Brahmaputra / Mahanadi river levels |

### data.gov.in
| Field | Value |
|---|---|
| **Source** | Government of India |
| **URL** | https://data.gov.in/ |
| **Variables** | Mixed administrative, environmental, infrastructure datasets |
| **Use in RS** | Census population, infrastructure catalogs |

---

## 9. Traffic

### pNEUMA (Open-Traffic)
| Field | Value |
|---|---|
| **Source** | EPFL |
| **URL** | https://open-traffic.epfl.ch/ |
| **Coverage** | Athens, Greece (sample) |
| **Variables** | Drone-captured naturalistic vehicle trajectories |
| **Use in RS** | Micro-level traffic behavior training during congestion |

> **Note:** For target cities, use city open data portals for GTFS transit and traffic count data.

---

## 10. Drainage / Sewer (Infrastructure)

### Houston Open Data
| Field | Value |
|---|---|
| **Source** | City of Houston |
| **URL** | https://cohgis-mycity.opendata.arcgis.com/ |
| **Variables** | Stormwater networks, inlets, channels, outfalls |
| **Use in RS** | 1D/2D coupled flood models with subterranean sewer interaction |

### Amsterdam Open Geodata
| Field | Value |
|---|---|
| **Source** | City of Amsterdam |
| **URL** | https://maps.amsterdam.nl/open_geodata/ |
| **Variables** | Extremely detailed 3D infrastructure, water management |

> **Note:** Detailed sewer/drainage data is rarely available as open data. For Indian cities, this is a known **DATA GAP**. Use synthetic engineering-demo layers for simulation, clearly labeled as ESTIMATED.

---

## DEMO REGION EVALUATION

| Criterion | Guwahati | Bhubaneswar | Chennai | Houston | Amsterdam |
|---|---|---|---|---|---|
| **Flood severity** | ★★★★★ | ★★★★ | ★★★★★ | ★★★★★ | ★★★ |
| **Terrain (LiDAR)** | ★★ | ★★ | ★★ | ★★★★★ | ★★★★★ |
| **Drainage data** | ★ | ★ | ★ | ★★★★★ | ★★★★★ |
| **Building data** | ★★★ | ★★★ | ★★★ | ★★★★★ | ★★★★★ |
| **Traffic data** | ★ | ★ | ★★ | ★★★★ | ★★★★ |
| **Weather data** | ★★★ | ★★★ | ★★★★ | ★★★★★ | ★★★★ |
| **Historical flood** | ★★★★ | ★★★ | ★★★★★ | ★★★★★ | ★★★ |
| **Heat (UHI)** | ★★★ | ★★★★ | ★★★★★ | ★★★★★ | ★★★ |
| **Overall** | ★★★ | ★★★ | ★★★★ | ★★★★★ | ★★★★ |

### ✅ RECOMMENDED PRIMARY DEMO REGION: Houston, TX, USA

**Why Houston?**
- Frequent and severe flooding (Hurricane Harvey, regular flash floods)
- 1 m USGS 3DEP LiDAR freely available
- City GIS portal provides extensive open stormwater, sewer, and drainage shapefiles
- Highly car-centric (excellent for traffic simulation stress tests)
- Significant Urban Heat Island effects
- Best combination of **disaster vulnerability** + **world-class open data availability**

### 🇮🇳 RECOMMENDED INDIA DEMO REGION: Chennai, Tamil Nadu

**Why Chennai?**
- 2015 floods are extremely well-documented with satellite imagery
- Better infrastructure data availability than Guwahati
- Strong heat island effects for dual flood+heat demonstration
- Copernicus/Sentinel coverage excellent

> **Data Gap Warning:** Detailed underground drainage/sewer network data for Indian cities is generally **not available as open data**. Use OSM-derived surface drainage + synthetic engineering layers clearly labeled as `ESTIMATED / SIMULATED`.

---

## DATASET MANIFEST TEMPLATE

For every dataset used in training, create an entry:

```yaml
dataset:
  name: ""
  source: ""
  url: ""
  download_date: ""
  license: ""
  variables: []
  resolution: ""
  geography: ""
  temporal_coverage: ""
  preprocessing: ""
  model_usage: ""
  known_limitations: ""
```
