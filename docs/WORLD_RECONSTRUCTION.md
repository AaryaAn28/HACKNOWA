# World Reconstruction

Reality Sculptor reconstructs the physical world in layers, transforming raw data into a fully interactive simulation environment.

## Three Reconstruction Levels

1.  **MAP_WORLD**:
    *   2D basemap layer.
    *   Sourced from OpenStreetMap, basic GIS data.
    *   Provides rough outlines of roads, buildings, and water bodies.
    *   *Usage*: Initial context, low-fidelity simulations.
2.  **SPATIAL_WORLD**:
    *   2.5D/3D extruded models based on blueprints, elevation data (DEM/DSM).
    *   Nodes and edges for networks (roads, pipes).
    *   Basic semantic understanding (this is a building, this is a road).
    *   *Usage*: Most simulations (flood, traffic, basic sewer/drainage).
3.  **HIGH_FIDELITY_WORLD**:
    *   Detailed 3D geometry from LiDAR, photogrammetry, detailed architectural models.
    *   Precise textures, materials, and structural details.
    *   *Usage*: Visual presentation, micro-climate simulations (wind flow around specific building features).

## Semantic World Graph

The world is not just a collection of meshes; it is a connected graph.
*   **Nodes**: Physical entities (Building, Road Segment, Manhole, Tree).
*   **Edges**: Relationships (Adjacent_To, Flows_Into, Intersects, Supports).

See `SEMANTIC_WORLD_MODEL.md` for details.

## Object-to-Simulation Binding

Physical objects in the World Graph are dynamically bound to simulation models.
*   A `RoadSegment` node is bound to the `TrafficModel` and `FloodModel`.
*   A `CatchBasin` node is bound to the `DrainageModel` and `FloodModel`.
*   When a simulation updates the state of a node (e.g., FloodModel calculates 0.5m water depth on RoadSegment X), this state is available to all other bound models (e.g., TrafficModel reduces capacity of RoadSegment X).

## Procedural Generation for Missing Geometry

When data is incomplete, the system procedurally generates plausible substitutes based on statistical priors.
*   *Missing Building Height*: Extrapolated from average heights in the neighborhood or zoning laws.
*   *Missing Pipe Invert*: Interpolated between known upstream and downstream inverts.
*   **Crucially**: Procedurally generated data is always tagged with a low confidence score (`ESTIMATED` or `SIMULATED`).

## World Reconstruction Status

The UI provides a dashboard showing reconstruction progress.
*   Percentage of area covered by specific data types (e.g., "70% Sewer coverage").
*   Confidence heatmaps (areas with high confidence vs. low confidence data).

## Automatic Region Bootstrap

When a user defines a new project boundary, the system automatically:
1.  Fetches OSM data.
2.  Fetches public DEM data.
3.  Builds the `MAP_WORLD` and a baseline `SPATIAL_WORLD` instantly.
4.  Generates a "Data Gap" report outlining what files the user needs to upload to achieve higher fidelity.
