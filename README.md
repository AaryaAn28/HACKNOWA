# Reality Sculptor

> **Physical World Programming Platform**
> *The World Is Programmable.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)]()
[![Unreal Engine 5](https://img.shields.io/badge/UE5-5.6+-purple.svg)]()
[![LightGBM](https://img.shields.io/badge/ML-LightGBM-orange.svg)]()

---

## What Is Reality Sculptor?

Reality Sculptor turns **any real physical location** into a **programmable spatial environment**. It is a closed-loop system that:

1. **Perceives** reality (maps, blueprints, satellite, sensors)
2. **Builds** a causal world model
3. **Simulates** progressive disasters (flood, heat, traffic cascade)
4. **Generates** interventions
5. **Finds** the minimal-force plan
6. **Installs** it virtually so the 3D world physically reacts
7. **Detects** reality drift from sensors
8. **Continuously replans**

It is NOT a chatbot, dashboard, or static digital twin. It is an **operating system for physical environments**.

---

## Quick Start

```bash
# 1. Clone and setup
cd reality-sculptor/backend
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your PostGIS database URL

# 3. Run
uvicorn app.main:app --reload --port 8000

# 4. Open API docs
# http://localhost:8000/docs
```

---

## Architecture

```
UPLOAD / SATELLITE / SENSORS
         │
    INGESTION LAYER (classify, georeference, extract)
         │
    WORLD STATE ENGINE (single source of truth)
         │
    ┌─────┼─────┬───────┬─────────┬──────────┐
    │     │     │       │         │          │
  FLOOD HEAT TRAFFIC SEWER VEGETATION EMERGENCY
    │     │     │       │         │          │
    └─────┴─────┴───┬───┴─────────┴──────────┘
                     │
              CASCADE ENGINE
                     │
         ┌───────────┼───────────┐
         │           │           │
    CAUSAL BRAIN  QUESTION   CRITICAL NODE
                  ENGINE     DETECTOR
         │
    INTERVENTION ENGINE
    (Library → Optimize → Critique → Futures)
         │
    VIRTUAL INSTALLATION
         │
    WebSocket → UNREAL ENGINE 5
    (Cesium + Nanite + Lumen + Niagara)
         │
    SENSOR NETWORK → DRIFT DETECTION → REPLAN
```

---

## Project Structure

```
reality-sculptor/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── core/             # World State Engine, config, audit
│   │   ├── models/           # SQLAlchemy + PostGIS models
│   │   ├── schemas/          # Pydantic v2 API schemas
│   │   ├── services/         # Business logic services
│   │   │   ├── question_engine.py
│   │   │   ├── region_scanner.py
│   │   │   ├── critical_node_detector.py
│   │   │   ├── sensor_network.py
│   │   │   ├── drift_detector.py
│   │   │   ├── data_gap_analyzer.py
│   │   │   └── demo_sequence.py
│   │   ├── simulation/       # Modular simulation engines
│   │   │   ├── interfaces.py
│   │   │   ├── flood/
│   │   │   ├── heat/
│   │   │   ├── traffic/
│   │   │   ├── drainage/
│   │   │   ├── sewer/
│   │   │   ├── vegetation/
│   │   │   ├── emergency/
│   │   │   └── cascade/
│   │   ├── causal/           # Causal Brain + X-Ray + Consequences
│   │   ├── intervention/     # Intervention Library + Optimizer
│   │   ├── ingestion/        # Upload + Blueprint + Georef
│   │   ├── ml/               # ML training + features + registry
│   │   └── websocket/        # Real-time state sync
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   ├── training/
│   │   ├── validation/
│   │   ├── demo/
│   │   └── synthetic/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATASETS.md
│   ├── BLUEPRINT_INGESTION.md
│   ├── WORLD_RECONSTRUCTION.md
│   ├── QUESTIONNAIRE_ENGINE.md
│   ├── SEWER_INTELLIGENCE.md
│   ├── DRAINAGE_INTELLIGENCE.md
│   ├── SIMULATION_ARCHITECTURE.md
│   ├── MODEL_TRAINING.md
│   ├── MODEL_VALIDATION.md
│   ├── DATA_CONFIDENCE.md
│   ├── DATA_SOURCES.md
│   ├── SEMANTIC_WORLD_MODEL.md
│   └── TRAFFIC_INTELLIGENCE.md
├── unreal/
│   └── README.md
└── frontend/
    └── src/
```

---

## Key Technologies

| Layer | Technology |
|---|---|
| **3D Visualization** | Unreal Engine 5.6+ / Cesium / Nanite / Lumen / Niagara |
| **Backend** | Python 3.11+ / FastAPI / WebSockets |
| **Database** | PostgreSQL + PostGIS / Time-series |
| **ML** | LightGBM (primary) / XGBoost (secondary) / Optuna |
| **Geospatial** | GeoPandas / Rasterio / OSMnx / Shapely / PyProj |
| **Graphs** | NetworkX (causal + infrastructure) |
| **Vision** | OpenCV / Tesseract OCR (blueprint analysis) |

---

## Core Loop

```
REAL LOCATION → 3D WORLD → DISASTER TRIGGER → CAUSAL ANALYSIS →
INTERVENTION GENERATION → MULTI-FUTURE SIM → MINIMAL FORCE →
VIRTUAL INSTALL → WORLD REACTS → SENSOR DRIFT → REPLAN
```

---

## Non-Negotiable Rules

1. Never fake intelligence, data, or confidence
2. Never make visual effects independent of simulation state
3. Never execute consequential actions without required information
4. Never hide trade-offs
5. Never optimize one metric while silently destroying another
6. Every model must be replaceable
7. Every simulation must be reproducible
8. Every recommendation must be explainable
9. Every output must have provenance
10. The 3D world is a visualization of world state, not a scripted movie

---

## HackNowa Global Hackathon 2026
**Track:** Smart & Sustainable Future
**Category:** Individual Entry

---

## License

Proprietary — HackNowa 2026 Submission
