"""
Generate supported_world_classes.json, dataset_to_world_mapping.json, 
and assets/asset_registry.json based on actual downloaded datasets.
Implements Directive Sections 2, 5, 23, 25, 41.
"""

import json
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor")
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Create subdirectories
subdirs = [
    "buildings", "roads", "terrain", "vegetation", "water", 
    "sewer", "drainage", "infrastructure", "vehicles", 
    "weather", "decals", "materials", "textures", "vfx"
]
for d in subdirs:
    (ASSETS_DIR / d).mkdir(parents=True, exist_ok=True)

# 2. Build supported_world_classes.json
supported_world_classes = {
    "schema_version": "2.0.0",
    "description": "Ground-truth semantic 3D classes supported by available datasets and trained models",
    "domains": {
        "terrain": {
            "description": "Topographical surface layers from ALOS DEM and Landslide4Sense",
            "classes": [
                {"class_name": "TERRAIN_SURFACE", "geometry_type": "HeightmapMesh", "provenance_default": "DERIVED", "source_dataset": "ALOS_DEM_30M"},
                {"class_name": "DEPRESSION_BASIN", "geometry_type": "PolygonVolume", "provenance_default": "DERIVED", "source_dataset": "Terrain_D8_Analysis"},
                {"class_name": "SLOPE_HAZARD_ZONE", "geometry_type": "PolygonOverlay", "provenance_default": "ESTIMATED", "model_id": "landslide_resnet18_v1", "source_dataset": "Landslide4Sense"}
            ]
        },
        "structures": {
            "description": "Building envelopes and structural footprints",
            "classes": [
                {"class_name": "BUILDING_RESIDENTIAL", "geometry_type": "ExtrudedFootprint", "provenance_default": "OBSERVED", "source_dataset": "MS_Building_Footprints"},
                {"class_name": "BUILDING_COMMERCIAL", "geometry_type": "ExtrudedFootprint", "provenance_default": "OBSERVED", "source_dataset": "MS_Building_Footprints"},
                {"class_name": "BUILDING_INDUSTRIAL", "geometry_type": "ExtrudedFootprint", "provenance_default": "OBSERVED", "source_dataset": "MS_Building_Footprints"},
                {"class_name": "BUILDING_EXTRACTED", "geometry_type": "SegmentedMaskToPolygon", "provenance_default": "ESTIMATED", "model_id": "building_unet_v1", "source_dataset": "IEEE_Building_Extraction"}
            ]
        },
        "transportation": {
            "description": "Roadway hierarchies, intersections, and corridors",
            "classes": [
                {"class_name": "ROAD_MOTORWAY", "geometry_type": "SplineCorridor", "lanes": 6, "width_m": 24.0, "provenance_default": "OBSERVED", "source_dataset": "OpenStreetMap"},
                {"class_name": "ROAD_PRIMARY", "geometry_type": "SplineCorridor", "lanes": 4, "width_m": 16.0, "provenance_default": "OBSERVED", "source_dataset": "OpenStreetMap"},
                {"class_name": "ROAD_SECONDARY", "geometry_type": "SplineCorridor", "lanes": 2, "width_m": 10.0, "provenance_default": "OBSERVED", "source_dataset": "OpenStreetMap"},
                {"class_name": "ROAD_RESIDENTIAL", "geometry_type": "SplineCorridor", "lanes": 2, "width_m": 7.0, "provenance_default": "OBSERVED", "source_dataset": "OpenStreetMap"},
                {"class_name": "TRAFFIC_CORRIDOR_SEGMENT", "geometry_type": "SplineWithSpeedVector", "provenance_default": "ESTIMATED", "model_id": "traffic_lightgbm_metrla_v1", "source_dataset": "METR_LA"}
            ]
        },
        "land_cover": {
            "description": "Surface vegetative and functional zoning",
            "classes": [
                {"class_name": "LANDCOVER_FOREST", "geometry_type": "PCGZone", "provenance_default": "ESTIMATED", "model_id": "landcover_resnet18_v1", "source_dataset": "EuroSAT"},
                {"class_name": "LANDCOVER_HERBACEOUS", "geometry_type": "PCGZone", "provenance_default": "ESTIMATED", "model_id": "landcover_resnet18_v1", "source_dataset": "EuroSAT"},
                {"class_name": "LANDCOVER_AGRICULTURAL", "geometry_type": "SurfaceTextureZone", "provenance_default": "ESTIMATED", "model_id": "landcover_resnet18_v1", "source_dataset": "EuroSAT"},
                {"class_name": "LANDCOVER_IMPERVIOUS", "geometry_type": "SurfaceTextureZone", "provenance_default": "ESTIMATED", "model_id": "landcover_resnet18_v1", "source_dataset": "EuroSAT"}
            ]
        },
        "hydrology": {
            "description": "Surface waterbodies and dynamic hydrodynamic inundation",
            "classes": [
                {"class_name": "WATERBODY_RIVER", "geometry_type": "RibbonMesh", "provenance_default": "OBSERVED", "source_dataset": "OpenStreetMap"},
                {"class_name": "WATERBODY_LAKE", "geometry_type": "PlanarPolygonMesh", "provenance_default": "OBSERVED", "source_dataset": "OpenStreetMap"},
                {"class_name": "WATERBODY_CANAL", "geometry_type": "RibbonChannelMesh", "provenance_default": "OBSERVED", "source_dataset": "OpenStreetMap"},
                {"class_name": "FLOOD_INUNDATION_CELL", "geometry_type": "DynamicHeightCell", "provenance_default": "SIMULATED", "model_id": "flood_lightgbm_v1", "source_dataset": "UrbanFloodBench"}
            ]
        },
        "underground_subsurface": {
            "description": "Underground pipe conduits, manholes, inlets, and outfalls",
            "classes": [
                {"class_name": "SEWER_PIPE_CIRCULAR", "geometry_type": "CylinderExtrusion", "provenance_default": "OBSERVED", "source_dataset": "UrbanFloodBench"},
                {"class_name": "DRAINAGE_CHANNEL_RECT", "geometry_type": "PrismaticConduit", "provenance_default": "OBSERVED", "source_dataset": "UrbanFloodBench"},
                {"class_name": "SEWER_MANHOLE", "geometry_type": "VerticalShaftWithCover", "provenance_default": "OBSERVED", "source_dataset": "UrbanFloodBench"},
                {"class_name": "SURFACE_DRAIN_INLET", "geometry_type": "GrateMeshWithInflowShaft", "provenance_default": "OBSERVED", "source_dataset": "UrbanFloodBench"},
                {"class_name": "CSO_OUTFALL", "geometry_type": "HeadwallPipeExit", "provenance_default": "OBSERVED", "model_id": "drainage_cso_lightgbm_v1", "source_dataset": "NYSDEC_CSO"},
                {"class_name": "PUMP_STATION", "geometry_type": "SubsurfaceVault", "provenance_default": "OBSERVED", "source_dataset": "NYSDEC_CSO"}
            ]
        }
    }
}

