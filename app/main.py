from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os, sys, logging

print("Python:", sys.version)
print("PORT:", os.environ.get("PORT"))

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
# DB Dependency (LAZY)
def get_db():
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# Routers (LAZY LOAD)
def include_routers(app: FastAPI):
    from app.api.feed import router as feed_router
    from app.api import subscriptions, incidents

    app.include_router(feed_router)
    app.include_router(subscriptions.router)
    app.include_router(incidents.router)

include_routers(app)

# ----------------------------
# Auth
@app.post("/auth/signup", status_code=201)
def signup(payload, db: Session = Depends(get_db)):
    from app import crud

    if crud.get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Username taken")

    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email exists")

    return crud.create_user(db, payload)

@app.post("/auth/token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from app import crud
    from app.auth import verify_password, create_access_token

    user = crud.get_user_by_username(db, form.username) or \
           crud.get_user_by_email(db, form.username)

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
# WebSocket
@app.websocket("/ws/incidents")
async def ws_incidents(websocket: WebSocket):
    from app.api.websocket_manager import manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
