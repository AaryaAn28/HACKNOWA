import typing
from typing import List, Dict, Any, Optional

class QuestionEngine:
    """Generates adaptive questions based on information value and confidence gaps."""

    def __init__(self):
        self.importance_weights = {
            "elevation": 0.9,
            "land_cover": 0.8,
            "drain_capacity": 0.7,
            "soil_type": 0.6
        }

    def compute_information_value(self, variable: str, world_state: Any) -> float:
        """Estimates how much knowing this variable would change simulation output."""
        # Simple heuristic based on lookup table
        importance = self.importance_weights.get(variable, 0.1)
        confidence = world_state.get_confidence(variable) if hasattr(world_state, 'get_confidence') else 1.0
        confidence_gap = 1.0 - confidence
        return importance * confidence_gap

    def translate_objective(self, natural_language: str) -> Dict[str, str]:
        """Parses natural language objectives into measurable targets."""
        nl_lower = natural_language.lower()
        if "flood" in nl_lower:
            return {"metric": "max_water_depth", "target": "< 0.15", "unit": "m"}
        elif "heat" in nl_lower:
            return {"metric": "max_surface_temp", "target": "< 35", "unit": "C"}
        elif "emergency" in nl_lower or "response" in nl_lower:
            return {"metric": "response_time", "target": "< 600", "unit": "seconds"}
        return {"metric": "unknown", "target": "unknown", "unit": "unknown"}

    def generate_questions(self, world_state: Any, confidence_threshold: float = 0.8, info_value_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Generates adaptive questions based on world state confidence."""
        variables = world_state.get_all_variables() if hasattr(world_state, 'get_all_variables') else []
        questions = []

        for var in variables:
            confidence = world_state.get_confidence(var) if hasattr(world_state, 'get_confidence') else 1.0
            if confidence < confidence_threshold:
                info_val = self.compute_information_value(var, world_state)
                if info_val > info_value_threshold:
                    questions.append({
                        "variable": var,
                        "information_value": info_val,
                        "question_text": f"Can you provide more accurate data for {var}? Current confidence is {confidence*100:.1f}%."
                    })

        # Sort descending by information value
        questions.sort(key=lambda x: x["information_value"], reverse=True)
        return questions

    def generate_followup(self, uploaded_data_type: str) -> Optional[str]:
        """Detects what was just uploaded and asks relevant follow-ups."""
        if uploaded_data_type == "elevation":
            return "Elevation data received. Do you have matching land cover data to refine roughness estimation?"
        elif uploaded_data_type == "drainage":
            return "Drainage network updated. What is the average maintenance status or blockage percentage?"
        return None
