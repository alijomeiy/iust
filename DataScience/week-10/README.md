# Week-10: GPS Distance & Notifications Pipeline

معماری: **دستگاه → API Gateway → RabbitMQ ← Logstash → Elasticsearch** و **Spark** از ES + Postgres برای محاسبه مسافت و ساخت ناتیف (پاداش).

## ترتیب اجرا

### ۱. بالا آوردن سرویس‌ها

```bash
docker compose up -d
```

سرویس‌ها: `postgres`, `rabbitmq`, `es`, `logstash`, `spark`, `kibana`. (API Gateway را جداگانه با پایتون اجرا کن.)

### ۲. اجرای API Gateway (دستی)

از پوشهٔ پروژه:

```bash
cd rest_api_gateway
pip install -r ../requirments.txt
export DATABASE_URL=postgresql://api:api@localhost:5432/api
export RABBIT_URL=amqp://rabbitmquser:rabbitmqpass@localhost:5672/
uvicorn main:app --reload --port 8000
```

اگر دیتابیس و RabbitMQ روی IP دیگری هستند، همان را در `DATABASE_URL` و `RABBIT_URL` بگذار.

### ۳. اجرای مایگریشن‌های دیتابیس

**با psql روی host:**
```bash
PGHOST=localhost PGUSER=api PGPASSWORD=api PGDATABASE=api ./run_migrations.sh
```

**با Docker:**
```bash
docker exec -i db psql -U api -d api < migrations/000_base.sql
docker exec -i db psql -U api -d api < migrations/001_device_events.sql
```

### ۴. تعریف ایونت (آستانه کیلومتر) برای هر دستگاه

برای اینکه بعد از مثلاً ۲۰۰۰ کیلومتر به دستگاه ناتیف (پاداش) داده شود، یک بار این درخواست را بزن:

```bash
curl -X POST http://localhost:8000/v1/device/events/config \
  -H "Content-Type: application/json" \
  -d '{"device_id": "DEVICE_ID", "event_name": "reward_2000km", "km_threshold": 2000}'
```

`DEVICE_ID` را با شناسه واقعی دستگاه عوض کن.

### ۵. اجرای دوره‌ای Spark job

مسافت هر دستگاه و ناتیف‌ها با job اسپارک به‌روز می‌شوند. یا دستی یا با cron.

**یک بار دستی (داخل Docker):**
```bash
docker exec -it spark bash -c "ES_HOST=es PG_HOST=db spark-submit --master local[*] --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0,org.postgresql:postgresql:42.6.0 /opt/spark/job/distance_events_job.py"
```

یا از پوشه پروژه:
```bash
./spark_job/run_job_in_docker.sh
```

**اجرای دوره‌ای (cron):** نمونه در `cron.example`. مثلاً هر ساعت:

```bash
0 * * * * /path/to/week-10/spark_job/run_job_in_docker.sh
```

### ۶. جریان داده

1. دستگاه با `POST /v1/sessions/start` سشن شروع می‌کند.
2. با `POST /v1/telemetry:batch` بچ تلهمتری (شامل رکوردهای GPS با `type: "gps"` و `data.lat`, `data.lon`) و در صورت نیاز `device_id` را می‌فرستد.
3. API Gateway به RabbitMQ publish می‌کند؛ Logstash از صف می‌خواند و در Elasticsearch ایندکس می‌کند.
4. Spark job از ES مسافت را حساب می‌کند، `device_odometer` را به‌روز می‌کند و در صورت رسیدن به آستانه، در `device_messages` ناتیف می‌سازد.
5. دستگاه ناتیف‌ها را با `GET /v1/device/{device_id}/messages` می‌گیرد و با `POST /v1/device/{device_id}/messages/{message_id}/ack` read می‌کند.

## اجرای Logstash با host خارج از Docker

اگر Logstash را بیرون از Docker اجرا می‌کنی، قبل از اجرا این متغیرها را تنظیم کن:

```bash
export RABBITMQ_HOST=192.168.21.81
export ES_HOSTS=192.168.21.81:9200
```

در صورت استفاده از مقادیر پیش‌فرض در `logstash.conf` (`rabbitmq` و `es:9200`) فقط داخل شبکه Docker درست کار می‌کند.
