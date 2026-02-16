import os
import sys
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app import models  # 👈 IMPORTANT (forces model registration)

print("Python:", sys.version)
print("PORT:", os.environ.get("PORT"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CrisisWatch API", version="1.0.0")

# ----------------------------
# CREATE TABLES
# ----------------------------
@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")

# ----------------------------
# CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# ROOT
# ----------------------------
@app.get("/")
def root():
    return {"status": "ok", "service": "CrisisWatch"}

# ----------------------------
# HEALTH
# ----------------------------
@app.get("/health")
def health(db: Session = Depends(get_db)):
    return {"status": "healthy", "db": "connected"}
