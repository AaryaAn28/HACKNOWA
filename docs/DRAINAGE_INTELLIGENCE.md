# Drainage Intelligence

The Drainage Intelligence engine focuses on stormwater management systems, assessing their ability to handle rainfall events and prevent surface flooding.

## Network Extraction

Extracted primarily from stormwater blueprints via the `BLUEPRINT_INGESTION` pipeline. Key features include catch basins, storm sewers, culverts, and outfalls.

## "Why is this drain failing?" Analysis

Similar to Sewer Intelligence, but focused on surface water ingress.
1.  **Grate Blockage**: Debris blocking catch basin grates (can be modeled probabilistically).
2.  **Inlet Capacity Exceeded**: Catch basin cannot swallow water fast enough, even if the underlying pipe has capacity.
3.  **Pipe Surcharge**: Storm sewer is full.
4.  **Outfall Submersion**: The river or ocean the system drains into is too high (tide/flood), preventing discharge.

## Capacity Estimation

Capacity is calculated based on:
1.  **Inlet Capacity**: Using weir/orifice equations based on grate type.
2.  **Conveyance Capacity**: Manning's equation for pipes and open channels.

## The Cascade Effect: Drain → Flood → Road → Traffic → Emergency

Drainage failure triggers a critical cascade in Reality Sculptor:
1.  **Drain Failure**: Catch basin capacity exceeded.
2.  **Flood**: Water accumulates on the surface.
3.  **Road**: Water depth on the connected road segment increases.
4.  **Traffic**: Road speed limit drops (or road becomes impassable).
5.  **Emergency**: Ambulances/fire trucks are delayed or rerouted.

## Bottleneck and Blockage Identification

The engine identifies the "weakest link" in the drainage chain.
*   If a street floods, but the underlying pipe is only 50% full, the bottleneck is the **Inlet** (need more catch basins).
*   If the street floods and the pipe is 100% full, the bottleneck is **Conveyance** (need larger pipes).

## Example Analysis

*   **Event**: 50mm/hr Rainfall (10-year storm).
*   **Location**: Intersection of 5th and Main.
*   **Observation**: Surface flooding 0.3m deep.
*   **Analysis**:
    *   Catch basins at intersection are at 100% inlet capacity.
    *   Downstream pipe is at 40% capacity.
    *   Outfall is clear.
*   **Diagnosis**: Inlet capacity deficiency. Adding two more catch basins will resolve the local flood without requiring pipe upgrades.
