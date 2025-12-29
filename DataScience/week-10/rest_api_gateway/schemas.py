from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# مدل برای metadata
class Metadata(BaseModel):
    key: str
    value: str

# مدل برای درخواست شروع جلسه
class SessionStartRequest(BaseModel):
    device_time: datetime
    session_metadata: Optional[List[Metadata]] = []  # تغییر نام از metadata به session_metadata

# مدل برای رکوردهای Telemetry
class TelemetryRecordRequest(BaseModel):
    seq: int
    type: str
    device_time: datetime
    data: Dict[str, Any]

# مدل برای درخواست ثبت رکوردهای Telemetry به صورت دسته‌ای
class TelemetryBatchRequest(BaseModel):
    session_id: str
    records: List[TelemetryRecordRequest]

# مدل برای درخواست Heartbeat دستگاه
class DeviceHeartbeatRequest(BaseModel):
    device_time: datetime
    battery_pct: int
    network: Dict[str, Any]
    storage_free_mb: int
    camera: Dict[str, Any]
