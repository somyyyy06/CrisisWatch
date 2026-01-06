from sqlalchemy import Column, Integer, String, Float, DateTime, func, Boolean, ForeignKey, Text
from geoalchemy2 import Geography
from backend.database import Base


# ----------------------------
# Incident model
# ----------------------------
class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    disaster_type = Column(String, nullable=False)
    credibility_score = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    photo_path = Column(String, nullable=True)   # ✅ NEW FIELD
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ----------------------------
# User model (for auth)
# ----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)  # ✅ Added username
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ----------------------------
# Subscription model
# ----------------------------
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)
    disaster_type = Column(String, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    radius_km = Column(Float, nullable=True)
    keywords = Column(String, nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ----------------------------
# Scraped Incidents model (NEW)
# ----------------------------
class ScrapedIncident(Base):
    __tablename__ = "scraped_incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    incident_type = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    location_text = Column(String, nullable=True)  # e.g. "Delhi, India"
    lon = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    credibility_score = Column(Float, nullable=True, default=0.0)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
