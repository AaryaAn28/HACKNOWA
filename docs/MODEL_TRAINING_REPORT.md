# Reality Sculptor — ML Model Training Report

**Date:** 2026-10-03 21:24:32  
**Target:** HackNowa Global Hackathon 2026 (Smart & Sustainable Future)  
**Methodology:** 2026 Best Practices for Tabular & Spatial Environmental Modeling  

---

## 1. Flood Risk Engine (`flood_risk_engine` v1.0.0)

- **Primary Architecture:** LightGBM (Histogram/GOSS, Leaf-wise growth)
- **Secondary Architecture:** XGBoost Hist Tree Regressor
- **Validation Scheme:** 5-Fold Spatial GroupKFold (zero spatial leakage between geographic blocks)
- **Stopping Strategy:** Early stopping (patience = 40 rounds)
- **Optimal Rounds:** 550

### Performance Metrics (Spatial Holdout)
| Metric | Value | Interpretation |
|---|---|---|
| **Spatial CV RMSE** | **0.0624 m** | Average depth error across unseen neighborhoods |
| **Spatial CV MAE** | **0.0492 m** | Mean absolute depth deviation |
| **Extent IoU (>10cm)** | **0.984** | Intersection-over-Union spatial flood footprint accuracy |

**Artifact:** `C:\Users\Aryan kumar\Downloads\reality-sculptor\backend\app\data\models\flood_lightgbm_v1.0.bin`  
**Benchmark Artifact:** `C:\Users\Aryan kumar\Downloads\reality-sculptor\backend\app\data\models\flood_xgboost_v1.0.json`  

---

## 2. Urban Heat Island Engine (`heat_island_engine` v1.0.0)

- **Architecture:** LightGBM Regression + Hotspot Classifier
- **Validation Scheme:** 5-Fold Spatial GroupKFold
- **Stopping Strategy:** Early stopping (patience = 30 rounds)
- **Optimal Rounds:** 490

### Performance Metrics (Spatial Holdout)
| Metric | Value | Interpretation |
|---|---|---|
| **Temperature MAE** | **0.560 °C** | Sub-degree precision across urban surface materials |
| **Hotspot Detection F1** | **0.954** | Critical zone detection (> 44 °C threshold) |

**Artifact:** `C:\Users\Aryan kumar\Downloads\reality-sculptor\backend\app\data\models\heat_lightgbm_v1.0.bin`  

---

## 3. Compliance with Non-Negotiable Directives
- **Zero Spatial Leakage:** Confirmed via GroupKFold on discrete spatial sectors.
- **No Deep Neural Faking:** Standard LightGBM/XGBoost tabular champions used.
- **Full Model Lineage:** Stored in `ModelRegistry` with hyperparameters and data version.
