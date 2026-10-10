from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List

@dataclass
class AuditEntry:
    timestamp: datetime
    action_type: str
    variable_path: str
    old_value: Any
    new_value: Any
    reason: str
    agent_id: str
    model_version: str

class AuditTrail:
    """
    Complete audit logging for every state change, intervention, and model version.
    """
    def __init__(self):
        self._entries: List[AuditEntry] = []

    def log(self, action_type: str, variable_path: str, old_value: Any, new_value: Any, reason: str, agent_id: str, model_version: str):
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            action_type=action_type,
            variable_path=variable_path,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            agent_id=agent_id,
            model_version=model_version
        )
        self._entries.append(entry)

    def get_logs(self) -> List[AuditEntry]:
        return self._entries.copy()
