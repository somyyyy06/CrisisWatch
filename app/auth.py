# backend/auth.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
# from app import models, crud
import os

# ----------------------------
# Config
# ----------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ----------------------------
# Password helpers
# ----------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ----------------------------
# Token helpers
# ----------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except JWTError:
        return None

# ----------------------------
# Authenticate user
# ----------------------------
# def authenticate_user(db: Session, username: str, password: str):
#     user = crud.get_user_by_username(db, username)
#     if not user:
#         return None
#     if not verify_password(password, user.hashed_password):
#         return None
#     return user

# ----------------------------
# FastAPI dependency
# ----------------------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    db = SessionLocal()
    try:
        user = db.query(models.User).get(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    finally:
        db.close()
