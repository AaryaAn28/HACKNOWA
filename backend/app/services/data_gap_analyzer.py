from pydantic import BaseModel
from typing import List, Dict, Any

class DataGap(BaseModel):
    variable: str
    location: str
    current_confidence: float
    target_confidence: float
    information_value: float
    suggested_source: str

class DataGapAnalyzer:
    """
    Scans the world state for missing or low-confidence variables and 
    generates prioritized DataGap entries to improve simulation accuracy.
    """
    def __init__(self):
        pass

    def scan_world_state(self, world_state: Dict[str, Any]) -> List[DataGap]:
        """Generate a map of data gaps based on the current world state."""
        gaps = []
        
        # Iterate through spatial regions or global variables
        for var_name, data in world_state.items():
            if isinstance(data, dict):
                conf = data.get("confidence", 0.0)
                if conf < 0.8:  # Arbitrary confidence threshold for gap flagging
                    info_val = 1.0 - conf # Simplified information value heuristic
                    gaps.append(DataGap(
                        variable=var_name,
                        location=data.get("location_id", "global"),
                        current_confidence=conf,
                        target_confidence=0.9,
                        information_value=info_val,
                        suggested_source="Sensor Network / City GIS Database"
                    ))
                    
        # Prioritize gaps by expected decision impact
        gaps.sort(key=lambda x: x.information_value, reverse=True)
        return gaps
        
    def get_top_gaps_summary(self, world_state: Dict[str, Any], top_n: int = 3) -> str:
        """Returns a string highlighting the top missing inputs."""
        gaps = self.scan_world_state(world_state)
        if not gaps:
            return "No significant data gaps found."
            
        top_gaps = gaps[:top_n]
        variables = [g.variable for g in top_gaps]
        return f"These {len(variables)} missing inputs would most improve the simulation: {', '.join(variables)}."
