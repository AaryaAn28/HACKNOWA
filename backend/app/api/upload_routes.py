from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

router = APIRouter(tags=["Upload"])

class ConflictResolutionRequest(BaseModel):
    conflict_id: str
    resolution_strategy: str
    selected_values: Dict[str, Any]

@router.post("/region")
async def upload_region(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "REGION"}

@router.post("/terrain")
async def upload_terrain(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "TERRAIN"}

@router.post("/drainage")
async def upload_drainage(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "DRAINAGE"}

@router.post("/sewer")
async def upload_sewer(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "SEWERAGE"}

@router.post("/roads")
async def upload_roads(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "ROADS_TRAFFIC"}

@router.post("/buildings")
async def upload_buildings(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "BUILDINGS"}

@router.post("/weather")
async def upload_weather(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "WEATHER"}

@router.post("/sensors")
async def upload_sensors(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "SENSORS"}

@router.post("/general")
async def upload_general(file: UploadFile = File(...)):
    return {"status": "accepted", "filename": file.filename, "category": "GENERAL"}

@router.post("/image-to-3d")
async def upload_image_to_3d(file: UploadFile = File(...)):
    """
    Perceives uploaded map/satellite/blueprint image, applies trained ML models,
    and returns a full 3D spatial twin with building, road, drainage, and risk predictions.
    """
    try:
        from app.services.image_to_3d import image_reconstructor
        content = await file.read()
        result = image_reconstructor.process_image(content, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image to 3D processing failed: {str(e)}")

@router.get("/status/{doc_id}")
async def get_upload_status(doc_id: str):
    return {"doc_id": doc_id, "status": "COMPLETED", "progress": 100}

@router.get("/conflicts")
async def list_conflicts():
    return {"conflicts": []}

@router.post("/resolve-conflict")
async def resolve_conflict(req: ConflictResolutionRequest):
    return {"status": "resolved", "conflict_id": req.conflict_id}
