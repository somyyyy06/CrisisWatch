import os
import shutil
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import database, models, schemas
from app.ml.inference import get_credibility_score
from app.auth import get_current_user
from app.ws import manager 

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Ensure uploads folder exists (absolute path for saving)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/submit", response_model=schemas.Incident)
async def submit_incident(
    title: str = Form(...),
    description: str = Form(...),
    disaster_type: str = Form(...),
    lon: float = Form(...),
    lat: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user),
):
    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only jpg/jpeg/png allowed."
        )

    # Generate unique filename
    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"

    # Absolute save path
    save_path = os.path.join(UPLOAD_DIR, filename)

    # Save file to disk
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run AI credibility scoring
    credibility = get_credibility_score(f"{title} {description}")

    # Store relative path in DB (so frontend can use /uploads/{filename})
    relative_path = f"uploads/{filename}"

    # Save incident to DB
    db_incident = models.Incident(
        title=title,
        description=description,
        disaster_type=disaster_type,
        credibility_score=credibility,
        lon=lon,
        lat=lat,
        photo_path=relative_path,
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
                "disaster_type": db_incident.disaster_type,
                "credibility_score": db_incident.credibility_score,
                "lon": db_incident.lon,
                "lat": db_incident.lat,
                # send relative path so frontend can construct a URL if you mount /uploads
                "photo_path": db_incident.photo_path,
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
                    "disaster_type": inc.disaster_type,
                    "credibility_score": inc.credibility_score,
                    "photo_path": inc.photo_path,
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
