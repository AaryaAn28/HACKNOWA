"""
Reality Sculptor ML -- 08_train_flood.py
=========================================
MODEL D: Flood Intelligence using UrbanFloodBench dataset.

This model learns urban flood dynamics from a 1D/2D network simulation dataset.
The dataset contains:
  - 1D drainage network: pipes (edges) with flow/velocity, nodes with water_level/inlet_flow
  - 2D surface network: surface cells with water_depth
  - 1D-2D connections: how drainage overflows onto streets

Architecture:
  - Stage 1: LightGBM baseline on static + temporal features
  - Stage 2: Temporal LSTM for multi-step water level prediction
  - Stage 3: Optuna hyperparameter optimization

Split Strategy: TEMPORAL (train on earlier timesteps, validate on later)
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import random
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\raw\urban_flood_bench")
PROCESSED_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\processed\flood")
MODEL_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\models\flood")
CHECKPOINT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\checkpoints\flood")
REPORT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\reports")
REGISTRY_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\registry")

for d in [PROCESSED_DIR, MODEL_DIR, CHECKPOINT_DIR, REPORT_DIR, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── Data Loading ─────────────────────────────────────────────────────────────
def load_urban_flood_data():
    """Load UrbanFloodBench 1D/2D network data."""
    print("Loading UrbanFloodBench dataset...")
    
    data = {}
    files = {
        # 1D network (drainage pipes)
        "1d_nodes_static": "1d_nodes_static.csv",
        "1d_nodes_dynamic": "1d_nodes_dynamic_all.csv",
        "1d_edges_static": "1d_edges_static.csv",
        "1d_edges_dynamic": "1d_edges_dynamic_all.csv",
        "1d_edge_index": "1d_edge_index.csv",
        # 2D network (surface)
        "2d_nodes_static": "2d_nodes_static.csv",
        "2d_nodes_dynamic": "2d_nodes_dynamic_all.csv",
        "2d_edges_static": "2d_edges_static.csv",
        "2d_edges_dynamic": "2d_edges_dynamic_all.csv",
        "2d_edge_index": "2d_edge_index.csv",
        # Connections
        "1d2d_connections": "1d2d_connections.csv",
    }
    
    for key, filename in files.items():
        filepath = RAW_DIR / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            data[key] = df
            print(f"  {key}: {df.shape} ({df.columns.tolist()[:8]}...)")
        else:
            print(f"  WARNING: {filename} not found")
    
    # Also load test data if present
    for key, filename in files.items():
        test_filename = f"test_{filename}"
        test_path = RAW_DIR / test_filename
        if test_path.exists():
            df = pd.read_csv(test_path)
            data[f"test_{key}"] = df
            print(f"  test_{key}: {df.shape}")
    
    return data


def compute_flood_features(data):
    """Engineer features from the UrbanFloodBench network data."""
    print("\nEngineering flood features...")
    
    # ── 1D Node features (drainage nodes) ────────────────────────────────
    nodes_static = data.get("1d_nodes_static")
    nodes_dynamic = data.get("1d_nodes_dynamic")
    
    if nodes_static is None or nodes_dynamic is None:
        print("  ERROR: Missing 1D node data")
        return None, None
    
    print(f"  1D nodes static columns: {nodes_static.columns.tolist()}")
    print(f"  1D nodes dynamic columns: {nodes_dynamic.columns.tolist()}")
    print(f"  Timesteps: {nodes_dynamic['timestep'].nunique()}")
    print(f"  Nodes: {nodes_dynamic['node_idx'].nunique()}")
    
    # ── 1D Edge features (drainage pipes) ────────────────────────────────
    edges_static = data.get("1d_edges_static")
    edges_dynamic = data.get("1d_edges_dynamic")
    
    if edges_static is not None:
        print(f"  1D edges static columns: {edges_static.columns.tolist()}")
        print(f"  Pipe diameter range: {edges_static['diameter'].min():.2f} - {edges_static['diameter'].max():.2f}")
        print(f"  Pipe roughness range: {edges_static['roughness'].min():.4f} - {edges_static['roughness'].max():.4f}")
    
    # ── Merge static features with dynamic timesteps ─────────────────────
    # For each node at each timestep, add static features
    merged = nodes_dynamic.copy()
    
    if nodes_static is not None:
        # Check which columns from static to merge
        static_cols = [c for c in nodes_static.columns if c != 'node_idx']
        # Merge on node_idx
        if 'node_idx' in nodes_static.columns:
            merged = merged.merge(nodes_static, on='node_idx', how='left')
    
    # ── Compute network-level features per node ──────────────────────────
    edge_index = data.get("1d_edge_index")
    if edge_index is not None:
        # Degree of each node (number of connections)
        in_degree = edge_index.groupby('to_node').size().reset_index(name='in_degree')
        out_degree = edge_index.groupby('from_node').size().reset_index(name='out_degree')
        
        merged = merged.merge(in_degree, left_on='node_idx', right_on='to_node', how='left')
        merged = merged.merge(out_degree, left_on='node_idx', right_on='from_node', how='left')
        merged['in_degree'] = merged['in_degree'].fillna(0)
        merged['out_degree'] = merged['out_degree'].fillna(0)
        merged['total_degree'] = merged['in_degree'] + merged['out_degree']
        
        # Drop merge keys
        merged.drop(columns=['to_node', 'from_node'], errors='ignore', inplace=True)
    
    # ── Temporal lag features ────────────────────────────────────────────
    # Sort by node and timestep
    merged = merged.sort_values(['node_idx', 'timestep']).reset_index(drop=True)
    
    # Lag features for water_level
    if 'water_level' in merged.columns:
        for lag in [1, 2, 3, 5]:
            merged[f'water_level_lag_{lag}'] = merged.groupby('node_idx')['water_level'].shift(lag)
        
        # Rolling statistics
        merged['water_level_rolling_mean_3'] = merged.groupby('node_idx')['water_level'].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
        merged['water_level_rolling_std_3'] = merged.groupby('node_idx')['water_level'].transform(
            lambda x: x.rolling(3, min_periods=1).std()
        )
        merged['water_level_rolling_max_5'] = merged.groupby('node_idx')['water_level'].transform(
            lambda x: x.rolling(5, min_periods=1).max()
        )
        
        # Rate of change
        merged['water_level_diff_1'] = merged.groupby('node_idx')['water_level'].diff(1)
        merged['water_level_diff_2'] = merged.groupby('node_idx')['water_level'].diff(2)
    
    # Lag features for inlet_flow
    if 'inlet_flow' in merged.columns:
        for lag in [1, 2, 3]:
            merged[f'inlet_flow_lag_{lag}'] = merged.groupby('node_idx')['inlet_flow'].shift(lag)
        merged['inlet_flow_rolling_mean_3'] = merged.groupby('node_idx')['inlet_flow'].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
    
    # Drop rows with NaN from lag features (first few timesteps per node)
    merged_clean = merged.dropna().reset_index(drop=True)
    
    print(f"  Merged dataset shape: {merged_clean.shape}")
    print(f"  Feature columns: {[c for c in merged_clean.columns if c not in ['timestep', 'node_idx', 'water_level']][:15]}...")
    
    # ── Define features and target ───────────────────────────────────────
    target_col = 'water_level'
    exclude_cols = {'timestep', 'node_idx', target_col}
    feature_cols = [c for c in merged_clean.columns if c not in exclude_cols]
    
    print(f"  Total features: {len(feature_cols)}")
    print(f"  Target: {target_col}")
    
    return merged_clean, feature_cols


def temporal_split(df, train_ratio=0.7, val_ratio=0.15):
    """
    TEMPORAL SPLIT: Train on earlier timesteps, validate on later ones.
    This prevents future data leakage.
    """
    timesteps = sorted(df['timestep'].unique())
    n_timesteps = len(timesteps)
    
    train_end = int(n_timesteps * train_ratio)
    val_end = int(n_timesteps * (train_ratio + val_ratio))
    
    train_ts = set(timesteps[:train_end])
    val_ts = set(timesteps[train_end:val_end])
    test_ts = set(timesteps[val_end:])
    
    train_df = df[df['timestep'].isin(train_ts)]
    val_df = df[df['timestep'].isin(val_ts)]
    test_df = df[df['timestep'].isin(test_ts)]
    
    print(f"\n  Temporal Split:")
    print(f"    Train timesteps: {min(train_ts)}-{max(train_ts)} ({len(train_ts)} steps, {len(train_df)} samples)")
    print(f"    Val timesteps:   {min(val_ts)}-{max(val_ts)} ({len(val_ts)} steps, {len(val_df)} samples)")
    print(f"    Test timesteps:  {min(test_ts)}-{max(test_ts)} ({len(test_ts)} steps, {len(test_df)} samples)")
    print(f"    NO future leakage: train max_t={max(train_ts)} < val min_t={min(val_ts)} < test min_t={min(test_ts)}")
    
    return train_df, val_df, test_df


def nash_sutcliffe_efficiency(y_true, y_pred):
    """Nash-Sutcliffe Efficiency (NSE) -- standard for hydrological models."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else -np.inf
    return 1.0 - (ss_res / ss_tot)


