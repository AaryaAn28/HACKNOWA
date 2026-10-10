from enum import Enum
from dataclasses import dataclass
from .confidence import ConfidenceLevel

class VariableType(str, Enum):
    RAINFALL = "rainfall"
    SOIL_SATURATION = "soil_saturation"
    SURFACE_RUNOFF = "surface_runoff"
    DRAIN_CAPACITY = "drain_capacity"
    DRAIN_LOAD = "drain_load"
    WATER_DEPTH = "water_depth"
    WATER_VELOCITY = "water_velocity"
    ROAD_ACCESSIBILITY = "road_accessibility"
    TRAFFIC_DENSITY = "traffic_density"
    HEAT_FLUX = "heat_flux"
    SURFACE_TEMPERATURE = "surface_temperature"
    VEGETATION_CANOPY = "vegetation_canopy"
    EMERGENCY_ACCESS = "emergency_access"
    INFRASTRUCTURE_EXPOSURE = "infrastructure_exposure"

@dataclass(frozen=True)
class VariableDefinition:
    type: VariableType
    unit: str
    min_value: float
    max_value: float

@dataclass
class StateValue:
    value: float
    confidence: ConfidenceLevel
