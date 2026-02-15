# app/main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

from app import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CrisisWatch API", version="1.0.0")


# ----------------------------
# STARTUP (CRITICAL)
@app.on_event("startup")
def startup_event():
    database.init_db()
    logger.info("✅ Database initialized")


# ----------------------------
# DB Dependency (SAFE)
def get_db():
    if database.SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not ready")
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
# HEALTH CHECK (THIS BINDS THE PORT)
@app.get("/health")
def health():
    return {"status": "ok"}
