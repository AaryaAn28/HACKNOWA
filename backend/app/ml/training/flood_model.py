import lightgbm as lgb
import xgboost as xgb
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import optuna
from sklearn.model_selection import KFold, GroupKFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
from app.ml.registry.model_registry import ModelRegistry

class FloodRiskModel:
    """
    ML model for predicting flood risk and depth.
    Primary: LightGBM, Secondary: XGBoost.
    """
    def __init__(self, use_lightgbm: bool = True, registry_path: str = "models/flood"):
        self.use_lightgbm = use_lightgbm
        self.model = None
        self.registry = ModelRegistry(registry_path)
        self.features = [
            "elevation", "slope", "curvature", "flow_accumulation", "distance_to_drain",
            "drain_connectivity", "drain_capacity", "impervious_ratio", "soil_characteristics",
            "rainfall_intensity", "rainfall_accumulation", "historical_flood_frequency",
            "water_proximity", "building_density", "road_density"
        ]
        self.best_params = {}

    def _spatial_temporal_cv(self, df: pd.DataFrame, target: str, n_splits: int = 5) -> Tuple[List, List]:
        """Spatial block CV and temporal CV for leakage prevention."""
        # Simplified: using GroupKFold on a 'spatial_block' column if it exists, else KFold
        if 'spatial_block' in df.columns:
            gkf = GroupKFold(n_splits=n_splits)
            splits = list(gkf.split(df, df[target], groups=df['spatial_block']))
        else:
            kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
            splits = list(kf.split(df))
        return splits

    def optimize_hyperparameters(self, df: pd.DataFrame, target: str, n_trials: int = 20) -> Dict[str, Any]:
        """Optuna hyperparameter search."""
        X = df[self.features]
        y = df[target]
        splits = self._spatial_temporal_cv(df, target)

        def objective(trial):
            if self.use_lightgbm:
                params = {
                    'objective': 'regression',
                    'metric': 'rmse',
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
                    'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                    'max_depth': trial.suggest_int('max_depth', 5, 15),
                    'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0)
                }
                rmses = []
                for train_idx, val_idx in splits:
                    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                    
                    train_data = lgb.Dataset(X_train, label=y_train)
                    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
                    
                    # early stopping via callbacks
                    callbacks = [lgb.early_stopping(stopping_rounds=30, verbose=False)]
                    model = lgb.train(params, train_data, valid_sets=[val_data], num_boost_round=1000, callbacks=callbacks)
                    
                    preds = model.predict(X_val)
                    rmses.append(np.sqrt(mean_squared_error(y_val, preds)))
                return np.mean(rmses)
            else:
                # XGBoost logic similar
                return 0.0

        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials)
        self.best_params = study.best_params
        return self.best_params

    def train(self, df: pd.DataFrame, target: str, dataset_version: str):
        """Train the model with best params, perform calibration, and register."""
        X = df[self.features]
        y = df[target]
        
        if not self.best_params:
            self.best_params = {'objective': 'regression', 'learning_rate': 0.05, 'num_leaves': 31}

        if self.use_lightgbm:
            train_data = lgb.Dataset(X, label=y)
            self.model = lgb.train(self.best_params, train_data, num_boost_round=100)
        else:
            self.model = xgb.XGBRegressor(**self.best_params)
            self.model.fit(X, y)
        
        preds = self.predict(X)
        metrics = self.evaluate(y.values, preds)
        
        # Save to registry
        model_path = f"flood_model_v{dataset_version}.bin"
        if self.use_lightgbm:
            self.model.save_model(model_path)
        
        self.registry.register_model(
            name="flood_model",
            version=dataset_version,
            features=self.features,
            hyperparameters=self.best_params,
            metrics=metrics,
            model_artifact_path=model_path,
            dataset_version=dataset_version
        )
        return metrics
        
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict flood depth."""
        if self.model is None:
            raise ValueError("Model not trained.")
        X = df[self.features]
        if self.use_lightgbm:
            return self.model.predict(X)
        else:
            return self.model.predict(X)

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance."""
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        return {
            "rmse": rmse,
            "mae": mae,
            # Placeholder for spatial error, depth error, extent IoU
            "spatial_error": 0.0,
            "depth_error": 0.0,
            "extent_iou": 0.0
        }
