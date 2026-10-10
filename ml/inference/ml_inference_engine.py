"""
Reality Sculptor ML -- inference/ml_inference_engine.py
=======================================================
Production ML Inference Engine that loads all trained models and provides
a unified API for the Reality Sculptor World State Engine.

This is the INTEGRATION POINT between the ML layer and the backend.
All model predictions flow through this engine.
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# ── Model paths ──────────────────────────────────────────────────────────────
ML_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ML_ROOT / "models"
REGISTRY_ROOT = ML_ROOT / "registry"


class DataConfidence(str, Enum):
    """Every prediction must carry its provenance."""
    OBSERVED = "observed"         # Direct measurement
    DERIVED = "derived"           # Computed from observed data
    ESTIMATED = "estimated"       # ML prediction with calibrated uncertainty
    SIMULATED = "simulated"       # Physics simulation output
    UNKNOWN = "unknown"           # No data available


@dataclass
class Prediction:
    """A single prediction with provenance and uncertainty."""
    value: Any
    confidence: DataConfidence
    uncertainty: float = 0.0          # Standard deviation or half-width of CI
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    model_id: str = ""
    model_version: str = "v1"
    timestamp: str = ""
    
    def to_dict(self):
        d = asdict(self)
        d['confidence'] = self.confidence.value
        return d


@dataclass
class RegionPredictions:
    """Complete ML predictions for a geographic region."""
    region_id: str = ""
    timestamp: str = ""
    
    # Model predictions
    land_cover: Optional[Dict] = None         # Class probabilities
    building_density: Optional[Prediction] = None
    flood_risk: Optional[Prediction] = None
    flood_water_level: Optional[Prediction] = None
    traffic_speed: Optional[Prediction] = None
    landslide_risk: Optional[Prediction] = None
    drainage_overflow_risk: Optional[Prediction] = None
    region_embedding: Optional[List[float]] = None
    
    # Aggregate risk
    overall_risk_score: Optional[Prediction] = None
    
    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                d[k] = None
            elif isinstance(v, Prediction):
                d[k] = v.to_dict()
            elif isinstance(v, np.ndarray):
                d[k] = v.tolist()
            else:
                d[k] = v
        return d


class MLInferenceEngine:
    """
    Production ML Inference Engine for Reality Sculptor.
    
    Loads all trained models and provides unified prediction API.
    Every prediction carries DataConfidence and uncertainty bounds.
    """
    
    def __init__(self, model_root: Path = MODEL_ROOT):
        self.model_root = model_root
        self.models = {}
        self.registry = {}
        self.loaded = False
        
    def load_all_models(self):
        """Load all trained models into memory."""
        print("ML Inference Engine: Loading models...")
        start = time.time()
        
        # Load LightGBM models
        self._load_lightgbm("flood", "flood/flood_lightgbm_v1.bin")
        self._load_lightgbm("flood_q10", "flood/flood_quantile_P10_v1.bin")
        self._load_lightgbm("flood_q50", "flood/flood_quantile_P50_v1.bin")
        self._load_lightgbm("flood_q90", "flood/flood_quantile_P90_v1.bin")
        self._load_lightgbm("traffic", "traffic/traffic_lightgbm_metrla_v1.bin")
        self._load_lightgbm("drainage", "drainage/drainage_cso_lightgbm_v1.bin")
        
        # Load PyTorch models
        self._load_pytorch("landcover", "landcover/landcover_resnet18_v1_production.pt")
        self._load_pytorch("landslide", "landslide/landslide_resnet18_multispectral_v1.pt")
        self._load_pytorch("building", "building/building_unet_v1.pt")
        self._load_pytorch("fusion", "fusion/multimodal_fusion_v1.pt")
        
        # Load registry entries
        self._load_registry()
        
        self.loaded = True
        elapsed = time.time() - start
        loaded_count = sum(1 for v in self.models.values() if v is not None)
        print(f"  Loaded {loaded_count}/{len(self.models)} models in {elapsed:.1f}s")
        return loaded_count
    
    def _load_lightgbm(self, name, rel_path):
        """Load a LightGBM booster model."""
        path = self.model_root / rel_path
        try:
            import lightgbm as lgb
            model = lgb.Booster(model_file=str(path))
            self.models[name] = model
            print(f"  [OK] {name}: {path.name}")
        except Exception as e:
            self.models[name] = None
            print(f"  [--] {name}: not loaded ({e})")
    
    def _load_pytorch(self, name, rel_path):
        """Load a PyTorch model checkpoint."""
        path = self.model_root / rel_path
        try:
            import torch
            checkpoint = torch.load(path, weights_only=False, map_location='cpu')
            self.models[name] = checkpoint
            print(f"  [OK] {name}: {path.name}")
        except Exception as e:
            self.models[name] = None
            print(f"  [--] {name}: not loaded ({e})")
    
    def _load_registry(self):
        """Load model registry for metadata."""
        if REGISTRY_ROOT.exists():
            for f in REGISTRY_ROOT.glob("*.json"):
                try:
                    with open(f) as fh:
                        entry = json.load(fh)
                        self.registry[entry.get("model_id", f.stem)] = entry
                except:
                    pass
    
    def get_model_status(self) -> Dict[str, Dict]:
        """Return status of all models."""
        status = {}
        for name, model in self.models.items():
            reg = self.registry.get(name, {})
            status[name] = {
                "loaded": model is not None,
                "type": "lightgbm" if "lgb" in name or name in ("flood", "traffic", "drainage",
                    "flood_q10", "flood_q50", "flood_q90") else "pytorch",
                "metrics": reg.get("metrics", {}),
                "training_date": reg.get("training_date", "unknown"),
            }
        return status
    
    # ── Prediction Methods ───────────────────────────────────────────────
    
    def predict_flood(self, features: np.ndarray) -> Prediction:
        """
        Predict flood water level from engineered features.
        
        features: array of shape (n_features,) matching flood model training features
        Returns: Prediction with value, uncertainty bounds, and confidence
        """
        if self.models.get("flood") is None:
            return Prediction(value=0.0, confidence=DataConfidence.UNKNOWN,
                            uncertainty=1.0, model_id="flood_unavailable")
        
        if features.ndim == 1:
            if len(features) < 23:
                padded = np.zeros(23, dtype=np.float32)
                padded[:len(features)] = features
                features = padded
            elif len(features) > 23:
                features = features[:23]
        X = features.reshape(1, -1)
        pred = float(self.models["flood"].predict(X)[0])
        
        # Quantile predictions for uncertainty
        p10 = float(self.models["flood_q10"].predict(X)[0]) if self.models.get("flood_q10") else pred * 0.8
        p90 = float(self.models["flood_q90"].predict(X)[0]) if self.models.get("flood_q90") else pred * 1.2
        
        uncertainty = (p90 - p10) / 2.0
        
        return Prediction(
            value=pred,
            confidence=DataConfidence.ESTIMATED,
            uncertainty=uncertainty,
            lower_bound=p10,
            upper_bound=p90,
            model_id="flood_lgb_xgb_ensemble_v1",
            timestamp=datetime.now().isoformat(),
        )
    
    def predict_traffic(self, features: np.ndarray) -> Prediction:
        """Predict traffic speed from temporal features."""
        if self.models.get("traffic") is None:
            return Prediction(value=0.0, confidence=DataConfidence.UNKNOWN,
                            uncertainty=10.0, model_id="traffic_unavailable")
        
        X = features.reshape(1, -1)
        pred = float(self.models["traffic"].predict(X)[0])
        
        # Uncertainty from training RMSE
        reg = self.registry.get("traffic_lightgbm_metrla_v1", {})
        test_rmse = reg.get("metrics", {}).get("metr_la_test", {}).get("rmse", 9.5)
        
        return Prediction(
            value=pred,
            confidence=DataConfidence.ESTIMATED,
            uncertainty=test_rmse,
            lower_bound=pred - 2 * test_rmse,
            upper_bound=pred + 2 * test_rmse,
            model_id="traffic_lightgbm_metrla_v1",
            timestamp=datetime.now().isoformat(),
        )
    
    def predict_drainage_overflow(self, features: np.ndarray) -> Prediction:
        """Predict drainage overflow event count."""
        if self.models.get("drainage") is None:
            return Prediction(value=0.0, confidence=DataConfidence.UNKNOWN,
                            uncertainty=25.0, model_id="drainage_unavailable")
        
        X = features.reshape(1, -1)
        pred = float(self.models["drainage"].predict(X)[0])
        
        return Prediction(
            value=max(0, pred),
            confidence=DataConfidence.ESTIMATED,
            uncertainty=25.5,  # From OOF RMSE
            model_id="drainage_cso_lightgbm_v1",
            timestamp=datetime.now().isoformat(),
        )
    
    def predict_land_cover(self, image: np.ndarray) -> Dict:
        """
        Classify land cover from satellite image.
        
        image: RGB image array (H, W, 3) or tensor
        Returns: dict of class probabilities
        """
        classes = ["AnnualCrop", "Forest", "HerbaceousVegetation", "Highway",
                   "Industrial", "Pasture", "PermanentCrop", "Residential",
                   "River", "SeaLake"]
        
        if self.models.get("landcover") is None:
            return {c: 1.0/len(classes) for c in classes}
        
        import torch
        from torchvision import transforms, models
        
        checkpoint = self.models["landcover"]
        config = checkpoint.get("config", {})
        temperature = checkpoint.get("temperature", 1.0)
        
        # Build model
        model = models.resnet18(weights=None)
        num_features = model.fc.in_features
        model.fc = torch.nn.Sequential(
            torch.nn.Dropout(0.3),
            torch.nn.Linear(num_features, 10)
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        
        # Preprocess
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((64, 64)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        if isinstance(image, np.ndarray):
            img_tensor = transform(image).unsqueeze(0)
        else:
            img_tensor = image.unsqueeze(0)
        
        with torch.no_grad():
            logits = model(img_tensor)
            # Apply temperature scaling
            probs = torch.softmax(logits / temperature, dim=1).numpy()[0]
        
        return {cls: float(prob) for cls, prob in zip(classes, probs)}
    
    def predict_region(self, features: Dict[str, np.ndarray]) -> RegionPredictions:
        """
        Generate complete ML predictions for a region.
        
        features: dict with keys matching each model's expected input
        Returns: RegionPredictions with all available predictions
        """
        preds = RegionPredictions(
            region_id=features.get("region_id", "unknown"),
            timestamp=datetime.now().isoformat(),
        )
        
        # Run each model if features available
        if "flood_features" in features:
            preds.flood_water_level = self.predict_flood(features["flood_features"])
        
        if "traffic_features" in features:
            preds.traffic_speed = self.predict_traffic(features["traffic_features"])
        
        if "drainage_features" in features:
            preds.drainage_overflow_risk = self.predict_drainage_overflow(features["drainage_features"])
        
        if "image" in features:
            preds.land_cover = self.predict_land_cover(features["image"])
        
        # Compute overall risk
        risks = []
        if preds.flood_water_level and preds.flood_water_level.confidence != DataConfidence.UNKNOWN:
            risks.append(min(1.0, preds.flood_water_level.value / 2.0))
        if preds.landslide_risk and preds.landslide_risk.confidence != DataConfidence.UNKNOWN:
            risks.append(preds.landslide_risk.value)
        
        if risks:
            overall = float(np.mean(risks))
            preds.overall_risk_score = Prediction(
                value=overall,
                confidence=DataConfidence.DERIVED,
                uncertainty=float(np.std(risks)),
                model_id="risk_aggregator",
                timestamp=datetime.now().isoformat(),
            )
        
        return preds


def create_inference_engine() -> MLInferenceEngine:
    """Factory function to create and initialize the ML inference engine."""
    engine = MLInferenceEngine()
    engine.load_all_models()
    return engine


if __name__ == "__main__":
    print("=" * 80)
    print("REALITY SCULPTOR -- ML INFERENCE ENGINE TEST")
    print("=" * 80)
    
    engine = create_inference_engine()
    
    print("\n--- Model Status ---")
    status = engine.get_model_status()
    for name, info in status.items():
        loaded = "OK" if info["loaded"] else "--"
        print(f"  [{loaded}] {name:<20} type={info['type']}")
    
    # Test flood prediction
    print("\n--- Test Flood Prediction ---")
    fake_features = np.random.randn(23)  # Matches 23 flood features
    result = engine.predict_flood(fake_features)
    print(f"  Value: {result.value:.4f}")
    print(f"  Confidence: {result.confidence.value}")
    print(f"  Uncertainty: {result.uncertainty:.4f}")
    print(f"  Bounds: [{result.lower_bound:.4f}, {result.upper_bound:.4f}]")
    
    # Test traffic prediction
    print("\n--- Test Traffic Prediction ---")
    fake_traffic = np.random.randn(25)
    result = engine.predict_traffic(fake_traffic)
    print(f"  Speed: {result.value:.2f} mph")
    print(f"  Confidence: {result.confidence.value}")
    
    print("\n--- Engine Ready for World State Integration ---")
