import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)

endpoints = [
    # Static & Health
    ("GET", "/", None),
    ("GET", "/health", None),
    ("GET", "/frontend/index.html", None),
    ("GET", "/frontend/style.css", None),
    ("GET", "/frontend/app.js", None),

    # Core World
    ("GET", "/api/world/chennai_velachery", None),
    ("GET", "/api/world/chennai_velachery/digital-twin", None),

    # Simulation
    ("POST", "/api/simulation/flood", {
        "region_id": "chennai_velachery",
        "duration_minutes": 60,
        "rainfall_intensity_mm_hr": 75.0
    }),
    ("POST", "/api/simulation/heat", {
        "region_id": "chennai_velachery",
        "time_of_day_hour": 14.0,
        "solar_radiation_w_m2": 950.0
    }),
    ("POST", "/api/simulation/fire", {
        "region_id": "chennai_velachery",
        "wind_speed_kmh": 32.0,
        "wind_direction_deg": 225.0,
        "relative_humidity_pct": 18.0,
        "fuel_moisture_pct": 6.5
    }),
    ("POST", "/api/simulation/traffic", {
        "region_id": "chennai_velachery",
        "rush_hour_factor": 1.45,
        "incident_corridor": "CORRIDOR-R42"
    }),
    ("POST", "/api/simulation/cascade", {
        "region_id": "chennai_velachery"
    }),

    # Interventions
    ("GET", "/api/interventions/library", None),
    ("GET", "/api/interventions/plans/chennai_velachery", None),
    ("POST", "/api/interventions/optimize", {
        "region_id": "chennai_velachery",
        "target_metric": "water_depth",
        "target_reduction_pct": 45.0,
        "budget_limit_inr": 3000000
    }),
    ("POST", "/api/interventions/install", {
        "plan_id": "MF_PLAN_#01_PARETO_OPTIMAL",
        "actions": [
            {"action_id": "ACT_01", "type": "PIPE_UPSIZING", "target_node": "pipe_P44"}
        ]
    }),

    # Questions
    ("GET", "/api/questions/chennai_velachery", None),
    ("GET", "/api/questions/chennai_velachery/gaps", None),
    ("POST", "/api/questions/chennai_velachery/answer", {
        "question_id": "Q_TIDAL_OUTFALL_01",
        "selected_option": "Motorized backflow gate"
    }),
    ("POST", "/api/questions/translate-objective", {
        "natural_language_goal": "Stop flooding in Memorial Corridor"
    }),

    # Causal
    ("GET", "/api/causal/graph/chennai_velachery", None),
    ("POST", "/api/causal/counterfactual", {
        "region_id": "chennai_velachery",
        "interventions": {"pipe_capacity": 6.0}
    }),
    ("POST", "/api/causal/xray", {
        "region_id": "chennai_velachery",
        "symptom_node": "road_accessibility"
    }),
    ("GET", "/api/causal/failure-chain/road_accessibility", None),
    ("POST", "/api/causal/why", {
        "region_id": "chennai_velachery",
        "node_id": "flood_depth"
    }),
]

print("=" * 60)
print("TESTING ALL FASTAPI ENDPOINTS")
print("=" * 60)

passed = 0
failed = 0

for method, url, body in endpoints:
    try:
        if method == "GET":
            resp = client.get(url)
        else:
            resp = client.post(url, json=body)
            
        status = resp.status_code
        if status in (200, 201, 204):
            print(f" [PASS] {method:<5} {url:<45} -> {status}")
            passed += 1
        else:
            print(f"![FAIL] {method:<5} {url:<45} -> {status} : {resp.text[:120]}")
            failed += 1
    except Exception as e:
        print(f"![ERR ] {method:<5} {url:<45} -> Exception: {e}")
        failed += 1

print("=" * 60)
print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {len(endpoints)} total.")
print("=" * 60)
