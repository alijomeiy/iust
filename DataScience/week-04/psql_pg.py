import psycopg2 as db
from faker import Faker
import pandas as pd


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

    def test_insert_many(self):
        fake = Faker()
        data = []
        for i in range(1000):
            data.append(
                (fake.name(), fake.street_address(), fake.city(), fake.zipcode())
            )
        self.insert_multiple_raw(data=data)
        pass

    def test_insert_single(self):
        fake = Faker()
        data = (fake.name(), fake.street_address(), fake.city(), fake.zipcode())
        self.insert_raw(data=data)
        pass

    def print_db_record(self):
        query = "select * from users;"
        self._cursor.execute(query)
        for record in self._cursor:
            print(record)
        pass

    def write_db_to_csf(self):
        query = "select * from users;"
        self._cursor.execute(query)
        csv_file = open("fromdb.csv", "w")
        self._cursor.copy_to(csv_file, "users", sep=",")
        csv_file.close()
        pass

    def load_db_in_pandas(self):
        return pd.read_sql("select * from users where id=400", self._connection)


if __name__ == "__main__":
    pg = PostgresqlConnectionPg(
        dbname="dataengineering",
        host="192.168.21.81",
        user="admin",
        password="adminpass",
        base_query="insert into users (id,name,street,city,zip) values(%s,%s,%s,%s,%s)",
    )

    frame = pg.load_db_in_pandas()
    print(frame.to_json(orient="records"))