# 3. Build dataset_to_world_mapping.json
dataset_to_world_mapping = {
    "schema_version": "2.0.0",
    "description": "Deterministic mapping from dataset raw features to 3D semantic objects, PBR materials, textures, and VFX",
    "mappings": [
        {
            "dataset_source": "OpenStreetMap",
            "feature_key": "highway=motorway",
            "semantic_class": "ROAD_MOTORWAY",
            "geometry_generator": "SplineExtruder",
            "geometry_params": {"width_m": 24.0, "curb_height_m": 0.15, "sidewalk_width_m": 2.0},
            "pbr_material": "M_Master_Road",
            "pbr_material_instance": "MI_Road_Highway_Asphalt",
            "texture_set": "ambientCG_Asphalt012",
            "dynamic_state_bindings": {"surface_wetness": "world_state.rainfall_intensity", "flooded": "world_state.water_depth > 0.05"},
            "vfx": "Niagara_TireSpray_Emitter"
        },
        {
            "dataset_source": "OpenStreetMap",
            "feature_key": "highway=primary",
            "semantic_class": "ROAD_PRIMARY",
            "geometry_generator": "SplineExtruder",
            "geometry_params": {"width_m": 16.0, "curb_height_m": 0.15, "sidewalk_width_m": 2.0},
            "pbr_material": "M_Master_Road",
            "pbr_material_instance": "MI_Road_Urban_Asphalt",
            "texture_set": "ambientCG_Asphalt008",
            "dynamic_state_bindings": {"surface_wetness": "world_state.rainfall_intensity"},
            "vfx": "None"
        },
        {
            "dataset_source": "MS_Building_Footprints",
            "feature_key": "building=yes",
            "semantic_class": "BUILDING_RESIDENTIAL",
            "geometry_generator": "BuildingFootprintExtruder",
            "geometry_params": {"default_height_m": 9.0, "parapet_height_m": 0.6, "roof_type": "flat_with_parapet"},
            "pbr_material": "M_Master_Building",
            "pbr_material_instance": "MI_Building_ConcreteFacade",
            "texture_set": "PolyHaven_Concrete_001",
            "dynamic_state_bindings": {"surface_temp": "world_state.surface_temperature", "water_line": "world_state.water_depth"},
            "vfx": "None"
        },
        {
            "dataset_source": "IEEE_Building_Extraction",
            "feature_key": "segmented_mask",
            "semantic_class": "BUILDING_EXTRACTED",
            "geometry_generator": "VectorizedMaskExtruder",
            "geometry_params": {"estimated_height_m": 8.0, "procedural_detail": "PROCEDURAL_APPROXIMATION"},
            "pbr_material": "M_Master_Building",
            "pbr_material_instance": "MI_Building_WeatheredBrick",
            "texture_set": "PolyHaven_GranularConcrete",
            "dynamic_state_bindings": {},
            "vfx": "None"
        },
        {
            "dataset_source": "EuroSAT",
            "feature_key": "class=Forest",
            "semantic_class": "LANDCOVER_FOREST",
            "geometry_generator": "PCGFoliageZone",
            "geometry_params": {"density_per_100sqm": 4.5, "height_variation": [6.0, 18.0]},
            "pbr_material": "M_Master_Vegetation",
            "pbr_material_instance": "MI_Foliage_Broadleaf",
            "texture_set": "PolyHaven_ForestFloor",
            "dynamic_state_bindings": {"wind_sway": "world_state.wind_speed"},
            "vfx": "Niagara_FallingLeaves"
        },
        {
            "dataset_source": "UrbanFloodBench",
            "feature_key": "link_type=conduit",
            "semantic_class": "SEWER_PIPE_CIRCULAR",
            "geometry_generator": "UndergroundCylinderPipeExtruder",
            "geometry_params": {"radius_m": "source.diameter_m / 2.0", "inlet_z": "source.inlet_elevation", "outlet_z": "source.outlet_elevation"},
            "pbr_material": "M_Master_Sewer",
            "pbr_material_instance": "MI_Sewer_ReinforcedConcrete",
            "texture_set": "PolyHaven_ConcreteFloor",
            "dynamic_state_bindings": {"flow_fill_fraction": "simulation.sewer_fill_ratio", "velocity_ms": "simulation.sewer_flow_velocity", "failure_flag": "simulation.failure_detected"},
            "vfx": "Niagara_InternalFluidFlow_Pulse"
        },
        {
            "dataset_source": "UrbanFloodBench",
            "feature_key": "node_type=manhole",
            "semantic_class": "SEWER_MANHOLE",
            "geometry_generator": "ManholeShaftGenerator",
            "geometry_params": {"depth_m": "source.rim_elev - source.invert_elev", "cover_radius_m": 0.45},
            "pbr_material": "M_Master_Metal",
            "pbr_material_instance": "MI_CastIron_ManholeCover",
            "texture_set": "ambientCG_Metal021",
            "dynamic_state_bindings": {"surcharge_overflow": "simulation.manhole_overflow_volume > 0"},
            "vfx": "Niagara_ManholeGeyser_Overflow"
        },
        {
            "dataset_source": "UrbanFloodBench",
            "feature_key": "cell_type=2d_water",
            "semantic_class": "FLOOD_INUNDATION_CELL",
            "geometry_generator": "DynamicWaterSurfaceMesh",
            "geometry_params": {"elevation_z": "world_state.terrain_elevation + world_state.water_depth"},
            "pbr_material": "M_Master_Water",
            "pbr_material_instance": "MI_Physical_WaterSurface",
            "texture_set": "WaterNormal_PBR",
            "dynamic_state_bindings": {"water_depth": "simulation.water_depth", "flow_dir": "simulation.flow_direction", "flow_speed": "simulation.flow_velocity"},
            "vfx": "Niagara_RaindropRipple_Emitter"
        },
        {
            "dataset_source": "NYSDEC_CSO",
            "feature_key": "facility_type=cso_outfall",
            "semantic_class": "CSO_OUTFALL",
            "geometry_generator": "OutfallHeadwallGenerator",
            "geometry_params": {"pipe_dia_m": 1.2, "apron_length_m": 3.0},
            "pbr_material": "M_Master_Sewer",
            "pbr_material_instance": "MI_Outfall_WeatheredConcrete",
            "texture_set": "PolyHaven_GranularConcrete",
            "dynamic_state_bindings": {"overflowing": "simulation.cso_discharge_active"},
            "vfx": "Niagara_TurbulentEffluentDischarge"
        }
    ]
}

