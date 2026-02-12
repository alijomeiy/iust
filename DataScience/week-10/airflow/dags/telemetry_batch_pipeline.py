"""
DAG: هر ساعت جاب Spark کیلومتر تجمعی هر خودرو را از ES حساب می‌کند
و در device_odometer می‌ریزد. اندپوینت GET /v1/device/{id}/oil-change-due بر اساس ۲۰۰۰ کیلومتر بولین برمی‌گرداند.

Airflow با استفاده از Docker API مستقیماً در کانتینر spark دستور spark-submit را اجرا می‌کند.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

SPARK_CMD = (
    "ES_HOST=es PG_HOST=db spark-submit --master local[*] "
    "--packages org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0,org.postgresql:postgresql:42.6.0 "
    "/opt/spark/job/distance_events_job.py"
)


def _run_spark_odometer_job(**context):
    import docker

    client = docker.from_env()
    container = client.containers.get("spark")
    exit_code, output = container.exec_run(
        ["bash", "-c", SPARK_CMD],
        workdir="/opt/spark",
    )
    out = output.decode() if isinstance(output, bytes) else output
    if exit_code != 0:
        raise RuntimeError(f"Spark job failed (exit={exit_code}):\n{out}")
    print(out)


with DAG(
    dag_id="telemetry_batch_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@hourly",
    tags=["telemetry", "spark", "oil-change"],
    catchup=False,
) as dag:
    PythonOperator(
        task_id="run_spark_odometer",
        python_callable=_run_spark_odometer_job,
    )
