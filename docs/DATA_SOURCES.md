# Data Sources & Ingestion

The Universal Upload Center handles all incoming data, categorizing and routing it to the appropriate pipelines.

## Universal Upload Center Categories (12)

1.  **Topography**: DEM, DSM, LiDAR point clouds.
2.  **Blueprints (Sewer)**: CAD, PDF, TIFF of sanitary networks.
3.  **Blueprints (Drainage)**: Stormwater networks.
4.  **Blueprints (Utility)**: Water, gas, electric lines.
5.  **Blueprints (Structural)**: Building plans, foundations.
6.  **GIS Vector**: Shapefiles, GeoJSON of roads, parcels, zoning.
7.  **Traffic Demand**: Origin-Destination (OD) matrices, sensor logs.
8.  **Meteorology**: Historical rainfall (CSV), weather station data.
9.  **Hydrology**: River gauge data, tide levels.
10. **Demographics**: Census data, population density grids.
11. **Sensors (Live)**: API endpoints for SCADA, IoT devices.
12. **Custom Overrides**: Manual CSV uploads overriding specific node parameters.

## Auto-classification Logic

When a user drags and drops files, the system attempts to auto-classify them:
*   `.shp`, `.dbf`, `.shx` -> GIS Vector.
*   `.tif` with coordinate metadata -> Topography.
*   PDF with keywords ("Sanitary", "Invert", "Manhole") -> Blueprints (Sewer).
*   If classification fails, it asks the user via the `QUESTIONNAIRE_ENGINE`.

## Incremental World Update

*   When new data is uploaded, the entire world is **not** rebuilt from scratch.
*   The system calculates a "diff" and updates only the affected nodes in the Semantic World Graph.
*   This triggers invalidation of cached simulation results in the affected region.

## Source Priority & Conflict Resolution

See `DATA_CONFIDENCE.md` for the priority hierarchy.
*   If a user uploads a detailed survey shapefile of roads, it will override the existing OSM road data.
*   Conflicts are flagged for user review if the geometries differ significantly (e.g., new road is 50m away from old road).

## Active Learning

*   When a user manually corrects an auto-classified blueprint or resolves a conflict, this action is recorded.
*   This data is used to retrain the parsing and classification models, improving future ingestion accuracy.
