import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class ModelRegistry:
    """
    Manages ML models, versions, metadata, and data lineage.
    Never silently overwrites models.
    """
    def __init__(self, storage_path: str = "models_registry/"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self.registry_file = os.path.join(self.storage_path, "registry.json")
        self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {}

    def _save_registry(self):
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=4)

    def register_model(self, name: str, version: str, features: List[str], hyperparameters: Dict[str, Any], 
                       metrics: Dict[str, float], model_artifact_path: str, dataset_version: str,
                       validation_methodology: str = "spatial_temporal_cv", geographic_coverage: str = "global",
                       known_limitations: str = "none", calibration: Dict = None, overwrite: bool = False):
        """Register a new model version."""
        if name not in self.registry:
            self.registry[name] = {}
            
        if version in self.registry[name] and not overwrite:
            raise ValueError(f"Model {name} version {version} already exists. Pass overwrite=True to update.")
            
        metadata = {
            "dataset_version": dataset_version,
            "features": features,
            "hyperparameters": hyperparameters,
            "training_date": datetime.utcnow().isoformat(),
            "validation_methodology": validation_methodology,
            "metrics": metrics,
            "calibration": calibration or {},
            "geographic_coverage": geographic_coverage,
            "known_limitations": known_limitations,
            "model_artifact_path": model_artifact_path
        }
        
        self.registry[name][version] = metadata
        self._save_registry()
        
    def get_model(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        return self.registry.get(name, {}).get(version)
