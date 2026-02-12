## Authentication (in all headers)

**Header**
- `Authorization: Device <device_token>`

---
## `/v1/sessions/start` (POST)
### request
- `device_time: time`
- `device_id: string` (optional)
- `metadata` or `session_metadata: array<{key, value}>` (optional)

### response
- `session_id: string`

---

## `/v1/sessions/end` (POST)
### request (query)
- `session_id: string`
- `device_time: time`

### body (optional)
- `device_id: string`

---

## `/v1/telemetry:batch` (POST)

### request
- `session_id: string`
- `device_id: string` (optional – برای محاسبه کیلومتر لازم است)
- `records: array<Record>`
  - `seq: int64`
  - `type: string` (gps|obd|...)
  - `device_time: time`
  - `data: object`

---

## `/v1/device/heartbeat` (POST)

### request
- `device_id: string` (optional)
- `device_time: time`
- `battery_pct: int32`
- `network: object`
- `storage_free_mb: int32`
- `camera: object`

---

## `/v1/device/{device_id}/oil-change-due` (GET)

بر اساس کیلومتر تجمعی خودرو (از جاب اسپارک) برمی‌گرداند آیا باید روغن عوض شود (۲۰۰۰ کیلومتر).

### response
- `oil_change_due: boolean`

---

## Media Stuff (POST)

todo!
