# دستورات اجرا (سرویس‌ها در داکر، API و generator روی ماشین)

## ۱) بالا آوردن سرویس‌های داکر

**روی لینوکس** اگر اولین بار است یا قبلاً خطای Permission برای Airflow گرفته‌اید، قبل از `docker compose up` یک بار این را اجرا کنید تا مالکیت پوشه‌ی لاگ درست شود:

```bash
cd /root/apg/iust/DataScience/week-10
# اگر پوشه‌ی logs قبلاً توسط داکر ساخته شده (مالک root)، مالکیت را به کاربر فعلی بدهید:
sudo chown -R $(id -u):0 airflow/logs airflow/dags 2>/dev/null || true
# UID کاربر فعلی را در .env بگذارید تا کانتینر با همین کاربر اجرا شود:
echo "AIRFLOW_UID=$(id -u)" > .env
```

سپس:

```bash
docker compose up -d
```

شامل: postgres، rabbitmq، Elasticsearch، Kibana، Logstash، Spark، **Airflow** (ارکستریشن).

- API (خودتان): `http://localhost:8000`
- Airflow UI: `http://localhost:8081` (لاگین/پسورد پیش‌فرض: `airflow` / `airflow`)
- Spark Master UI: `http://localhost:8080`

---

## ۲) نصب وابستگی‌های پایتون (یک بار)

```bash
cd /root/apg/iust/DataScience/week-10
pip install -r requirments.txt
```

---

## ۳) مایگریشن دیتابیس

```bash
cd /root/apg/iust/DataScience/week-10
./run_migrations.sh
```

---

## ۴) اجرای API (FastAPI)

```bash
cd /root/apg/iust/DataScience/week-10/rest_api_gateway
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

داکیومنت: `http://localhost:8000/docs`

---

## ۵) دمو: فرستادن داده با generator

```bash
cd /root/apg/iust/DataScience/week-10
python generator.py
```

تعداد ماشین و روز را وارد کنید؛ داده به API و صف‌های RabbitMQ فرستاده می‌شود. Logstash از RabbitMQ می‌خواند و در Elasticsearch می‌ریزد.

**مثال استفاده:** در اجرا دو سؤال به‌صورت تعاملی پرسیده می‌شود:

```
=== Telemetry Generator ===

Tedad mashin: 3
Chand rooz: 7
```

- **تعداد ماشین:** عدد بین ۱ تا ۵۰۰ (مثلاً `3` برای سه خودرو: `car-001`, `car-002`, `car-003`).
- **چند روز:** عدد بین ۱ تا ۳۶۵ (مثلاً `7` برای شبیه‌سازی یک هفته).

بعد از اتمام، خلاصهٔ هر ماشین و فایل `run_summary.json` در همان پوشه ساخته می‌شود. برای اجرای بدون تعامل (مثلاً از اسکریپت) می‌توانید ورودی را از stdin بدهید:

```bash
echo -e "2\n5" | python generator.py
```

(۲ ماشین، ۵ روز)

---

## ۶) جاب اسپارک (کیلومتر تجمعی + روغن)

بعد از اینکه دادهٔ GPS در ES بود:

```bash
./spark_job/run_job_in_docker.sh
```

یا با docker مستقیم:

```bash
docker exec spark bash -c 'ES_HOST=es PG_HOST=db spark-submit --master local[*] \
  --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0,org.postgresql:postgresql:42.6.0 \
  /opt/spark/job/distance_events_job.py'
```

جاب کیلومتر تجمعی هر `device_id` را از ES حساب می‌کند و در جدول `device_odometer` می‌نویسد.

---

## ۷) چک کردن «روغن عوض کن»

وقتی کیلومتر تجمعی یک خودرو به ۲۰۰۰ یا بیشتر برسد، اندپوینت زیر `true` برمی‌گرداند:

```bash
curl http://localhost:8000/v1/device/car-001/oil-change-due
# {"oil_change_due": true} یا {"oil_change_due": false}
```

---

## خلاصه ترتیب

| مرحله | دستور |
|--------|--------|
| ۱ | `docker compose up -d` |
| ۲ | `pip install -r requirments.txt` و `./run_migrations.sh` |
| ۳ | `cd rest_api_gateway && uvicorn main:app --reload --host 0.0.0.0 --port 8000` |
| ۴ | `python generator.py` (دمو) |
| ۵ | `./spark_job/run_job_in_docker.sh` (بعد از ورود داده به ES) |
| ۶ | `curl .../v1/device/{device_id}/oil-change-due` |
