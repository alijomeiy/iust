from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    device_time = Column(DateTime, default=datetime.utcnow)
    session_metadata = Column(JSON)  # تغییر نام از metadata به session_metadata

class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    seq = Column(Integer)
    type = Column(String)
    device_time = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON)

class DeviceHeartbeat(Base):
    __tablename__ = "device_heartbeats"
    id = Column(Integer, primary_key=True, index=True)
    device_time = Column(DateTime, default=datetime.utcnow)
    battery_pct = Column(Integer)
    network = Column(JSON)
    storage_free_mb = Column(Integer)
    camera = Column(JSON)
