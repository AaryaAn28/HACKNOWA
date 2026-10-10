# Model Validation

Rigorous validation is required before any simulation output is presented to the user with high confidence.

## Validation Sources

Models are validated against:
1.  **Historical Events**: Comparing flood simulation of a known past storm against documented flood extents (FEMA maps, insurance claims, news photos).
2.  **Sensors**: Comparing traffic simulation against live traffic loop data, or sewer simulation against SCADA flow meters.
3.  **Known Behavior**: Heuristic checks (e.g., water must flow downhill).

## Domain-Specific Metrics

### Flood
*   **Depth Error**: Mean Absolute Error (MAE) between simulated and observed peak depths at specific points.
*   **Extent IoU**: Intersection over Union of the simulated flood polygon vs. observed flood footprint.
*   **Duration Error**: Error in the time it takes for water to recede.

### Heat
*   **Temperature MAE**: Difference between simulated surface temp and satellite thermal imagery (e.g., Landsat).
*   **Hotspot Detection**: Precision/Recall of identifying the top 5% hottest areas in a neighborhood.

## Synthetic Data Policy

*   Synthetic data (e.g., outputs from a high-fidelity 2D physics model used to train a fast ML surrogate) can be used for training and *initial* validation.
*   **Rule**: Synthetic data is **never** used as the *sole* evidence for validating a model intended for production. Ground truth validation is always required.
*   Data augmentation (rotating maps, adding noise) is permitted but strictly documented.

## Geographic Generalization Requirements

A model trained in City A cannot be deployed to City B without passing a geographic generalization test.
*   The model must achieve acceptable metrics on a holdout set from a geographically distinct region with similar characteristics before being marked as globally available.