# 4. Build assets/asset_registry.json
asset_registry = {
    "registry_version": "2.0.0",
    "description": "Authoritative registry of PBR materials, textures, geometry templates, and VFX assets",
    "materials": [
        {
            "material_id": "MAT_ROAD_ASPHALT_01",
            "master_material": "M_Master_Road",
            "instance_name": "MI_Road_Highway_Asphalt",
            "category": "transportation",
            "maps": {"base_color": "T_Asphalt_01_BC", "normal": "T_Asphalt_01_N", "roughness": "T_Asphalt_01_R", "ao": "T_Asphalt_01_AO"},
            "source": "ambientCG",
            "license": "CC0",
            "uv_scale": [0.25, 0.25]
        },
        {
            "material_id": "MAT_CONCRETE_FACADE_01",
            "master_material": "M_Master_Building",
            "instance_name": "MI_Building_ConcreteFacade",
            "category": "buildings",
            "maps": {"base_color": "T_Concrete_01_BC", "normal": "T_Concrete_01_N", "roughness": "T_Concrete_01_R", "ao": "T_Concrete_01_AO"},
            "source": "PolyHaven",
            "license": "CC0",
            "uv_scale": [0.5, 0.5]
        },
        {
            "material_id": "MAT_SEWER_PIPE_01",
            "master_material": "M_Master_Sewer",
            "instance_name": "MI_Sewer_ReinforcedConcrete",
            "category": "sewer",
            "maps": {"base_color": "T_SewerConc_BC", "normal": "T_SewerConc_N", "roughness": "T_SewerConc_R", "metallic": "T_SewerConc_M"},
            "source": "PolyHaven",
            "license": "CC0",
            "uv_scale": [1.0, 4.0]
        },
        {
            "material_id": "MAT_WATER_PHYSICAL_01",
            "master_material": "M_Master_Water",
            "instance_name": "MI_Physical_WaterSurface",
            "category": "water",
            "maps": {"normal_a": "T_WaterWave_Normal_A", "normal_b": "T_WaterWave_Normal_B", "roughness_foam": "T_WaterFoam_R"},
            "source": "Unreal_Water_System",
            "license": "Epic Content License",
            "dynamic_params": ["DepthAbsorption", "WaveSpeed", "RefractionIndex", "Turbidity"]
        },
        {
            "material_id": "MAT_CAST_IRON_01",
            "master_material": "M_Master_Metal",
            "instance_name": "MI_CastIron_ManholeCover",
            "category": "infrastructure",
            "maps": {"base_color": "T_CastIron_BC", "normal": "T_CastIron_N", "roughness": "T_CastIron_R", "metallic": "T_CastIron_M"},
            "source": "ambientCG",
            "license": "CC0",
            "uv_scale": [1.0, 1.0]
        }
    ],
    "vfx_emitters": [
        {
            "vfx_id": "VFX_RAIN_HEAVY_01",
            "system_name": "Niagara_HeavyPrecipitation",
            "category": "weather",
            "max_particles": 50000,
            "gpu_sim": True,
            "dynamic_bindings": ["world_state.rainfall_intensity"]
        },
        {
            "vfx_id": "VFX_SEWER_INTERNAL_FLOW_01",
            "system_name": "Niagara_InternalFluidFlow_Pulse",
            "category": "sewer",
            "max_particles": 8000,
            "gpu_sim": True,
            "dynamic_bindings": ["simulation.sewer_flow_velocity", "simulation.sewer_fill_ratio"]
        },
        {
            "vfx_id": "VFX_MANHOLE_OVERFLOW_01",
            "system_name": "Niagara_ManholeGeyser_Overflow",
            "category": "drainage",
            "max_particles": 12000,
            "gpu_sim": True,
            "dynamic_bindings": ["simulation.overflow_rate"]
        }
    ]
}

# Write files
(BASE_DIR / "supported_world_classes.json").write_text(json.dumps(supported_world_classes, indent=2), encoding="utf-8")
(BASE_DIR / "dataset_to_world_mapping.json").write_text(json.dumps(dataset_to_world_mapping, indent=2), encoding="utf-8")
(ASSETS_DIR / "asset_registry.json").write_text(json.dumps(asset_registry, indent=2), encoding="utf-8")

print(f"Generated:")
print(f"  - supported_world_classes.json ({len(supported_world_classes['domains'])} domains)")
print(f"  - dataset_to_world_mapping.json ({len(dataset_to_world_mapping['mappings'])} mappings)")
print(f"  - assets/asset_registry.json ({len(asset_registry['materials'])} materials, {len(asset_registry['vfx_emitters'])} VFX)")
