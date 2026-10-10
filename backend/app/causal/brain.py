import networkx as nx
from typing import Dict, List, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import copy

class CausalEdge(BaseModel):
    source: str
    target: str
    strength: float = Field(..., description="-1.0 to 1.0, magnitude of causal effect")
    confidence: float = Field(..., description="0.0 to 1.0, confidence in relationship")
    evidence_source: str = "expert_domain"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True

class CausalNode(BaseModel):
    id: str
    name: str
    variable_type: str
    current_value: float = 0.0
    baseline_value: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CausalBrain:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.snapshots: Dict[str, nx.DiGraph] = {}
        
    def add_node(self, node: CausalNode):
        self.graph.add_node(node.id, **node.model_dump())
        
    def update_node_value(self, node_id: str, new_value: float):
        if node_id in self.graph:
            self.graph.nodes[node_id]['current_value'] = new_value
            
    def add_edge(self, edge: CausalEdge):
        if edge.source not in self.graph or edge.target not in self.graph:
            raise ValueError("Source or target node does not exist")
        self.graph.add_edge(edge.source, edge.target, **edge.model_dump())
        
    def remove_edge(self, source: str, target: str):
        if self.graph.has_edge(source, target):
            self.graph.remove_edge(source, target)
            
    def create_snapshot(self, version_name: str):
        self.snapshots[version_name] = copy.deepcopy(self.graph)
        
    def get_failure_chain(self, effect_node_id: str, min_confidence: float = 0.5) -> List[List[str]]:
        """Trace backward from an effect to root causes."""
        if effect_node_id not in self.graph:
            return []
            
        chains = []
        for root in self.graph.nodes():
            if root != effect_node_id and self.graph.in_degree(root) == 0:
                paths = nx.all_simple_paths(self.graph, source=root, target=effect_node_id)
                for path in paths:
                    valid = True
                    for i in range(len(path)-1):
                        u, v = path[i], path[i+1]
                        if self.graph[u][v].get('confidence', 0) < min_confidence or not self.graph[u][v].get('active', True):
                            valid = False
                            break
                    if valid:
                        chains.append(path)
        return chains

    def dominant_pathway(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find the pathway with the highest combined strength and confidence."""
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return None
            
        paths = list(nx.all_simple_paths(self.graph, source=source_id, target=target_id))
        if not paths:
            return None
            
        best_path = None
        best_score = -1
        
        for path in paths:
            score = 1.0
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                edge_data = self.graph[u][v]
                if not edge_data.get('active', True):
                    score = 0
                    break
                strength = abs(edge_data.get('strength', 0))
                conf = edge_data.get('confidence', 0)
                score *= (strength * conf)
            
            if score > best_score:
                best_score = score
                best_path = path
                
        return best_path

    def counterfactual_query(self, interventions: Dict[str, float]) -> Dict[str, float]:
        """
        'What if' query: Apply interventions (node_id -> new_value) and compute expected changes.
        """
        temp_graph = copy.deepcopy(self.graph)
        changes = {k: v for k, v in interventions.items()}
        
        queue = list(interventions.keys())
        while queue:
            current = queue.pop(0)
            current_change = changes[current]
            
            for successor in temp_graph.successors(current):
                edge_data = temp_graph[current][successor]
                if not edge_data.get('active', True):
                    continue
                    
                strength = edge_data.get('strength', 0.0)
                effect = current_change * strength
                
                if successor not in changes:
                    changes[successor] = 0.0
                changes[successor] += effect
                
                queue.append(successor)
                
        return changes
