from typing import Dict, List, Any
from pydantic import BaseModel
from .brain import CausalBrain
import networkx as nx

class ConsequenceReport(BaseModel):
    action_id: str
    direct_effects: List[Dict[str, Any]]
    secondary_effects: List[Dict[str, Any]]
    tertiary_effects: List[Dict[str, Any]]
    cascade_paths: List[List[str]]
    trade_offs: List[Dict[str, Any]]
    reversibility_score: float
    failure_modes: List[str]
    long_term_effects: List[Dict[str, Any]]

class ConsequenceEngine:
    def __init__(self, brain: CausalBrain):
        self.brain = brain
        
    def evaluate_action(self, action_id: str, action_node: str, intervention_magnitude: float) -> ConsequenceReport:
        """Trace consequences outward from an action point."""
        direct = []
        secondary = []
        tertiary = []
        trade_offs = []
        
        if action_node not in self.brain.graph:
            raise ValueError(f"Action node {action_node} not in Causal Brain.")
            
        successors_d1 = list(self.brain.graph.successors(action_node))
        
        successors_d2 = []
        for n in successors_d1:
            direct.append({"node": n, "impact": intervention_magnitude * self.brain.graph[action_node][n].get("strength", 0)})
            successors_d2.extend(list(self.brain.graph.successors(n)))
            
        successors_d3 = []
        for n in set(successors_d2):
            secondary.append({"node": n, "type": "secondary"})
            successors_d3.extend(list(self.brain.graph.successors(n)))
            
        for n in set(successors_d3):
            tertiary.append({"node": n, "type": "tertiary"})
            
        cf_results = self.brain.counterfactual_query({action_node: intervention_magnitude})
        
        positive_impacts = []
        negative_impacts = []
        for node, change in cf_results.items():
            if node == action_node: continue
            if change > 0:
                positive_impacts.append(node)
            elif change < 0:
                negative_impacts.append(node)
                
        if positive_impacts and negative_impacts:
            trade_offs.append({
                "improves": positive_impacts,
                "degrades": negative_impacts
            })
            
        cascade = self.brain.get_failure_chain(action_node) 
        
        return ConsequenceReport(
            action_id=action_id,
            direct_effects=direct,
            secondary_effects=secondary,
            tertiary_effects=tertiary,
            cascade_paths=cascade,
            trade_offs=trade_offs,
            reversibility_score=0.8,
            failure_modes=["Unintended resonance", "Resource exhaustion"],
            long_term_effects=[]
        )
