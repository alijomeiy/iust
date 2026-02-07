from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Metadata(BaseModel):
    key: str
    value: str

class SessionStartRequest(BaseModel):
    device_time: datetime
    device_id: Optional[str] = None  # machine id (can also be extracted from metadata)
    session_metadata: Optional[List[Metadata]] = []

class TelemetryRecordRequest(BaseModel):
    seq: int
    type: str
    device_time: datetime
    data: Dict[str, Any]

class TelemetryBatchRequest(BaseModel):
    session_id: str
    device_id: Optional[str] = None  # required for distance calculation
    records: List[TelemetryRecordRequest]

class DeviceEventConfigCreate(BaseModel):
    device_id: str
    event_name: str
    km_threshold: float


class DeviceHeartbeatRequest(BaseModel):
    device_time: datetime
    battery_pct: int
    network: Dict[str, Any]
    storage_free_mb: int
    camera: Dict[str, Any]
