#!/bin/bash
# Run Spark job
# In Docker: docker exec -it spark bash -c "ES_HOST=es PG_HOST=db spark-submit --master local[*] --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0,org.postgresql:postgresql:42.6.0 /opt/spark/job/distance_events_job.py"
# On host: ES_HOST=192.168.21.81 PG_HOST=192.168.21.81 ./run_job.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ES_HOST=${ES_HOST:-192.168.21.81}
export PG_HOST=${PG_HOST:-192.168.21.81}

spark-submit \
  --master "local[*]" \
  --packages "org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0,org.postgresql:postgresql:42.6.0" \
  "$SCRIPT_DIR/distance_events_job.py"
