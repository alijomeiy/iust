import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from config import QUEUE_HEARTBEAT, QUEUE_SESSION_EVENTS, QUEUE_TELEMETRY
from deps import get_db
from models import Session as SessionModel
from rabbitmq import publisher
from schemas import DeviceHeartbeatRequest, SessionStartRequest, TelemetryBatchRequest

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    await publisher.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    await publisher.close()


@app.post("/v1/sessions/start")
async def start_session(request: SessionStartRequest, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())

    # MVP: session را همین‌جا در DB می‌نویسیم چون باید فوری session_id برگردد
    db_session = SessionModel(
        session_id=session_id,
        device_time=request.device_time,
        session_metadata=request.session_metadata,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    # Event اختیاری
    await publisher.publish_json(
        QUEUE_SESSION_EVENTS,
        {
            "event": "session_started",
            "session_id": session_id,
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
