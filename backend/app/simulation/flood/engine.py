import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import time

try:
    from app.simulation.interfaces import ISimulationModel
except ImportError:
    # Fallback if interface is not available in environment
    class ISimulationModel:
        def initialize(self, world_state: Any) -> None:
            pass
        def step(self, dt: float, world_state: Any) -> Tuple[Any, List[Any]]:
            pass

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    RAIN_START = "RAIN_START"
    DRAIN_STRESS = "DRAIN_STRESS"
    DRAIN_OVERFLOW = "DRAIN_OVERFLOW"
    FLOOD_ZONE_CREATED = "FLOOD_ZONE_CREATED"
    ROAD_CLOSED = "ROAD_CLOSED"

@dataclass
class SimulationEvent:
    type: str
    timestamp: float
    details: Dict[str, Any]
    location: Optional[Tuple[int, int]] = None

class FloodSimulationEngine(ISimulationModel):
    """
    Grid-based flood simulation engine with physical processes:
    - Rainfall and Vegetation Interception
    - SCS Curve Number infiltration
    - Surface flow using Manning's equation
    - Drainage infrastructure interactions
    - Road accessibility tracking
    """

    # SCS Curve Numbers by land cover type (using arbitrary integer mapping for land cover)
    # 1=impervious, 2=urban, 3=grass, 4=forest, 5=water
    CN_VALUES = {
        1: 98,
        2: 85,
        3: 61,
        4: 55,
        5: 100
    }

    # Manning's n roughness coefficients
    MANNING_N = {
        1: 0.015, # asphalt
        2: 0.013, # concrete
        3: 0.035, # grass
        4: 0.10,  # forest
        5: 0.025  # channel
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cell_size = config.get('cell_size', 1.0) # meters
        self.cell_area = self.cell_size ** 2
        self.max_velocity = config.get('max_velocity', 5.0) # m/s
        self.demo_mode = config.get('demo_mode', False)
        
        if self.demo_mode:
            np.random.seed(config.get('seed', 42))
            
        self.water_depth = None
        self.drain_loads = None
        self.initialized = False
        self.current_time = 0.0
        
        # State grids
        self.elevation = None
        self.land_cover = None
        self.cn_grid = None
        self.n_grid = None
        self.drains = None # Grid of drain capacities
        self.drain_remaining_capacity = None
        self.road_mask = None
        
        # Cumulative states
        self.cumulative_rainfall = 0.0 # mm

    def initialize(self, world_state: Any) -> None:
        """Initialize simulation grids from world state."""
        # Assuming world_state has a method get_layer(name) returning a 2D numpy array
        try:
            self.elevation = np.array(world_state.get_layer("elevation"), dtype=np.float32)
            self.land_cover = np.array(world_state.get_layer("land_cover"), dtype=np.int32)
            
            # Optional layers
            try:
                self.drains = np.array(world_state.get_layer("drains"), dtype=np.float32)
            except Exception:
                self.drains = np.zeros_like(self.elevation)
                
            try:
                self.road_mask = np.array(world_state.get_layer("roads"), dtype=bool)
            except Exception:
                self.road_mask = np.zeros_like(self.elevation, dtype=bool)
                
        except Exception as e:
            logger.warning(f"Failed to read from world_state, using defaults: {e}")
            # Fallback for testing
            shape = (100, 100)
            self.elevation = np.zeros(shape, dtype=np.float32)
            self.land_cover = np.ones(shape, dtype=np.int32) * 2 # default urban
            self.drains = np.zeros(shape, dtype=np.float32)
            self.road_mask = np.zeros(shape, dtype=bool)

        shape = self.elevation.shape
        self.water_depth = np.zeros(shape, dtype=np.float32)
        self.drain_loads = np.zeros(shape, dtype=np.float32)
        self.drain_remaining_capacity = np.copy(self.drains)
        
        # Precompute CN and Manning's n grids
        self.cn_grid = np.vectorize(lambda x: self.CN_VALUES.get(x, 85))(self.land_cover).astype(np.float32)
        self.n_grid = np.vectorize(lambda x: self.MANNING_N.get(x, 0.013))(self.land_cover).astype(np.float32)
        
        self.initialized = True
        logger.info("Flood simulation engine initialized.")

    def _calculate_infiltration(self, rainfall_mm: float) -> np.ndarray:
        """SCS Curve Number infiltration calculation."""
        S = (25400.0 / self.cn_grid) - 254.0 # Potential maximum retention in mm
        Ia = 0.2 * S # Initial abstraction
        
        # P must be greater than Ia for runoff to occur
        P = self.cumulative_rainfall
        
        # Total runoff depth up to this point
        Q_total = np.where(P > Ia, ((P - Ia) ** 2) / (P - Ia + S), 0.0)
        
        # Runoff for this timestep is difference between total runoff and previous total
        # For simplicity in this incremental step, we approximate incremental runoff
        # A more precise way is tracking cumulative Q, but we can do incremental:
        
        # Infiltration = Rainfall - Runoff
        # Actually, let's just use a simplified capacity approach based on CN for incremental
        infil_capacity = (S / 24.0) * (self.cell_size) # approximate hourly rate to dt
        return infil_capacity

    def step(self, dt: float, world_state: Any) -> Tuple[Any, List[SimulationEvent]]:
        """
        Execute one simulation step.
        dt: time step in seconds.
        """
        if not self.initialized:
            self.initialize(world_state)
            
        events = []
        
        # 1. CFL Condition check
        max_v = np.max(self.water_depth) # rough proxy for velocity limits in simple cases
        if max_v > 0 and dt > self.cell_size / min(self.max_velocity, max_v + 1e-6):
            # Cap dt for stability
            dt = self.cell_size / min(self.max_velocity, max_v + 1e-6)
            
        # 2. Rainfall and Interception
        precip_rate_mm_hr = self.config.get('precipitation_rate', 0.0) # mm/hr
        if precip_rate_mm_hr > 0 and self.current_time == 0:
            events.append(SimulationEvent(EventType.RAIN_START, self.current_time, {"rate": precip_rate_mm_hr}))
            
        precip_m = (precip_rate_mm_hr / 3600.0) * dt / 1000.0 # convert to meters
        self.cumulative_rainfall += precip_rate_mm_hr * (dt / 3600.0)
        
        # Simple interception (canopy fraction * capacity)
        interception = np.where(self.land_cover == 4, 0.002, 0.0) # 2mm for forest
        net_precip_m = np.maximum(0, precip_m - interception)
        
        # 3. Add net precipitation to water depth
        self.water_depth += net_precip_m
        
        # 4. Infiltration (SCS CN)
        # S (in meters) = ((25400 / CN) - 254) / 1000
        S = ((25400.0 / self.cn_grid) - 254.0) / 1000.0
        Ia = 0.2 * S
        
        # Only infiltrate if depth > 0
        active_infil = self.water_depth > 0
        if np.any(active_infil):
            # Simplified infiltration rate based on available capacity
            infil_rate = (S / 3600.0) * dt # m per timestep (rough approximation)
            actual_infil = np.minimum(self.water_depth, infil_rate)
            self.water_depth -= actual_infil
            
        # 5. Surface flow using Manning's equation
        # Calculate water surface elevation
        wse = self.elevation + self.water_depth
        
        # Calculate gradients (slopes) in x and y
        dy, dx = np.gradient(wse, self.cell_size)
        slope = np.sqrt(dx**2 + dy**2)
        
        # Avoid division by zero
        slope_clamped = np.maximum(slope, 1e-6)
        
        # Flow velocity: V = (1/n) * R^(2/3) * S^(1/2)
        # For overland, R ≈ water_depth
        velocity = (1.0 / self.n_grid) * (self.water_depth ** (2.0/3.0)) * np.sqrt(slope)
        velocity = np.clip(velocity, 0, self.max_velocity)
        
        # Calculate fluxes between cells (simplified explicit upwind scheme)
        flux_x = -velocity * (dx / slope_clamped) * self.water_depth * dt / self.cell_size
        flux_y = -velocity * (dy / slope_clamped) * self.water_depth * dt / self.cell_size
        
        # Compute divergence to update depths
        # Ensure we don't extract more water than available
        div_x = np.gradient(flux_x, axis=1)
        div_y = np.gradient(flux_y, axis=0)
        
        net_flow = (div_x + div_y)
        self.water_depth = np.maximum(0.0, self.water_depth + net_flow)
        
        # 6. Drain intake modeling
        has_drain = self.drains > 0
        if np.any(has_drain):
            # Intake is min of water above drain and drain capacity per timestep
            intake = np.minimum(self.water_depth[has_drain], self.drain_remaining_capacity[has_drain] * dt)
            self.water_depth[has_drain] -= intake
            self.drain_loads[has_drain] += intake
            
            # Overflow
            overflow_mask = self.drain_loads > self.drains
            if np.any(overflow_mask):
                # We need to map overflow_mask (which is on the has_drain subset) back to the full grid
                full_overflow_mask = np.zeros_like(self.water_depth, dtype=bool)
                # Assign values back using boolean indexing
                drain_indices = np.where(has_drain)
                # Filter drain_indices by overflow_mask
                overflow_idx = (drain_indices[0][overflow_mask], drain_indices[1][overflow_mask])
                
                overflow_amount = self.drain_loads[overflow_idx] - self.drains[overflow_idx]
                self.drain_loads[overflow_idx] = self.drains[overflow_idx]
                self.water_depth[overflow_idx] += overflow_amount
                
                events.append(SimulationEvent(
                    EventType.DRAIN_OVERFLOW, 
                    self.current_time, 
                    {"overflow_cells": int(np.sum(overflow_mask))}
                ))
            
            # Check stress
            stress_mask = self.drain_loads > (self.drains * 0.9)
            if np.any(stress_mask) and np.random.random() < 0.1: # Throttle event generation
                events.append(SimulationEvent(
                    EventType.DRAIN_STRESS,
                    self.current_time,
                    {"stressed_cells": int(np.sum(stress_mask))}
                ))
                
        # 7. Road impacts
        if self.road_mask is not None and np.any(self.road_mask):
            road_water = self.water_depth[self.road_mask]
            closed_roads = np.sum(road_water >= 0.3)
            
            if closed_roads > 0:
                events.append(SimulationEvent(
                    EventType.ROAD_CLOSED,
                    self.current_time,
                    {"closed_road_cells": int(closed_roads)}
                ))
                
            # Update world state with accessibility
            road_accessibility = np.ones_like(self.water_depth, dtype=bool)
            road_accessibility[self.road_mask] = self.water_depth[self.road_mask] < 0.3
            if hasattr(world_state, 'update_layer'):
                world_state.update_layer("road_accessibility", road_accessibility)

        # 8. Flood zones
        flood_cells = np.sum(self.water_depth > 0.1)
        if flood_cells > 0 and np.random.random() < 0.05:
            events.append(SimulationEvent(
                EventType.FLOOD_ZONE_CREATED,
                self.current_time,
                {"flooded_cells": int(flood_cells)}
            ))

        # Update world state with water depth
        if hasattr(world_state, 'update_layer'):
            world_state.update_layer("water_depth", self.water_depth)
            
        self.current_time += dt
        
        return world_state, events

    def reset(self) -> None:
        """Reset simulation state."""
        self.initialized = False
        self.current_time = 0.0
        self.cumulative_rainfall = 0.0
        self.water_depth = None
        self.drain_loads = None
        logger.info("Flood simulation engine reset.")

    def get_state(self) -> Dict[str, Any]:
        """Return current physical flood state summary."""
        return {
            "current_time_sec": self.current_time,
            "cumulative_rainfall_mm": self.cumulative_rainfall,
            "max_water_depth_m": float(np.max(self.water_depth)) if self.water_depth is not None else 0.0,
            "mean_water_depth_m": float(np.mean(self.water_depth)) if self.water_depth is not None else 0.0,
            "initialized": self.initialized
        }

