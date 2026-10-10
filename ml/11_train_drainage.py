"""
Reality Sculptor ML -- 11_train_drainage.py
=============================================
MODEL F: Drainage/Sewer Intelligence using NYSDEC CSO dataset.

Architecture: LightGBM classifier for sewer overflow event prediction
Dataset: NYSDEC Combined Sewer Overflows (CSV with lat/lon, overflow events)
Task: Predict overflow frequency from facility/geographic features
Split: Spatial cross-validation (leave-one-county-out)
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

import lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

MODEL_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\models\drainage")
REGISTRY_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\registry")
RAW_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\raw\nysdec_cso")

for d in [MODEL_DIR, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SEED = 42
np.random.seed(SEED)

def main():
    print("=" * 80)
    print("REALITY SCULPTOR ML -- MODEL F: DRAINAGE/SEWER INTELLIGENCE")
    print("=" * 80)
    training_start = time.time()

    # 1. Load CSO data
    csv_path = RAW_DIR / "combined-sewer-overflows-csos-beginning-2013.csv"
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found")
        return
    
    df = pd.read_csv(csv_path)
    print(f"  Loaded: {df.shape}")
    print(f"  Columns: {df.columns.tolist()}")

    # 2. Feature engineering
    print("\n--- Feature Engineering ---")

    # Clean column names
    df.columns = df.columns.str.strip()

    # Target: Number of Overflow Events
    target_col = 'Number of Overflow Events'
    if target_col not in df.columns:
        # Try alternative names
        for col in df.columns:
            if 'overflow' in col.lower() and 'event' in col.lower():
                target_col = col
                break

    print(f"  Target: {target_col}")
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
    df = df.dropna(subset=[target_col])
    print(f"  After dropping NaN targets: {len(df)} rows")
    print(f"  Target range: {df[target_col].min()} - {df[target_col].max()}")
    print(f"  Target mean: {df[target_col].mean():.2f}")

    # Features
    feature_cols = []

    # Numeric features
    for col in ['Number of Permitted Outfalls', 'Latitude', 'Longtitude']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            feature_cols.append(col)

    # Categorical features (encode)
    le_dict = {}
    for col in ['DEC Region', 'County', 'Discharge Activation Type']:
        if col in df.columns:
            le = LabelEncoder()
            df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
            feature_cols.append(f'{col}_encoded')
            le_dict[col] = le

    # Spatial features
    if 'Latitude' in df.columns and 'Longtitude' in df.columns:
        df['lat_rounded'] = df['Latitude'].round(1)
        df['lon_rounded'] = df['Longtitude'].round(1)
        feature_cols.extend(['lat_rounded', 'lon_rounded'])

    print(f"  Features ({len(feature_cols)}): {feature_cols}")

    # Drop rows with NaN features
    df = df.dropna(subset=feature_cols + [target_col])
    print(f"  Clean dataset: {len(df)} rows")

    # 3. Spatial CV (Leave-One-County-Out)
    print("\n--- Spatial Cross-Validation (Leave-One-County-Out) ---")
    
    group_col = 'County' if 'County' in df.columns else None
    if group_col is None:
        print("  WARNING: No county column. Using random 5-fold CV.")
        groups = np.random.randint(0, 5, size=len(df))
    else:
        groups = df[group_col].astype(str).values

    X = df[feature_cols].values
    y = df[target_col].values

    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    n_splits = min(5, n_groups)
    
    gkf = GroupKFold(n_splits=n_splits)
    
    oof_preds = np.zeros(len(df))
    fold_metrics = []

    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        val_counties = np.unique(groups[val_idx])
        
        params = {
            'objective': 'regression', 'metric': 'rmse', 'boosting_type': 'gbdt',
            'learning_rate': 0.05, 'num_leaves': 31, 'max_depth': 6,
            'min_child_samples': 5, 'verbose': -1, 'seed': SEED, 'n_jobs': -1,
        }
        
        dtrain = lgb.Dataset(X_train, label=y_train, feature_name=feature_cols)
        dval = lgb.Dataset(X_val, label=y_val, feature_name=feature_cols, reference=dtrain)
        
        model = lgb.train(
            params, dtrain, num_boost_round=500,
            valid_sets=[dval], callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)]
        )
        
        preds = model.predict(X_val)
        oof_preds[val_idx] = preds
        
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        mae = mean_absolute_error(y_val, preds)
        r2 = r2_score(y_val, preds) if len(y_val) > 1 else 0
        
        fold_metrics.append({"fold": fold, "rmse": rmse, "mae": mae, "r2": r2,
                             "val_counties": list(val_counties[:3])})
        print(f"  Fold {fold}: RMSE={rmse:.4f} MAE={mae:.4f} R2={r2:.4f} "
              f"(val counties: {val_counties[:3]})")

    # Overall OOF metrics
    oof_rmse = np.sqrt(mean_squared_error(y, oof_preds))
    oof_mae = mean_absolute_error(y, oof_preds)
    oof_r2 = r2_score(y, oof_preds)
    print(f"\n  OOF RMSE: {oof_rmse:.4f}")
    print(f"  OOF MAE:  {oof_mae:.4f}")
    print(f"  OOF R2:   {oof_r2:.4f}")

    # 4. Train final model on all data
    print("\n--- Final Model Training ---")
    dtrain_full = lgb.Dataset(X, label=y, feature_name=feature_cols)
    final_model = lgb.train(
        params, dtrain_full, num_boost_round=model.best_iteration or 200,
    )

    model_path = MODEL_DIR / "drainage_cso_lightgbm_v1.bin"
    final_model.save_model(str(model_path))
    print(f"  Saved: {model_path}")

    # Feature importance
    importance = final_model.feature_importance(importance_type='gain')
    feat_imp = sorted(zip(feature_cols, importance), key=lambda x: -x[1])
    print(f"\n  Feature Importance:")
    for fname, imp in feat_imp:
        print(f"    {fname:<35} {imp:>10.1f}")

    # 5. Registry
    total_time = time.time() - training_start
    registry = {
        "model_id": "drainage_cso_lightgbm_v1",
        "dataset": "nysdec_cso",
        "architecture": "lightgbm",
        "task": "regression (overflow event count prediction)",
        "training_date": datetime.now().isoformat(),
        "training_duration_seconds": round(total_time, 1),
        "split": f"spatial_group_kfold ({n_splits} folds, leave-county-out)",
        "metrics": {
            "oof_rmse": float(oof_rmse), "oof_mae": float(oof_mae), "oof_r2": float(oof_r2),
            "fold_details": fold_metrics,
        },
        "features": feature_cols,
        "artifacts": {"model": str(model_path)},
        "seed": SEED,
    }
    with open(REGISTRY_DIR / "drainage_cso_lightgbm_v1.json", 'w') as f:
        json.dump(registry, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"DRAINAGE MODEL COMPLETE | OOF RMSE: {oof_rmse:.4f} | R2: {oof_r2:.4f} | {total_time:.0f}s")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
