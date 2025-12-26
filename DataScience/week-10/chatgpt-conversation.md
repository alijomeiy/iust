
# صورت مسئله
من یه دستگاه دارم که می‌خوام باهاش اطلاعاتی که تو پورت اودیبی ماشین هست و اطلاعات دیگه (یعنی جی‌پی‌اس، فیلم‌های ضبط شده دوربین که به خود دستگاه وصل هست، اطلاعات مربوط به دما، اطلاعات صدای ضبط شده که از بلندگوی دستگاه ضبط شده) رو به یه سروری بفرستم که تجمیع بشه و بتونم روش پردازش انجام بدم، فکر می‌کنم باید یه اندپوینت رستی داشته باشم، برام طرح این اندپوینتی که باید داشته باشم رو بده

موضوع زمان و تایم سرور هم وجود داره، آیا سشن‌ها هم به نظرت نکته‌ای داره؟ خوبه که سشن‌ها این طرف هندل بشه یا سمت سرور باشه!؟

این که چه ای پی آی‌هایی باید داشته باشه و ریکوئست و ریسپانس‌ها چطور باشه رو برام تشریح کن، در آخر هم یه فهرست دقیق از ورودی‌ها و خروجی‌های هر کدوم بده،‌ یه چیز شبه سوگر، یعنی می‌خوام به یکی دیگه بدم و بهش بگم مثلا این‌طوری می‌تونی ازش استفاده کنی، حالا البته فرمش مهم نیست مثلا از هر کدوم یک مثال هم بزنی خوبه، راه دیگه خیلی سریعی هم که به چیزی مثلا نرم‌افزاری نیاز نداشته باشه به نظرم خوبه

ویدئو و صدا رو کم‌تر ایده دارم که چطوری باید بفرستم، یکمی در مورد این بخش بیش‌تر توضیح بده؟ مثلا باید از استریم معکوس استفاده کنم؟

البته می‌دونم که تو آی او تی از ام کیو تی تی معمولا استفاده می‌شه اما نکته اینه که چون یه ام وی پی طوری می‌خوام بیارم بالا حدسم اینه که رست سریع‌تر خواهد بود



# پاسخ
باشه—بیاییم یک طرح «MVP ولی درست‌حسابی» برای API سمت سرور بچینیم که دستگاهت بتونه داده‌های OBD، GPS، دما، لاگ‌ها، و همچنین ویدئو/صدا رو ارسال کنه، سمت سرور تجمیع بشه و بعداً پردازش/آنالیتیکس روش انجام بدی.

من اینو طوری می‌نویسم که بشه به یک نفر دیگه داد و بگه «طبق همین استفاده کن» (شبه‌Swagger)، با مثال درخواست/پاسخ. آخرش هم یک فهرست دقیق ورودی/خروجی می‌ذارم.

---

## 1) معماری پیشنهادی MVP (REST-first)

### اصل‌ها
- **داده‌های سنسوری/OBD/GPS**: JSON به صورت batch (چند رکورد در یک درخواست) که هم سریع‌تره هم کم‌هزینه‌تر.
- **ویدئو و صدا**: جدا از JSON. یا:
    
    1. **آپلود فایل/تکه‌ای (Chunked Upload)** روی REST (پیشنهادی برای MVP)
        
    2. **استریم زنده** (بعداً، با WebRTC/RTSP/…)، نه برای MVP مگر واقعاً لازم باشه.
        

### چرا chunked upload؟

- شبکه موبایل قطع و وصل دارد.
    
- فایل‌های بزرگ را می‌شود از وسط ادامه داد.
    
- ساده‌تر از “reverse streaming” و قابل پیاده‌سازی با REST.
    

---

## 2) زمان و “تایم سرور” و سینک‌کردن

مشکل اصلی: ساعت دستگاه‌ها دقیق نیست، و شبکه هم latency دارد.

### راه MVP و کاربردی

- دستگاه **هر رکورد** را با دو زمان بفرستد:
    
    - `device_time_ms` (ساعت خود دستگاه)
        
    - `monotonic_ms` (زمان یکنواخت از لحظه روشن شدن دستگاه/اپ—برای ترتیب داخلی)
        
- سرور هم هنگام دریافت، `server_received_ms` ثبت می‌کند.
    
- دستگاه گه‌گاه endpoint سینک زمان را می‌زند و **offset** می‌گیرد:
    
    - `offset_ms = server_time - device_time`
        
- در پردازش، برای timeline دقیق‌تر از `device_time + offset` استفاده می‌کنی، ولی همیشه `server_received` را هم نگه می‌داری.
    

> نکته‌ی طلایی: برای جلوگیری از بهم‌ریختگی ترتیب، روی هر پیام یک `seq` افزایشی بگذار.

---

