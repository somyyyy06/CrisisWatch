from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import os, sys

print("Python version:", sys.version)
print("PORT:", os.environ.get("PORT"))

app = FastAPI(title="CrisisWatch API")

def get_db():
    from app.database import SessionLocal  # LAZY IMPORT
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    return {"db": "connected"}
