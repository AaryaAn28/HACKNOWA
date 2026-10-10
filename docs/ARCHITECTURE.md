# Reality Sculptor — System Architecture

> **Physical World Programming Platform**
> Turn any real physical location into a programmable spatial environment.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REALITY SCULPTOR ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   UPLOAD     │  │  SATELLITE   │  │   SENSORS    │              │
│  │   CENTER     │  │  + OSM       │  │   + WEATHER  │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         ▼                 ▼                 ▼                       │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              INGESTION & PERCEPTION LAYER               │        │
│  │  Document Classifier → Blueprint Analyzer → Georef     │        │
│  │  OCR → Symbol Detection → Network Reconstruction       │        │
│  └────────────────────────┬───────────────────────────────┘        │
│                           │                                         │
│                           ▼                                         │
│  ┌────────────────────────────────────────────────────────┐        │
│  │             WORLD STATE ENGINE (Single Source)          │        │
│  │                                                        │        │
│  │  Versioned State │ Spatial Grid │ Confidence Labels    │        │
│  │  State Transitions │ Audit Trail │ Observable Pattern  │        │
│  │                                                        │        │
│  │  Variables: rainfall, soil_saturation, surface_runoff,  │        │
│  │  drain_capacity, drain_load, water_depth, water_velocity│        │
│  │  road_accessibility, traffic_density, heat_flux,        │        │
│  │  surface_temperature, vegetation_canopy, emergency_access│       │
│  └────┬───────┬───────┬───────┬───────┬───────┬───────────┘        │
│       │       │       │       │       │       │                     │
│       ▼       ▼       ▼       ▼       ▼       ▼                     │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              SIMULATION SUBSYSTEMS (Modular)            │        │
│  │                                                        │        │
│  │  ┌─────────┐ ┌────────┐ ┌─────────┐ ┌───────────┐    │        │
│  │  │  FLOOD  │ │  HEAT  │ │ TRAFFIC │ │ DRAINAGE  │    │        │
│  │  │ Engine  │ │ Engine │ │ Engine  │ │  Engine   │    │        │
│  │  └────┬────┘ └───┬────┘ └────┬────┘ └─────┬─────┘    │        │
│  │       │          │           │             │          │        │
│  │  ┌────┴────┐ ┌───┴────┐ ┌───┴──────┐ ┌───┴──────┐   │        │
│  │  │  SEWER  │ │ VEGETA-│ │EMERGENCY │ │ CASCADE  │   │        │
│  │  │ Engine  │ │ TION   │ │ ACCESS   │ │  Engine  │   │        │
│  │  └─────────┘ └────────┘ └──────────┘ └──────────┘   │        │
│  └────────────────────────┬───────────────────────────────┘        │
│                           │                                         │
│              ┌────────────┼────────────┐                           │
│              ▼            ▼            ▼                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐           │
│  │ CAUSAL BRAIN │ │ QUESTION     │ │ CRITICAL NODE    │           │
│  │              │ │ ENGINE       │ │ DETECTOR         │           │
│  │ Directed     │ │              │ │                  │           │
│  │ Causal Graph │ │ Adaptive     │ │ Multi-factor     │           │
│  │ Counterfact. │ │ Questions    │ │ Scoring          │           │
│  │ X-Ray        │ │ Info Value   │ │ WHY? Generation  │           │
│  │ Failure Chain│ │ Data Gaps    │ │ Cross-domain     │           │
│  └──────┬───────┘ └──────────────┘ └──────────────────┘           │
│         │                                                           │
│         ▼                                                           │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              INTERVENTION ENGINE                        │        │
│  │                                                        │        │
│  │  Intervention Library (14 types, 5 categories)         │        │
│  │  → Candidate Generation                                │        │
│  │  → Composition (non-linear combined simulation)        │        │
│  │  → Consequence Analysis (direct → cascade → trade-offs)│        │
│  │  → Minimal Force Optimizer (progressive search)        │        │
│  │  → Pareto Front (multi-objective)                      │        │
│  │  → Adversarial Critic (stress test)                    │        │
│  │  → Multi-Future Simulation (8 scenarios)               │        │
│  └────────────────────────┬───────────────────────────────┘        │
│                           │                                         │
│                           ▼                                         │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              VIRTUAL INSTALLATION                       │        │
│  │                                                        │        │
│  │  ACTION → STATE CHANGE → SIMULATION UPDATE →           │        │
│  │  WORLD STATE UPDATE → 3D VISUAL UPDATE →               │        │
│  │  METRIC UPDATE → CAUSAL GRAPH UPDATE                   │        │
│  └────────────────────────┬───────────────────────────────┘        │
│                           │                                         │
│              ┌────────────┼────────────┐                           │
│              ▼            ▼            ▼                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│  │ SENSOR       │ │ REALITY      │ │ REPLANNING   │               │
│  │ NETWORK      │ │ DRIFT        │ │              │               │
│  │              │ │ DETECTOR     │ │ Recalibrate  │               │
│  │ Feedback Lock│ │              │ │ → Re-optimize│               │
│  │ Compare pred │ │ GREEN/YELLOW │ │ → Re-install │               │
│  │ vs observed  │ │ ORANGE/RED   │ │              │               │
│  └──────────────┘ └──────────────┘ └──────────────┘               │
│                                                                     │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              ML LAYER                                   │        │
│  │                                                        │        │
│  │  LightGBM (primary) + XGBoost (secondary)             │        │
│  │  Flood Risk Model │ Heat Model │ Drift Model          │        │
│  │  Feature Engineering │ Spatial CV │ Early Stopping     │        │
│  │  Optuna HPO │ Model Registry │ Data Lineage           │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                     │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              COMMUNICATION LAYER                        │        │
│  │                                                        │        │
│  │  FastAPI REST │ WebSocket (state sync to UE5)          │        │
│  │  Channels: simulation_state, water_field, heat_field,  │        │
│  │  traffic_state, intervention_state, causal_events,     │        │
│  │  sensor_events, cinematic_events, drift_events         │        │
│  └────────────────────────┬───────────────────────────────┘        │
│                           │                                         │
│                           ▼                                         │
│  ┌────────────────────────────────────────────────────────┐        │
│  │       UNREAL ENGINE 5 VISUALIZATION LAYER               │        │
│  │                                                        │        │
│  │  Cesium │ Nanite │ Lumen │ Niagara │ Chaos │ TSR      │        │
│  │  World Partition │ Virtual Shadow Maps │ MegaLights   │        │
│  │                                                        │        │
│  │  Data-driven VFX: rain ↔ rainfall, water ↔ depth,     │        │
│  │  heat haze ↔ temperature, traffic ↔ density            │        │
│  │                                                        │        │
│  │  Camera System: free, follow, street, disaster-follow, │        │
│  │  causal, emergency-route, before/after                 │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                     │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              STORAGE                                    │        │
│  │                                                        │        │
│  │  PostGIS (spatial objects, infrastructure, regions)     │        │
│  │  Time-series (simulation state snapshots, sensor data) │        │
│  │  Model Registry (artifacts, versions, metrics)         │        │
│  │  Upload Store (documents, blueprints, versioned)       │        │
│  │  Audit Log (every consequential decision)              │        │
│  └────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## State Transition Model

