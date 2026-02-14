from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
import os
import logging

# ✅ ABSOLUTE IMPORTS (CRITICAL)
from app import database, models, crud, schemas
from app.auth import verify_password, create_access_token
from app.api.feed import router as feed_router
from app.api import subscriptions, incidents
from app.api.websocket_manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CrisisWatch API", version="1.0.0")

# ----------------------------
# Static uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ----------------------------
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# DB Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# Routers
app.include_router(feed_router)
app.include_router(subscriptions.router)
app.include_router(incidents.router)

# ----------------------------
# Auth
@app.post("/auth/signup", response_model=schemas.UserOut, status_code=201)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.create_user(db, payload)
    return user

@app.post("/auth/token", response_model=schemas.Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

# ----------------------------
# Health
@app.get("/health")
def health():
    return {"status": "ok"}

# ----------------------------
# Metrics Summary
@app.get("/metrics/summary")
def get_metrics_summary(db: Session = Depends(get_db)):
    """
    Return dashboard metrics: incident counts by severity, totals, etc.
    """
    total = db.query(models.Incident).count()
    scraped_total = db.query(models.ScrapedIncident).count()
    
    # Count by credibility score ranges
    critical = db.query(models.Incident).filter(models.Incident.credibility_score >= 0.8).count()
    moderate = db.query(models.Incident).filter(
        models.Incident.credibility_score >= 0.5,
        models.Incident.credibility_score < 0.8
    ).count()
    resolved = db.query(models.Incident).filter(models.Incident.credibility_score < 0.5).count()
    
    return {
        "total_incidents": total,
        "active_incidents": critical + moderate,
        "critical": critical,
        "moderate": moderate,
        "resolved": resolved,
        "scraped_feed_count": scraped_total,
        "ai_accuracy": 0.75,
        "response_time": "2.4m",
        "data_sources": 5,
    }

# ----------------------------
# WebSocket
@app.websocket("/ws/incidents")
async def ws_incidents(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
