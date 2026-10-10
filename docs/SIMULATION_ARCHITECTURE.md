# Simulation Architecture

Reality Sculptor employs a multi-physics, coupled simulation architecture where distinct domain models interact continuously.

## Modular ISimulationModel Interface

All engines implement a common interface allowing them to be plugged into the World State Engine.
*   `init(world_graph)`
*   `step(dt)`
*   `get_state()`
*   `apply_event(event)`

## The Engines

### 1. Flood Physical Pipeline (Detailed)
*   **Input**: Rainfall (hyetograph), terrain (DEM/DSM), land cover (roughness, infiltration), drainage network state.
*   **Process**:
    *   Solves 2D Shallow Water Equations (SWE) for surface flow.
    *   Coupled 1D model for pipe flow (drainage/sewer).
    *   Exchanges volume between 1D and 2D domains at catch basins/manholes.
*   **Output**: Water depth, velocity, and duration per cell/node.

### 2. Heat Spatial Energy Model
*   **Input**: Solar radiation, building materials, vegetation cover, anthropogenic heat sources (traffic, HVAC).
*   **Process**: Calculates surface temperatures and mean radiant temperatures (MRT) considering shadowing and material albedo.
*   **Output**: Heat maps, thermal stress indices.

### 3. Traffic Dynamic System
*   **Input**: Road network, vehicle demand (OD matrices), signal timing.
*   **Process**: Agent-based or macroscopic flow models. Speed is dynamically reduced by flood depth.
*   **Output**: Vehicle speeds, queue lengths, travel times.

### 4. Sewer & Drainage Network Models
*   *See specific documentation files.*

### 5. Vegetation Growth Model
*   **Input**: Tree species, current age, soil type, water availability.
*   **Process**: Simulates canopy growth over years, affecting shading (Heat Model) and interception (Flood Model).
*   **Output**: Canopy diameter, height, root depth.

### 6. Emergency Access Model
*   **Input**: Traffic state, road closures (floods/debris).
*   **Process**: Calculates shortest path and travel time for emergency vehicles from depots to critical infrastructure.
*   **Output**: Response time heatmaps, isolated zones.

## Cascade Engine Connecting All

The Cascade Engine orchestrates the interaction between models during a `step()`.
1.  Rainfall occurs.
2.  Flood model runs `step()`. Updates water depth on roads.
3.  Cascade Engine passes water depth to Traffic model.
4.  Traffic model runs `step()`. Speeds decrease, congestion builds.
5.  Cascade Engine passes traffic state to Emergency model.
6.  Emergency model runs `step()`. Response times increase.

## Three Time Modes

1.  **REAL_TIME**: 1 second simulation = 1 second real life (used for live digital twins connected to sensors).
2.  **ACCELERATED**: Run a 24-hour storm event in minutes (standard analysis mode).
3.  **LONG_HORIZON**: Run years/decades to simulate vegetation growth, urban development, or climate change trends (low temporal resolution, e.g., 1 step = 1 month).

## Data-driven VFX Requirements

The simulation output drives the visual rendering in the frontend.
*   Flood depth maps drive water shaders (depth, flow direction).
*   Traffic data drives vehicle particle systems.
*   Heat data drives thermal camera visual overlays.
