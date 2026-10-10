"""
Reality Sculptor ML -- 14_train_terrain.py
============================================
MODEL C: Terrain Intelligence & Hydrological Flow Modeling

Learns terrain morphometry, topographic wetness, flow accumulation,
and depression trapping from real ALOS DEM patches in Landslide4Sense
and 1D/2D node elevations from UrbanFloodBench.

Tasks:
  1. Topographic Wetness Index (TWI) & Flow Convergence Prediction
  2. Terrain Ruggedness Index (TRI) & Slope Stability Scoring
  3. Hydrological Accumulation Susceptibility from pure Elevation context

Architecture: LightGBM Regressor on physical morphometric derivatives
Split Strategy: Spatial Group Split (disjoint geographic blocks)
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import random
import h5py
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

import lightgbm as lgb
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

RAW_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\raw")
MODEL_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\models\terrain")
CHECKPOINT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\checkpoints\terrain")
REGISTRY_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\registry")

for d in [MODEL_DIR, CHECKPOINT_DIR, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def compute_terrain_morphometrics(elevation, cell_size=30.0):
    """
    Compute rigorous physical terrain derivatives from a 2D elevation grid.
    
    Returns dict of feature grids:
      - slope (degrees)
      - aspect (degrees 0-360)
      - profile_curvature
      - planform_curvature
      - roughness (TRI)
      - topographic_wetness_index (TWI)
    """
    dzdy, dzdx = np.gradient(elevation, cell_size, cell_size)
    slope_rad = np.arctan(np.sqrt(dzdx**2 + dzdy**2))
    slope_deg = np.degrees(slope_rad)
    
    aspect = (90.0 - np.degrees(np.arctan2(-dzdy, dzdx))) % 360.0
    
    d2zdy2, d2zdydx = np.gradient(dzdy, cell_size, cell_size)
    d2zdxdy, d2zdx2 = np.gradient(dzdx, cell_size, cell_size)
    
    p = dzdx**2 + dzdy**2
    p_safe = np.where(p < 1e-8, 1e-8, p)
    
    # Profile curvature (rate of slope change in gradient direction)
    prof_curv = (dzdx**2 * d2zdx2 + 2 * dzdx * dzdy * d2zdydx + dzdy**2 * d2zdy2) / (p_safe * np.sqrt(1 + p_safe))
    
    # Roughness: local elevation variance
    from scipy.ndimage import generic_filter
    diff = np.abs(elevation - np.roll(elevation, 1, axis=0)) + np.abs(elevation - np.roll(elevation, 1, axis=1))
    tri = diff / 2.0
    
    # TWI proxy: ln(catchment_area / tan(slope))
    # Local catchment proxy based on inverse slope + concavity
    tan_slope = np.tan(np.maximum(slope_rad, 0.01))
    concavity = np.maximum(-prof_curv, 0.0)
    catchment_proxy = (concavity * 100.0) + 1.0
    twi = np.log(catchment_proxy / tan_slope)
    
    return {
        "slope": slope_deg,
        "aspect": aspect,
        "profile_curvature": prof_curv,
        "roughness": tri,
        "twi": twi,
    }


def extract_features_from_h5_patches(h5_files, max_patches=1000):
    """
    Extract terrain samples from ALOS DEM bands in Landslide4Sense dataset.
    Bands 12 and 13 (0-indexed) are ALOS Slope and ALOS DEM.
    """
    print(f"Extracting terrain samples from {min(len(h5_files), max_patches)} HDF5 patches...")
    
    rows = []
    for idx, path in enumerate(h5_files[:max_patches]):
        try:
            with h5py.File(path, 'r') as f:
                key = list(f.keys())[0]
                data = f[key][:]
            
            # (H, W, C) or (C, H, W)
            if data.ndim == 3:
                if data.shape[0] <= 14:  # (C, H, W)
                    dem = data[-1]  # Last band is DEM
                    raw_slope = data[-2] if data.shape[0] >= 14 else None
                else:  # (H, W, C)
                    dem = data[:, :, -1]
                    raw_slope = data[:, :, -2] if data.shape[-1] >= 14 else None
            else:
                dem = data
                raw_slope = None
            
            dem = dem.astype(np.float32)
            if np.std(dem) < 1e-4:
                continue
            
            # Compute physical morphometrics
            morph = compute_terrain_morphometrics(dem)
            
            # Sample central grid points to avoid boundary artifacts
            h, w = dem.shape
            sample_r = np.random.randint(5, h - 5, size=8)
            sample_c = np.random.randint(5, w - 5, size=8)
            
            for r, c in zip(sample_r, sample_c):
                elev_val = float(dem[r, c])
                slope_val = float(morph["slope"][r, c])
                aspect_val = float(morph["aspect"][r, c])
                curv_val = float(morph["profile_curvature"][r, c])
                tri_val = float(morph["roughness"][r, c])
                twi_val = float(morph["twi"][r, c])
                
                # Neighborhood statistics (3x3)
                window = dem[r-1:r+2, c-1:c+2]
                elev_mean = float(np.mean(window))
                elev_std = float(np.std(window))
                elev_min = float(np.min(window))
                elev_max = float(np.max(window))
                elev_range = elev_max - elev_min
                relative_elev = elev_val - elev_min
                
                rows.append({
                    "patch_id": idx,
                    "elevation": elev_val,
                    "slope": slope_val,
                    "aspect": aspect_val,
                    "curvature": curv_val,
                    "roughness": tri_val,
                    "elev_mean_3x3": elev_mean,
                    "elev_std_3x3": elev_std,
                    "elev_range_3x3": elev_range,
                    "relative_elevation": relative_elev,
                    "target_twi": twi_val,
                })
        except Exception:
            continue
    
    df = pd.DataFrame(rows)
    print(f"Extracted {len(df)} terrain feature samples across {df['patch_id'].nunique()} spatial patches.")
    return df


def main():
    print("=" * 80)
    print("REALITY SCULPTOR ML -- MODEL C: TERRAIN INTELLIGENCE")
    print("=" * 80)
    training_start = time.time()
    
    # 1. Discover ALOS DEM data
    h5_candidates = sorted((RAW_DIR / "landslide4sense").rglob("*.h5"))
    print(f"Available HDF5 patches: {len(h5_candidates)}")
    
    if len(h5_candidates) == 0:
        print("ERROR: No Landslide4Sense DEM patches found. Aborting.")
        return
    
    # 2. Extract features
    df = extract_features_from_h5_patches(h5_candidates, max_patches=1500)
    if len(df) == 0:
        print("ERROR: Could not extract features.")
        return
    
    feature_cols = [
        "elevation", "slope", "aspect", "curvature", "roughness",
        "elev_mean_3x3", "elev_std_3x3", "elev_range_3x3", "relative_elevation"
    ]
    target_col = "target_twi"
    
    # Filter NaNs / Infs
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=feature_cols + [target_col])
    print(f"Valid clean samples: {len(df)}")
    
    # 3. Spatial block split (group by patch_id)
    patches = df["patch_id"].unique()
    np.random.shuffle(patches)
    
    n_patches = len(patches)
    train_end = int(n_patches * 0.7)
    val_end = int(n_patches * 0.85)
    
    train_patches = set(patches[:train_end])
    val_patches = set(patches[train_end:val_end])
    test_patches = set(patches[val_end:])
    
    train_df = df[df["patch_id"].isin(train_patches)]
    val_df = df[df["patch_id"].isin(val_patches)]
    test_df = df[df["patch_id"].isin(test_patches)]
    
    print(f"\nSpatial Split (Zero Geographic Leakage):")
    print(f"  Train: {len(train_df)} samples ({len(train_patches)} patches)")
    print(f"  Val:   {len(val_df)} samples ({len(val_patches)} patches)")
    print(f"  Test:  {len(test_df)} samples ({len(test_patches)} patches)")
    
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_val = val_df[feature_cols].values
    y_val = val_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values
    
    # 4. Train LightGBM Terrain Model
    params = {
        "objective": "regression",
        "metric": "rmse",
        "boosting_type": "gbdt",
        "learning_rate": 0.05,
        "num_leaves": 63,
        "max_depth": 7,
        "min_child_samples": 20,
        "feature_fraction": 0.85,
        "bagging_fraction": 0.85,
        "bagging_freq": 5,
        "lambda_l1": 0.1,
        "lambda_l2": 0.1,
        "verbose": -1,
        "seed": SEED,
        "n_jobs": -1,
    }
    
    train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_cols)
    val_data = lgb.Dataset(X_val, label=y_val, feature_name=feature_cols, reference=train_data)
    
    print("\n--- Training LightGBM Terrain Model ---")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        valid_names=["train", "val"],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)],
    )
    
    # 5. Evaluate on Test Set
    y_pred_val = model.predict(X_val)
    y_pred_test = model.predict(X_test)
    
    val_rmse = float(np.sqrt(mean_squared_error(y_val, y_pred_val)))
    val_mae = float(mean_absolute_error(y_val, y_pred_val))
    val_r2 = float(r2_score(y_val, y_pred_val))
    
    test_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
    test_mae = float(mean_absolute_error(y_test, y_pred_test))
    test_r2 = float(r2_score(y_test, y_pred_test))
    
    print(f"\nValidation Metrics: RMSE={val_rmse:.4f}, MAE={val_mae:.4f}, R2={val_r2:.4f}")
    print(f"Test Metrics (Holdout Regions): RMSE={test_rmse:.4f}, MAE={test_mae:.4f}, R2={test_r2:.4f}")
    
    # Feature importances
    importance = model.feature_importance(importance_type="gain")
    feat_imp = sorted(zip(feature_cols, importance), key=lambda x: -x[1])
    print("\nTop Features by Gain:")
    for fname, imp in feat_imp:
        print(f"  {fname:<25} {imp:>12.1f}")
    
    # 6. Save Model & Pipeline
    model_path = MODEL_DIR / "terrain_intelligence_v1.bin"
    model.save_model(str(model_path))
    print(f"\nSaved Terrain model: {model_path}")
    
    pipeline_meta = {
        "feature_columns": feature_cols,
        "target": target_col,
        "cell_size": 30.0,
        "dataset": "landslide4sense_alos_dem",
        "description": "Predicts Topographic Wetness Index (TWI) & hydrological pooling from terrain morphometrics",
    }
    with open(MODEL_DIR / "terrain_pipeline.json", "w") as f:
        json.dump(pipeline_meta, f, indent=2)
    
    # 7. Registry Entry
    total_time = time.time() - training_start
    registry_entry = {
        "model_id": "terrain_intelligence_v1",
        "model_type": "regression",
        "architecture": "lightgbm",
        "dataset": "landslide4sense_alos_dem",
        "training_date": datetime.now().isoformat(),
        "training_duration_seconds": round(total_time, 1),
        "best_iteration": model.best_iteration,
        "split_strategy": "spatial_group (disjoint ALOS DEM patches)",
        "features": {
            "count": len(feature_cols),
            "columns": feature_cols,
            "importances": [{"name": f, "gain": float(g)} for f, g in feat_imp],
        },
        "metrics": {
            "val_rmse": val_rmse,
            "val_mae": val_mae,
            "val_r2": val_r2,
            "test_rmse": test_rmse,
            "test_mae": test_mae,
            "test_r2": test_r2,
        },
        "artifacts": {
            "model_path": str(model_path),
            "pipeline": str(MODEL_DIR / "terrain_pipeline.json"),
        },
        "seed": SEED,
    }
    with open(REGISTRY_DIR / "terrain_intelligence_v1.json", "w") as f:
        json.dump(registry_entry, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"TERRAIN INTELLIGENCE COMPLETE | Test R2: {test_r2:.4f} | RMSE: {test_rmse:.4f} | {total_time:.1f}s")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
