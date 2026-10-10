import networkx as nx
from typing import List, Dict, Any, Tuple
import math

class PipeNetwork:
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def add_pipe(self, pipe_id: str, u: str, v: str, diameter: float, length: float, roughness: float, slope: float, degradation: float = 1.0):
        # Manning's capacity (full pipe)
        area = math.pi * (diameter / 2) ** 2
        radius_hydro = diameter / 4
        capacity = (1.0 / roughness) * area * (radius_hydro ** (2/3)) * math.sqrt(abs(slope)) * degradation
        self.graph.add_edge(u, v, pipe_id=pipe_id, diameter=diameter, length=length, 
                            roughness=roughness, slope=slope, capacity=capacity, 
                            degradation=degradation, current_load=0.0)
        self.graph.nodes[u]['type'] = 'node'
        self.graph.nodes[v]['type'] = 'node'

    def step(self, inflows: Dict[str, float], dt: float) -> Tuple[Dict[str, float], List[str]]:
        # Reset loads
        for u, v, data in self.graph.edges(data=True):
            data['current_load'] = 0.0
            
        overflows = {node: 0.0 for node in self.graph.nodes}
        
        # Topological sort for gravity flow
        try:
            sorted_nodes = list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            # Handle cycles (shouldn't happen in purely gravity network without pumps, but fallback)
            sorted_nodes = list(self.graph.nodes)

        node_loads = {node: inflows.get(node, 0.0) for node in self.graph.nodes}
        
        bottleneck_pipes = []

        for node in sorted_nodes:
            out_edges = list(self.graph.out_edges(node, data=True))
            if not out_edges:
                continue
            
            # Distribute load to outgoing pipes (simple proportional or all to single outlet)
            total_capacity = sum(data['capacity'] for _, _, data in out_edges)
            
            load_to_distribute = node_loads[node]
            
            if total_capacity == 0:
                overflows[node] += load_to_distribute * dt
                continue

            for u, v, data in out_edges:
                fraction = data['capacity'] / total_capacity
                pipe_inflow = load_to_distribute * fraction
                
                if pipe_inflow > data['capacity']:
                    overflow_rate = pipe_inflow - data['capacity']
                    overflows[node] += overflow_rate * dt
                    actual_flow = data['capacity']
                else:
                    actual_flow = pipe_inflow
                    
                data['current_load'] += actual_flow
                node_loads[v] = node_loads.get(v, 0.0) + actual_flow
                
                ratio = data['current_load'] / data['capacity']
                if ratio > 0.8:
                    bottleneck_pipes.append(data['pipe_id'])
                    
        return overflows, bottleneck_pipes

    def diagnose_failure(self, pipe_id: str) -> Dict[str, Any]:
        target_edge = None
        for u, v, data in self.graph.edges(data=True):
            if data['pipe_id'] == pipe_id:
                target_edge = (u, v, data)
                break
                
        if not target_edge:
            return {"error": "Pipe not found"}
            
        u, v, data = target_edge
        
        upstream_nodes = list(nx.ancestors(self.graph, u))
        upstream_nodes.append(u)
        
        upstream_inflow = sum(self.graph.nodes[n].get('inflow', 0.0) for n in upstream_nodes)
        
        # Check downstream backpressure
        downstream_edges = list(self.graph.out_edges(v, data=True))
        backpressure = False
        if downstream_edges:
            for du, dv, ddata in downstream_edges:
                if ddata['current_load'] >= ddata['capacity']:
                    backpressure = True
                    break

        diagnosis = {
            "pipe_id": pipe_id,
            "load_ratio": data['current_load'] / data['capacity'] if data['capacity'] > 0 else float('inf'),
            "too_much_inflow": data['current_load'] > data['capacity'],
            "downstream_backpressure": backpressure,
            "low_capacity": data['capacity'] < 0.1, # Arbitrary threshold
            "degradation_impact": data['degradation'] < 0.8
        }
        
        reasons = []
        if diagnosis['too_much_inflow']: reasons.append("Upstream inflow exceeds capacity.")
        if diagnosis['downstream_backpressure']: reasons.append("Downstream network is backed up.")
        if diagnosis['low_capacity']: reasons.append("Pipe capacity is inherently low (possibly flat slope or small diameter).")
        if diagnosis['degradation_impact']: reasons.append("Pipe condition degradation restricts flow.")
        
        diagnosis["root_cause"] = " | ".join(reasons) if reasons else "Normal operation"
        
        return diagnosis