Every action in Reality Sculptor follows:

```
CURRENT STATE → ACTION → TRANSITION MODEL → NEW STATE → CONSEQUENCES
```

Example:

```
OPEN_DRAIN(D17)
├── drain_capacity[D17] ↑
├── upstream_water_depth ↓
├── downstream_flow ↑
├── downstream_drain_load ↑
├── downstream_risk recalculated
├── traffic accessibility recalculated
└── emergency access recalculated
```

The visual engine then renders the resulting state.

---

## Data Confidence Labels

Every piece of data carries provenance:

| Label | Meaning |
|---|---|
| `OBSERVED` | Directly measured by sensor or verified survey |
| `DERIVED` | Calculated from observed data using established methods |
| `ESTIMATED` | Inferred with moderate confidence from available evidence |
| `SIMULATED` | Generated by simulation model |
| `UNKNOWN` | No information available |

Confidence propagates: if drain capacity confidence = 55%, downstream flood prediction reflects that uncertainty.

---

## API Architecture

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/region` | Create/upload region |
| `POST` | `/api/upload/{category}` | Universal file upload |
| `GET` | `/api/world/{region_id}` | Get world state |
| `POST` | `/api/scan` | Trigger full region scan |
| `POST` | `/api/simulate/flood` | Run flood simulation |
| `POST` | `/api/simulate/heat` | Run heat simulation |
| `POST` | `/api/simulate/traffic` | Run traffic simulation |
| `POST` | `/api/simulate/cascade` | Run cascading simulation |
| `GET` | `/api/causal/graph/{region_id}` | Get causal graph |
| `POST` | `/api/causal/counterfactual` | Run counterfactual |
| `POST` | `/api/causal/xray` | Causal X-Ray |
| `POST` | `/api/causal/why` | Explain why |
| `POST` | `/api/intervention/generate` | Generate interventions |
| `POST` | `/api/intervention/optimize` | Minimal force optimization |
| `POST` | `/api/intervention/install` | Virtual installation |
| `POST` | `/api/intervention/critique` | Adversarial critic |
| `POST` | `/api/intervention/futures` | Multi-future stress test |
| `GET` | `/api/questions/{region_id}` | Get adaptive questions |
| `POST` | `/api/questions/{region_id}/answer` | Submit answers |
| `GET` | `/api/questions/{region_id}/gaps` | Data gap map |
| `GET` | `/api/sensors/{region_id}` | Sensor readings |
| `POST` | `/api/drift/check` | Reality drift check |
| `GET` | `/api/critical-nodes/{region_id}` | Critical node analysis |
| `WS` | `/ws/state` | Live state updates |

---

## 90-Second Cinematic Demo Sequence

| Time | Event | Camera |
|---|---|---|
| 0–8s | Cinematic flyover of Houston | Aerial sweep |
| 8–15s | Reality Scan — semantic detection | Top-down scanning |
| 15–22s | World reconstruction status | Dashboard overlay |
| 22–30s | Disaster trigger — progressive rain | Sky darken, rain begins |
| 30–42s | Flood simulation — full pipeline | Follow water flow |
| 42–48s | Causal X-Ray — failure chain | Causal graph view |
| 48–52s | Critical nodes pulse | Infrastructure close-up |
| 52–58s | Question Engine asks 2 questions | UI overlay |
| 58–65s | Intervention generation + search | Split-screen optimization |
| 65–72s | Multi-future stress test | Grid of futures |
| 72–78s | Virtual installation — drain + bioswale | Construction animation |
| 78–84s | World reacts — water recedes | Before/after split |
| 84–88s | Sensor contradiction → Reality Drift | Alert animation |
| 88–93s | Automatic replan | New intervention |
| 93–95s | Final impact dashboard | Full-screen metrics |

---

## Build Priority

| Priority | Component | Status |
|---|---|---|
| 1 | World State Engine | ✅ Complete |
| 2 | Real location + 3D world | ✅ Architecture |
| 3 | Progressive flood simulation | ✅ Complete |
| 4 | Causal Brain | ✅ Complete |
| 5 | Necessary Question Engine | ✅ Complete |
| 6 | Intervention + Consequence Engine | ✅ Complete |
| 7 | Minimal Force Optimizer | ✅ Complete |
| 8 | Virtual Installation + World Reaction | ✅ Complete |
| 9 | Multi-Future Simulation | ✅ Complete |
| 10 | Reality Drift + Replanning | ✅ Complete |
| 11 | Heat Simulation | ✅ Complete |
| 12 | Traffic/Emergency Cascade | ✅ Complete |
| 13 | Advanced Animations | 🔧 UE5 Blueprints |
| 14 | Additional Disasters | 🔧 Framework ready |
