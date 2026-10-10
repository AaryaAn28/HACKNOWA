"""
Reality Sculptor ML -- configs/training_config.yaml
=====================================================
Master configuration for the entire ML training pipeline.
Every training run reads from this config — no hardcoded parameters.
"""

# -- This is a Python-parseable config module --
# Using Python dict instead of YAML to avoid external dependency at this stage

TRAINING_CONFIG = {
    "project": {
        "name": "reality_sculptor_ml",
        "version": "1.0.0",
        "seed": 42,
        "data_root": r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\raw",
        "processed_root": r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\processed",
        "checkpoint_root": r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\checkpoints",
        "model_root": r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\models",
        "report_root": r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\reports",
        "registry_root": r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\registry",
    },

    # ── Model A: Land Cover Classification (EuroSAT) ─────────────────────────
    "landcover": {
        "dataset": "eurosat",
        "architecture": "resnet18_transfer",  # Start simple, upgrade if needed
        "num_classes": 10,
        "classes": [
            "AnnualCrop", "Forest", "HerbaceousVegetation", "Highway",
            "Industrial", "Pasture", "PermanentCrop", "Residential",
            "River", "SeaLake"
        ],
        "input_size": 64,
        "batch_size": 64,
        "epochs": 150,
        "early_stopping_patience": 20,
        "optimizer": "adamw",
        "lr": 1e-3,
        "weight_decay": 1e-4,
        "scheduler": "cosine_annealing",
        "augmentation": {
            "horizontal_flip": True,
            "vertical_flip": True,
            "rotation": 15,
            "color_jitter": {"brightness": 0.2, "contrast": 0.2, "saturation": 0.2},
            "normalize": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
        },
        "split": {
            "train_ratio": 0.7,
            "val_ratio": 0.15,
            "test_ratio": 0.15,
            "strategy": "stratified",  # Ensures class balance
        },
        "calibration": "temperature_scaling",
        "uncertainty": "mc_dropout",
    },

    # ── Model B: Building Extraction (IEEE BigData Cup) ──────────────────────
    "building": {
        "dataset": "ieee_building_extraction",
        "architecture": "unet_resnet34",  # U-Net with ResNet34 encoder
        "input_size": 256,
        "batch_size": 16,
        "epochs": 150,
        "early_stopping_patience": 25,
        "optimizer": "adamw",
        "lr": 3e-4,
        "weight_decay": 1e-4,
        "scheduler": "cosine_annealing_warm_restarts",
        "loss": "bce_dice",  # BCE + Dice combined loss
        "augmentation": {
            "horizontal_flip": True,
            "vertical_flip": True,
            "rotation": 90,
            "scale": [0.8, 1.2],
            "elastic": True,
            "normalize": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
        },
        "split": {
            "strategy": "spatial_group",  # Hold out entire image regions
            "val_ratio": 0.15,
            "test_ratio": 0.15,
        },
        "metrics": ["iou", "dice", "precision", "recall", "f1"],
        "calibration": "temperature_scaling",
    },

    # ── Model C: Flood Intelligence (UrbanFloodBench) ────────────────────────
    "flood": {
        "dataset": "urban_flood_bench",
        "architectures": {
            "baseline": "lightgbm",
            "advanced": "graph_temporal",
        },
        "lightgbm": {
            "n_estimators": 1000,
            "early_stopping_rounds": 50,
            "learning_rate": 0.05,
            "max_depth": 8,
            "num_leaves": 63,
            "min_child_samples": 20,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "lambda_l1": 0.1,
            "lambda_l2": 0.1,
        },
        "temporal": {
            "sequence_length": 12,
            "prediction_horizon": 6,
            "hidden_dim": 128,
            "num_layers": 2,
            "dropout": 0.2,
            "epochs": 150,
            "batch_size": 32,
            "lr": 1e-3,
        },
        "split": {
            "strategy": "temporal",  # Train on earlier timesteps, validate on later
            "train_ratio": 0.7,
            "val_ratio": 0.15,
            "test_ratio": 0.15,
        },
        "targets": ["water_level", "flow", "velocity"],
        "metrics": ["rmse", "mae", "r2", "nse"],
        "calibration": "quantile_regression",
    },

    # ── Model D: Traffic Forecasting (METR-LA / PEMS-BAY) ────────────────────
    "traffic": {
        "datasets": ["metr_la", "pems_bay"],
        "primary": "metr_la",
        "holdout_region": "pems_bay",  # Full region holdout for generalization
        "architectures": {
            "baseline": "lightgbm",
            "advanced": "graph_wavenet",
        },
        "lightgbm": {
            "n_estimators": 1000,
            "early_stopping_rounds": 50,
            "learning_rate": 0.05,
            "max_depth": 7,
            "num_leaves": 63,
        },
        "temporal": {
            "sequence_length": 12,  # 1 hour of 5-min intervals
            "prediction_horizon": 12,  # Predict next 1 hour
            "hidden_dim": 64,
            "epochs": 150,
            "batch_size": 64,
            "lr": 1e-3,
        },
        "split": {
            "strategy": "temporal",
            "train_ratio": 0.7,
            "val_ratio": 0.1,
            "test_ratio": 0.2,
        },
        "targets": ["speed"],
        "metrics": ["rmse", "mae", "mape"],
    },

    # ── Model E: Landslide Susceptibility (Landslide4Sense) ──────────────────
    "landslide": {
        "dataset": "landslide4sense",
        "architecture": "resnet18_multispectral",
        "num_bands": 14,  # Sentinel-2 (B1-B12) + ALOS slope + ALOS DEM
        "num_classes": 2,  # landslide / no-landslide
        "input_size": 128,
        "batch_size": 32,
        "epochs": 150,
        "early_stopping_patience": 20,
        "optimizer": "adamw",
        "lr": 1e-3,
        "weight_decay": 1e-4,
        "loss": "focal",  # Focal loss for class imbalance
        "focal_alpha": 0.75,
        "focal_gamma": 2.0,
        "augmentation": {
            "horizontal_flip": True,
            "vertical_flip": True,
            "rotation": 90,
        },
        "split": {
            "strategy": "spatial_group",  # Spatial block split
            "val_ratio": 0.15,
            "test_ratio": 0.15,
        },
        "metrics": ["accuracy", "precision", "recall", "f1", "auc_roc", "auc_pr"],
        "calibration": "temperature_scaling",
        "uncertainty": "mc_dropout",
    },

    # ── Model F: Drainage/Sewer Intelligence (CSO + Flood Network) ───────────
    "drainage": {
        "dataset": "nysdec_cso",
        "supplementary": "urban_flood_bench",
        "architecture": "lightgbm",
        "lightgbm": {
            "n_estimators": 500,
            "learning_rate": 0.05,
            "max_depth": 6,
            "num_leaves": 31,
            "early_stopping_rounds": 30,
        },
        "features": [
            "num_permitted_outfalls", "county", "dec_region",
            "latitude", "longitude", "activation_type",
        ],
        "targets": ["num_overflow_events"],
    },

    # ── Optuna Hyperparameter Optimization ───────────────────────────────────
    "optuna": {
        "n_trials": 50,
        "pruning": True,
        "pruner": "median",
        "sampler": "tpe",
        "study_storage": "sqlite:///ml/experiments/optuna.db",
    },

    # ── Ensemble Configuration ───────────────────────────────────────────────
    "ensemble": {
        "method": "weighted_average",
        "weight_optimization": "validation_oof",
        "models_to_ensemble": {
            "flood": ["lightgbm", "xgboost"],
            "traffic": ["lightgbm", "graph_temporal"],
        },
    },

    # ── Calibration ──────────────────────────────────────────────────────────
    "calibration": {
        "methods": ["temperature_scaling", "isotonic_regression", "platt_scaling"],
        "evaluation_bins": 15,
    },
}
