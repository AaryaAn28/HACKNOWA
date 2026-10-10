import abc
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

class SimulationTimeMode(str, Enum):
    REAL_TIME = "REAL_TIME"
    ACCELERATED = "ACCELERATED"
    LONG_HORIZON = "LONG_HORIZON"

@dataclass
class SimulationEvent:
    event_type: str
    timestamp: float
    data: Dict[str, Any]
    source: str
    severity: int = 1

class ISimulationModel(abc.ABC):
    @abc.abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        pass
        
    @abc.abstractmethod
    def step(self, dt: float) -> List[SimulationEvent]:
        pass
        
    @abc.abstractmethod
    def get_state(self) -> Dict[str, Any]:
        pass

class IFloodModel(abc.ABC):
    @abc.abstractmethod
    def get_water_depth(self) -> Any:
        pass

class IHeatModel(abc.ABC):
    @abc.abstractmethod
    def get_temperature(self) -> Any:
        pass

class ITrafficModel(abc.ABC):
    @abc.abstractmethod
    def get_traffic_flow(self) -> Any:
        pass

class IDrainageModel(abc.ABC):
    @abc.abstractmethod
    def get_drainage_capacity(self) -> Any:
        pass
