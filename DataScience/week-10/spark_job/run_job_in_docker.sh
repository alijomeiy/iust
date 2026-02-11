#!/bin/bash
# Run the distance/events Spark job inside the spark container.
# Use this from cron for periodic runs, e.g.:
#   0 * * * * /path/to/week-10/spark_job/run_job_in_docker.sh

set -e
CONTAINER=${SPARK_CONTAINER:-spark}
docker exec "$CONTAINER" bash -c \
  'ES_HOST=es PG_HOST=db spark-submit --master local[*] \
   --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0,org.postgresql:postgresql:42.6.0 \
   /opt/spark/job/distance_events_job.py'
