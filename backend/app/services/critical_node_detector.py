import typing
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CriticalNode:
    id: str
    composite_score: float
    factors: Dict[str, float]
    explanation: str

class CriticalNodeDetector:
    """Detects critical vulnerable nodes across the region based on multi-factor scoring."""

    def __init__(self):
        self.weights = {
            "flood": 0.3,
            "infrastructure": 0.2,
            "population": 0.15,
            "traffic": 0.1,
            "emergency": 0.1,
            "drainage": 0.1,
            "heat": 0.05
        }

    def detect_nodes(self, world_state: Any, causal_brain: Any, threshold: float = 0.6) -> List[CriticalNode]:
        """Detects nodes whose composite risk score exceeds the threshold."""
        nodes = world_state.get_nodes() if hasattr(world_state, 'get_nodes') else []
        critical_nodes = []

        for node in nodes:
            factors = self._compute_factors(node, world_state, causal_brain)
            composite_score = sum(factors[k] * self.weights.get(k, 0) for k in factors)

            if composite_score > threshold:
                explanation = self.generate_explanation(node, factors, causal_brain)
                critical_nodes.append(CriticalNode(
                    id=node.get('id', 'unknown'),
                    composite_score=composite_score,
                    factors=factors,
                    explanation=explanation
                ))
        
        return critical_nodes

    def _compute_factors(self, node: Dict[str, Any], world_state: Any, causal_brain: Any) -> Dict[str, float]:
        """Computes individual risk factors for a node."""
        factors = {}
        
        # Flood score
        depth = node.get("water_depth", 0.0)
        max_tol = node.get("max_tolerable_depth", 0.5)
        factors["flood"] = min(1.0, depth / max_tol) if max_tol > 0 else 0.0

        # Infrastructure score (from causal graph dependencies)
        deps = causal_brain.get_dependencies(node.get('id')) if hasattr(causal_brain, 'get_dependencies') else []
        factors["infrastructure"] = min(1.0, len(deps) / 10.0)

        # Population score
        density = node.get("building_density", 0.0)
        floors = node.get("floors", 1)
        factors["population"] = min(1.0, (density * floors) / 100.0)

        # Traffic score
        traffic_den = node.get("traffic_density", 0.0)
        capacity = node.get("road_capacity", 1.0)
        factors["traffic"] = min(1.0, traffic_den / capacity) if capacity > 0 else 0.0

        # Emergency score
        norm_resp = node.get("normal_response_time", 300)
        dis_resp = node.get("disaster_response_time", 300)
        factors["emergency"] = max(0.0, 1.0 - (norm_resp / dis_resp)) if dis_resp > 0 else 0.0

        # Drainage score
        load = node.get("drain_load", 0.0)
        drain_cap = node.get("drain_capacity", 1.0)
        factors["drainage"] = min(1.0, load / drain_cap) if drain_cap > 0 else 0.0

        # Heat score
        temp = node.get("surface_temperature", 25.0)
        heat_thresh = node.get("heat_threshold", 40.0)
        factors["heat"] = min(1.0, temp / heat_thresh) if heat_thresh > 0 else 0.0

        return factors

    def generate_explanation(self, node: Dict[str, Any], factors: Dict[str, float], causal_brain: Any) -> str:
        """Generates a causal explanation tracing backwards."""
        node_id = node.get('id', 'unknown')
        
        reasons = []
        if factors.get("flood", 0) > 0.8:
            reasons.append("high flood depth (SIMULATED)")
        if factors.get("infrastructure", 0) > 0.5:
            reasons.append("many dependent systems (DERIVED)")
        if factors.get("drainage", 0) > 0.9:
            reasons.append("drain capacity exceeded (SIMULATED)")
            
        reason_str = ", ".join(reasons) if reasons else "multiple interacting factors"
        return f"Node {node_id} is critical because: {reason_str}"
