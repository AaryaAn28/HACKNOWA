import networkx as nx
from typing import Dict, List, Any
import numpy as np
from .brain import CausalBrain, CausalNode, CausalEdge

class GraphBuilder:
    def __init__(self, brain: CausalBrain):
        self.brain = brain
        self.templates = {
            "storm_drain": [
                ("rainfall", "runoff", 0.9),
                ("runoff", "drain_load", 0.8),
                ("drain_load", "overflow", 0.7),
                ("overflow", "flooding", 0.95)
            ],
            "traffic_disruption": [
                ("flooding", "road_closure", 0.8),
                ("road_closure", "traffic_congestion", 0.9),
                ("traffic_congestion", "emergency_delay", 0.7)
            ]
        }

    def apply_domain_template(self, template_name: str, prefix: str = ""):
        """Apply pre-defined causal structures to the brain."""
        if template_name not in self.templates:
            return
            
        relationships = self.templates[template_name]
        for src, tgt, strength in relationships:
            src_id = f"{prefix}{src}" if prefix else src
            tgt_id = f"{prefix}{tgt}" if prefix else tgt
            
            if src_id not in self.brain.graph:
                self.brain.add_node(CausalNode(id=src_id, name=src_id, variable_type="template_var"))
            if tgt_id not in self.brain.graph:
                self.brain.add_node(CausalNode(id=tgt_id, name=tgt_id, variable_type="template_var"))
                
            self.brain.add_edge(CausalEdge(
                source=src_id,
                target=tgt_id,
                strength=strength,
                confidence=0.8,
                evidence_source=f"template:{template_name}"
            ))

    def detect_from_timeseries(self, data: Dict[str, List[float]], correlation_threshold: float = 0.6):
        """Infer causal edges from correlated timeseries data."""
        variables = list(data.keys())
        for i in range(len(variables)):
            for j in range(len(variables)):
                if i == j: continue
                
                var1 = variables[i]
                var2 = variables[j]
                
                ts1 = np.array(data[var1])
                ts2 = np.array(data[var2])
                
                if len(ts1) < 2 or len(ts1) != len(ts2):
                    continue
                
                corr = np.corrcoef(ts1[:-1], ts2[1:])[0, 1]
                
                if abs(corr) > correlation_threshold:
                    if var1 not in self.brain.graph:
                        self.brain.add_node(CausalNode(id=var1, name=var1, variable_type="inferred"))
                    if var2 not in self.brain.graph:
                        self.brain.add_node(CausalNode(id=var2, name=var2, variable_type="inferred"))
                        
                    self.brain.add_edge(CausalEdge(
                        source=var1,
                        target=var2,
                        strength=float(corr),
                        confidence=abs(float(corr)),
                        evidence_source="timeseries_inference"
                    ))
