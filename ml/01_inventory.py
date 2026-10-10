"""
Reality Sculptor ML -- 01_inventory.py
======================================
Dataset Forensics: Scans ALL downloaded datasets, identifies contents,
extracts schemas, computes statistics, and generates dataset_manifest.json.

EXCLUDES: chest_xray (medical, not geospatial), wildfire datasets.
"""

import sys
# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import sys
import json
import time
import zipfile
import hashlib
import struct
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

DOWNLOADS = Path(r"C:\Users\Aryan kumar\Downloads")
ML_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml")
REPORTS_DIR = ML_DIR / "reports"
DATASETS_DIR = ML_DIR / "datasets"
RAW_DIR = DATASETS_DIR / "raw"

# ── Dataset Map ──────────────────────────────────────────────────────────────
# Maps archive filenames to semantic dataset identifiers
DATASET_MAP = {
    "archive (1).zip": {
        "id": "landslide4sense",
        "name": "Landslide4Sense",
        "description": "Multi-sensor landslide detection (Sentinel-2, ALOS PALSAR, DEM). HDF5 images with 14 spectral/DEM bands.",
        "category": "landslide_detection",
        "use_for": ["landslide susceptibility", "terrain representation", "slope features", "remote sensing", "DEM features"]
    },
    "archive (2).zip": {
        "id": "eurosat",
        "name": "EuroSAT",
        "description": "Satellite land-use/land-cover classification dataset. 10 classes, 27,000 images from Sentinel-2.",
        "category": "land_cover_classification",
        "use_for": ["land-cover classification", "satellite representation learning", "urban/rural/vegetation/water context"]
    },
    "archive (3).zip": {
        "id": "metr_la",
        "name": "METR-LA Traffic",
        "description": "Los Angeles traffic speed sensors. 207 sensors, 4 months, 5-min intervals. Graph adjacency + time series.",
        "category": "traffic_forecasting",
        "use_for": ["traffic time-series", "traffic forecasting", "road-network temporal relationships", "graph-based traffic"]
    },
    "archive (4).zip": {
        "id": "pems_bay",
        "name": "PEMS-BAY Traffic",
        "description": "San Francisco Bay Area traffic sensors. 325 sensors, 6 months. Complementary traffic dataset.",
        "category": "traffic_forecasting",
        "use_for": ["traffic time-series", "traffic forecasting", "graph generalization testing"]
    },
    "archive (5).zip": {
        "id": "nysdec_cso",
        "name": "NYSDEC Combined Sewer Overflows",
        "description": "New York State combined sewer overflow events since 2013. CSV with location, duration, volume.",
        "category": "drainage_sewer",
        "use_for": ["supplementary sewer/drainage context", "overflow event patterns"]
    },
    "urban-flood-modelling.zip": {
        "id": "urban_flood_bench",
        "name": "UrbanFloodBench",
        "description": "1D/2D urban flood simulation network data. Nodes, edges, static/dynamic features, temporal flood propagation.",
        "category": "flood_simulation",
        "use_for": ["flood dynamics", "water levels", "surface flooding", "drainage interaction", "flood propagation"]
    },
    "building-extraction-generalization-2024.zip": {
        "id": "ieee_building_extraction",
        "name": "IEEE BigData Cup Building Extraction 2024",
        "description": "High-resolution satellite imagery for building extraction/segmentation. India-focused generalization challenge.",
        "category": "building_extraction",
        "use_for": ["building extraction", "satellite image understanding", "building segmentation"]
    },
    "GlobalMLBuildingFootprints-main.zip": {
        "id": "ms_building_footprints",
        "name": "Microsoft Global ML Building Footprints",
        "description": "Microsoft's worldwide ML-derived building footprints. Scripts/notebooks for accessing GeoJSON data.",
        "category": "building_footprints",
        "use_for": ["building detection", "building density", "urban morphology", "spatial building representation"]
    },
    "floods-in-india-eda-ml-model.ipynb": {
        "id": "floods_india",
        "name": "Floods in India EDA + ML Model",
        "description": "Jupyter notebook with India flood risk EDA and ML modeling. Contains embedded data references.",
        "category": "flood_risk",
        "use_for": ["supplementary flood/environmental information", "India-specific flood patterns"]
    }
}

# Datasets to EXCLUDE
EXCLUDED = {"archive.zip"}  # chest_xray — medical, not geospatial