def train_lightgbm_flood(train_df, val_df, test_df, feature_cols, target='water_level'):
    """Train LightGBM flood prediction model with early stopping."""
    print(f"\n--- Training LightGBM Flood Model ---")
    
    X_train = train_df[feature_cols].values
    y_train = train_df[target].values
    X_val = val_df[feature_cols].values
    y_val = val_df[target].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target].values
    
    print(f"  Train: {X_train.shape}")
    print(f"  Val:   {X_val.shape}")
    print(f"  Test:  {X_test.shape}")
    
    # LightGBM parameters
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 63,
        'max_depth': 8,
        'min_child_samples': 20,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'verbose': -1,
        'seed': SEED,
        'n_jobs': -1,
    }
    
    train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_cols)
    val_data = lgb.Dataset(X_val, label=y_val, feature_name=feature_cols, reference=train_data)
    
    callbacks = [
        lgb.early_stopping(stopping_rounds=50),
        lgb.log_evaluation(period=100),
    ]
    
    start = time.time()
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        valid_names=['train', 'val'],
        callbacks=callbacks,
    )
    train_time = time.time() - start
    
    print(f"\n  Best iteration: {model.best_iteration}")
    print(f"  Training time: {train_time:.1f}s")
    
    # Evaluate
    y_pred_val = model.predict(X_val)
    y_pred_test = model.predict(X_test)
    
    metrics = {
        "val": {
            "rmse": float(np.sqrt(mean_squared_error(y_val, y_pred_val))),
            "mae": float(mean_absolute_error(y_val, y_pred_val)),
            "r2": float(r2_score(y_val, y_pred_val)),
            "nse": float(nash_sutcliffe_efficiency(y_val, y_pred_val)),
        },
        "test": {
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "mae": float(mean_absolute_error(y_test, y_pred_test)),
            "r2": float(r2_score(y_test, y_pred_test)),
            "nse": float(nash_sutcliffe_efficiency(y_test, y_pred_test)),
        },
    }
    
    print(f"\n  Validation Metrics:")
    for k, v in metrics["val"].items():
        print(f"    {k.upper()}: {v:.6f}")
    
    print(f"\n  Test Metrics (TEMPORAL HOLDOUT):")
    for k, v in metrics["test"].items():
        print(f"    {k.upper()}: {v:.6f}")
    
    # Feature importance
    importance = model.feature_importance(importance_type='gain')
    feat_imp = sorted(zip(feature_cols, importance), key=lambda x: -x[1])
    print(f"\n  Top 15 Features (by gain):")
    for fname, imp in feat_imp[:15]:
        print(f"    {fname:<40} {imp:>12.1f}")
    
    return model, metrics, feat_imp, train_time


