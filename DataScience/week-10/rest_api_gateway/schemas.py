from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Metadata(BaseModel):
    key: str
    value: str

class SessionStartRequest(BaseModel):
    device_time: datetime
    device_id: Optional[str] = None
    session_metadata: Optional[List[Metadata]] = Field(default=None, alias="metadata")

    model_config = {"populate_by_name": True}

class TelemetryRecordRequest(BaseModel):
    seq: int
    type: str
    device_time: datetime
    data: Dict[str, Any]

class TelemetryBatchRequest(BaseModel):
    session_id: str
    device_id: Optional[str] = None
    records: List[TelemetryRecordRequest]

class DeviceHeartbeatRequest(BaseModel):
    device_id: Optional[str] = None
    device_time: datetime
    battery_pct: int
    network: Dict[str, Any]
    storage_free_mb: int
    camera: Dict[str, Any]
