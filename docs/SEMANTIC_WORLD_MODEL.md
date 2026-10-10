# Semantic World Model

The core of Reality Sculptor is the Semantic World Graph, a spatial and relational database representing the physical environment.

## Object Types (Nodes)

*   **Infrastructure**: `Building`, `RoadSegment`, `Bridge`, `Tunnel`.
*   **Hydraulics**: `Pipe`, `Manhole`, `CatchBasin`, `PumpStation`, `Outfall`, `Channel`.
*   **Environment**: `Tree`, `Park`, `WaterBody`, `TerrainCell`.
*   **Agents**: `Vehicle`, `Pedestrian` (often transient, not permanently stored in the base graph).

## Relationships (Edges)

Edges define topology, spatial relationships, and causal links.

*   **Spatial**: `ADJACENT_TO`, `CONTAINS`, `INTERSECTS`, `ABOVE`, `BELOW`.
*   **Topological (Networks)**: `FLOWS_TO`, `CONNECTS_TO`.
*   **Semantic**: `SERVES` (e.g., Pipe serves Building), `OWNED_BY`.

### Example Graphs

```text
[Building_101] --(ADJACENT_TO)--> [RoadSegment_MainSt]
[Building_101] --(DISCHARGES_TO)--> [Manhole_S12]

[CatchBasin_CB5] --(FLOWS_TO)--> [Pipe_D8] --(FLOWS_TO)--> [Outfall_River]
[CatchBasin_CB5] --(LOCATED_ON)--> [RoadSegment_ElmSt]
```

## Cross-domain Causal Connections

The graph allows multi-domain analysis simply by traversing edges.
*   If `Pipe_D8` fails (blockage).
*   Trace upstream: `CatchBasin_CB5` overflows.
*   Trace spatial relations: `CatchBasin_CB5` is `LOCATED_ON` `RoadSegment_ElmSt`.
*   Conclusion: `RoadSegment_ElmSt` will flood.

## Critical Node Detection Algorithm

We identify critical infrastructure using multi-factor scoring based on graph centrality and semantics.
1.  **Betweenness Centrality**: Nodes that sit on many shortest paths (e.g., a main trunk sewer).
2.  **Upstream Area**: Nodes that receive flow from a massive area.
3.  **Semantic Importance**: Nodes connected to critical facilities (Hospitals, Fire Stations).

`Criticality Score = w1*(Centrality) + w2*(Upstream_Volume) + w3*(Semantic_Value)`

High criticality nodes are prioritized in bottleneck analysis and highlighted in the UI.