## 3) سشن‌ها (Session/Trip): سمت دستگاه یا سمت سرور؟

### پیشنهاد عملی

- **سشن را “مالکیتش” سمت دستگاه باشد، “اعتبارسنجی و بستن” سمت سرور.**
    
- یعنی دستگاه می‌گوید “من الان Trip شماره X را شروع کردم” و همه داده‌ها را با `session_id` می‌فرستد.
    
- سرور هم:
    
    - session را ایجاد/ثبت می‌کند
        
    - اگر دستگاه session نفرستاد، سرور می‌تواند با قوانین خودش auto-session بسازد (fallback)
        

**چرا این بهتره؟**

- دستگاه بهتر می‌فهمد چه زمانی ignition روشن/خاموش شده، یا چه زمانی رکورد جدید منطقیه.
    
- سرور هم می‌تواند sessionهای ناقص را ببندد (مثلاً اگر ۳۰ دقیقه دیتایی نیامد).
    

---

## 4) احراز هویت (Auth) ساده و امن برای MVP

دو گزینه:

1. **API Key per device** (ساده، MVP)
    
2. JWT/Mutual TLS (بعداً)
    

برای MVP:

- هر دستگاه یک `device_token` دارد.
    
- در Header می‌فرستد:
    
    - `Authorization: Device <token>`
        

---

## 5) APIها (طرح شبه‌Swagger)

### Base

- `POST /v1/...`
    
- پاسخ‌ها JSON
    
- خطاها با ساختار ثابت
    

### ساختار خطا (استاندارد پیشنهادی)

```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "session_id is required",
    "details": { "field": "session_id" }
  }
}
```

---

# A) Device / Bootstrap

## 1) ثبت دستگاه (اختیاری، اگر provisioning داری)

**POST** `/v1/devices/register`

**Request**

```json
{
  "serial": "DV-001-ABC",
  "model": "edgebox-v1",
  "firmware": "1.0.3",
  "public_key": "..." 
}
```

**Response**

```json
{
  "device_id": "dev_123",
  "device_token": "tok_xxx",
  "config": {
    "telemetry_batch_max": 200,
    "upload_chunk_size_bytes": 5242880
  }
}
```

---

## 2) گرفتن کانفیگ و قابلیت‌ها

**GET** `/v1/devices/me`

**Response**

```json
{
  "device_id": "dev_123",
  "server_time_ms": 1760000000000,
  "config": { "telemetry_batch_max": 200 }
}
```

---

# B) Time Sync

## 3) سینک زمان

**POST** `/v1/time/sync`

ایده: دستگاه زمان خودش را می‌فرستد، سرور زمان خودش را برمی‌گرداند + offset پیشنهادی.

**Request**

```json
{
  "device_time_ms": 1760000000123
}
```

**Response**

```json
{
  "server_time_ms": 1760000000456,
  "offset_ms": 333,
  "round_trip_hint_ms": 80
}
```

---

# C) Sessions (Trip / Recording Session)

## 4) شروع سشن

**POST** `/v1/sessions/start`

**Request**

```json
{
  "session_type": "trip",
  "device_time_ms": 1760000100000,
  "metadata": {
    "vehicle_vin": "WVWZZZ...",
    "driver_id": "drv_9",
    "reason": "ignition_on"
  }
}
```

**Response**

```json
{
  "session_id": "ses_abc123",
  "server_time_ms": 1760000100123
}
```

---

## 5) پایان سشن

**POST** `/v1/sessions/end`

**Request**

```json
{
  "session_id": "ses_abc123",
  "device_time_ms": 1760000800000,
  "reason": "ignition_off"
}
```

**Response**

```json
{
  "session_id": "ses_abc123",
  "closed": true
}
```

---

# D) Telemetry ingest (GPS/OBD/Temp/Events/Audio-metadata)

## 6) ارسال batch تلِمتری (اصلی‌ترین endpoint)

**POST** `/v1/telemetry:batch`

**Request**

```json
{
  "session_id": "ses_abc123",
  "seq_start": 1200,
  "records": [
    {
      "seq": 1200,
      "type": "gps",
      "device_time_ms": 1760000101000,
      "monotonic_ms": 50123,
      "data": { "lat": 35.7001, "lon": 51.4002, "speed_kph": 42.1, "heading_deg": 120 }
    },
    {
      "seq": 1201,
      "type": "obd",
      "device_time_ms": 1760000101200,
      "monotonic_ms": 50323,
      "data": {
        "pid": "010C",
        "name": "engine_rpm",
        "value": 2150,
        "unit": "rpm",
        "raw": "41 0C 21 5C"
      }
    },
    {
      "seq": 1202,
      "type": "temp",
      "device_time_ms": 1760000101500,
      "monotonic_ms": 50623,
      "data": { "celsius": 28.6, "sensor": "device_internal" }
    },
    {
      "seq": 1203,
      "type": "event",
      "device_time_ms": 1760000101800,
      "monotonic_ms": 50923,
      "data": { "name": "camera_connected", "level": "info" }
    }
  ]
}
```

