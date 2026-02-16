from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Subscription
from app.auth import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class SubscriptionCreate(BaseModel):
    location_text: str
    incident_types: Optional[str] = None  # Can store JSON array as text
    lon: Optional[float] = None
    lat: Optional[float] = None
    radius_km: Optional[float] = 10.0


@router.post("/")
def create_subscription(
    payload: SubscriptionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        sub = Subscription(
            user_id=current_user.id,
            location_text=payload.location_text,
            lon=payload.lon,
            lat=payload.lat,
            radius_km=payload.radius_km or 10.0,
            incident_types=payload.incident_types,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)

        return {
            "id": sub.id,
            "location_text": payload.location_text,
            "lon": payload.lon,
            "lat": payload.lat,
            "radius_km": payload.radius_km,
            "incident_types": payload.incident_types,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating subscription: {str(e)}")


@router.get("/")
def list_subscriptions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Subscription).filter(Subscription.user_id == current_user.id).all()


@router.delete("/{sub_id}")
def delete_subscription(sub_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(
        Subscription.id == sub_id, Subscription.user_id == current_user.id
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(sub)
    db.commit()
    return {"status": "deleted"}