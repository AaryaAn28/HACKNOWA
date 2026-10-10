# Model Training Approach

While Reality Sculptor relies heavily on physical simulations (like 2D SWE for floods), Machine Learning models are used as fast surrogates, parameter estimators, and for classifying semantic data.

## LightGBM (Primary) & XGBoost (Secondary)

We prioritize Gradient Boosting Decision Trees (GBDTs) over deep learning for tabular and spatial-tabular data due to:
*   Faster training and inference times.
*   Superior performance on tabular data out-of-the-box.
*   Better interpretability (feature importance).
*   LightGBM is the primary choice for speed; XGBoost is a fallback for specific edge cases or ensembles.

## Feature Engineering (30+ Features)

Spatial features are critical. Examples include:
*   **Topographic**: Elevation, Slope, Aspect, Topographic Wetness Index (TWI), Profile Curvature.
*   **Hydrological**: Distance to nearest drain, Distance to nearest water body, Upstream contributing area.
*   **Urban**: Impervious surface fraction, Building density, Distance to nearest road.
*   **Network**: Node centrality, Edge betweenness, Downstream capacity ratio.

## Leakage Prevention

Standard cross-validation fails on spatial data due to spatial autocorrelation (Tobler's First Law).
*   **Spatial Block CV**: The map is divided into large grid blocks. Entire blocks are held out for validation, ensuring the model generalizes to new areas, not just interpolating nearby pixels.
*   **Temporal CV**: When training on historical events (e.g., traffic data), split by time (train on past, predict future).

## Early Stopping Strategy

*   Monitor validation loss during training.
*   Stop training when validation loss fails to improve for `N` consecutive rounds to prevent overfitting.

## Optuna Hyperparameter Search

*   Use Optuna for Bayesian optimization of hyperparameters (learning rate, tree depth, num_leaves, subsample).
*   Objective function: Minimize Spatial Block CV error.

## Model Evaluation Metrics

*   **Regression**: RMSE, MAE, R-squared.
*   **Classification**: F1-score (macro/micro), Precision, Recall, spatial IoU.

## Calibration and Stress Testing

*   **Calibration**: Ensure probability outputs reflect true likelihoods (e.g., using Platt scaling or Isotonic Regression).
*   **Stress Testing**: Test model behavior with extreme, out-of-distribution inputs (e.g., 500-year rainfall) to ensure graceful degradation, not silent failure.

## Model Registry & Data Lineage

*   Every trained model is saved to a Model Registry with its metadata, hyperparameters, and evaluation metrics.
*   **Data Lineage**: The exact dataset version used for training is recorded to ensure reproducibility.

## Training Data Pipeline

1.  Extract features from World Graph.
2.  Join with target variables (e.g., historical flood depths, sensor data, or high-fidelity physical simulation outputs).
3.  Preprocess (handle missing values, encode categoricals).
4.  Train.
