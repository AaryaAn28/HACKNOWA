# Blueprint Ingestion

The Blueprint Analyzer is a critical pipeline in Reality Sculptor that extracts structured 3D spatial data and semantics from 2D engineering blueprints.

## Pipeline Architecture

```text
UPLOAD → PARSE → RENDER → OCR → SYMBOL_DETECT → LINE_NODE_EXTRACT → TEXT_LABEL → GEOMETRY_RECONSTRUCT → GEOREFERENCE → SEMANTIC_CLASSIFY → NETWORK_RECONSTRUCT → WORLD_UPDATE
```

1. **UPLOAD**: Document is uploaded to the system.
2. **PARSE**: Determine file type (PDF, CAD, TIFF, etc.).
3. **RENDER**: Render document to a high-resolution raster format for analysis.
4. **OCR**: Extract all text and numerical values.
5. **SYMBOL_DETECT**: Detect standardized symbols (manholes, catch basins, valves).
6. **LINE_NODE_EXTRACT**: Extract line work connecting symbols.
7. **TEXT_LABEL**: Associate extracted text with nearby symbols or lines (e.g., diameter labels for pipes).
8. **GEOMETRY_RECONSTRUCT**: Reconstruct 2D geometry of the features.
9. **GEOREFERENCE**: Align the reconstructed geometry with real-world coordinates.
10. **SEMANTIC_CLASSIFY**: Classify elements based on context and type (e.g., sewer pipe vs. drainage pipe).
11. **NETWORK_RECONSTRUCT**: Reconstruct topological connections (direction of flow, upstream/downstream).
12. **WORLD_UPDATE**: Inject the reconstructed network into the Spatial World Engine.

## Supported Blueprint Types

*   **Sewer**: Sanitary sewer networks.
*   **Drainage**: Stormwater drainage networks.
*   **Road**: Street and highway layouts, elevations.
*   **Building**: Footprints, roof types, HVAC locations.
*   **Utility**: Water, gas, electrical, telecommunications.

## Extraction Entities

| Blueprint Type | Extracted Entities | Attributes |
| :--- | :--- | :--- |
| Sewer | Pipes, Manholes, Pump Stations | Diameter, Material, Invert Elevation, Flow Direction |
| Drainage | Pipes, Catch Basins, Outfalls | Diameter, Invert Elevation, Grate Type, Capacity |
| Road | Centerlines, Curbs, Gutters | Width, Slope, Material, Elevation Profile |

## Georeferencing Approaches

1.  **Coordinate Grids**: Using extracted coordinate grids on the blueprint.
2.  **Known Features**: Matching extracted features (e.g., building corners, road intersections) with existing baseline data (e.g., OpenStreetMap, building footprints).
3.  **Manual Anchors**: Human-provided anchor points matching blueprint pixels to map coordinates.

## Conflict Resolution

When blueprints conflict with existing world data or other blueprints:
1.  **Confidence Score**: Higher confidence sources win (e.g., CAD > scanned PDF).
2.  **Date**: Newer documents generally override older ones.
3.  **Human Review**: Flagged for human-in-the-loop review if conflicts are significant.

## Human-in-the-loop Correction

The system provides an interface for users to manually correct extraction errors.
*   Add/remove/move nodes and edges.
*   Correct text OCR errors (e.g., 800mm instead of 80mm).
*   These corrections feed back into the active learning loop to improve future extraction.

## Blueprint Versioning & Diff

Blueprints are versioned. Uploading a newer version of a blueprint will generate a diff.
*   Removed elements are deactivated in the simulation.
*   Added elements are activated.
*   Modified elements are updated.

## Example: Sewer Blueprint Analysis

```text
[Manhole A] ----(Pipe: 300mm PVC)----> [Manhole B]
    ^                                      |
    | (Flow)                               | (Flow)
    |                                      v
[Lateral 1]                            [Outfall]
```
The resulting network is fed directly into the `SewerIntelligenceEngine` to calculate flow capacities and potential bottlenecks.
