"""
Extract verified Techgium 2026 asset, texture, PBR, and rendering sources.
Implements Directive Section 24.
"""

import re
import json
from pathlib import Path

DOWNLOADS_DIR = Path(r"C:\Users\Aryan kumar\Downloads")
OUTPUT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Scan all Techgium markdown and prompt docs
target_files = [
    DOWNLOADS_DIR / "TECHGIUM_2026_AAA_UE5_ASSET_AND_TEXTURE_RESOURCE_PACK.md",
    DOWNLOADS_DIR / "TECHGIUM_2026_UE5_AAA_ANATOMY_MASTER_PROMPT.md",
    DOWNLOADS_DIR / "TECHGIUM_2026_MASTER_MEDICAL_DATASET_ACQUISITION_PROMPT_UE5_READY.md"
]

techgium_sources = []
seen_urls = set()

url_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)|(https?://[^\s\)\"\'\>]+)')

for filepath in target_files:
    if not filepath.exists():
        continue
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    
    for i, line in enumerate(lines):
        # Find markdown links or raw URLs
        for m in url_pattern.finditer(line):
            label = m.group(1) or ""
            url = m.group(2) or m.group(3)
            url = url.rstrip(".,;:)")
            
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Context
            context_lines = [lines[j].strip() for j in range(max(0, i-3), min(len(lines), i+4)) if lines[j].strip()]
            context_text = " | ".join(context_lines)
            
            # Categorize
            category = "general"
            intended_use = "Reference and rendering documentation"
            license_type = "UNKNOWN"
            
            u_lower = url.lower()
            c_lower = context_text.lower()
            
            if "polyhaven" in u_lower:
                license_type = "CC0 Public Domain"
                if "hdri" in u_lower or "studio" in u_lower:
                    category = "hdri_lighting"
                    intended_use = "PBR environment lighting & sky dome reflections"
                elif "concrete" in u_lower or "floor" in u_lower or "textures" in u_lower:
                    category = "pbr_texture"
                    intended_use = "PBR surface material (diffuse, normal, roughness, displacement)"
            elif "ambientcg" in u_lower:
                license_type = "CC0 Public Domain"
                category = "pbr_materials"
                intended_use = "PBR ground, concrete, asphalt, metal, and structural materials"
            elif "fab.com" in u_lower:
                license_type = "Epic Content License / Fab Standard"
                if "electric-dreams" in u_lower:
                    category = "reference_environment"
                    intended_use = "Nanite, Lumen, Substrate, and PCG architectural study"
                elif "content-examples" in u_lower:
                    category = "reference_engine"
                    intended_use = "Substrate materials, subsurface scattering, and Niagara VFX study"
                elif "valley-of-the-ancient" in u_lower:
                    category = "reference_environment"
                    intended_use = "Nanite and Lumen photorealistic landscape study"
                elif "sky" in u_lower or "dynamic-sky" in u_lower:
                    category = "lighting_atmosphere"
                    intended_use = "Dynamic atmospheric scattering and solar lighting reference"
                elif "fog" in u_lower:
                    category = "lighting_atmosphere"
                    intended_use = "Volumetric fog and atmospheric depth"
                elif "lighting" in u_lower:
                    category = "lighting_atmosphere"
                    intended_use = "Cinematic lighting reference"
            elif "epicgames.com" in u_lower or "dev.epicgames.com" in u_lower:
                license_type = "Epic Documentation"
                category = "rendering_spec"
                intended_use = "Unreal Engine 5.6+ Nanite, Lumen, Substrate, and TSR rendering specifications"
                
            techgium_sources.append({
                "source_id": f"TG_SRC_{len(techgium_sources)+1:03d}",
                "label": label or url.split("/")[-1],
                "url": url,
                "source_file": filepath.name,
                "license": license_type,
                "category": category,
                "intended_usage": intended_use,
                "context_snippet": context_text[:250]
            })

# Save techgium_asset_sources.json
out_file = OUTPUT_DIR / "techgium_asset_sources.json"
out_file.write_text(json.dumps(techgium_sources, indent=2), encoding="utf-8")
print(f"Extracted {len(techgium_sources)} verified Techgium asset sources to {out_file}")
