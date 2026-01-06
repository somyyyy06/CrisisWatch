from sqlalchemy.orm import Session
from sqlalchemy import func, text
from fastapi import HTTPException, status

from . import models, schemas
from .auth import get_password_hash
from .tasks import notify_user_email
from .ml.inference import get_credibility_score

# ----------------------------
# USER CRUD
# ----------------------------
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    db_user = models.User(
        username=user.username or user.email,
        email=user.email,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ----------------------------
# INCIDENT CRUD
# ----------------------------
def create_incident(db: Session, title: str, description: str, disaster_type: str, lon: float, lat: float):
    credibility_score = get_credibility_score(title, description)

    incident = models.Incident(
        title=title,
        description=description,
        disaster_type=disaster_type,
        credibility_score=credibility_score,
        lon=lon,
        lat=lat,
        location=func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    sql = """
    SELECT id, user_id, radius_km
    FROM subscriptions
    WHERE ST_DWithin(
        location,
        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
        radius_km * 1000
    )
    """
    rows = db.execute(text(sql), {"lon": lon, "lat": lat}).fetchall()
    for row in rows:
        notify_user_email.delay(row.user_id, incident.id)

    return incident
