# backend/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime
from fastapi import HTTPException, status

from app import models, schemas
from app.auth import get_password_hash
from app.ml.inference import get_credibility_score

# ----------------------------
# USER CRUD
# ----------------------------
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Email check is now done in the endpoint, so just create the user
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username or user.email,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ----------------------------
# Severity helpers
# ----------------------------
def severity_from_score(score: float | None) -> str:
    """
    Map credibility_score (0..1) to severity buckets.
    Thresholds:
      - critical: score >= 0.80
      - moderate: 0.50 <= score < 0.80
      - resolved: score < 0.50
    Rationale: higher credibility -> more critical to act on. 'resolved' used
    as low-cred bucket per your UI naming (if you want a real resolved flag,
    add a DB column later).
    """
    if score is None:
        return "moderate"
    try:
        s = float(score)
    except Exception:
        return "moderate"
    if s >= 0.80:
        return "critical"
    if s >= 0.50:
        return "moderate"
    return "resolved"

def get_severity_counts(db: Session):
    """
    Return aggregated counts for each severity bucket and total incidents.
    """
    critical_count = db.query(func.count(models.Incident.id)).filter(
        models.Incident.credibility_score >= 0.80
    ).scalar() or 0

    moderate_count = db.query(func.count(models.Incident.id)).filter(
        models.Incident.credibility_score >= 0.50,
        models.Incident.credibility_score < 0.80
    ).scalar() or 0

    resolved_count = db.query(func.count(models.Incident.id)).filter(
        models.Incident.credibility_score < 0.50
    ).scalar() or 0

    total = db.query(func.count(models.Incident.id)).scalar() or 0

    return {
        "critical": int(critical_count),
        "moderate": int(moderate_count),
        "resolved": int(resolved_count),
        "total": int(total),
    }

# ----------------------------
# INCIDENT CRUD
# ----------------------------
def create_incident(db: Session, title: str, description: str, incident_type: str, lon: float, lat: float):
    from app.tasks import notify_user_email

    credibility_score = get_credibility_score(title, description)

    db_incident = models.Incident(
        title=title,
        description=description,
        incident_type=incident_type,
        lon=lon,
        lat=lat
    )

    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # Notify subscribers (simplified - check all subscriptions with basic distance)
    # For production, consider using PostGIS or a proper geospatial index
    # This is a simplified version without PostGIS
    subscriptions = db.query(models.Subscription).all()
    for sub in subscriptions:
        if sub.lon and sub.lat and sub.radius_km:
            # Simple distance check (rough approximation)
            # For accurate distance, use haversine formula in production
            dist_km = ((sub.lon - lon)**2 + (sub.lat - lat)**2)**0.5 * 111  # ~111km per degree
            if dist_km <= sub.radius_km:
                notify_user_email.delay(sub.user_id, db_incident.id)

    return db_incident

def get_incidents(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Incident).offset(skip).limit(limit).all()

def get_incidents_nearby(db: Session, lon: float, lat: float, radius_km: float = 5.0, limit: int = 50):
    # Simplified version without PostGIS - fetches all and filters in Python
    # For production with many incidents, use PostGIS or spatial index
    all_incidents = db.query(models.Incident).filter(
        models.Incident.lon.isnot(None),
        models.Incident.lat.isnot(None)
    ).all()
    
    # Filter by distance (rough approximation)
    nearby = []
    for inc in all_incidents:
        dist_km = ((inc.lon - lon)**2 + (inc.lat - lat)**2)**0.5 * 111  # ~111km per degree
        if dist_km <= radius_km:
            nearby.append((dist_km, inc))
    
    # Sort by distance and limit
    nearby.sort(key=lambda x: x[0])
    return [inc for _, inc in nearby[:limit]]