def get_file_hash(filepath, block_size=65536):
    """Compute SHA-256 hash of a file (first 10MB for speed)."""
    sha = hashlib.sha256()
    max_bytes = 10 * 1024 * 1024
    read = 0
    try:
        with open(filepath, 'rb') as f:
            while read < max_bytes:
                data = f.read(block_size)
                if not data:
                    break
                sha.update(data)
                read += len(data)
    except:
        return "UNREADABLE"
    return sha.hexdigest()[:16]

def scan_zip_contents(zip_path):
    """Scan a zip file and return structured information about its contents."""
    info = {
        "total_files": 0,
        "total_size_bytes": 0,
        "total_size_mb": 0,
        "file_types": Counter(),
        "directories": set(),
        "sample_files": [],
        "min_file_size": float('inf'),
        "max_file_size": 0,
        "image_count": 0,
        "csv_count": 0,
        "h5_count": 0,
        "tif_count": 0,
        "parquet_count": 0,
        "json_count": 0,
        "pkl_count": 0,
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for zi in zf.infolist():
                if zi.is_dir():
                    info["directories"].add(zi.filename)
                    continue
                
                info["total_files"] += 1
                info["total_size_bytes"] += zi.file_size
                
                ext = Path(zi.filename).suffix.lower()
                info["file_types"][ext] += 1
                
                if zi.file_size < info["min_file_size"]:
                    info["min_file_size"] = zi.file_size
                if zi.file_size > info["max_file_size"]:
                    info["max_file_size"] = zi.file_size
                
                # Count by type
                if ext in ('.jpg', '.jpeg', '.png', '.bmp'):
                    info["image_count"] += 1
                elif ext == '.csv':
                    info["csv_count"] += 1
                elif ext in ('.h5', '.hdf5'):
                    info["h5_count"] += 1
                elif ext in ('.tif', '.tiff'):
                    info["tif_count"] += 1
                elif ext == '.parquet':
                    info["parquet_count"] += 1
                elif ext == '.json':
                    info["json_count"] += 1
                elif ext == '.pkl':
                    info["pkl_count"] += 1
                
                if len(info["sample_files"]) < 30:
                    info["sample_files"].append({
                        "name": zi.filename,
                        "size": zi.file_size,
                        "compressed": zi.compress_size
                    })
    except Exception as e:
        info["error"] = str(e)
    
    info["total_size_mb"] = round(info["total_size_bytes"] / (1024*1024), 2)
    info["file_types"] = dict(info["file_types"])
    info["directories"] = sorted(list(info["directories"]))[:20]
    if info["min_file_size"] == float('inf'):
        info["min_file_size"] = 0
    
    return info

def analyze_csv_from_zip(zip_path, csv_filename, max_rows=5000):
    """Extract and analyze a CSV file from within a zip archive."""
    import io
    analysis = {}
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            with zf.open(csv_filename) as f:
                # Read header and sample rows
                raw = f.read(2 * 1024 * 1024)  # First 2MB
                text = raw.decode('utf-8', errors='replace')
                lines = text.strip().split('\n')
                
                header = lines[0].strip()
                columns = [c.strip().strip('"') for c in header.split(',')]
                
                analysis["columns"] = columns
                analysis["num_columns"] = len(columns)
                analysis["sample_rows"] = min(len(lines) - 1, max_rows)
                analysis["header"] = header[:500]
                
                # Sample first few data rows
                data_rows = []
                for line in lines[1:6]:
                    data_rows.append(line.strip()[:300])
                analysis["sample_data"] = data_rows
                
    except Exception as e:
        analysis["error"] = str(e)
    
    return analysis

def main():
    print("=" * 80)
    print("REALITY SCULPTOR ML — DATASET FORENSICS ENGINE")
    print("=" * 80)
    print(f"Scan started: {datetime.now().isoformat()}")
    print(f"Downloads directory: {DOWNLOADS}")
    print()
    
    manifest = {
        "scan_timestamp": datetime.now().isoformat(),
        "scan_directory": str(DOWNLOADS),
        "total_datasets_found": 0,
        "total_size_gb": 0,
        "excluded_datasets": [],
        "datasets": {}
    }
    
    total_size = 0
    
    # ── Scan each known dataset ──────────────────────────────────────────────
    for filename, meta in DATASET_MAP.items():
        filepath = DOWNLOADS / filename
        dataset_id = meta["id"]
        
        print(f"┌─ Scanning: {meta['name']} ({filename})")
        
        entry = {
            "dataset_id": dataset_id,
            "name": meta["name"],
            "description": meta["description"],
            "category": meta["category"],
            "use_for": meta["use_for"],
            "source_file": filename,
            "source_path": str(filepath),
            "exists": filepath.exists(),
        }
        
        if not filepath.exists():
            entry["status"] = "NOT_FOUND"
            print(f"│  ⚠ File not found: {filepath}")
            print(f"└─ Status: NOT_FOUND")
        else:
            file_size = filepath.stat().st_size
            entry["file_size_bytes"] = file_size
            entry["file_size_mb"] = round(file_size / (1024*1024), 2)
            entry["file_hash_sha256_partial"] = get_file_hash(filepath)
            entry["last_modified"] = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
            total_size += file_size
            
            if filename.endswith('.zip'):
                print(f"│  Scanning zip contents...")
                contents = scan_zip_contents(filepath)
                entry["contents"] = contents
                
                # Analyze CSV files inside the zip
                csv_analyses = {}
                if contents.get("csv_count", 0) > 0:
                    try:
                        with zipfile.ZipFile(filepath, 'r') as zf:
                            csv_files = [n for n in zf.namelist() if n.endswith('.csv') and not n.startswith('__MACOSX')]
                            for csv_file in csv_files[:5]:  # Analyze up to 5 CSVs
                                print(f"│  Analyzing CSV: {csv_file}")
                                csv_analyses[csv_file] = analyze_csv_from_zip(filepath, csv_file)
                    except Exception as e:
                        csv_analyses["error"] = str(e)
                entry["csv_analyses"] = csv_analyses
                
                # Analyze parquet files if any
                if contents.get("parquet_count", 0) > 0:
                    entry["has_parquet"] = True
                
                entry["status"] = "SCANNED"
                print(f"│  Files: {contents['total_files']}, Size: {contents['total_size_mb']} MB")
                print(f"│  Types: {contents['file_types']}")
                
            elif filename.endswith('.ipynb'):
                entry["file_type"] = "jupyter_notebook"
                entry["status"] = "SCANNED"
                print(f"│  Notebook: {entry['file_size_mb']} MB")
            
            print(f"└─ Status: SCANNED ✓")
        
        manifest["datasets"][dataset_id] = entry
        print()
    
    # ── Scan for excluded datasets ───────────────────────────────────────────
    for excl in EXCLUDED:
        filepath = DOWNLOADS / excl
        if filepath.exists():
            manifest["excluded_datasets"].append({
                "file": excl,
                "reason": "Medical dataset (chest X-ray), not geospatial",
                "size_mb": round(filepath.stat().st_size / (1024*1024), 2)
            })
    
    # ── Summary ──────────────────────────────────────────────────────────────
    manifest["total_datasets_found"] = sum(1 for d in manifest["datasets"].values() if d.get("exists"))
    manifest["total_size_gb"] = round(total_size / (1024**3), 2)
    
    # ── Write manifest ───────────────────────────────────────────────────────
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = ML_DIR / "dataset_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"✓ Manifest written to: {manifest_path}")
    
    # ── Print summary table ──────────────────────────────────────────────────
    print("\n" + "=" * 100)
    print("DATASET INVENTORY SUMMARY")
    print("=" * 100)
    print(f"{'ID':<25} {'Name':<35} {'Size MB':>10} {'Files':>8} {'Status':<12}")
    print("-" * 100)
    for did, d in manifest["datasets"].items():
        name = d["name"][:34]
        size = d.get("file_size_mb", 0)
        nfiles = d.get("contents", {}).get("total_files", "N/A")
        status = d.get("status", "UNKNOWN")
        print(f"{did:<25} {name:<35} {size:>10} {str(nfiles):>8} {status:<12}")
    print("-" * 100)
    print(f"Total: {manifest['total_datasets_found']} datasets, {manifest['total_size_gb']} GB")
    print(f"Excluded: {len(manifest['excluded_datasets'])} datasets")
    
    # ── Print detailed CSV schemas ───────────────────────────────────────────
    print("\n" + "=" * 100)
    print("CSV SCHEMA DETAILS")
    print("=" * 100)
    for did, d in manifest["datasets"].items():
        if "csv_analyses" in d and d["csv_analyses"]:
            print(f"\n── {d['name']} ──")
            for csv_file, analysis in d["csv_analyses"].items():
                if isinstance(analysis, dict) and "columns" in analysis:
                    print(f"  File: {csv_file}")
                    print(f"  Columns ({analysis['num_columns']}): {', '.join(analysis['columns'][:20])}")
                    if analysis.get("sample_data"):
                        print(f"  Sample: {analysis['sample_data'][0][:200]}")
                    print()
    
    print("\n✓ Dataset forensics complete.")
    return manifest

if __name__ == "__main__":
    main()
