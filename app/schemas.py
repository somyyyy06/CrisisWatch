from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


# ----------------------------
# Incident Schemas
# ----------------------------
class IncidentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    incident_type: Optional[str] = None
    location_text: Optional[str] = None
    lon: Optional[float] = Field(None, ge=-180.0, le=180.0)
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    severity: Optional[str] = None


class IncidentCreate(IncidentBase):
    pass


class Incident(IncidentBase):
    id: int
    reported_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----------------------------
# User Schemas
# ----------------------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=4)


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ----------------------------
# Scraped Incident Schemas (NEW)
# ----------------------------
class ScrapedIncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    incident_type: Optional[str] = None
    source_url: Optional[str] = None
    location_text: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    credibility_score: Optional[float] = None
    summary: Optional[str] = None

class ScrapedIncident(ScrapedIncidentBase):
    id: int
    created_at: Optional[datetime] = None
    severity: Optional[str] = None  # computed field

    class Config:
        from_attributes = True