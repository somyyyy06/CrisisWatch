import requests
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import crud, models


USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
# You can change to "all_day.geojson" for more events.

def _exists_similar(db: Session, title: str, lon: float, lat: float):
    # Lightweight de-dup: same title & ~same coordinates
    return db.query(models.Incident).filter(
        models.Incident.incident_type == "Earthquake",
        models.Incident.title == title,
        func.abs(models.Incident.lon - lon) < 0.0001,
        func.abs(models.Incident.lat - lat) < 0.0001
    ).first() is not None

def fetch_and_store(db: Session, min_mag: float = 0.0):
    r = requests.get(USGS_URL, timeout=15)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features", [])
    inserted = 0

    for f in feats:
        geom = f.get("geometry") or {}
        props = f.get("properties") or {}
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            continue
        lon, lat = coords[0], coords[1]
        mag = props.get("mag")
        place = props.get("place") or "Earthquake"
        title = f"M{mag} - {place}" if mag is not None else place
        if mag is not None and mag < min_mag:
            continue
        if _exists_similar(db, title, lon, lat):
            continue

        crud.create_incident(
            db=db,
            title=title,
            description=props.get("url") or "USGS event",
            incident_type="Earthquake",
            lon=float(lon),
            lat=float(lat),
        )
        inserted += 1

    return {"source_count": len(feats), "inserted": inserted}
