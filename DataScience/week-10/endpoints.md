## Authentication (in all headers)

**Header**
- `Authorization: Device <device_token>`

---
## `/v1/sessions/start` (POST)
### request    
- `device_time: time`
- `metadata: object`  
### response
- `session_id: string`

---

## `/v1/sessions/end` (POST)
### request
- `session_id: string`
- `device_time: time`

---

## `/v1/telemetry:batch` (POST)

### request
- `session_id: string`
- `device_id: string` (optional - required for distance calculation)
- `records: array<Record>`
    - `seq: int64`
    - `type: string (gps|obd|temp|event|audio_meta|...)`
    - `device_time: time`
    - `data: object`

---

## `/v1/device/heartbeat` (POST)

### request
- `device_time: time`
- `battery_pct: int32`
- `network: object`
- `storage_free_mb: int32`
- `camera: object`  

---

## `/v1/device/{device_id}/messages` (GET)

Devices poll this endpoint to fetch messages (e.g. when km event threshold is reached).

### query
- `unread_only: bool` (default: true)

### response
- `messages: array<{id, event_name, message, km_at_trigger, created_at}>`

---

## `/v1/device/{device_id}/messages/{message_id}/ack` (POST)

Mark message as read by device.

---

## Media Stuff (POST)


 todo!
---