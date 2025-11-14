import datetime as dt
from datetime import timedelta

import textwrap
from datetime import datetime, timedelta

from airflow.providers.standard.operators.python import PythonOperator

from airflow.sdk import DAG
import pandas as pd
import psycopg2 as db
from elasticsearch import Elasticsearch


class PostgresqlConnectionPg:
    def __init__(self, dbname, host, user, password, base_query):
        self._connection_string = (
            f"dbname='{dbname}' host='{host}' user='{user}' password='{password}'"
        )
        self._connection = db.connect(self._connection_string)
        self._cursor = self._connection.cursor()
        self._base_query = base_query
        pass

    def insert_raw(self, data):
        self._cursor.execute(self._base_query, data)
        pass

    def insert_multiple_raw(self, data: list):
        temp = tuple(data)
        self._cursor.executemany(self._base_query, temp)
        pass

    def print_db_record(self):
        query = "select * from users;"
        self._cursor.execute(query)
        for record in self._cursor:
            print(record)
        pass

    def write_db_to_csv(self, csv_file_name: str):
        query = "select * from users;"
        self._cursor.execute(query)
        csv_file = open(csv_file_name, "w")
        self._cursor.copy_to(csv_file, "users", sep=",")
        csv_file.close()
        pass

    def load_db_in_pandas(self):
        return pd.read_sql("select * from users where id=400", self._connection)


ps = PostgresqlConnectionPg(
    dbname="dataengineering",
    host="192.168.21.81",
    user="admin",
    password="adminpass",
    base_query="insert into users (id,name,street,city,zip) values(%s,%s,%s,%s,%s)",
)


def queryPostgresql():
    ps.write_db_to_csv("postgresqldata.csv")
    print("-------Data Saved------")


def insertElasticsearch():
    es = Elasticsearch("http://192.168.21.81:9200")
    df = pd.read_csv("postgresqldata.csv")
    for i, r in df.iterrows():
        doc = r.to_json()
        res = es.index(index="frompostgresql", doc_type="doc", body=doc)
        print(res)


with DAG(
    "psql-to-es",
    default_args={
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(hours=2),
        # 'queue': 'bash_queue',
        # 'pool': 'backfill',
        # 'priority_weight': 10,
        # 'end_date': datetime(2016, 1, 1),
        # 'wait_for_downstream': False,
        # 'execution_timeout': timedelta(seconds=300),
        # 'on_failure_callback': some_function, # or list of functions
        # 'on_success_callback': some_other_function, # or list of functions
        # 'on_retry_callback': another_function, # or list of functions
        # 'sla_miss_callback': yet_another_function, # or list of functions
        # 'on_skipped_callback': another_function, #or list of functions
        # 'trigger_rule': 'all_success'
    },
    # [END default_args]
    description="Chapter 4 Implementation",
    schedule=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["data-pipline-pg"],
) as dag:

    getData = PythonOperator(task_id="QueryPostgreSQL", python_callable=queryPostgresql)

    insertData = PythonOperator(
        task_id="InsertDataElasticsearch", python_callable=insertElasticsearch
    )


getData >> insertData
