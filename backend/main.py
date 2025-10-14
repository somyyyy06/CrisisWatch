# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Request, status, WebSocket, WebSocketDisconnect, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordRequestForm
import json
import logging
import os
from datetime import datetime, timedelta
from sqlalchemy import func
from typing import Optional

# Import database and models
from backend import database, models, crud, schemas
from backend.api.feed import router as feed_router
from backend.ml.inference import get_credibility_score
from backend.api import subscriptions, incidents
from backend.api.usgs_ingestor import fetch_and_store
from backend.api.websocket_manager import manager
from backend.auth import get_password_hash, verify_password, create_access_token, decode_access_token, get_current_user
from backend.ws import manager as ws_manager  # ensure you have correct ws manager
from backend.auth import decode_access_token
from backend import database as _database 

# ✅ NEW IMPORT for summarization
from backend.ml.summarizer import generate_summary

# ---------------------------- #
# JWT + password utils
# ---------------------------- #
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key")  # put real secret in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ---------------------------- #
# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------- #
# FastAPI App
app = FastAPI(title="CrisisWatch API", version="1.0.0")

# ---------------------------- #
# Mount uploads as static (dev convenience)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# serve backend/uploads directory at /uploads
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

# ---------------------------- #
# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------- #
# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.include_router(feed_router)

# ---------------------------- #
# Auth Endpoints
@app.post("/auth/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user_in.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db, user_in)

@app.post("/auth/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

# ---------------------------- #
# Health Check
@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------- #
# Root
@app.get("/")
def root():
    return {"message": "CrisisWatch API running 🚀"}

# ---------------------------- #
# ✅ NEW: Summarization Endpoint
@app.post("/summarize")
async def summarize_text(payload: dict):
    """
    Accepts a long news text and returns a summarized version.
    Example request: {"text": "long news article ..."}
    """
    text = payload.get("text")
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        summary = generate_summary(text)
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating summary")

# ---------------------------- #
# CRUD: Incidents
@app.post("/incidents/", response_model=schemas.Incident)
async def create_incident(
    title: str = Form(...),
    description: str = Form(...),
    disaster_type: str = Form(...),
    lon: float = Form(...),
    lat: float = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_incident = crud.create_incident(
        db=db,
        title=title,
        description=description,
        disaster_type=disaster_type,
        lon=lon,
        lat=lat,
    )

    if file:
        save_dir = os.path.join("backend", "uploads")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file.filename)
        with open(save_path, "wb") as buffer:
            buffer.write(await file.read())

    severity = crud.severity_from_score(db_incident.credibility_score)
    counts = crud.get_severity_counts(db)

    from asyncio import create_task
    create_task(manager.broadcast({
        "type": "incident_created",
        "incident": {
            "id": db_incident.id,
            "title": db_incident.title,
            "description": db_incident.description,
            "disaster_type": db_incident.disaster_type,
            "credibility_score": db_incident.credibility_score,
            "lat": db_incident.lat,
            "lon": db_incident.lon,
            "severity": severity,
            "created_at": db_incident.created_at.isoformat() if db_incident.created_at else None
        },
        "counts": counts
    }))

    return db_incident

@app.get("/incidents/", response_model=list[schemas.Incident])
def read_incidents(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_incidents(db, skip=skip, limit=limit)

@app.get("/incidents/geojson")
def read_incidents_geojson(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    incidents = crud.get_incidents(db, skip=skip, limit=limit)
    features = []
    for inc in incidents:
        features.append({
            "type": "Feature",
            "properties": {
                "id": inc.id,
                "title": inc.title,
                "description": inc.description,
                "disaster_type": inc.disaster_type,
                "credibility_score": inc.credibility_score,
                "severity": crud.severity_from_score(inc.credibility_score),
                "created_at": inc.created_at.isoformat() if inc.created_at else None
            },
            "geometry": {"type": "Point", "coordinates": [inc.lon, inc.lat]}
        })
    return JSONResponse({"type": "FeatureCollection", "features": features})

@app.get("/incidents/nearby")
def read_incidents_nearby(
    lon: float,
    lat: float,
    radius_km: float = 10.0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    incidents = crud.get_incidents_nearby(db, lon=lon, lat=lat, radius_km=radius_km, limit=limit)
    features = []
    for inc in incidents:
        features.append({
            "type": "Feature",
            "properties": {
                "id": inc.id,
                "title": inc.title,
                "description": inc.description,
                "disaster_type": inc.disaster_type,
                "credibility_score": inc.credibility_score,
                "severity": crud.severity_from_score(inc.credibility_score),
                "created_at": inc.created_at.isoformat() if inc.created_at else None
            },
            "geometry": {"type": "Point", "coordinates": [inc.lon, inc.lat]}
        })
    return JSONResponse({"type": "FeatureCollection", "features": features})

# ---------------------------- #
# Routers
app.include_router(subscriptions.router)
app.include_router(incidents.router)

@app.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        auth = dict(websocket.headers).get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

    user = None
    if token:
        try:
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                user_id = int(payload["sub"])
                db = _database.SessionLocal()
                try:
                    user = db.query(models.User).get(user_id)
                finally:
                    db.close()
        except Exception:
            user = None

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/ingest/usgs")
async def ingest_usgs_data(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        result = await fetch_and_store(db)
        return {"message": "USGS data ingestion completed", "results": result}
    except Exception as e:
        logger.error(f"Error ingesting USGS data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ingesting data: {str(e)}")

# ---------------------------- #
# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = exc.body
    if isinstance(body, (bytes, bytearray)):
        try:
            body = body.decode("utf-8", errors="ignore")
        except Exception:
            body = str(body)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.get("/users/me", response_model=schemas.UserOut)
def read_user_me(current_user=Depends(get_current_user)):
    return current_user

@app.get("/metrics/summary")
def metrics_summary(db: Session = Depends(get_db)):
    try:
        now = datetime.utcnow()
        start_24h = now - timedelta(hours=24)

        active_incidents = (
            db.query(func.count(models.Incident.id))
            .filter(models.Incident.created_at >= start_24h)
            .scalar()
            or 0
        )

        total_incidents = db.query(func.count(models.Incident.id)).scalar() or 0

        ai_accuracy = float(os.getenv("AI_ACCURACY", "0.75"))
        avg_response_seconds = float(os.getenv("AVG_RESPONSE_SECONDS", "252"))
        response_time_text = f"{round(avg_response_seconds / 60, 1)}m"
        data_sources = int(os.getenv("DATA_SOURCES", "4"))

        return {
            "active_incidents": int(active_incidents),
            "total_incidents": int(total_incidents),
            "ai_accuracy": ai_accuracy,
            "response_time": response_time_text,
            "data_sources": data_sources,
        }
    except Exception as e:
        return {
            "active_incidents": 0,
            "total_incidents": 0,
            "ai_accuracy": float(os.getenv("AI_ACCURACY", "0.75")),
            "response_time": f"{round(float(os.getenv('AVG_RESPONSE_SECONDS','252'))/60,1)}m",
            "data_sources": int(os.getenv("DATA_SOURCES", "4")),
            "error": str(e),
        }
