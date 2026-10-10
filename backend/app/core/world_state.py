import threading
import copy
from datetime import datetime
from typing import Dict, Any, List, Callable, Tuple
from dataclasses import dataclass, field

from .state_variables import VariableType, StateValue
from .audit_trail import AuditTrail
from .confidence import ConfidenceLevel

@dataclass(frozen=True)
class SpatialCell:
    cell_id: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float

@dataclass
class WorldStateSnapshot:
    version: int
    timestamp: datetime
    cells: Dict[str, Dict[VariableType, StateValue]]
    global_vars: Dict[str, Any]

class WorldState:
    """
    The centralized World State Engine. SINGLE SOURCE OF TRUTH.
    Thread-safe, observable, versioned.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._version: int = 0
        self._timestamp = datetime.utcnow()
        
        # Spatial grid mapping cell_id -> {VariableType: StateValue}
        self._grid: Dict[str, Dict[VariableType, StateValue]] = {}
        self._cells: Dict[str, SpatialCell] = {}
        
        # Global variables not bound to specific cells
        self._global_vars: Dict[str, Any] = {}
        
        self.audit_trail = AuditTrail()
        self._listeners: List[Callable[[int, Dict[str, Any]], None]] = []

    def initialize_grid(self, cells: List[SpatialCell]):
        with self._lock:
            for cell in cells:
                self._cells[cell.cell_id] = cell
                self._grid[cell.cell_id] = {}

    def get_version(self) -> int:
        with self._lock:
            return self._version

    def update_cell_variable(
        self, 
        cell_id: str, 
        var_type: VariableType, 
        value: float, 
        confidence: ConfidenceLevel,
        reason: str,
        agent_id: str = "system",
        model_version: str = "1.0"
    ):
        with self._lock:
            if cell_id not in self._grid:
                raise ValueError(f"Cell {cell_id} not initialized in WorldState.")
                
            old_val = self._grid[cell_id].get(var_type)
            new_val = StateValue(value=value, confidence=confidence)
            
            self._grid[cell_id][var_type] = new_val
            
            # Update version and timestamp
            self._version += 1
            self._timestamp = datetime.utcnow()
            
            # Audit log
            var_path = f"cell:{cell_id}:{var_type.value}"
            self.audit_trail.log(
                action_type="UPDATE_VAR",
                variable_path=var_path,
                old_value=old_val,
                new_value=new_val,
                reason=reason,
                agent_id=agent_id,
                model_version=model_version
            )
            
            self._notify_listeners(
                delta={"type": "CELL_UPDATE", "cell_id": cell_id, "var": var_type, "value": value}
            )

    def get_cell_variable(self, cell_id: str, var_type: VariableType) -> StateValue:
        with self._lock:
            return self._grid.get(cell_id, {}).get(var_type)

    def subscribe(self, callback: Callable[[int, Dict[str, Any]], None]):
        """Observable pattern: add a listener for state changes."""
        with self._lock:
            self._listeners.append(callback)

    def _notify_listeners(self, delta: Dict[str, Any]):
        version = self._version
        for listener in self._listeners:
            try:
                listener(version, delta)
            except Exception as e:
                # Log exception in real world
                pass

    def create_snapshot(self) -> WorldStateSnapshot:
        """Snapshot/restore for multi-future simulation."""
        with self._lock:
            return WorldStateSnapshot(
                version=self._version,
                timestamp=self._timestamp,
                cells=copy.deepcopy(self._grid),
                global_vars=copy.deepcopy(self._global_vars)
            )

    def restore_snapshot(self, snapshot: WorldStateSnapshot, reason: str = "Restore snapshot"):
        with self._lock:
            self._version = snapshot.version
            self._timestamp = snapshot.timestamp
            self._grid = copy.deepcopy(snapshot.cells)
            self._global_vars = copy.deepcopy(snapshot.global_vars)
            
            self.audit_trail.log(
                action_type="RESTORE_SNAPSHOT",
                variable_path="ALL",
                old_value="CURRENT_STATE",
                new_value=f"SNAPSHOT_V{self._version}",
                reason=reason,
                agent_id="system",
                model_version="N/A"
            )
            self._notify_listeners(delta={"type": "FULL_RESTORE", "version": self._version})

    def get_layer(self, layer_name: str) -> Any:
        import numpy as np
        with self._lock:
            if not hasattr(self, "_layers"):
                self._layers = {}
            if layer_name not in self._layers or self._layers[layer_name] is None:
                shape = (50, 50)
                if layer_name == "elevation":
                    self._layers[layer_name] = (np.linspace(15.0, 2.0, 50)[:, None] + np.random.normal(0, 0.2, shape)).astype(np.float32)
                elif layer_name == "land_cover":
                    self._layers[layer_name] = np.ones(shape, dtype=np.int32) * 2
                elif layer_name == "drains":
                    d = np.zeros(shape, dtype=np.float32)
                    d[25, 25] = 3.2
                    self._layers[layer_name] = d
                elif layer_name == "roads":
                    r = np.zeros(shape, dtype=bool)
                    r[20:30, :] = True
                    self._layers[layer_name] = r
                else:
                    self._layers[layer_name] = np.zeros(shape, dtype=np.float32)
            return self._layers[layer_name]

    def update_layer(self, layer_name: str, array: Any) -> None:
        with self._lock:
            if not hasattr(self, "_layers"):
                self._layers = {}
            self._layers[layer_name] = array
            self._version += 1

    def advance_time(self, dt: float) -> None:
        with self._lock:
            self._version += 1

