#!/usr/bin/env python3
"""
Spark Job: Calculate distance per device from GPS data and trigger messages when event thresholds are reached.
Reads from ES, writes results to Postgres.
"""
import json
import os
import math
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
from pyspark.sql.window import Window

ES_HOST = os.getenv("ES_HOST", "192.168.21.81")
ES_PORT = os.getenv("ES_PORT", "9200")
PG_HOST = os.getenv("PG_HOST", "192.168.21.81")
PG_DSN = f"host={PG_HOST} port=5432 dbname=api user=api password=api"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km."""
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def main():
    spark = (
        SparkSession.builder.appName("DistanceEventsJob")
        .config(
            "spark.jars.packages",
            "org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0,org.postgresql:postgresql:42.6.0",
        )
        .getOrCreate()
    )

    # Read from ES
    es_options = {
        "es.nodes": ES_HOST,
        "es.port": ES_PORT,
        "es.read.field.include": "session_id,device_id,record_type,record_device_time,data",
    }
    df = spark.read.format("es").options(**es_options).load("telemetry-*")

    # GPS records with device_id only
    gps = (
        df.filter(F.col("record_type") == "gps")
        .filter(F.col("device_id").isNotNull())
        .select(
            F.col("device_id"),
            F.col("session_id"),
            F.to_timestamp(F.col("record_device_time")).alias("device_time"),
            F.col("data.lat").cast(DoubleType()).alias("lat"),
            F.col("data.lon").cast(DoubleType()).alias("lon"),
        )
        .filter(F.col("lat").isNotNull() & F.col("lon").isNotNull())
    )

    if gps.count() == 0:
        spark.stop()
        return

    # Haversine UDF
    @F.udf(DoubleType())
    def haversine_udf(lat1, lon1, lat2, lon2):
        return haversine_km(
            float(lat1) if lat1 else None,
            float(lon1) if lon1 else None,
            float(lat2) if lat2 else None,
            float(lon2) if lon2 else None,
        )

    # Window for previous point
    w = Window.partitionBy("device_id", "session_id").orderBy("device_time")
    gps_lag = (
        gps.withColumn("prev_lat", F.lag("lat").over(w))
        .withColumn("prev_lon", F.lag("lon").over(w))
    )

    # Distance between consecutive points
    with_dist = gps_lag.withColumn(
        "km",
        haversine_udf(F.col("prev_lat"), F.col("prev_lon"), F.col("lat"), F.col("lon")),
    ).na.fill(0, ["km"])

    # Sum distance per device
    total_km = with_dist.groupBy("device_id").agg(F.sum("km").alias("total_km"))

    # Update odometer in Postgres
    import psycopg2

    conn = psycopg2.connect(PG_DSN)
    cur = conn.cursor()
    for row in total_km.collect():
        cur.execute(
            """
            INSERT INTO device_odometer (device_id, total_km, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (device_id) DO UPDATE SET
                total_km = EXCLUDED.total_km,
                updated_at = EXCLUDED.updated_at
            """,
            (row.device_id, float(row.total_km), datetime.utcnow()),
        )
    conn.commit()
    cur.close()
    conn.close()

    # Read config and messages
    config_df = spark.read.format("jdbc").options(
        url=f"jdbc:postgresql://{PG_HOST}:5432/api",
        dbtable="device_event_config",
        user="api",
        password="api",
        driver="org.postgresql.Driver",
    ).load()

    triggered_df = (
        spark.read.format("jdbc")
        .options(
            url=f"jdbc:postgresql://{PG_HOST}:5432/api",
            dbtable="device_messages",
            user="api",
            password="api",
            driver="org.postgresql.Driver",
        )
        .load()
        .select("event_config_id")
        .distinct()
    )

    # Devices that crossed threshold but haven't received message yet
    join_df = total_km.join(config_df, "device_id").filter(
        F.col("total_km") >= F.col("km_threshold")
    )
    join_df = join_df.join(
        triggered_df, F.col("id") == F.col("event_config_id"), "left_anti"
    ).select("device_id", "id", "event_name", "km_threshold", "total_km")

    # Insert new messages
    rows = join_df.collect()
    if rows:
        conn = psycopg2.connect(PG_DSN)
        cur = conn.cursor()
        for row in rows:
            msg = {"event": row.event_name, "km": float(row.km_threshold)}
            cur.execute(
                """
                INSERT INTO device_messages (device_id, event_config_id, event_name, message, km_at_trigger, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    row.device_id,
                    row.id,
                    row.event_name,
                    json.dumps(msg),
                    float(row.total_km),
                    datetime.utcnow(),
                ),
            )
        conn.commit()
        cur.close()
        conn.close()

    spark.stop()


if __name__ == "__main__":
    main()
