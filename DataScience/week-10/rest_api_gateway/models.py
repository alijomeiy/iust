from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    device_id = Column(String, index=True)
    device_time = Column(DateTime, default=datetime.utcnow)
    session_metadata = Column(JSON)

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


class DeviceEventConfig(Base):
    """Per-device event config - each device can have different events with different km thresholds"""
    __tablename__ = "device_event_config"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    event_name = Column(String)
    km_threshold = Column(Float)


class DeviceOdometer(Base):
    """Cumulative odometer per device"""
    __tablename__ = "device_odometer"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    total_km = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceMessage(Base):
    """Messages sent to devices when event threshold is reached"""
    __tablename__ = "device_messages"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    event_config_id = Column(Integer, index=True)
    event_name = Column(String)
    message = Column(JSON)
    km_at_trigger = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
