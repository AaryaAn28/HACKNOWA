"""
Upload Center for Reality Sculptor
Handles ingestion of various file formats and extracts initial metadata.
"""

import os
import csv
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try importing heavy geospatial libraries
try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    import fiona
    FIONA_AVAILABLE = True
except ImportError:
    FIONA_AVAILABLE = False

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class SourcePriority(Enum):
    CURRENT_SENSOR = 7
    RECENT_ENGINEERING = 6
    VERIFIED_SURVEY = 5
    OFFICIAL_GIS = 4
    HISTORICAL = 3
    MODEL_ESTIMATE = 2
    GENERIC_ASSUMPTION = 1

@dataclass
class UploadResult:
    file_path: str
    file_type: str
    mime_type: str
    classification: Any
    spatial_metadata: Dict[str, Any]
    georef_confidence: float
    conflicts: List[Dict[str, Any]]
    extracted_features: List[Any]


def detect_file_type(file_path: str) -> str:
    """Detect MIME type using python-magic or fallback to extension."""
    if MAGIC_AVAILABLE:
        try:
            return magic.from_file(file_path, mime=True)
        except Exception as e:
            logger.warning(f"Magic detection failed: {e}")
            
    # Fallback
    ext = os.path.splitext(file_path)[1].lower()
    ext_map = {
        '.tif': 'image/tiff', '.tiff': 'image/tiff',
        '.shp': 'application/x-esri-shape',
        '.geojson': 'application/geo+json',
        '.json': 'application/json',
        '.csv': 'text/csv',
        '.pdf': 'application/pdf',
        '.kml': 'application/vnd.google-earth.kml+xml',
        '.kmz': 'application/vnd.google-earth.kmz',
        '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'
    }
    return ext_map.get(ext, 'application/octet-stream')

def extract_geotiff_meta(file_path: str) -> Dict[str, Any]:
    if not RASTERIO_AVAILABLE:
        return {"error": "rasterio not available"}
    try:
        with rasterio.open(file_path) as src:
            return {
                "crs": src.crs.to_string() if src.crs else None,
                "bounds": list(src.bounds),
                "resolution": src.res,
                "band_count": src.count,
                "nodata": src.nodatavals
            }
    except Exception as e:
        return {"error": str(e)}

def extract_vector_meta(file_path: str) -> Dict[str, Any]:
    if not FIONA_AVAILABLE:
        return {"error": "fiona not available"}
    try:
        with fiona.open(file_path) as src:
            return {
                "crs": src.crs.get('init') if src.crs else None,
                "bounds": list(src.bounds),
                "feature_count": len(src),
                "schema": dict(src.schema.get('properties', {}))
            }
    except Exception as e:
        return {"error": str(e)}

def extract_csv_meta(file_path: str) -> Dict[str, Any]:
    meta = {"is_spatial": False, "headers": []}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            meta['delimiter'] = dialect.delimiter
            reader = csv.reader(f, dialect)
            headers = next(reader, [])
            meta['headers'] = headers
            
            spatial_cols = {'lat', 'lon', 'latitude', 'longitude', 'x', 'y'}
            lower_headers = [h.lower() for h in headers]
            if any(c in lower_headers for c in spatial_cols):
                meta['is_spatial'] = True
    except Exception as e:
        meta['error'] = str(e)
    return meta

def extract_kml_meta(file_path: str) -> Dict[str, Any]:
    meta = {"placemarks_count": 0, "geometries": set()}
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        # Very basic namespace handling
        for elem in root.iter():
            if 'Placemark' in elem.tag:
                meta['placemarks_count'] += 1
            if any(geom in elem.tag for geom in ['Point', 'LineString', 'Polygon']):
                meta['geometries'].add(elem.tag.split('}')[-1])
        meta['geometries'] = list(meta['geometries'])
    except Exception as e:
        meta['error'] = str(e)
    return meta

def compute_georef_confidence(spatial_meta: Dict[str, Any]) -> float:
    conf = 0.0
    if spatial_meta.get("crs"):
        conf += 0.4
        crs_str = str(spatial_meta.get("crs")).lower()
        if "epsg:" in crs_str:
            conf += 0.2
    if spatial_meta.get("bounds") and len(spatial_meta.get("bounds", [])) == 4:
        conf += 0.3
        # bounds_plausible check (basic)
        b = spatial_meta["bounds"]
        if b[0] != b[2] and b[1] != b[3]:
            conf += 0.1
    return min(conf, 1.0)

def conflict_detection(new_data: Dict[str, Any], existing_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Compare new data values against existing WorldState values
    conflicts = []
    # Dummy comparison logic
    for key, val in new_data.items():
        if key in existing_state:
            # Assuming numeric values for simplicity
            try:
                if abs(float(val) - float(existing_state[key])) > 10.0:  # threshold
                    conflicts.append({"key": key, "new": val, "old": existing_state[key]})
            except (ValueError, TypeError):
                pass
    return conflicts

def process_upload(file_path: str, existing_world_state: Optional[Dict[str, Any]] = None) -> UploadResult:
    mime_type = detect_file_type(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    spatial_metadata = {}
    if ext in ['.tif', '.tiff']:
        spatial_metadata = extract_geotiff_meta(file_path)
    elif ext in ['.shp', '.geojson']:
        spatial_metadata = extract_vector_meta(file_path)
    elif ext == '.csv':
        spatial_metadata = extract_csv_meta(file_path)
    elif ext in ['.kml', '.kmz']:
        spatial_metadata = extract_kml_meta(file_path)
        
    georef_confidence = compute_georef_confidence(spatial_metadata)
    
    conflicts = []
    if existing_world_state:
        # Dummy mock extracted dict for conflict detection
        conflicts = conflict_detection(spatial_metadata, existing_world_state)
        
    # Classification is handled by DocumentClassifier (external)
    classification = None 
    
    return UploadResult(
        file_path=file_path,
        file_type=ext,
        mime_type=mime_type,
        classification=classification,
        spatial_metadata=spatial_metadata,
        georef_confidence=georef_confidence,
        conflicts=conflicts,
        extracted_features=[]
    )
