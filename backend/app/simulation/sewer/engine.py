from enum import Enum
from typing import Dict, Any, List

class Confidence(Enum):
    OBSERVED = "OBSERVED"
    ESTIMATED = "ESTIMATED"
    INFERRED = "INFERRED"
    SIMULATED = "SIMULATED"
    UNKNOWN = "UNKNOWN"

class DiagnosisCause(Enum):
    INSUFFICIENT_DIAMETER = "Insufficient pipe diameter"
    LOW_SLOPE = "Low slope / gradient"
    UPSTREAM_OVERLOAD = "Upstream overload (too much inflow)"
    DOWNSTREAM_BACKPRESSURE = "Downstream backpressure (downstream pipe at capacity)"
    BLOCKAGE = "Blockage (from inspection data or estimated)"
    SEDIMENT_ACCUMULATION = "Sediment accumulation"
    COLLAPSED_SEGMENT = "Collapsed segment"
    DISCONNECTED_PIPE = "Disconnected pipe"
    EXCESSIVE_SURFACE_INFLOW = "Excessive inflow from surface"
    PUMP_STATION_LIMITATION = "Pump station limitation"
    CAPACITY_MISMATCH = "Capacity mismatch at junction"
    TIDAL_BACKWATER = "Tidal/backwater influence"
    INCORRECT_FLOW_DIR = "Incorrect flow direction (design error)"
    BOTTLENECK_JUNCTION = "Bottleneck junction (multiple pipes converging)"
    HIGH_INFILTRATION = "High infiltration/inflow (groundwater)"

class DiagnosticScore:
    def __init__(self, cause: DiagnosisCause, score: float, confidence: Confidence, details: str):
        self.cause = cause
        self.score = score
        self.confidence = confidence
        self.details = details

class SewerDiagnostician:
    def diagnose(self, pipe_data: Dict[str, Any], network_context: Dict[str, Any]) -> List[DiagnosticScore]:
        results = []
        
        # 1. Insufficient pipe diameter
        dia = pipe_data.get('diameter', 0)
        if dia < 0.3:
            results.append(DiagnosticScore(DiagnosisCause.INSUFFICIENT_DIAMETER, 0.8, Confidence.OBSERVED, f"Diameter is {dia}m, which is small."))
            
        # 2. Low slope
        slope = pipe_data.get('slope', 0)
        if slope < 0.005:
            results.append(DiagnosticScore(DiagnosisCause.LOW_SLOPE, 0.9, Confidence.OBSERVED, f"Slope is {slope}, below 0.5%."))
            
        # 3. Upstream overload
        inflow = pipe_data.get('inflow', 0)
        cap = pipe_data.get('capacity', 1)
        if inflow > cap:
            results.append(DiagnosticScore(DiagnosisCause.UPSTREAM_OVERLOAD, min(1.0, inflow/cap), Confidence.SIMULATED, f"Inflow {inflow} exceeds capacity {cap}."))
            
        # 4. Downstream backpressure
        if network_context.get('downstream_full', False):
            results.append(DiagnosticScore(DiagnosisCause.DOWNSTREAM_BACKPRESSURE, 0.85, Confidence.SIMULATED, "Downstream pipe is at full capacity."))
            
        # 5. Blockage
        if pipe_data.get('inspection_blockage', False):
            results.append(DiagnosticScore(DiagnosisCause.BLOCKAGE, 1.0, Confidence.OBSERVED, "CCTV inspection indicates blockage."))
        elif inflow > 0 and pipe_data.get('outflow', 0) == 0:
            results.append(DiagnosticScore(DiagnosisCause.BLOCKAGE, 0.7, Confidence.INFERRED, "Inflow exists but no outflow detected."))
            
        # 6. Sediment
        age = pipe_data.get('age_years', 0)
        if age > 20 and pipe_data.get('velocity', 1) < 0.6:
            results.append(DiagnosticScore(DiagnosisCause.SEDIMENT_ACCUMULATION, 0.6, Confidence.ESTIMATED, "Old pipe with low velocity likely has sediment."))
            
        # 7. Collapsed segment
        if pipe_data.get('surface_depression_above', False):
            results.append(DiagnosticScore(DiagnosisCause.COLLAPSED_SEGMENT, 0.8, Confidence.INFERRED, "Surface depression correlates with potential collapse."))
            
        # 8. Disconnected pipe
        if network_context.get('missing_connection', False):
            results.append(DiagnosticScore(DiagnosisCause.DISCONNECTED_PIPE, 1.0, Confidence.OBSERVED, "GIS data shows disconnected topology."))
            
        # 9. Excessive surface inflow
        if network_context.get('heavy_rainfall', False) and pipe_data.get('type') == 'combined':
            results.append(DiagnosticScore(DiagnosisCause.EXCESSIVE_SURFACE_INFLOW, 0.9, Confidence.SIMULATED, "Combined sewer during heavy rainfall event."))
            
        # 10. Pump limitation
        if network_context.get('pump_status') == 'at_capacity':
            results.append(DiagnosticScore(DiagnosisCause.PUMP_STATION_LIMITATION, 1.0, Confidence.OBSERVED, "Downstream pump is operating at max capacity."))
            
        # 11. Capacity mismatch
        us_cap = network_context.get('upstream_capacity', 0)
        if us_cap > cap * 1.5:
            results.append(DiagnosticScore(DiagnosisCause.CAPACITY_MISMATCH, 0.9, Confidence.OBSERVED, "Upstream capacity is significantly larger than current pipe."))
            
        # 12. Tidal/backwater
        if network_context.get('tide_level', 0) > pipe_data.get('invert_elevation', 100):
            results.append(DiagnosticScore(DiagnosisCause.TIDAL_BACKWATER, 0.95, Confidence.SIMULATED, "Tide elevation exceeds pipe invert."))
            
        # 13. Incorrect flow direction
        if slope < 0:
            results.append(DiagnosticScore(DiagnosisCause.INCORRECT_FLOW_DIR, 1.0, Confidence.OBSERVED, "Pipe slope is negative relative to intended flow direction."))
            
        # 14. Bottleneck junction
        if network_context.get('converging_pipes_count', 1) > 3:
            results.append(DiagnosticScore(DiagnosisCause.BOTTLENECK_JUNCTION, 0.75, Confidence.ESTIMATED, "Multiple pipes converge here causing turbulent bottlenecks."))
            
        # 15. High infiltration
        if network_context.get('groundwater_level', -10) > pipe_data.get('invert_elevation', 100) and age > 30:
            results.append(DiagnosticScore(DiagnosisCause.HIGH_INFILTRATION, 0.7, Confidence.ESTIMATED, "High groundwater and old pipe suggest infiltration."))
            
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results
