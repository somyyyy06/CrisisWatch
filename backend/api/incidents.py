import os
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from .. import database, models, schemas
from ..ml.inference import get_credibility_score
from ..auth import get_current_user
from ..ws import manager

router = APIRouter(prefix="/incidents", tags=["incidents"])

# backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only jpg/jpeg/png allowed.",
        )

    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    credibility = get_credibility_score(f"{title} {description}")
    relative_path = f"uploads/{filename}"

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
        await manager.broadcast(
            {
                "event": "new_incident",
                "data": {
                    "id": db_incident.id,
                    "title": db_incident.title,
                    "description": db_incident.description,
                    "disaster_type": db_incident.disaster_type,
                    "credibility_score": db_incident.credibility_score,
                    "lon": db_incident.lon,
                    "lat": db_incident.lat,
                    "photo_path": db_incident.photo_path,
                    "created_at": (
                        db_incident.created_at.isoformat()
                        if db_incident.created_at
                        else None
                    ),
                },
            }
        )
    except Exception as e:
        print("WebSocket broadcast failed:", e)

    return db_incident
