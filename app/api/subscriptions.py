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
    email: str
    disaster_type: str
    location_lat: float
    location_lon: float
    radius_km: Optional[float] = 5.0
    keywords: Optional[str] = ""


@router.post("/")
def create_subscription(
    payload: SubscriptionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        sub = Subscription(
            user_id=current_user.id,
            email=payload.email,
            disaster_type=payload.disaster_type,
            location_lat=payload.location_lat,
            location_lon=payload.location_lon,
            radius_km=payload.radius_km,
            keywords=payload.keywords,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)

        # ✅ Use text() for raw SQL
        db.execute(
            text(
                "UPDATE subscriptions "
                "SET location = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) "
                "WHERE id = :id"
            ),
            {"lon": payload.location_lon, "lat": payload.location_lat, "id": sub.id},
        )
        db.commit()

        return {
            "id": sub.id,
            "email": payload.email,
            "disaster_type": payload.disaster_type,
            "location_lat": payload.location_lat,
            "location_lon": payload.location_lon,
            "radius_km": payload.radius_km,
            "keywords": payload.keywords,
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