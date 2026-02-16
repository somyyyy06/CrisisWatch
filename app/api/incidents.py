import os
import shutil
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import database, models, schemas
from app.auth import get_current_user
from app.ws import manager 

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Ensure uploads folder exists (absolute path for saving)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/submit")
async def submit_incident(
    title: str = Form(...),
    description: str = Form(...),
    incident_type: str = Form(...),
    location_text: str = Form(None),
    severity: str = Form("moderate"),
    lon: float = Form(...),
    lat: float = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    # Optional file upload (for future use)
    # if file:
    #     file_ext = os.path.splitext(file.filename)[1].lower()
    #     if file_ext not in [".jpg", ".jpeg", ".png"]:
    #         raise HTTPException(
    #             status_code=400, detail="Invalid file type. Only jpg/jpeg/png allowed."
    #         )

    # Save incident to DB with new schema
    db_incident = models.Incident(
        title=title,
        description=description,
        incident_type=incident_type,
        location_text=location_text,
        severity=severity,
        lon=lon,
        lat=lat,
        reported_by=current_user.id,
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    try:
        payload = {
            "event": "new_incident",
            "data": {
                "id": db_incident.id,
                "title": db_incident.title,
                "description": db_incident.description,
                "incident_type": db_incident.incident_type,
                "severity": db_incident.severity,
                "location_text": db_incident.location_text,
                "lon": db_incident.lon,
                "lat": db_incident.lat,
                "created_at": db_incident.created_at.isoformat() if db_incident.created_at else None,
            },
        }
        # manager.broadcast is async; await it
        await manager.broadcast(payload)
    except Exception as e:
        # Do not fail the request if broadcast fails; log to console
        print("WebSocket broadcast failed:", e)

    return db_incident


@router.get("/geojson")
def get_incidents_geojson(db: Session = Depends(database.get_db)):
    """
    Return all incidents as GeoJSON FeatureCollection for map display.
    """
    incidents = db.query(models.Incident).all()
    
    features = []
    for inc in incidents:
        if inc.lon is not None and inc.lat is not None:
            feature = {
                "type": "Feature",
                "properties": {
                    "id": inc.id,
                    "title": inc.title,
                    "description": inc.description,
                    "incident_type": inc.incident_type,
                    "severity": inc.severity,
                    "location_text": inc.location_text,
                    "created_at": inc.created_at.isoformat() if inc.created_at else None,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [inc.lon, inc.lat]
                }
            }
            features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }
