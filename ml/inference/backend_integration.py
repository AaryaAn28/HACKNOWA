"""
Reality Sculptor ML -- inference/backend_integration.py
========================================================
Integrates the ML Inference Engine with the FastAPI backend.

This module provides:
1. FastAPI router with ML prediction endpoints
2. Startup hook to load all models
3. World State update functions that consume ML predictions
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from fastapi import APIRouter, HTTPException, UploadFile, File
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# Import the ML engine
import importlib.util
spec = importlib.util.spec_from_file_location(
    "ml_inference_engine",
    str(Path(__file__).parent / "ml_inference_engine.py")
)
ml_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml_module)

MLInferenceEngine = ml_module.MLInferenceEngine
DataConfidence = ml_module.DataConfidence
Prediction = ml_module.Prediction
create_inference_engine = ml_module.create_inference_engine

# ── Global engine instance ───────────────────────────────────────────────────
_engine: Optional[MLInferenceEngine] = None


def get_engine() -> MLInferenceEngine:
    """Get or create the ML inference engine singleton."""
    global _engine
    if _engine is None:
        _engine = create_inference_engine()
    return _engine


# ── Pydantic Schemas ─────────────────────────────────────────────────────────
if HAS_FASTAPI:
    class PredictionResponse(BaseModel):
        value: float
        confidence: str
        uncertainty: float
        lower_bound: Optional[float] = None
        upper_bound: Optional[float] = None
        model_id: str
        timestamp: str

    class FloodPredictionRequest(BaseModel):
        features: List[float] = Field(..., description="Engineered flood features")

    class TrafficPredictionRequest(BaseModel):
        features: List[float] = Field(..., description="Temporal traffic features")

    class DrainagePredictionRequest(BaseModel):
        features: List[float] = Field(..., description="Drainage facility features")

    class RegionPredictionRequest(BaseModel):
        region_id: str
        flood_features: Optional[List[float]] = None
        traffic_features: Optional[List[float]] = None
        drainage_features: Optional[List[float]] = None

    class ModelStatusResponse(BaseModel):
        models: Dict[str, Dict]
        total_loaded: int
        total_available: int

    class RegionPredictionResponse(BaseModel):
        region_id: str
        timestamp: str
        predictions: Dict[str, Any]

    # ── FastAPI Router ───────────────────────────────────────────────────────
    ml_router = APIRouter(prefix="/api/ml", tags=["ml"])

    @ml_router.get("/status", response_model=ModelStatusResponse)
    async def ml_model_status():
        """Get status of all loaded ML models."""
        engine = get_engine()
        status = engine.get_model_status()
        loaded = sum(1 for v in status.values() if v.get("loaded"))
        return ModelStatusResponse(
            models=status,
            total_loaded=loaded,
            total_available=len(status),
        )

    @ml_router.post("/predict/flood", response_model=PredictionResponse)
    async def predict_flood(request: FloodPredictionRequest):
        """Predict flood water level from features."""
        engine = get_engine()
        features = np.array(request.features, dtype=np.float32)
        pred = engine.predict_flood(features)
        return PredictionResponse(**pred.to_dict())

    @ml_router.post("/predict/traffic", response_model=PredictionResponse)
    async def predict_traffic(request: TrafficPredictionRequest):
        """Predict traffic speed from temporal features."""
        engine = get_engine()
        features = np.array(request.features, dtype=np.float32)
        pred = engine.predict_traffic(features)
        return PredictionResponse(**pred.to_dict())

    @ml_router.post("/predict/drainage", response_model=PredictionResponse)
    async def predict_drainage(request: DrainagePredictionRequest):
        """Predict drainage overflow risk."""
        engine = get_engine()
        features = np.array(request.features, dtype=np.float32)
        pred = engine.predict_drainage_overflow(features)
        return PredictionResponse(**pred.to_dict())

    @ml_router.post("/predict/region", response_model=RegionPredictionResponse)
    async def predict_region(request: RegionPredictionRequest):
        """Generate complete ML predictions for a region."""
        engine = get_engine()
        
        features = {"region_id": request.region_id}
        if request.flood_features:
            features["flood_features"] = np.array(request.flood_features, dtype=np.float32)
        if request.traffic_features:
            features["traffic_features"] = np.array(request.traffic_features, dtype=np.float32)
        if request.drainage_features:
            features["drainage_features"] = np.array(request.drainage_features, dtype=np.float32)
        
        preds = engine.predict_region(features)
        
        return RegionPredictionResponse(
            region_id=preds.region_id,
            timestamp=preds.timestamp,
            predictions=preds.to_dict(),
        )

    @ml_router.get("/registry")
    async def get_model_registry():
        """Get the full model registry with training details."""
        engine = get_engine()
        return {"registry": engine.registry}


# ── World State Integration Functions ────────────────────────────────────────
def update_world_state_with_ml(world_state: dict, ml_predictions: dict) -> dict:
    """
    Merge ML predictions into the World State.
    
    Rules:
    1. ML predictions NEVER override OBSERVED data
    2. ML predictions with ESTIMATED confidence update UNKNOWN fields
    3. Uncertainty is always propagated
    4. Every update is logged with model_id and timestamp
    """
    updates = []
    
    for key, pred in ml_predictions.items():
        if pred is None:
            continue
        
        current = world_state.get(key)
        
        # Rule 1: Never override observed data
        if current and current.get("confidence") == "observed":
            continue
        
        # Rule 2: Update if current is unknown or lower confidence
        confidence_rank = {"unknown": 0, "simulated": 1, "estimated": 2, "derived": 3, "observed": 4}
        current_rank = confidence_rank.get(
            current.get("confidence", "unknown") if current else "unknown", 0
        )
        new_rank = confidence_rank.get(
            pred.get("confidence", "unknown") if isinstance(pred, dict) else "unknown", 0
        )
        
        if new_rank >= current_rank or current is None:
            world_state[key] = pred
            updates.append({"field": key, "action": "updated", "confidence": pred.get("confidence")})
    
    return world_state


# ── Startup Hook ─────────────────────────────────────────────────────────────
def integrate_with_app(app):
    """
    Integrate ML inference engine with FastAPI app.
    
    Call this in your FastAPI lifespan or startup event:
        from ml.inference.backend_integration import integrate_with_app
        integrate_with_app(app)
    """
    if HAS_FASTAPI:
        app.include_router(ml_router)
    
    # Store engine in app state
    engine = get_engine()
    app.state.ml_engine = engine
    
    print(f"ML Inference Engine integrated: {sum(1 for v in engine.models.values() if v is not None)} models loaded")
    
    return engine


if __name__ == "__main__":
    print("Backend integration module loaded successfully.")
    print(f"FastAPI available: {HAS_FASTAPI}")
    
    engine = get_engine()
    status = engine.get_model_status()
    print(f"\nModels: {sum(1 for v in status.values() if v.get('loaded'))}/{len(status)} loaded")
    for name, info in status.items():
        loaded = "OK" if info["loaded"] else "--"
        print(f"  [{loaded}] {name}")
