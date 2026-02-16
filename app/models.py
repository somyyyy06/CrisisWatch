from sqlalchemy import Column, Integer, String, Float, DateTime, func, Boolean, ForeignKey, Text
from app.database import Base


# ----------------------------
# Incident model
# ----------------------------
class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    incident_type = Column(String, nullable=True)  # Changed from disaster_type
    location_text = Column(String, nullable=True)
    lon = Column(Float, nullable=True)
    lat = Column(Float, nullable=True)
    severity = Column(String, nullable=True)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    location_text = Column(String, nullable=False)
    radius_km = Column(Float,nullable=False, server_default='10.0')
    lon = Column(Float, nullable=True)  # Renamed from location_lon
    lat = Column(Float, nullable=True)  # Renamed from location_lat
    incident_types = Column(Text, nullable=True)  # Changed from disaster_type - can store JSON array as text
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
