from __future__ import annotations

import json
import aio_pika
from aio_pika import DeliveryMode, Message

from config import (
    PREFETCH_COUNT,
    QUEUE_HEARTBEAT,
    QUEUE_SESSION_EVENTS,
    QUEUE_TELEMETRY,
    RABBIT_URL,
)


class RabbitPublisher:
    def __init__(self, url: str):
        self.url = url
        self.conn: aio_pika.RobustConnection | None = None   
        self.channel: aio_pika.RobustChannel | None = None

    async def connect(self) -> None:
        self.conn = await aio_pika.connect_robust(self.url)
        self.channel = await self.conn.channel()
        await self.channel.set_qos(prefetch_count=PREFETCH_COUNT)

        # Declare queues durable so they survive restart
        await self.channel.declare_queue(QUEUE_TELEMETRY, durable=True)
        await self.channel.declare_queue(QUEUE_HEARTBEAT, durable=True)
        await self.channel.declare_queue(QUEUE_SESSION_EVENTS, durable=True)

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    async def publish_json(self, queue: str, payload: dict) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized. Did you call connect()?")

        body = json.dumps(payload, default=str).encode("utf-8")
        msg = Message(body=body, delivery_mode=DeliveryMode.PERSISTENT)
        await self.channel.default_exchange.publish(msg, routing_key=queue)


publisher = RabbitPublisher(RABBIT_URL)
