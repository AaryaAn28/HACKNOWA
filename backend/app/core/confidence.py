from enum import IntEnum
from typing import List

class ConfidenceLevel(IntEnum):
    """
    Confidence levels for data provenance.
    Higher values indicate higher confidence/accuracy.
    """
    UNKNOWN = 0
    SIMULATED = 1
    ESTIMATED = 2
    DERIVED = 3
    OBSERVED = 4

def propagate_confidence(confidences: List[ConfidenceLevel]) -> ConfidenceLevel:
    """
    Determine the confidence level of a derived value based on its inputs.
    The rule of thumb is that derived data cannot have higher confidence than its weakest input.
    """
    if not confidences:
        return ConfidenceLevel.UNKNOWN
    return min(confidences)
