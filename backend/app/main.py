"""
Reality Sculptor — Authoritative Physical World Programming Server
===================================================================

Main FastAPI application entry point. Starts server with all physics engines,
causal graphs, spatial optimizers, WebSocket state synchronization, and
data-driven APIs.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, RedirectResponse
from loguru import logger

# Core Engines
from app.core.world_state import WorldState
from app.world.region_knowledge_model import RegionKnowledgeModel
from app.simulation.flood.engine import FloodSimulationEngine
from app.simulation.heat.engine import HeatSimulationEngine
from app.causal.brain import CausalBrain, CausalNode, CausalEdge
from app.intervention.engine import MinimalForceOptimizer, InterventionLibrary
from app.services.question_engine import QuestionEngine
from app.services.sensor_network import SensorNetwork
from app.services.drift_detector import DriftDetector
from app.services.demo_sequence import DemoSequencer
from app.websocket.manager import WebSocketManager

# Routers
from app.api.routes import router as core_router
from app.api.simulation_routes import router as simulation_router
from app.api.causal_routes import router as causal_router
from app.api.intervention_routes import router as intervention_router
from app.api.question_routes import router as question_router
from app.api.upload_routes import router as upload_router


# ---------------------------------------------------------------------------
# Application Lifespan (Singletons Initialization)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("╔═════════════════════════════════════════════════════════════╗")
    logger.info("║     REALITY SCULPTOR — Physical World Programming Server    ║")
    logger.info("║     DATA-DRIVEN AI + REAL SIMULATION + UNREAL 5.6 READY    ║")
    logger.info("╚═════════════════════════════════════════════════════════════╝")

    # 1. Central World State Engine (Single Source of Truth)
    world_state = WorldState()
    app.state.world_state = world_state

    # 2. Region Knowledge Model (Load real processed geographic data)
    rkm = RegionKnowledgeModel(region_id="chennai_velachery")
    processed_data_path = Path(__file__).resolve().parents[2] / "data" / "processed" / "chennai_velachery_spatial_entities.json"
    if not processed_data_path.exists():
        # Fallback to Houston
        processed_data_path = Path(__file__).resolve().parents[2] / "data" / "processed" / "houston_medical_center_spatial_entities.json"
        
    if processed_data_path.exists():
        rkm.load_processed_data(processed_data_path)
        logger.info(f"Loaded Region Knowledge Model: {rkm.region_id} ({len(rkm.nodes)} nodes, {len(rkm.relationships)} relations)")
    else:
        logger.warning("Processed geospatial extract not found. Running with baseline RKM.")
    app.state.rkm = rkm

    # 3. Physics Simulation Engines
    flood_engine = FloodSimulationEngine({"cell_size": 20.0, "demo_mode": True})
    flood_engine.initialize(world_state)
    app.state.flood_engine = flood_engine

    heat_engine = HeatSimulationEngine()
    app.state.heat_engine = heat_engine

    # 4. Causal Brain (NetworkX Graph seeded from physical knowledge)
    causal_brain = CausalBrain()
    # Seed default physical causal chain: Rain -> Runoff -> Drain Inflow -> Pipe Load -> Flood Depth -> Road Closure -> Emergency Delay
    causal_brain.add_node(CausalNode(id="rainfall", name="Rainfall Intensity (mm/hr)", variable_type="weather", baseline_value=0.0))
    causal_brain.add_node(CausalNode(id="surface_runoff", name="Surface Runoff (m3/s)", variable_type="hydrology", baseline_value=0.0))
    causal_brain.add_node(CausalNode(id="drain_load", name="Drain D-17 Intake Load (%)", variable_type="drainage", baseline_value=15.0))
    causal_brain.add_node(CausalNode(id="pipe_capacity", name="Pipe P-44 Capacity (m3/s)", variable_type="sewerage", baseline_value=3.2))
    causal_brain.add_node(CausalNode(id="flood_depth", name="Depression Flood Depth (m)", variable_type="hazard", baseline_value=0.0))
    causal_brain.add_node(CausalNode(id="road_accessibility", name="Arterial Road Accessibility (%)", variable_type="traffic", baseline_value=100.0))
    causal_brain.add_node(CausalNode(id="emergency_delay", name="Ambulance Route Delay (min)", variable_type="emergency", baseline_value=0.0))

    causal_brain.add_edge(CausalEdge(source="rainfall", target="surface_runoff", strength=0.92, confidence=0.98))
    causal_brain.add_edge(CausalEdge(source="surface_runoff", target="drain_load", strength=0.88, confidence=0.95))
    causal_brain.add_edge(CausalEdge(source="drain_load", target="flood_depth", strength=0.85, confidence=0.90))
    causal_brain.add_edge(CausalEdge(source="pipe_capacity", target="drain_load", strength=-0.75, confidence=0.88))
    causal_brain.add_edge(CausalEdge(source="flood_depth", target="road_accessibility", strength=-0.90, confidence=0.95))
    causal_brain.add_edge(CausalEdge(source="road_accessibility", target="emergency_delay", strength=-0.85, confidence=0.92))
    app.state.causal_brain = causal_brain


    # 5. Minimal Force Pareto Optimizer
    intervention_lib = InterventionLibrary()
    optimizer = MinimalForceOptimizer(library=intervention_lib)
    app.state.optimizer = optimizer


    # 6. Action Governor & Supporting Services
    app.state.question_engine = QuestionEngine()
    app.state.sensor_network = SensorNetwork()
    app.state.drift_detector = DriftDetector()
    app.state.demo_sequencer = DemoSequencer()
    app.state.ws_manager = WebSocketManager()

    # 7. Physical World ML Intelligence Layer
    try:
        import sys
        ml_dir = Path(__file__).resolve().parents[2] / "ml"
        if str(ml_dir) not in sys.path:
            sys.path.insert(0, str(ml_dir))
        from inference.backend_integration import get_engine
        app.state.ml_engine = get_engine()
        logger.info("ML Physical World Intelligence Layer loaded and attached to app state.")
    except Exception as e:
        logger.warning(f"ML engine initialization deferred: {e}")

    logger.info("All Core Physical, Causal & ML Intelligence Engines Operational.")
    yield
    logger.info("Reality Sculptor server shutting down.")


# ---------------------------------------------------------------------------
# FastAPI Application Declaration
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Reality Sculptor",
    description="Physical World Programming Engine: Real Geospatial AI + Physics Simulation + Minimal Force Optimization.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router Ingestion
# ---------------------------------------------------------------------------
app.include_router(core_router, prefix="/api", tags=["Core World State"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["Physics Simulation"])
app.include_router(causal_router, prefix="/api/causal", tags=["Causal Brain"])
app.include_router(intervention_router, prefix="/api/interventions", tags=["Minimal Force Interventions"])
app.include_router(question_router, prefix="/api/questions", tags=["Necessary Question Engine"])
app.include_router(upload_router, prefix="/api/upload", tags=["Ingestion & Upload"])

# ML Prediction Router
try:
    import sys
    ml_dir = Path(__file__).resolve().parents[2] / "ml"
    if str(ml_dir) not in sys.path:
        sys.path.insert(0, str(ml_dir))
    from inference.backend_integration import ml_router
    app.include_router(ml_router)
except Exception as e:
    logger.warning(f"ML router inclusion deferred: {e}")


# ---------------------------------------------------------------------------
# WebSocket State Synchronization Endpoint
# ---------------------------------------------------------------------------
@app.websocket("/ws/state")
async def websocket_state_endpoint(websocket: WebSocket, client_id: str = "web_client"):
    """Streams live simulation state, physical water depth, and 120 FPS telemetry."""
    ws_manager = app.state.ws_manager
    client = await ws_manager.connect(websocket, client_id=client_id, client_type="frontend")
    try:
        while True:
            msg = await websocket.receive_text()
            # Handle client commands if sent
    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    return {
        "status": "operational",
        "system": "Reality Sculptor Physical World Engine",
        "version": "2.0.0-rebuild",
        "fps_target": 120,
        "active_region": getattr(app.state, "rkm", None).region_id if hasattr(app.state, "rkm") else "none",
        "total_nodes_loaded": len(app.state.rkm.nodes) if hasattr(app.state, "rkm") else 0,
        "modules": {
            "world_state_engine": "online",
            "region_knowledge_model": "online",
            "flood_simulation": "online",
            "heat_simulation": "online",
            "causal_brain": "online",
            "minimal_force_optimizer": "online",
            "sensor_network": "online",
            "websocket_manager": "online"
        }
    }


# ---------------------------------------------------------------------------
# Static Web App & Favicon Mount (Must come last)
# ---------------------------------------------------------------------------
frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    fav = frontend_dir / "assets" / "favicon.ico"
    if fav.exists():
        return FileResponse(fav)
    return Response(status_code=204)

if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir), html=True), name="frontend_mount")
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend_root")

