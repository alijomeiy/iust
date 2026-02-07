import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from config import QUEUE_HEARTBEAT, QUEUE_SESSION_EVENTS, QUEUE_TELEMETRY
from deps import get_db
from models import Session as SessionModel, DeviceMessage, DeviceEventConfig
from rabbitmq import publisher
from schemas import (
    DeviceEventConfigCreate,
    DeviceHeartbeatRequest,
    SessionStartRequest,
    TelemetryBatchRequest,
)

app = FastAPI()


def _extract_device_id(request: SessionStartRequest) -> str | None:
    if request.device_id:
        return request.device_id
    if request.session_metadata:
        for m in request.session_metadata:
            if m.key == "device_id":
                return m.value
    return None


@app.on_event("startup")
async def startup() -> None:
    await publisher.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    await publisher.close()


@app.post("/v1/sessions/start")
async def start_session(request: SessionStartRequest, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    device_id = _extract_device_id(request)

    db_session = SessionModel(
        session_id=session_id,
        device_id=device_id,
        device_time=request.device_time,
        session_metadata=request.session_metadata,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    await publisher.publish_json(
        QUEUE_SESSION_EVENTS,
        {
            "event": "session_started",
            "session_id": session_id,
            "device_id": device_id,
            "device_time": request.device_time,
            "session_metadata": request.session_metadata,
        },
    )

    return {"session_id": session_id}


@app.post("/v1/sessions/end")
async def end_session(
    session_id: str, device_time: datetime, db: Session = Depends(get_db)
):
    db_session = (
        db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    db_session.device_time = device_time
    db.commit()

    await publisher.publish_json(
        QUEUE_SESSION_EVENTS,
        {
            "event": "session_ended",
            "session_id": session_id,
            "device_time": device_time,
        },
    )

    return {"message": "Session ended successfully"}


@app.post("/v1/telemetry:batch")
async def telemetry_batch(request: TelemetryBatchRequest):
    await publisher.publish_json(QUEUE_TELEMETRY, request.model_dump())
    return {"message": "Telemetry batch queued"}


@app.post("/v1/device/heartbeat")
async def device_heartbeat(request: DeviceHeartbeatRequest):
    await publisher.publish_json(QUEUE_HEARTBEAT, request.model_dump())
    return {"message": "Heartbeat queued"}


@app.post("/v1/device/events/config")
async def create_event_config(
    request: DeviceEventConfigCreate, db: Session = Depends(get_db)
):
    """Create event config for a device - each device can have multiple events with different km thresholds"""
    cfg = DeviceEventConfig(
        device_id=request.device_id,
        event_name=request.event_name,
        km_threshold=request.km_threshold,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return {"id": cfg.id, "device_id": cfg.device_id, "event_name": cfg.event_name, "km_threshold": cfg.km_threshold}


@app.get("/v1/device/{device_id}/messages")
async def get_device_messages(
    device_id: str, unread_only: bool = True, db: Session = Depends(get_db)
):
    q = db.query(DeviceMessage).filter(DeviceMessage.device_id == device_id)
    if unread_only:
        q = q.filter(DeviceMessage.read_at.is_(None))
    msgs = q.order_by(DeviceMessage.created_at.desc()).limit(50).all()
    return {
        "messages": [
            {
                "id": m.id,
                "event_name": m.event_name,
                "message": m.message,
                "km_at_trigger": m.km_at_trigger,
                "created_at": m.created_at,
            }
            for m in msgs
        ]
    }


@app.post("/v1/device/{device_id}/messages/{message_id}/ack")
async def ack_message(
    device_id: str, message_id: int, db: Session = Depends(get_db)
):
    msg = (
        db.query(DeviceMessage)
        .filter(DeviceMessage.id == message_id, DeviceMessage.device_id == device_id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.read_at = datetime.utcnow()
    db.commit()
    return {"ok": True}
