from enum import Enum
import networkx as nx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

class EmergencyVehicleType(Enum):
    AMBULANCE = "AMBULANCE"
    FIRE_ENGINE = "FIRE_ENGINE"
    RESCUE = "RESCUE"
    EVACUATION_BUS = "EVACUATION_BUS"

@dataclass
class TradeOff:
    metric_improved: str
    metric_degraded: str
    description: str

class EmergencyResponseEngine:
    def __init__(self):
        self.road_network = nx.DiGraph()
        
        # Base speeds in km/h
        self.base_speeds = {
            EmergencyVehicleType.AMBULANCE: 80.0,
            EmergencyVehicleType.FIRE_ENGINE: 70.0,
            EmergencyVehicleType.RESCUE: 75.0,
            EmergencyVehicleType.EVACUATION_BUS: 50.0
        }
        self.congested_speeds = {
            EmergencyVehicleType.AMBULANCE: 40.0,
            EmergencyVehicleType.FIRE_ENGINE: 35.0,
            EmergencyVehicleType.RESCUE: 40.0,
            EmergencyVehicleType.EVACUATION_BUS: 20.0
        }
        
    def add_road_segment(self, u: str, v: str, length_km: float, congestion: float = 0.0, flood_depth_m: float = 0.0):
        self.road_network.add_edge(u, v, length_km=length_km, congestion=congestion, flood_depth=flood_depth_m)

    def calculate_effective_speed(self, vehicle: EmergencyVehicleType, congestion: float, flood_depth: float) -> float:
        if flood_depth > 0.3:
            return 0.0
        
        flood_factor = 1.0 if flood_depth < 0.1 else 0.5
        
        base = self.base_speeds[vehicle]
        congested = self.congested_speeds[vehicle]
        
        # Linear interpolation between base and congested based on congestion factor (0 to 1)
        speed = base - (base - congested) * congestion
        
        return speed * flood_factor

    def calculate_response_time(self, source: str, target: str, vehicle: EmergencyVehicleType) -> Optional[float]:
        def weight_func(u, v, d):
            speed = self.calculate_effective_speed(vehicle, d['congestion'], d['flood_depth'])
            if speed <= 0.0:
                return float('inf')
            # time in minutes = (distance / speed) * 60
            return (d['length_km'] / speed) * 60.0

        try:
            length = nx.dijkstra_path_length(self.road_network, source, target, weight=weight_func)
            return length if length != float('inf') else None
        except nx.NetworkXNoPath:
            return None

    def calculate_accessibility_changes(self, source: str, target: str, vehicle: EmergencyVehicleType) -> Dict[str, Any]:
        # Normal (no flood, no congestion)
        original_states = {}
        for u, v, d in self.road_network.edges(data=True):
            original_states[(u,v)] = (d['congestion'], d['flood_depth'])
            d['congestion'] = 0.0
            d['flood_depth'] = 0.0
            
        normal_time = self.calculate_response_time(source, target, vehicle)
        
        # Restore disaster states
        for u, v, d in self.road_network.edges(data=True):
            d['congestion'], d['flood_depth'] = original_states[(u,v)]
            
        disaster_time = self.calculate_response_time(source, target, vehicle)
        
        return {
            "normal_time_min": normal_time,
            "disaster_time_min": disaster_time,
            "delay_min": (disaster_time - normal_time) if (disaster_time and normal_time) else None,
            "accessible": disaster_time is not None
        }

    def detect_trade_offs(self, intervention_name: str, flood_reduction_pct: float, 
                          original_response_time: float, new_response_time: float, 
                          target_name: str) -> Optional[TradeOff]:
        if flood_reduction_pct > 0 and new_response_time > original_response_time:
            desc = (f"Intervention {intervention_name} reduces flood by {flood_reduction_pct}% "
                    f"but increases ambulance response to {target_name} from {original_response_time:.1f}min to {new_response_time:.1f}min")
            return TradeOff(
                metric_improved="Flood Reduction",
                metric_degraded="Emergency Access",
                description=desc
            )
        return None
