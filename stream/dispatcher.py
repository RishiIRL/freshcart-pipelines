#!/usr/bin/env python3
"""
Dispatcher script for Part D (RabbitMQ topic exchange).

Publishes ride/food dispatch requests every 2 seconds to a topic exchange
called 'rapido-dispatch'. Every 10th message is intentionally malformed
(missing the 'zone' field) to test D3 ACK/NACK handling.
"""

import os
import random
import time
import json
import pika

EXCHANGE_NAME = "rapido-dispatch"
CITIES = ["bangalore", "chennai"]
ZONES = {
    "bangalore": ["koramangala", "indiranagar", "whitefield"],
    "chennai": ["tnagar", "adyar", "velachery"]
}
TYPES = ["ride", "food"]


def get_connection(amqp_url: str | None = None) -> pika.BlockingConnection:
    """Establish a blocking connection to the RabbitMQ broker."""
    url = amqp_url or os.environ.get("AMQP_URL", "amqp://guest:guest@localhost:5672/")
    return pika.BlockingConnection(pika.URLParameters(url))


def build_message(msg_count: int) -> tuple[str, dict]:
    """
    Build a dispatch request message.
    Every 10th message is intentionally malformed (missing 'zone').
    Returns (routing_key, message_body).
    """
    city = random.choice(CITIES)
    req_type = random.choice(TYPES)
    is_bad = (msg_count % 10 == 0)

    if is_bad:
        # Malformed message missing 'zone' field for D3 testing
        routing_key = f"{city}.{req_type}"
        message = {
            "id": f"REQ-{msg_count:04d}",
            "city": city,
            "type": req_type,
            "ts": time.time(),
            "malformed": True
        }
    else:
        zone = random.choice(ZONES[city])
        routing_key = f"{city}.{zone}.{req_type}"
        message = {
            "id": f"REQ-{msg_count:04d}",
            "city": city,
            "zone": zone,
            "type": req_type,
            "ts": time.time()
        }

    return routing_key, message


def main():
    connection = get_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic")

    print(f"[*] Dispatcher started. Publishing to exchange '{EXCHANGE_NAME}'. Press Ctrl+C to exit.")
    msg_count = 0

    try:
        while True:
            msg_count += 1
            routing_key, message = build_message(msg_count)

            if "malformed" in message:
                print(f"[!] Sending BAD message #{msg_count} (missing zone): routing_key={routing_key}")
            else:
                print(f"[x] Sent #{msg_count}: routing_key={routing_key}, body={message}")

            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=routing_key,
                body=json.dumps(message)
            )
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[*] Dispatcher stopped.")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
