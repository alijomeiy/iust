from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Session as SessionModel, TelemetryRecord, DeviceHeartbeat
from schemas import SessionStartRequest, TelemetryBatchRequest, DeviceHeartbeatRequest  # وارد کردن مدل‌های Pydantic
import uuid
from datetime import datetime

app = FastAPI()

# تابعی برای ایجاد Session به دیتابیس
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/v1/sessions/start")
async def start_session(request: SessionStartRequest, db: Session = Depends(get_db)):
    # ایجاد شناسه جلسه
    session_id = str(uuid.uuid4())
    
    # تغییر نام از metadata به session_metadata
    db_session = SessionModel(session_id=session_id, device_time=request.device_time, session_metadata=request.session_metadata)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return {"session_id": session_id}

@app.post("/v1/sessions/end")
async def end_session(session_id: str, device_time: datetime, db: Session = Depends(get_db)):
    # جستجو برای session با session_id خاص
    db_session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # به روز رسانی یا انجام عملیات پایان جلسه
    db_session.device_time = device_time
    db.commit()
    
    return {"message": "Session ended successfully"}

@app.post("/v1/telemetry:batch")
async def telemetry_batch(request: TelemetryBatchRequest, db: Session = Depends(get_db)):
    # ذخیره تمام رکوردهای telemetry
    for record in request.records:
        db_record = TelemetryRecord(
            session_id=request.session_id,
            seq=record.seq,
            type=record.type,
            device_time=record.device_time,
            data=record.data
        )
        db.add(db_record)
    db.commit()

    return {"message": "Telemetry records added successfully"}

@app.post("/v1/device/heartbeat")
async def device_heartbeat(request: DeviceHeartbeatRequest, db: Session = Depends(get_db)):
    # ذخیره اطلاعات heartbeat
    db_heartbeat = DeviceHeartbeat(
        device_time=request.device_time,
        battery_pct=request.battery_pct,
        network=request.network,
        storage_free_mb=request.storage_free_mb,
        camera=request.camera
    )
    db.add(db_heartbeat)
    db.commit()

    return {"message": "Device heartbeat added successfully"}
