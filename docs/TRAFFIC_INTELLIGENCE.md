# Traffic Intelligence

Traffic in Reality Sculptor is not treated as a static heatmap, but as a dynamic, responsive system that interacts with environmental hazards.

## Traffic as a Dynamic System

*   **Vehicles**: Represented macroscopically (flow density) or microscopically (individual agents), depending on simulation scale.
*   **Road Capacity**: The maximum number of vehicles a segment can handle per hour.
*   **Speed**: Free-flow speed vs. congested speed.
*   **Propagation**: Congestion on one segment spills backward to upstream segments (shockwaves).

## Environmental Interaction: Flood → Traffic

The most critical interaction is how environmental factors degrade traffic performance.
1.  **Flood Depth Function**:
    *   `Depth < 5cm`: No effect on speed.
    *   `5cm < Depth < 15cm`: Speed reduces linearly (hydroplaning risk).
    *   `Depth > 15cm`: Capacity drops sharply.
    *   `Depth > 30cm`: Road segment becomes impassable (Capacity = 0).
2.  **Dynamic Routing**: As roads flood, simulated vehicles actively attempt to reroute, pushing congestion onto secondary roads that may not be designed for high volume.

## Emergency Route Intelligence

The system continuously calculates accessibility for emergency services.
*   **Input**: Locations of Fire Stations, Hospitals, Police Depots.
*   **Simulation**: Uses the *degraded* traffic state (post-flood or post-hazard) to calculate travel times to all nodes.
*   **Output**: Identifies "Islands" — areas where emergency response time exceeds acceptable thresholds (e.g., > 15 minutes) due to flooded access routes.

## Trade-off Detection

The Traffic Intelligence engine helps identify unintended consequences of interventions.
*   *Intervention*: Build a flood wall to protect a neighborhood.
*   *Consequence*: The wall displaces water onto a major arterial road.
*   *Trade-off*: Neighborhood flood damage decreases, but city-wide traffic delay increases by 40%, and emergency access to the hospital is cut off.
*   The system highlights these trade-offs to the user during scenario comparison.
