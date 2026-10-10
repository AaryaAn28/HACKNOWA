"""
Reality Sculptor ML -- 02_extract_and_prepare.py
=================================================
Extracts all zip archives into ml/datasets/raw/ and performs initial
data validation. Creates standardized directory structure.
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import zipfile
import shutil
import json
import time
from pathlib import Path

DOWNLOADS = Path(r"C:\Users\Aryan kumar\Downloads")
RAW_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\raw")

# Extraction map: source zip -> target directory name
EXTRACTIONS = [
    ("archive (2).zip",  "eurosat"),
    ("archive (3).zip",  "metr_la"),
    ("archive (4).zip",  "pems_bay"),
    ("archive (5).zip",  "nysdec_cso"),
    ("urban-flood-modelling.zip",  "urban_flood_bench"),
    ("GlobalMLBuildingFootprints-main.zip",  "ms_building_footprints"),
]

# Large archives - extract selectively or with progress
LARGE_EXTRACTIONS = [
    ("archive (1).zip",  "landslide4sense"),
    ("building-extraction-generalization-2024.zip",  "ieee_building_extraction"),
]


def extract_zip(zip_path, target_dir, max_files=None):
    """Extract zip archive to target directory with progress reporting."""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already extracted
    if target_dir.exists() and any(target_dir.iterdir()):
        existing = sum(1 for _ in target_dir.rglob("*") if _.is_file())
        if existing > 5:
            print(f"  Already extracted ({existing} files). Skipping.")
            return existing
    
    print(f"  Extracting to {target_dir.name}/...")
    start = time.time()
    extracted = 0
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            members = [m for m in zf.infolist() if not m.filename.startswith('__MACOSX')]
            total = len(members)
            if max_files:
                members = members[:max_files]
            
            for i, member in enumerate(members):
                if member.is_dir():
                    continue
                try:
                    zf.extract(member, target_dir)
                    extracted += 1
                except Exception as e:
                    pass
                
                if (i + 1) % 1000 == 0:
                    elapsed = time.time() - start
                    print(f"    Progress: {i+1}/{total} files ({elapsed:.0f}s)")
        
        elapsed = time.time() - start
        print(f"  Extracted {extracted} files in {elapsed:.1f}s")
        return extracted
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0


def extract_selective(zip_path, target_dir, extensions=None, max_per_ext=None):
    """Extract only specific file types from large archives."""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already extracted
    if target_dir.exists() and any(target_dir.iterdir()):
        existing = sum(1 for _ in target_dir.rglob("*") if _.is_file())
        if existing > 5:
            print(f"  Already extracted ({existing} files). Skipping.")
            return existing
    
    print(f"  Selective extraction to {target_dir.name}/...")
    start = time.time()
    extracted = 0
    ext_counts = {}
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            members = [m for m in zf.infolist() 
                      if not m.filename.startswith('__MACOSX') and not m.is_dir()]
            
            for member in members:
                ext = Path(member.filename).suffix.lower()
                
                if extensions and ext not in extensions:
                    continue
                
                if max_per_ext:
                    count = ext_counts.get(ext, 0)
                    if count >= max_per_ext:
                        continue
                    ext_counts[ext] = count + 1
                
                try:
                    zf.extract(member, target_dir)
                    extracted += 1
                except:
                    pass
                
                if extracted % 500 == 0 and extracted > 0:
                    print(f"    Extracted {extracted} files...")
        
        elapsed = time.time() - start
        print(f"  Extracted {extracted} files in {elapsed:.1f}s")
        return extracted
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0


def copy_notebook(src_name, target_dir, target_name=None):
    """Copy a notebook file to the raw datasets directory."""
    src = DOWNLOADS / src_name
    target_dir.mkdir(parents=True, exist_ok=True)
    dst = target_dir / (target_name or src_name)
    
    if dst.exists():
        print(f"  Already copied. Skipping.")
        return True
    
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  Copied {src_name} -> {dst.name}")
        return True
    else:
        print(f"  Source not found: {src}")
        return False


def main():
    print("=" * 80)
    print("REALITY SCULPTOR ML -- DATASET EXTRACTION & PREPARATION")
    print("=" * 80)
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    
    # 1. Extract smaller datasets (< 200MB compressed)
    print("\n--- Phase 1: Small/Medium Datasets ---")
    for zip_name, dir_name in EXTRACTIONS:
        zip_path = DOWNLOADS / zip_name
        target = RAW_DIR / dir_name
        print(f"\n[{dir_name}] {zip_name} ({zip_path.stat().st_size / 1024**2:.1f} MB)")
        
        if zip_path.exists():
            count = extract_zip(zip_path, target)
            results[dir_name] = count
        else:
            print(f"  NOT FOUND: {zip_path}")
            results[dir_name] = 0
    
    # 2. Extract large Landslide4Sense (2.9 GB HDF5 - extract all, needed for training)
    print("\n--- Phase 2: Landslide4Sense (2.9 GB) ---")
    l4s_zip = DOWNLOADS / "archive (1).zip"
    l4s_dir = RAW_DIR / "landslide4sense"
    if l4s_zip.exists():
        print(f"\n[landslide4sense] archive (1).zip ({l4s_zip.stat().st_size / 1024**3:.1f} GB)")
        count = extract_zip(l4s_zip, l4s_dir)
        results["landslide4sense"] = count
    
    # 3. Extract IEEE Building Extraction (1.2 GB - extract all)
    print("\n--- Phase 3: IEEE Building Extraction (1.2 GB) ---")
    bld_zip = DOWNLOADS / "building-extraction-generalization-2024.zip"
    bld_dir = RAW_DIR / "ieee_building_extraction"
    if bld_zip.exists():
        print(f"\n[ieee_building_extraction] ({bld_zip.stat().st_size / 1024**3:.1f} GB)")
        count = extract_zip(bld_zip, bld_dir)
        results["ieee_building_extraction"] = count
    
    # 4. Copy notebook
    print("\n--- Phase 4: Notebooks & Supplementary Files ---")
    floods_dir = RAW_DIR / "floods_india"
    print(f"\n[floods_india] floods-in-india-eda-ml-model.ipynb")
    copy_notebook("floods-in-india-eda-ml-model.ipynb", floods_dir)
    
    # Copy CSO PDF
    cso_pdf = DOWNLOADS / "NYSDEC_CombinedSewerOverflows_CSOs_DataFileLayout.pdf"
    if cso_pdf.exists():
        cso_dir = RAW_DIR / "nysdec_cso"
        cso_dir.mkdir(parents=True, exist_ok=True)
        dst = cso_dir / cso_pdf.name
        if not dst.exists():
            shutil.copy2(cso_pdf, dst)
            print(f"  Copied CSO PDF")
    
    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    for name, count in results.items():
        status = "OK" if count > 0 else "EMPTY/MISSING"
        print(f"  {name:<30} {count:>8} files  [{status}]")
    
    # Verify extraction
    print("\n--- Verification ---")
    for name in results:
        d = RAW_DIR / name
        if d.exists():
            total = sum(1 for _ in d.rglob("*") if _.is_file())
            size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / (1024**2)
            print(f"  {name:<30} {total:>8} files  {size_mb:>10.1f} MB")
    
    print("\nExtraction complete.")


if __name__ == "__main__":
    main()