**Response**

```json
{
  "accepted": 4,
  "rejected": 0,
  "next_expected_seq": 1204
}
```

نکته‌ها:

- `seq` به سرور کمک می‌کند duplicate/out-of-order را کنترل کند.
    
- `type` اجازه می‌دهد schema را ساده نگه داری ولی قابل توسعه.
    

---

## 7) ارسال وضعیت/هارت‌بیت

**POST** `/v1/device/heartbeat`

**Request**

```json
{
  "device_time_ms": 1760000105000,
  "battery_pct": 78,
  "network": { "type": "lte", "rssi": -85 },
  "storage_free_mb": 1200,
  "camera": { "connected": true, "recording": true }
}
```

**Response**

```json
{
  "ok": true,
  "server_time_ms": 1760000105123,
  "commands": [
    { "name": "set_upload_chunk_size", "value": 5242880 }
  ]
}
```

(این بخش MVP را خیلی خوش‌دست می‌کند چون کانفیگ/فرمان ساده هم می‌توانی بدهی.)

---

# E) Media (Video/Audio) — آپلود فایل + chunk

اینجا دو مدل رایج داریم:

### مدل 1: Multipart upload روی خود API (ساده، ولی سرور باید فایل بزرگ را هندل کند)

- `POST /v1/media/upload` با `multipart/form-data`
    
- خوب برای فایل‌های کوچک (مثلاً کلیپ ۱۰ ثانیه‌ای)
    

### مدل 2 (پیشنهادی): آپلود تکه‌ای (Resumable / Chunked)

سه مرحله: init → upload parts → complete

## 8) init آپلود

**POST** `/v1/media/uploads/init`

**Request**

```json
{
  "session_id": "ses_abc123",
  "media_type": "video",
  "content_type": "video/mp4",
  "file_size_bytes": 104857600,
  "sha256": "base16_or_base64",
  "device_time_ms": 1760000110000,
  "metadata": {
    "camera_id": "front",
    "start_time_ms": 1760000109000,
    "duration_ms": 120000,
    "resolution": "1920x1080",
    "fps": 30
  }
}
```

**Response**

```json
{
  "upload_id": "up_789",
  "chunk_size_bytes": 5242880,
  "parts": [
    { "part_number": 1, "url": "/v1/media/uploads/up_789/parts/1" }
  ],
  "expires_in_sec": 3600
}
```

> اگر خواستی حرفه‌ای‌ترش کنی: به‌جای `url` داخلی، “pre-signed URL” برای object storage بده (S3/MinIO). برای MVP هم می‌تونی همین مسیر داخلی را نگه داری.

---

## 9) آپلود هر تکه

**PUT** `/v1/media/uploads/{upload_id}/parts/{part_number}`

**Headers**

- `Content-Type: application/octet-stream`
    
- `Content-Range: bytes 0-5242879/104857600` (اختیاری ولی مفید)
    
- `X-Content-SHA256: ...` (اختیاری)
    

**Body**

- بایت‌های chunk
    

**Response**

```json
{
  "upload_id": "up_789",
  "part_number": 1,
  "received_bytes": 5242880,
  "etag": "etag_like_value"
}
```

---

## 10) complete آپلود

**POST** `/v1/media/uploads/{upload_id}/complete`

**Request**

```json
{
  "parts": [
    { "part_number": 1, "etag": "..." },
    { "part_number": 2, "etag": "..." }
  ]
}
```

**Response**

```json
{
  "media_id": "med_456",
  "status": "ready",
  "playback": {
    "download_url": "/v1/media/med_456"
  }
}
```

---

## 11) ثبت “قطعه مدیا” بدون آپلود (وقتی فایل قبلاً جایی ذخیره شده)

**POST** `/v1/media/register`

برای حالتی که دستگاه خودش فایل را روی یک فضای ذخیره‌سازی می‌گذارد (یا بعداً).

---

# F) Media streaming — آیا reverse streaming لازم است؟

برای MVP: معمولاً نه.

**reverse streaming** (اینکه سرور “از دستگاه بکشه”) در دنیای واقعی دردسر دارد چون:

- NAT/Carrier NAT اجازه اتصال ورودی به دستگاه را نمی‌دهد
    
- امنیت و مدیریت اتصال پیچیده می‌شود
    

اگر **واقعاً** استریم زنده لازم شد، گزینه‌های تمیز:

- **WebRTC** (بهترین برای real-time، ولی پیاده‌سازی سنگین‌تر)
    
- **RTSP** (کلاسیک، اما NAT و امنیت دردسر)
    
