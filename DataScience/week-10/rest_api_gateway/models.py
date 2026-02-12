from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Used by API + generator
OIL_CHANGE_KM_THRESHOLD = 2000.0

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    device_id = Column(String, index=True)
    device_time = Column(DateTime, default=datetime.utcnow)
    session_metadata = Column(JSON)


class DeviceOdometer(Base):
    """Cumulative km per device – filled by Spark batch job from telemetry."""
    __tablename__ = "device_odometer"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    total_km = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

