from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

class RegionCreate(BaseModel):
    name: str = Field(..., description="The name of the spatial region.")
    bounds: List[float] = Field(..., description="Bounding box [min_x, min_y, max_x, max_y].")
    crs: str = Field(default="EPSG:4326", description="Coordinate Reference System.")

class RegionResponse(BaseModel):
    id: int
    name: str
    crs: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SimulationRequest(BaseModel):
    region_id: int
    parameters: Dict[str, Any] = Field(default_factory=dict)

class SimulationResponse(BaseModel):
    id: int
    region_id: int
    status: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class InterventionGenerateRequest(BaseModel):
    region_id: int
    goal: str
    constraints: Optional[Dict[str, Any]] = None

class InterventionResponse(BaseModel):
    id: int
    actions: List[Dict[str, Any]]
    cost: float
    robustness: float

class CausalGraphResponse(BaseModel):
    id: int
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    version: str

class GapResponse(BaseModel):
    variable: str
    importance: float
    confidence_impact: float

class DriftCheckRequest(BaseModel):
    region_id: int
    recent_sensor_data: List[Dict[str, Any]]

class UploadResponse(BaseModel):
    id: int
    filename: str
    classification: str
    georef_confidence: float
