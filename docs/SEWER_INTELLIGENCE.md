# Sewer Intelligence

The Sewer Intelligence engine analyzes sanitary sewer networks to identify capacities, bottlenecks, and failure points.

## Network Graph Construction

Sewer networks are represented as directed acyclic graphs (DAGs) in most cases, though loops can occur in combined systems.
*   **Nodes**: Manholes, pump stations, treatment plants.
*   **Edges**: Pipes. Flow direction is determined by invert elevations.

## "What is slowing this sewer?" Analysis

The engine can diagnose up to 15 different causes for bottlenecks. Common diagnoses include:
1.  **Insufficient Pipe Diameter**: Pipe is too small for upstream contributing area.
2.  **Negative/Flat Slope**: Pipe slope does not support gravity flow.
3.  **Pump Failure/Under-capacity**: Pump station cannot handle inflow.
4.  **Downstream Surcharge**: Backwater effects from a flooded downstream node.
5.  **Infiltration/Inflow (I&I)**: Excessive groundwater or stormwater entering the sanitary system.
6.  **Sedimentation**: Assumed reduction in capacity due to age/lack of maintenance.

## Bottleneck Identification

A bottleneck is defined as a node or edge where `Inflow > Capacity`. The engine traces back from the bottleneck to determine the contributing factors.

## Sewer → Flood Causal Connection

In combined sewer systems (or sanitary systems with extreme I&I), sewer surcharge leads directly to surface flooding.
*   When a manhole node reaches capacity (HGL > ground elevation), water volume is transferred to the connected surface `FloodModel` node.

## Manning's Equation

Pipe capacity is primarily estimated using Manning's equation for open channel/full pipe flow:
`Q = (1.00 / n) * A * R^(2/3) * S^(1/2)` (Metric)
*   `Q` = Flow Rate
*   `n` = Manning's roughness coefficient (based on pipe material)
*   `A` = Cross-sectional area
*   `R` = Hydraulic radius
*   `S` = Slope

## Confidence Labels

Every diagnosis includes a confidence label based on data provenance.
*   *Diagnosis*: Insufficient Diameter.
*   *Confidence*: `DERIVED` (if diameter was explicitly in a blueprint).
*   *Confidence*: `ESTIMATED` (if diameter was procedurally guessed).

## Example: Pipe S-042 Near-Capacity Bottleneck Analysis

*   **Target**: Pipe S-042 (Diameter: 200mm, Slope: 0.005)
*   **Calculated Capacity**: 0.04 m³/s
*   **Simulated Peak Flow**: 0.038 m³/s
*   **Diagnosis**: Near Capacity (95%).
*   **Root Cause**: Significant development upstream (150 new homes added to node M-10) without downstream capacity upgrades.
*   **Recommendation**: Upgrade S-042 to 300mm or divert flow at M-10.
