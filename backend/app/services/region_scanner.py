import typing
from typing import Dict, Any, List
import networkx as nx

class RegionScanner:
    """Pipeline for scanning and initializing regional models from raw data."""

    def __init__(self, ingestion_pipeline, critical_node_detector, data_gap_analyzer, question_engine, simulation_engine):
        self.ingestion = ingestion_pipeline
        self.detector = critical_node_detector
        self.gap_analyzer = data_gap_analyzer
        self.question_engine = question_engine
        self.sim_engine = simulation_engine

    def scan_everything(self, files: List[str]) -> Dict[str, Any]:
        """Executes the full scanning and initialization pipeline."""
        progress = 0.0
        self._update_progress(progress, "Starting ingestion")
        
        # 1. Ingestion
        extracted_data = self.ingestion.process(files)
        progress = 20.0
        self._update_progress(progress, "Building spatial inventory")

        # 2. Inventory & Graph Construction
        inventory = self._build_inventory(extracted_data)
        infrastructure_graph = self._build_graphs(extracted_data)
        progress = 40.0
        self._update_progress(progress, "Initializing World State")

        # 3. World State
        world_state = self._initialize_world_state(inventory, infrastructure_graph)
        progress = 60.0
        self._update_progress(progress, "Running baseline simulation")

        # 4. Baseline Simulation
        baseline_results = self.sim_engine.run_baseline(world_state)
        progress = 80.0
        self._update_progress(progress, "Analyzing risks and gaps")

        # 5. Analysis
        critical_nodes = self.detector.detect_nodes(world_state, baseline_results)
        data_gaps = self.gap_analyzer.find_gaps(world_state)
        questions = self.question_engine.generate_questions(world_state)
        
        progress = 100.0
        self._update_progress(progress, "Scan complete")

        # Calculate completeness
        completeness = self._calculate_completeness(data_gaps)

        return {
            "status": "success",
            "extracted_objects_count": len(inventory),
            "graph_nodes_count": infrastructure_graph.number_of_nodes(),
            "critical_nodes": critical_nodes,
            "data_gaps": data_gaps,
            "questions": questions,
            "reconstruction_completeness": completeness
        }

    def _update_progress(self, percentage: float, status: str):
        """Updates internal progress tracking."""
        self.current_progress = percentage
        self.current_status = status

    def _build_inventory(self, data: Any) -> List[Any]:
        return data.get("objects", []) if isinstance(data, dict) else []

    def _build_graphs(self, data: Any) -> nx.Graph:
        G = nx.Graph()
        # Mock graph construction logic
        G.add_node("Road_1")
        G.add_node("Drain_1")
        G.add_edge("Road_1", "Drain_1")
        return G

    def _initialize_world_state(self, inventory: List[Any], graph: nx.Graph) -> Any:
        class MockWorldState:
            def __init__(self, inv, g):
                self.inventory = inv
                self.graph = g
        return MockWorldState(inventory, graph)
        
    def _calculate_completeness(self, data_gaps: List[Any]) -> float:
        if not data_gaps:
            return 100.0
        return max(0.0, 100.0 - len(data_gaps) * 5.0)
