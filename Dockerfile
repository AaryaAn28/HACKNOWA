# ============================================================
# Reality Sculptor — Production Container for Render.com
# ============================================================
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    DEMO_MODE=true

WORKDIR /app

# Install minimal OS dependencies for LightGBM (libgomp1) and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source directories
COPY backend /app/backend
COPY frontend /app/frontend
COPY regions /app/regions
COPY assets /app/assets
COPY supported_world_classes.json /app/supported_world_classes.json
COPY dataset_to_world_mapping.json /app/dataset_to_world_mapping.json
COPY run.py /app/run.py

# Copy ML models and inference package (datasets and checkpoints are excluded via .dockerignore)
COPY ml/inference /app/ml/inference
COPY ml/models /app/ml/models
COPY ml/registry /app/ml/registry

# Render dynamically sets $PORT at runtime
EXPOSE 8080

# Health check matching Render's health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Launch production server via run.py which dynamically binds to $PORT
CMD ["sh", "-c", "python run.py"]
