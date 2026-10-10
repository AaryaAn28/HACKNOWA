from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()

class SimulationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SpatialRegion(Base):
    """Represents a spatial region (e.g., a city block or a neighborhood)."""
    __tablename__ = 'spatial_region'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    geometry = Column(Geometry(geometry_type='POLYGON', srid=4326))
    bounds = Column(JSON)  # [min_x, min_y, max_x, max_y]
    crs = Column(String, default="EPSG:4326")
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class SpatialObject(Base):
    """A generic spatial object representing physical items in the region."""
    __tablename__ = 'spatial_object'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    object_type = Column(String, index=True)  # e.g., building, road
    geometry = Column(Geometry(geometry_type='GEOMETRY', srid=4326))
    attributes = Column(JSON)
    confidence = Column(Float)
    source = Column(String)
    dependencies = Column(JSON)


class DrainageNetwork(Base):
    """Drainage network topology."""
    __tablename__ = 'drainage_network'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    pipes = Column(JSON)
    nodes = Column(JSON)
    capacity = Column(Float)
    connectivity_graph = Column(JSON)


class SewerNetwork(Base):
    """Sewer infrastructure network."""
    __tablename__ = 'sewer_network'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    pipes = Column(JSON)
    manholes = Column(JSON)
    pumps = Column(JSON)
    capacity = Column(Float)
    condition = Column(String)


class RoadNetwork(Base):
    """Road infrastructure and emergency corridors."""
    __tablename__ = 'road_network'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    segments = Column(JSON)
    intersections = Column(JSON)
    lanes = Column(JSON)
    emergency_corridors = Column(JSON)


class Building(Base):
    """Buildings within a spatial region."""
    __tablename__ = 'building'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    footprint = Column(Geometry(geometry_type='POLYGON', srid=4326))
    height = Column(Float)
    floors = Column(Integer)
    material = Column(String)


class WaterBody(Base):
    """Water bodies like rivers or lakes."""
    __tablename__ = 'water_body'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    body_type = Column(String)
    geometry = Column(Geometry(geometry_type='POLYGON', srid=4326))
    elevation = Column(Float)
    seasonal_behavior = Column(JSON)


class Vegetation(Base):
    """Vegetation coverage."""
    __tablename__ = 'vegetation'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    veg_type = Column(String)
    canopy = Column(Geometry(geometry_type='POLYGON', srid=4326))
    growth_state = Column(String)
    shade_potential = Column(Float)


class SimulationRun(Base):
    """Execution context for a simulation."""
    __tablename__ = 'simulation_run'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    parameters = Column(JSON)
    state_version = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(SimulationStatus))


class SimulationState(Base):
    """Time-series state snapshots of a running simulation."""
    __tablename__ = 'simulation_state'
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey('simulation_run.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    snapshot = Column(JSON)


class InterventionPlan(Base):
    """A proposed set of interventions for a region."""
    __tablename__ = 'intervention_plan'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    actions = Column(JSON)
    cost = Column(Float)
    robustness = Column(Float)
    consequences = Column(JSON)
    status = Column(String)


class Intervention(Base):
    """A single intervention type definition."""
    __tablename__ = 'intervention'
    id = Column(Integer, primary_key=True, index=True)
    intervention_type = Column(String)
    params = Column(JSON)
    requirements = Column(JSON)
    cost_model = Column(JSON)
    time_model = Column(JSON)


class CausalGraph(Base):
    """Causal relationship graph."""
    __tablename__ = 'causal_graph'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    nodes = Column(JSON)
    edges = Column(JSON)
    version = Column(String)


class SensorReading(Base):
    """Sensor readings from physical locations."""
    __tablename__ = 'sensor_reading'
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    sensor_type = Column(String)
    value = Column(Float)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)


class UploadedDocument(Base):
    """Documents uploaded to augment models."""
    __tablename__ = 'uploaded_document'
    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(String)
    filename = Column(String)
    classification = Column(String)
    georef_confidence = Column(Float)
    extracted_features = Column(JSON)


class ModelRegistry(Base):
    """Registered machine learning models."""
    __tablename__ = 'model_registry'
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, index=True)
    version = Column(String)
    dataset = Column(String)
    features = Column(JSON)
    hyperparams = Column(JSON)
    metrics = Column(JSON)
    artifact_path = Column(String)


class AuditLog(Base):
    """Audit logs for actions."""
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    user_id = Column(String)
    data = Column(JSON)
    model_version = Column(String)
    sim_version = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class DataGap(Base):
    """Identified data gaps in the region state."""
    __tablename__ = 'data_gap'
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('spatial_region.id'))
    variable = Column(String)
    importance = Column(Float)
    confidence_impact = Column(Float)
