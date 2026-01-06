import requests
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import crud, models

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"


def _exists_similar(db: Session, title: str, lon: float, lat: float) -> bool:
    return (
        db.query(models.Incident)
        .filter(
            models.Incident.disaster_type == "Earthquake",
            models.Incident.title == title,
            func.abs(models.Incident.lon - lon) < 0.0001,
            func.abs(models.Incident.lat - lat) < 0.0001,
        )
        .first()
        is not None
    )


def fetch_and_store(db: Session, min_mag: float = 0.0):
    response = requests.get(USGS_URL, timeout=15)
    response.raise_for_status()

    data = response.json()
    features = data.get("features", [])
    inserted = 0

    for feature in features:
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        coords = geometry.get("coordinates") or []

        if len(coords) < 2:
            continue

        lon, lat = float(coords[0]), float(coords[1])
        mag = properties.get("mag")
        place = properties.get("place") or "Earthquake"

        title = f"M{mag} - {place}" if mag is not None else place

        if mag is not None and mag < min_mag:
            continue

        if _exists_similar(db, title, lon, lat):
            continue

        credibility = (
            0.95
            if mag is None
            else max(0.6, min(0.99, 0.6 + (float(mag) / 10)))
        )

        crud.create_incident(
            db=db,
            title=title,
            description=properties.get("url") or "USGS event",
            disaster_type="Earthquake",
            credibility_score=credibility,
            lon=lon,
            lat=lat,
        )

        inserted += 1

    return {"source_count": len(features), "inserted": inserted}
