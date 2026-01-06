# backend/api/feed.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal
from sqlalchemy import desc

router = APIRouter(prefix="/feed", tags=["feed"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _severity_from_score(score: float):
    if score is None:
        return "unknown"
    if score >= 0.8:
        return "critical"
    if score >= 0.6:
        return "moderate"
    return "resolved"

@router.get("/live", response_model=list[schemas.ScrapedIncident])
def get_live_feed(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(models.ScrapedIncident).order_by(desc(models.ScrapedIncident.created_at)).limit(limit).all()
    # Add severity computed field before returning (but pydantic schema has fixed shape).
    # You can extend schema to include severity, but if you don't want to change DB, compute on the fly in response.
    result = []
    for r in rows:
        d = {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "incident_type": r.incident_type,
            "source_url": r.source_url,
            "location_text": r.location_text,
            "lon": r.lon,
            "lat": r.lat,
            "credibility_score": r.credibility_score,
            "summary": r.summary,
            "created_at": r.created_at,
            "severity": _severity_from_score(r.credibility_score),
        }
        result.append(d)
    return result