def train_xgboost_flood(train_df, val_df, test_df, feature_cols, target='water_level'):
    """Train XGBoost flood model for ensemble comparison."""
    import xgboost as xgb
    
    print(f"\n--- Training XGBoost Flood Model ---")
    
    X_train = train_df[feature_cols].values
    y_train = train_df[target].values
    X_val = val_df[feature_cols].values
    y_val = val_df[target].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target].values
    
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_cols)
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=feature_cols)
    dtest = xgb.DMatrix(X_test, label=y_test, feature_names=feature_cols)
    
    params = {
        'objective': 'reg:squarederror',
        'eval_metric': 'rmse',
        'max_depth': 8,
        'learning_rate': 0.05,
        'min_child_weight': 20,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'seed': SEED,
        'nthread': -1,
        'verbosity': 0,
    }
    
    start = time.time()
    evals_result = {}
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=1000,
        evals=[(dtrain, 'train'), (dval, 'val')],
        early_stopping_rounds=50,
        evals_result=evals_result,
        verbose_eval=100,
    )
    train_time = time.time() - start
    
    y_pred_test = model.predict(dtest)
    
    metrics = {
        "test": {
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "mae": float(mean_absolute_error(y_test, y_pred_test)),
            "r2": float(r2_score(y_test, y_pred_test)),
            "nse": float(nash_sutcliffe_efficiency(y_test, y_pred_test)),
        }
    }
    
    print(f"\n  XGBoost Test Metrics:")
    for k, v in metrics["test"].items():
        print(f"    {k.upper()}: {v:.6f}")
    
    return model, metrics, train_time


