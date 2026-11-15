#!/usr/bin/env python3
"""
Driver script for Part D (RabbitMQ consumer).
Consumes messages matching a binding pattern from the 'rapido-dispatch' topic exchange.
Implements D3 ACK / NACK handling:
- Rejects messages missing 'zone' field with basic_nack(requeue=False).
- Acknowledges valid messages with basic_ack.
"""

import sys
import os
import json
import pika

EXCHANGE_NAME = "rapido-dispatch"


def get_connection(amqp_url: str | None = None) -> pika.BlockingConnection:
    """Establish a blocking connection to the RabbitMQ broker."""
    url = amqp_url or os.environ.get("AMQP_URL", "amqp://guest:guest@localhost:5672/")
    return pika.BlockingConnection(pika.URLParameters(url))


def process_message(driver_name: str, ch, method, body: bytes) -> None:
    """
    Process a single incoming message.
    - Parses JSON body.
    - If malformed JSON or missing 'zone' field, NACK with requeue=False.
    - Otherwise, print and ACK.
    """
    try:
        data = json.loads(body.decode("utf-8"))
    except Exception as e:
        print(f"[{driver_name}] ERROR: Failed to parse JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    # D3 Validation: Check if 'zone' field is present and non-empty
    if "zone" not in data or not data["zone"]:
        print(f"[{driver_name}] NACK (malformed/missing zone): {data}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    else:
        print(f"[{driver_name}] ACK (processed successfully): routing_key={method.routing_key}, msg={data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <DriverName> <BindingPattern>")
        print(f"Example: python {sys.argv[0]} Ravi 'bangalore.koramangala.*'")
        sys.exit(1)

    driver_name = sys.argv[1]
    binding_pattern = sys.argv[2]

    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic")

    # Declare exclusive private queue for this driver instance
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=binding_pattern)

    print(f"[*] Driver {driver_name} ready. Bound to '{EXCHANGE_NAME}' with pattern '{binding_pattern}'. Waiting for requests...")

    def callback(ch, method, properties, body):
        process_message(driver_name, ch, method, body)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"\n[*] Driver {driver_name} stopped.")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