- **WebSocket streaming** (MVP-ish، ولی برای ویدئو خیلی بهینه نیست)
    

پس پیشنهاد:  
**فعلاً ضبط محلی + آپلود تکه‌ای + (اگر لازم شد) کلیپ‌های کوتاه event-based**.  
استریم زنده را فاز ۲.

---

## 6) “راه خیلی سریع بدون نیاز نرم‌افزاری خاص”

اگر منظورت اینه که سریع‌ترین مسیر با کمترین زیرساخت اضافی چی هست:

- فقط یک REST API + دیتابیس + فضای فایل (حتی روی دیسک)
    
- JSON برای telemetry
    
- `multipart/form-data` برای کلیپ‌های کوچک
    
- chunked upload برای فایل‌های بزرگ
    

این بدون MQTT، بدون Kafka، بدون پیچیدگی اضافه MVP را بالا می‌آورد.

---

# 7) فهرست دقیق Endpointها + ورودی/خروجی

## Auth (همه endpointها)

**Header**

- `Authorization: Device <device_token>`
    

---

## `/v1/time/sync` (POST)

**Input**

- `device_time_ms: int64`  
    **Output**
    
- `server_time_ms: int64`
    
- `offset_ms: int64`
    
- `round_trip_hint_ms: int32`
    

---

## `/v1/sessions/start` (POST)

**Input**

- `session_type: string (trip|recording|...)`
    
- `device_time_ms: int64`
    
- `metadata: object`  
    **Output**
    
- `session_id: string`
    
- `server_time_ms: int64`
    

---

## `/v1/sessions/end` (POST)

**Input**

- `session_id: string`
    
- `device_time_ms: int64`
    
- `reason: string`  
    **Output**
    
- `session_id: string`
    
- `closed: boolean`
    

---

## `/v1/telemetry:batch` (POST)

**Input**

- `session_id: string`
    
- `seq_start: int64` (اختیاری)
    
- `records: array<Record>`
    
    - `seq: int64`
        
    - `type: string (gps|obd|temp|event|audio_meta|...)`
        
    - `device_time_ms: int64`
        
    - `monotonic_ms: int64` (اختیاری ولی توصیه‌شده)
        
    - `data: object` (بسته به type)  
        **Output**
        
- `accepted: int32`
    
- `rejected: int32`
    
- `next_expected_seq: int64`
    
- `rejects?: array<{seq, reason}>` (اختیاری)
    

---

## `/v1/device/heartbeat` (POST)

**Input**

- `device_time_ms: int64`
    
- `battery_pct: int32`
    
- `network: object`
    
- `storage_free_mb: int32`
    
- `camera: object`  
    **Output**
    
- `ok: boolean`
    
- `server_time_ms: int64`
    
- `commands: array<object>` (اختیاری)
    

---

## `/v1/media/uploads/init` (POST)

**Input**

- `session_id: string`
    
- `media_type: string (video|audio)`
    
- `content_type: string`
    
- `file_size_bytes: int64`
    
- `sha256: string` (اختیاری ولی عالی)
    
- `device_time_ms: int64`
    
- `metadata: object`  
    **Output**
    
- `upload_id: string`
    
- `chunk_size_bytes: int32`
    
- `expires_in_sec: int32`
    

---

## `/v1/media/uploads/{upload_id}/parts/{part_number}` (PUT)

**Input**

- binary chunk  
    **Output**
    
- `upload_id: string`
    
- `part_number: int32`
    
- `received_bytes: int32`
    
- `etag: string`
    

---

## `/v1/media/uploads/{upload_id}/complete` (POST)

**Input**

- `parts: array<{part_number:int32, etag:string}>`  
    **Output**
    
- `media_id: string`
    
- `status: string (ready|processing)`
    
- `download_url?: string`
    

---

# 8) چند نکته‌ی اجرایی خیلی مهم (برای اینکه فردا درد نکشی)

- **Idempotency**: برای `/telemetry:batch` یا `/sessions/start` می‌توانی `Idempotency-Key` header بگذاری تا اگر دستگاه retry کرد، دوباره‌کاری نشود.
    
- **Compression**: اگر داده زیاد شد، gzip روی JSON خیلی کمک می‌کند (`Content-Encoding: gzip`).
    
- **Schema versioning**: داخل telemetry رکوردها یک `schema_ver` بگذار یا نسخه را در مسیر API نگه دار (همین `/v1`).
    
- **Storage**: ویدئو/صدا را بهتره مستقیم در object storage نگه داری، DB فقط metadata و مسیر فایل.
    

---

اگر بخوای، می‌تونم همین طرح رو به شکل یک فایل OpenAPI (YAML) هم دربیارم که واقعاً “سوگرگونه” بشه، ولی همین الان هم به اندازه کافی دقیق هست که یک تیم شروع کنه.