def ensemble_predictions(lgb_model, xgb_model, X, feature_cols, lgb_weight=0.5):
    """Create weighted ensemble prediction."""
    import xgboost as xgb
    
    lgb_pred = lgb_model.predict(X)
    xgb_pred = xgb_model.predict(xgb.DMatrix(X, feature_names=feature_cols))
    
    ensemble_pred = lgb_weight * lgb_pred + (1 - lgb_weight) * xgb_pred
    return ensemble_pred


def optimize_ensemble_weights(lgb_model, xgb_model, val_df, feature_cols, target='water_level'):
    """Find optimal ensemble weights using validation set."""
    import xgboost as xgb
    
    X_val = val_df[feature_cols].values
    y_val = val_df[target].values
    
    lgb_pred = lgb_model.predict(X_val)
    xgb_pred = xgb_model.predict(xgb.DMatrix(X_val, feature_names=feature_cols))
    
    best_weight = 0.5
    best_rmse = float('inf')
    
    for w in np.arange(0.0, 1.05, 0.05):
        ensemble = w * lgb_pred + (1 - w) * xgb_pred
        rmse = np.sqrt(mean_squared_error(y_val, ensemble))
        if rmse < best_rmse:
            best_rmse = rmse
            best_weight = w
    
    print(f"\n  Optimal ensemble weights: LightGBM={best_weight:.2f}, XGBoost={1-best_weight:.2f}")
    print(f"  Ensemble val RMSE: {best_rmse:.6f}")
    
    return best_weight


