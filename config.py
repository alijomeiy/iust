import os

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://rabbitmquser:rabbitmqpass@localhost:5672/")

QUEUE_TELEMETRY = os.getenv("QUEUE_TELEMETRY", "telemetry_batch")
QUEUE_HEARTBEAT = os.getenv("QUEUE_HEARTBEAT", "device_heartbeat")
QUEUE_SESSION_EVENTS = os.getenv("QUEUE_SESSION_EVENTS", "session_events")

# PREFETCH_COUNT = int(os.getenv("RABBIT_PREFETCH", "200"))
PREFETCH_COUNT = 200
