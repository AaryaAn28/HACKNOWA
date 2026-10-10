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

# Add backend and ml to sys.path so all imports resolve seamlessly
current_dir = os.path.dirname(os.path.abspath(__file__))
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