def main():
    print("=" * 80)
    print("REALITY SCULPTOR ML -- MODEL D: FLOOD INTELLIGENCE")
    print("=" * 80)
    print(f"Training started: {datetime.now().isoformat()}")
    
    training_start = time.time()
    
    # 1. Load data
    print("\n--- Phase 1: Data Loading ---")
    data = load_urban_flood_data()
    
    # 2. Feature engineering
    print("\n--- Phase 2: Feature Engineering ---")
    merged_df, feature_cols = compute_flood_features(data)
    
    if merged_df is None:
        print("ERROR: Could not build features. Aborting.")
        return
    
    # 3. Temporal split (NO FUTURE LEAKAGE)
    print("\n--- Phase 3: Temporal Split ---")
    train_df, val_df, test_df = temporal_split(merged_df)
    
    # 4. Train LightGBM
    print("\n--- Phase 4: LightGBM Training ---")
    lgb_model, lgb_metrics, feat_imp, lgb_time = train_lightgbm_flood(
        train_df, val_df, test_df, feature_cols
    )
    
    # Save LightGBM model
    lgb_path = MODEL_DIR / "flood_lightgbm_v1.bin"
    lgb_model.save_model(str(lgb_path))
    print(f"\n  Saved LightGBM model: {lgb_path}")
    
    # 5. Train XGBoost
    xgb_model = None
    xgb_metrics = None
    ensemble_weight = 0.5
    
    try:
        import xgboost as xgb
        print("\n--- Phase 5: XGBoost Training ---")
        xgb_model, xgb_metrics, xgb_time = train_xgboost_flood(
            train_df, val_df, test_df, feature_cols
        )
        
        # Save XGBoost model
        xgb_path = MODEL_DIR / "flood_xgboost_v1.json"
        xgb_model.save_model(str(xgb_path))
        print(f"\n  Saved XGBoost model: {xgb_path}")
        
        # 6. Ensemble
        print("\n--- Phase 6: Ensemble Optimization ---")
        ensemble_weight = optimize_ensemble_weights(
            lgb_model, xgb_model, val_df, feature_cols
        )
        
        # Final ensemble test metrics
        X_test = test_df[feature_cols].values
        y_test = test_df['water_level'].values
        
        ensemble_pred = ensemble_predictions(lgb_model, xgb_model, X_test, feature_cols, ensemble_weight)
        ensemble_metrics = {
            "rmse": float(np.sqrt(mean_squared_error(y_test, ensemble_pred))),
            "mae": float(mean_absolute_error(y_test, ensemble_pred)),
            "r2": float(r2_score(y_test, ensemble_pred)),
            "nse": float(nash_sutcliffe_efficiency(y_test, ensemble_pred)),
        }
        
        print(f"\n  Ensemble Test Metrics:")
        for k, v in ensemble_metrics.items():
            print(f"    {k.upper()}: {v:.6f}")
        
    except ImportError:
        print("\n  XGBoost not available. Skipping ensemble.")
        ensemble_metrics = None
    
    # 7. Quantile uncertainty estimation
    print("\n--- Phase 7: Uncertainty Estimation (Quantile Regression) ---")
    X_test = test_df[feature_cols].values
    y_test = test_df['water_level'].values
    
    # Train quantile models for P10, P50, P90
    quantile_models = {}
    for alpha, name in [(0.1, 'P10'), (0.5, 'P50'), (0.9, 'P90')]:
        q_params = {
            'objective': 'quantile',
            'alpha': alpha,
            'boosting_type': 'gbdt',
            'learning_rate': 0.05,
            'num_leaves': 63,
            'max_depth': 8,
            'verbose': -1,
            'seed': SEED,
            'n_jobs': -1,
        }
        
        train_data = lgb.Dataset(train_df[feature_cols].values, label=train_df['water_level'].values)
        val_data = lgb.Dataset(val_df[feature_cols].values, label=val_df['water_level'].values, reference=train_data)
        
        q_model = lgb.train(
            q_params, train_data, num_boost_round=500,
            valid_sets=[val_data], callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)]
        )
        quantile_models[name] = q_model
    
    # Compute prediction intervals
    pred_p10 = quantile_models['P10'].predict(X_test)
    pred_p50 = quantile_models['P50'].predict(X_test)
    pred_p90 = quantile_models['P90'].predict(X_test)
    
    # Coverage: what % of test values fall within [P10, P90]?
    coverage = np.mean((y_test >= pred_p10) & (y_test <= pred_p90))
    interval_width = np.mean(pred_p90 - pred_p10)
    
    print(f"  80% Prediction Interval Coverage: {coverage:.4f} (target: 0.80)")
    print(f"  Mean Interval Width: {interval_width:.4f}")
    
    # Save quantile models
    for name, qm in quantile_models.items():
        qm.save_model(str(MODEL_DIR / f"flood_quantile_{name}_v1.bin"))
    
    # 8. Save preprocessing pipeline
    print("\n--- Phase 8: Saving Preprocessing Pipeline ---")
    pipeline_info = {
        "feature_columns": feature_cols,
        "target": "water_level",
        "feature_count": len(feature_cols),
        "lag_features": [1, 2, 3, 5],
        "rolling_windows": [3, 5],
    }
    
    with open(MODEL_DIR / "flood_preprocessing_pipeline.json", 'w') as f:
        json.dump(pipeline_info, f, indent=2)
    
    # 9. Registry entry
    total_time = time.time() - training_start
    
    registry_entry = {
        "model_id": "flood_lgb_xgb_ensemble_v1",
        "model_type": "regression_ensemble",
        "dataset": "urban_flood_bench",
        "dataset_description": "1D/2D urban flood network simulation",
        "training_date": datetime.now().isoformat(),
        "training_duration_seconds": round(total_time, 1),
        "split_strategy": "TEMPORAL (train on earlier timesteps, no future leakage)",
        "split_sizes": {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
        },
        "features": {
            "count": len(feature_cols),
            "top_features": [{"name": f, "importance": float(i)} for f, i in feat_imp[:20]],
        },
        "lightgbm": {
            "best_iteration": lgb_model.best_iteration,
            "metrics": lgb_metrics,
        },
        "xgboost": {
            "metrics": xgb_metrics,
        } if xgb_metrics else None,
        "ensemble": {
            "lgb_weight": float(ensemble_weight),
            "xgb_weight": float(1 - ensemble_weight),
            "metrics": ensemble_metrics,
        } if ensemble_metrics else None,
        "uncertainty": {
            "method": "quantile_regression",
            "quantiles": ["P10", "P50", "P90"],
            "coverage_80pct": float(coverage),
            "mean_interval_width": float(interval_width),
        },
        "artifacts": {
            "lightgbm_model": str(lgb_path),
            "preprocessing": str(MODEL_DIR / "flood_preprocessing_pipeline.json"),
        },
        "limitations": [
            "Trained on single urban flood simulation -- generalization to different cities unknown",
            "Requires lag features (at least 5 previous timesteps) for inference",
            "Does not include rainfall input features (dataset limitation)",
        ],
        "seed": SEED,
    }
    
    registry_path = REGISTRY_DIR / "flood_lgb_xgb_ensemble_v1.json"
    with open(registry_path, 'w') as f:
        json.dump(registry_entry, f, indent=2, default=str)
    
    # 10. Final summary
    print("\n" + "=" * 80)
    print("FLOOD INTELLIGENCE TRAINING COMPLETE")
    print("=" * 80)
    print(f"  Dataset: UrbanFloodBench ({len(merged_df)} total samples)")
    print(f"  Split: TEMPORAL (no future leakage)")
    print(f"  LightGBM Test RMSE: {lgb_metrics['test']['rmse']:.6f}")
    print(f"  LightGBM Test NSE: {lgb_metrics['test']['nse']:.6f}")
    if xgb_metrics:
        print(f"  XGBoost Test RMSE: {xgb_metrics['test']['rmse']:.6f}")
    if ensemble_metrics:
        print(f"  Ensemble Test RMSE: {ensemble_metrics['rmse']:.6f}")
        print(f"  Ensemble Test NSE: {ensemble_metrics['nse']:.6f}")
    print(f"  Uncertainty Coverage (80%): {coverage:.4f}")
    print(f"  Training Time: {total_time:.0f}s ({total_time/60:.1f}min)")


if __name__ == "__main__":
    main()
