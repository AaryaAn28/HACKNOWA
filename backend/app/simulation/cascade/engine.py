import typing
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class CascadeEvent:
    trigger: str
    affected_systems: List[str]
    chain_description: str
    time: float
    location: Optional[Dict[str, float]] = None

class CascadeEngine:
    """Engine responsible for managing cross-domain cascade effects between physical systems."""

    def __init__(self, flood_engine, heat_engine, traffic_engine, sewer_engine, emergency_engine, vegetation_engine):
        self.flood_engine = flood_engine
        self.heat_engine = heat_engine
        self.traffic_engine = traffic_engine
        self.sewer_engine = sewer_engine
        self.emergency_engine = emergency_engine
        self.vegetation_engine = vegetation_engine
        self.cascade_events: List[CascadeEvent] = []

    def run_cascade(self, world_state: Any, duration: float, dt: float) -> Dict[str, Any]:
        """Runs the cascade simulation for the given duration at steps of dt."""
        current_time = 0.0
        
        # State capture (before)
        initial_state = world_state.clone() if hasattr(world_state, 'clone') else world_state

        while current_time < duration:
            # 1. Run flood simulation
            flood_state = self.flood_engine.step(world_state, dt)
            
            # 2. Update road accessibility based on flood state
            road_closures = self.traffic_engine.update_accessibility(flood_state)
            
            # 3. Run traffic simulation with updated accessibility
            traffic_state = self.traffic_engine.step(world_state, dt)
            
            # 4. Run emergency simulation considering traffic and road closures
            emergency_state = self.emergency_engine.step(world_state, traffic_state, dt)

            # 5. Check and detect cascades
            self._detect_cascades(current_time, flood_state, road_closures, traffic_state, emergency_state)
            
            current_time += dt

        # State capture (after)
        final_state = world_state.clone() if hasattr(world_state, 'clone') else world_state

        return {
            "initial_state": initial_state,
            "final_state": final_state,
            "events": self.cascade_events
        }

    def _detect_cascades(self, current_time: float, flood_state, road_closures, traffic_state, emergency_state):
        """Detects cascading events based on subsystem interactions."""
        if road_closures and len(road_closures) > 0:
            # Check if traffic rerouted significantly
            if hasattr(traffic_state, 'rerouted') and traffic_state.rerouted:
                # Check if emergency response is delayed
                if hasattr(emergency_state, 'delay_increased') and emergency_state.delay_increased:
                    event = CascadeEvent(
                        trigger="flood",
                        affected_systems=["traffic", "emergency"],
                        chain_description="Flood caused road closure, leading to traffic rerouting and increased emergency response delay.",
                        time=current_time
                    )
                    self.cascade_events.append(event)

    def generate_cinematic_events(self) -> List[Dict[str, Any]]:
        """Generates a timeline of events for the camera system."""
        timeline = []
        for event in self.cascade_events:
            timeline.append({
                "time": event.time,
                "focus": event.location,
                "description": event.chain_description,
                "systems": event.affected_systems
            })
        return timeline

    def trace_cascade_chain(self, event: CascadeEvent) -> List[str]:
        """Traces the propagation path across subsystems."""
        path = [event.trigger]
        path.extend(event.affected_systems)
        return path
