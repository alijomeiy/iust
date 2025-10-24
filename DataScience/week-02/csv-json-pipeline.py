import datetime as dt
from datetime import timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator


def scv_to_json():
    df = pd.read_CSV("./data.CSV")
    for i, r in df.iterrows():
        print(r["name"])
    df.to_JSON("fromAirflow.JSON", orient="records")


default_args = {
    "owner": "paulcrickard",
    "start_date": dt.datetime(2025, 10, 24),
    "retries": 1,
    "retry_delay": dt.timedelta(minutes=5),
}


with DAG(
    "MyCSVDAG",
    default_args=default_args,
    schedule_interval=timedelta(minutes=5),
    # '0 * * * *',
) as dag:
    print_starting = BashOperator(
        task_id="starting", bash_command='echo "I am reading the CSV now....."'
    )
    CSVJson = PythonOperator(task_id="convertCSVtoJson", python_callable=scv_to_json)
