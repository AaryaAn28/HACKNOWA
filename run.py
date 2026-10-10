#!/usr/bin/env python3
"""
Reality Sculptor — Physical World Programming Server Runner
============================================================
Launches FastAPI backend serving the full Three.js 3D Cyber-Physical OS.
Designed for local execution and direct production deployment on Render.com.
"""

import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

current_dir = os.path.dirname(os.path.abspath(__file__))

# Auto-detect virtualenv site-packages if invoked outside activated venv
for venv_path in [
    os.path.join(current_dir, ".venv", "lib"),
    os.path.join(current_dir, "venv", "lib"),
    "/opt/render/project/src/.venv/lib"
]:
    if os.path.isdir(venv_path):
        for entry in os.listdir(venv_path):
            sp = os.path.join(venv_path, entry, "site-packages")
            if os.path.isdir(sp) and sp not in sys.path:
                sys.path.insert(0, sp)

# Add backend and ml to sys.path so all imports resolve seamlessly
backend_dir = os.path.join(current_dir, "backend")
ml_dir = os.path.join(current_dir, "ml")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if ml_dir not in sys.path:
    sys.path.insert(0, ml_dir)

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "false").lower() in ("true", "1", "yes")

    print(f"Starting Reality Sculptor Server on {host}:{port} (Render-Ready)...")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[backend_dir] if reload else None,
    )
