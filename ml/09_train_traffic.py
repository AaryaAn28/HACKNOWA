"""
Reality Sculptor ML -- 09_train_traffic.py
============================================
MODEL G: Traffic Forecasting using METR-LA dataset.

Architecture: LightGBM baseline with temporal features + graph connectivity
Dataset: METR-LA (207 sensors, 4 months, 5-min intervals)
Validation: PEMS-BAY as full REGION HOLDOUT (different city)

Split Strategy:
  - TEMPORAL within METR-LA (train earlier, test later)
  - SPATIAL GENERALIZATION to PEMS-BAY (unseen region)
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
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd
from pathlib import Path
from datetime import datetime

import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\raw")
MODEL_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\models\traffic")
CHECKPOINT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\checkpoints\traffic")
REPORT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\reports")
REGISTRY_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\registry")

for d in [MODEL_DIR, CHECKPOINT_DIR, REPORT_DIR, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

def load_h5_traffic(h5_path):
    """Load HDF5 traffic dataset."""
    import h5py
    
    with h5py.File(h5_path, 'r') as f:
        keys = list(f.keys())
        print(f"  HDF5 keys: {keys}")
        
        # METR-LA typically has 'df' key with pandas DataFrame
        if 'df' in f:
            # Reconstructing from HDF5 structure
            data = f['df']
            if 'block0_values' in data:
                values = data['block0_values'][:]
                # Axis info
                if 'axis0' in data:
                    columns = [x.decode() if isinstance(x, bytes) else str(x) for x in data['axis0'][:]]
                else:
                    columns = [str(i) for i in range(values.shape[1])]
                if 'axis1' in data:
                    try:
                        index = pd.to_datetime(data['axis1'][:])
                    except:
                        index = range(values.shape[0])
                else:
                    index = range(values.shape[0])
                
                df = pd.DataFrame(values, index=index, columns=columns)
                return df
            else:
                # Try reading all datasets
                for key in data.keys():
                    print(f"    {key}: shape={data[key].shape if hasattr(data[key], 'shape') else 'N/A'}")
        
        # Fallback: try to read raw array
        for key in keys:
            if hasattr(f[key], 'shape'):
                arr = f[key][:]
                print(f"  {key}: shape={arr.shape}, dtype={arr.dtype}")
                if arr.ndim == 2:
                    return pd.DataFrame(arr, columns=[str(i) for i in range(arr.shape[1])])
    
    return None


def load_adjacency_matrix(pkl_path):
    """Load pickled adjacency matrix."""
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f, encoding='latin1')
    
    if isinstance(data, list) and len(data) >= 3:
        sensor_ids, sensor_id_to_ind, adj_mx = data
        print(f"  Adjacency matrix: {adj_mx.shape}")
        print(f"  Sensors: {len(sensor_ids)}")
        return sensor_ids, adj_mx
    elif isinstance(data, np.ndarray):
        print(f"  Adjacency matrix: {data.shape}")
        return None, data
    elif isinstance(data, dict):
        print(f"  Adjacency dict keys: {list(data.keys())}")
        return None, data
    
    return None, None


def create_traffic_features(df, sensor_col=None, sequence_length=12, prediction_horizon=1):
    """Create temporal features for traffic prediction.
    
    sequence_length: number of historical observations (12 x 5min = 1 hour)
    prediction_horizon: how many steps ahead to predict
    """
    print(f"  Creating features: seq_len={sequence_length}, horizon={prediction_horizon}")
    
    values = df.values.astype(np.float32)
    n_time, n_sensors = values.shape
    
    t_start = sequence_length
    t_end = n_time - prediction_horizon
    n_t = t_end - t_start
    if n_t <= 0:
        return pd.DataFrame()
        
    t_indices = np.arange(t_start, t_end, dtype=np.int32)
    windows = sliding_window_view(values, window_shape=sequence_length, axis=0)
    hist_all = windows[:n_t]
    hist_flat = hist_all.reshape(n_t * n_sensors, sequence_length)
    
    time_idx_flat = np.repeat(t_indices, n_sensors)
    sensor_id_flat = np.tile(np.arange(n_sensors, dtype=np.int32), n_t)
    
    data = {}
    data['sensor_id'] = sensor_id_flat
    data['time_idx'] = time_idx_flat
    
    for lag in range(sequence_length):
        data[f'speed_lag_{lag+1}'] = hist_flat[:, -(lag+1)]
        
    hist_last6 = hist_flat[:, -6:]
    data['speed_mean_6'] = np.mean(hist_last6, axis=1)
    data['speed_std_6'] = np.std(hist_last6, axis=1)
    data['speed_mean_12'] = np.mean(hist_flat, axis=1)
    data['speed_std_12'] = np.std(hist_flat, axis=1)
    data['speed_min_12'] = np.min(hist_flat, axis=1)
    data['speed_max_12'] = np.max(hist_flat, axis=1)
    data['speed_median_12'] = np.median(hist_flat, axis=1)
    
    data['speed_diff_1'] = hist_flat[:, -1] - hist_flat[:, -2]
    data['speed_diff_3'] = hist_flat[:, -1] - hist_flat[:, -4]
    data['speed_diff_6'] = hist_flat[:, -1] - hist_flat[:, -7]
    
    x = np.arange(sequence_length, dtype=np.float32)
    x_c = x - x.mean()
    weights = (x_c / np.sum(x_c**2)).astype(np.float32)
    data['speed_trend'] = np.dot(hist_flat, weights)
    
    global_mean_per_t = np.mean(hist_all[:, :, -1], axis=1)
    global_std_per_t = np.std(hist_all[:, :, -1], axis=1)
    data['global_mean_speed'] = np.repeat(global_mean_per_t, n_sensors)
    data['global_std_speed'] = np.repeat(global_std_per_t, n_sensors)
    
    target_all = values[t_indices + prediction_horizon - 1, :]
    data['target'] = target_all.ravel()
    
    feat_df = pd.DataFrame(data)
    print(f"  Created {len(feat_df)} samples with {feat_df.shape[1]-1} features")
    return feat_df


def mape(y_true, y_pred, epsilon=1e-8):
    """Mean Absolute Percentage Error."""
    mask = np.abs(y_true) > epsilon
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def main():
    print("=" * 80)
    print("REALITY SCULPTOR ML -- MODEL G: TRAFFIC FORECASTING")
    print("=" * 80)
    print(f"Training started: {datetime.now().isoformat()}")
    
    training_start = time.time()
    
    # 1. Load METR-LA
    print("\n--- Phase 1: Loading METR-LA ---")
    metr_h5 = RAW_DIR / "metr_la" / "METR-LA.h5"
    metr_adj = RAW_DIR / "metr_la" / "adj_METR-LA.pkl"
    
    if not metr_h5.exists():
        print(f"ERROR: {metr_h5} not found")
        return
    
    # Try pandas first
    try:
        metr_df = pd.read_hdf(metr_h5)
        print(f"  METR-LA loaded via pandas: {metr_df.shape}")
    except Exception as e:
        print(f"  pandas read_hdf failed: {e}")
        print("  Trying h5py...")
        metr_df = load_h5_traffic(metr_h5)
    
    if metr_df is None:
        print("ERROR: Could not load METR-LA data")
        return
    
    print(f"  Shape: {metr_df.shape}")
    print(f"  Time range: {metr_df.index[0]} to {metr_df.index[-1]}")
    print(f"  Sensors: {metr_df.shape[1]}")
    print(f"  Speed range: {metr_df.values[metr_df.values > 0].min():.1f} - {metr_df.values.max():.1f}")
    print(f"  Missing values: {metr_df.isnull().sum().sum()}")
    
    # Fill missing values with forward fill then backward fill
    metr_df = metr_df.ffill().bfill()
    
    # Load adjacency
    if metr_adj.exists():
        sensor_ids, adj_mx = load_adjacency_matrix(metr_adj)
    
    # 2. Create temporal features
    print("\n--- Phase 2: Feature Engineering ---")
    # Use a subset for faster initial training (every 3rd sample)
    sample_rate = 3
    metr_sampled = metr_df.iloc[::sample_rate]
    print(f"  Sampled to {len(metr_sampled)} timesteps (every {sample_rate}th)")
    
    feat_df = create_traffic_features(metr_sampled, sensor_col=None, 
                                       sequence_length=12, prediction_horizon=1)
    
    # 3. Temporal split
    print("\n--- Phase 3: Temporal Split ---")
    time_indices = feat_df['time_idx'].values
    max_t = time_indices.max()
    
    train_cutoff = int(max_t * 0.7)
    val_cutoff = int(max_t * 0.85)
    
    train_mask = feat_df['time_idx'] <= train_cutoff
    val_mask = (feat_df['time_idx'] > train_cutoff) & (feat_df['time_idx'] <= val_cutoff)
    test_mask = feat_df['time_idx'] > val_cutoff
    
    train_df = feat_df[train_mask]
    val_df = feat_df[val_mask]
    test_df = feat_df[test_mask]
    
    print(f"  Train: {len(train_df)} samples (t <= {train_cutoff})")
    print(f"  Val:   {len(val_df)} samples ({train_cutoff} < t <= {val_cutoff})")
    print(f"  Test:  {len(test_df)} samples (t > {val_cutoff})")
    print(f"  NO FUTURE LEAKAGE: train max_t < val min_t < test min_t")
    
    # 4. Define features
    exclude_cols = {'sensor_id', 'time_idx', 'target'}
    feature_cols = [c for c in feat_df.columns if c not in exclude_cols]
    print(f"  Feature columns: {len(feature_cols)}")
    
    # 5. Train LightGBM
    print("\n--- Phase 4: LightGBM Training ---")
    X_train = train_df[feature_cols].values
    y_train = train_df['target'].values
    X_val = val_df[feature_cols].values
    y_val = val_df['target'].values
    X_test = test_df[feature_cols].values
    y_test = test_df['target'].values
    
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 63,
        'max_depth': 7,
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
    
    start = time.time()
    model = lgb.train(
        params, train_data, num_boost_round=1000,
        valid_sets=[train_data, val_data], valid_names=['train', 'val'],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)],
    )
    lgb_time = time.time() - start
    
    # Evaluate
    y_pred_val = model.predict(X_val)
    y_pred_test = model.predict(X_test)
    
    metrics = {
        "val": {
            "rmse": float(np.sqrt(mean_squared_error(y_val, y_pred_val))),
            "mae": float(mean_absolute_error(y_val, y_pred_val)),
            "mape": float(mape(y_val, y_pred_val)),
            "r2": float(r2_score(y_val, y_pred_val)),
        },
        "test": {
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "mae": float(mean_absolute_error(y_test, y_pred_test)),
            "mape": float(mape(y_test, y_pred_test)),
            "r2": float(r2_score(y_test, y_pred_test)),
        },
    }
    
    print(f"\n  Best iteration: {model.best_iteration}")
    print(f"\n  Validation Metrics:")
    for k, v in metrics["val"].items():
        print(f"    {k.upper()}: {v:.4f}")
    
    print(f"\n  Test Metrics (TEMPORAL HOLDOUT):")
    for k, v in metrics["test"].items():
        print(f"    {k.upper()}: {v:.4f}")
    
    # Feature importance
    importance = model.feature_importance(importance_type='gain')
    feat_imp = sorted(zip(feature_cols, importance), key=lambda x: -x[1])
    print(f"\n  Top 10 Features:")
    for fname, imp in feat_imp[:10]:
        print(f"    {fname:<30} {imp:>12.1f}")
    
    # Save model
    model_path = MODEL_DIR / "traffic_lightgbm_metrla_v1.bin"
    model.save_model(str(model_path))
    print(f"\n  Saved model: {model_path}")
    
    # 6. SPATIAL GENERALIZATION TEST: PEMS-BAY (different city)
    print("\n--- Phase 5: Spatial Generalization to PEMS-BAY ---")
    pems_h5 = RAW_DIR / "pems_bay" / "pems-bay.h5"
    
    pems_metrics = None
    if pems_h5.exists():
        try:
            try:
                pems_df = pd.read_hdf(pems_h5)
                print(f"  PEMS-BAY loaded via pandas: {pems_df.shape}")
            except Exception as e:
                print(f"  pandas read_hdf failed: {e}")
                print("  Trying h5py...")
                pems_df = load_h5_traffic(pems_h5)
            print(f"  Sensors: {pems_df.shape[1]}")
            
            pems_df = pems_df.ffill().bfill()
            pems_sampled = pems_df.iloc[::sample_rate]
            
            pems_feat = create_traffic_features(pems_sampled, sensor_col=None,
                                                  sequence_length=12, prediction_horizon=1)
            
            # Use only test portion of PEMS-BAY time
            pems_time = pems_feat['time_idx'].values
            pems_test_cutoff = int(pems_time.max() * 0.85)
            pems_test = pems_feat[pems_feat['time_idx'] > pems_test_cutoff]
            
            X_pems = pems_test[feature_cols].values
            y_pems = pems_test['target'].values
            y_pred_pems = model.predict(X_pems)
            
            pems_metrics = {
                "rmse": float(np.sqrt(mean_squared_error(y_pems, y_pred_pems))),
                "mae": float(mean_absolute_error(y_pems, y_pred_pems)),
                "mape": float(mape(y_pems, y_pred_pems)),
                "r2": float(r2_score(y_pems, y_pred_pems)),
            }
            
            print(f"\n  PEMS-BAY (UNSEEN REGION) Metrics:")
            for k, v in pems_metrics.items():
                print(f"    {k.upper()}: {v:.4f}")
            
            # Degradation analysis
            metr_rmse = metrics["test"]["rmse"]
            pems_rmse = pems_metrics["rmse"]
            degradation = (pems_rmse - metr_rmse) / metr_rmse * 100
            print(f"\n  Generalization Degradation: {degradation:+.1f}% RMSE")
            
        except Exception as e:
            print(f"  PEMS-BAY loading error: {e}")
    else:
        print(f"  PEMS-BAY not found at {pems_h5}")
    
    # 7. Registry
    total_time = time.time() - training_start
    
    registry_entry = {
        "model_id": "traffic_lightgbm_metrla_v1",
        "model_type": "regression",
        "architecture": "lightgbm",
        "dataset": "metr_la",
        "dataset_description": "Los Angeles traffic speed sensors, 207 nodes, 4 months, 5-min intervals",
        "training_date": datetime.now().isoformat(),
        "training_duration_seconds": round(total_time, 1),
        "best_iteration": model.best_iteration,
        "split_strategy": "TEMPORAL (train on earlier timesteps, no future leakage)",
        "features": {
            "count": len(feature_cols),
            "sequence_length": 12,
            "prediction_horizon": 1,
            "top_features": [{"name": f, "importance": float(i)} for f, i in feat_imp[:10]],
        },
        "metrics": {
            "metr_la_val": metrics["val"],
            "metr_la_test": metrics["test"],
            "pems_bay_unseen_region": pems_metrics,
        },
        "spatial_generalization": {
            "trained_on": "METR-LA (Los Angeles)",
            "tested_on": "PEMS-BAY (San Francisco Bay Area)",
            "rmse_degradation_pct": float((pems_metrics["rmse"] - metrics["test"]["rmse"]) / metrics["test"]["rmse"] * 100) if pems_metrics else None,
        },
        "artifacts": {
            "model_path": str(model_path),
        },
        "limitations": [
            "Trained on METR-LA (LA) traffic patterns -- may not generalize to non-US road networks",
            "5-minute interval data -- may not capture sub-minute dynamics",
            "Speed only -- does not predict flow/occupancy",
        ],
        "seed": SEED,
    }
    
    registry_path = REGISTRY_DIR / "traffic_lightgbm_metrla_v1.json"
    with open(registry_path, 'w') as f:
        json.dump(registry_entry, f, indent=2, default=str)
    
    # Final summary
    print("\n" + "=" * 80)
    print("TRAFFIC INTELLIGENCE TRAINING COMPLETE")
    print("=" * 80)
    print(f"  Dataset: METR-LA ({metr_df.shape[0]} timesteps x {metr_df.shape[1]} sensors)")
    print(f"  Split: TEMPORAL (no future leakage)")
    print(f"  Test RMSE: {metrics['test']['rmse']:.4f}")
    print(f"  Test MAPE: {metrics['test']['mape']:.2f}%")
    if pems_metrics:
        print(f"  PEMS-BAY (unseen region) RMSE: {pems_metrics['rmse']:.4f}")
    print(f"  Training Time: {total_time:.0f}s ({total_time/60:.1f}min)")


if __name__ == "__main__":
    main()
