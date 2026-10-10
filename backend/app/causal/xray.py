import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel
from .brain import CausalBrain

class XRayResult(BaseModel):
    baseline_predictions: Dict[str, float]
    modified_predictions: Dict[str, float]
    impact_diff: Dict[str, float]
    sensitivity_scores: Dict[str, float]

class CausalXRay:
    def __init__(self, brain: CausalBrain):
        self.brain = brain
        
    def toggle_edge(self, source: str, target: str, active: bool):
        """Temporarily disable or enable an edge to see its structural importance."""
        if self.brain.graph.has_edge(source, target):
            self.brain.graph[source][target]['active'] = active
            
    def run_sensitivity_analysis(self, target_nodes: List[str]) -> Dict[Tuple[str, str], float]:
        """Determine which edges have the most impact on target nodes."""
        sensitivity = {}
        roots = [n for n, d in self.brain.graph.in_degree() if d == 0]
        
        for edge in self.brain.graph.edges():
            u, v = edge
            original_state = self.brain.graph[u][v].get('active', True)
            
            self.toggle_edge(u, v, False)
            
            impact_score = 0.0
            for target in target_nodes:
                for root in roots:
                    if nx.has_path(self.brain.graph, root, target):
                        impact_score += 0.1
                    else:
                        impact_score += 1.0 
            
            sensitivity[(u, v)] = impact_score
            self.toggle_edge(u, v, original_state)
            
        return sensitivity

    def generate_visual_data(self) -> Dict[str, Any]:
        """Export graph data for frontend causal animation."""
        nodes = []
        for n, data in self.brain.graph.nodes(data=True):
            nodes.append({
                "id": n,
                "label": data.get("name", n),
                "value": data.get("current_value", 0.0)
            })
            
        edges = []
        for u, v, data in self.brain.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "strength": data.get("strength", 0.0),
                "confidence": data.get("confidence", 0.0),
                "active": data.get("active", True)
            })
            
        return {
            "nodes": nodes,
            "edges": edges
        }
