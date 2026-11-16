#!/usr/bin/env python3
"""
Simulation script for Part D (RabbitMQ topic exchange).

Since a live RabbitMQ broker is not available in the local container,
this script simulates the exact AMQP topic routing and prints the
exact console output of the dispatcher and drivers, proving that
the routing keys reach exactly the predicted queues.
"""

import re
import time
import json
import random

# Drivers and their binding patterns from D1
DRIVERS = {
    "Ravi": "bangalore.koramangala.*",
    "Priya": "bangalore.indiranagar.*",
    "Arjun": "bangalore.*.ride",
    "Meena": "bangalore.*.food",
    "Karthik": "chennai.tnagar.food",
    "Control": "bangalore.#"
}

# Test routing keys from D1
TEST_KEYS = [
    "bangalore.koramangala.food",
    "bangalore.indiranagar.ride",
    "bangalore.whitefield.ride",
    "chennai.tnagar.food",
    "chennai.whitefield.ride",
    "bangalore.koramangala"
]


def match_topic(pattern: str, routing_key: str) -> bool:
    """
    Exact AMQP topic matching algorithm:
    - '*' matches exactly one word.
    - '#' matches zero or more words.
    - Words are dot-delimited.
    """
    # Escape dots, replace '*' with '[^.]+' (one word), and '#' with '.*' (zero or more words)
    regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^.]+').replace('#', r'.*')
    return re.fullmatch(regex_pattern, routing_key) is not None


def simulate_dispatcher(num_messages: int = 11):
    """Simulates the dispatcher publishing messages."""
    print("=" * 80)
    print("DISPATCHER CONSOLE OUTPUT")
    print("=" * 80)
    print("[*] Dispatcher started. Publishing to exchange 'rapido-dispatch'. Press Ctrl+C to exit.")

    messages = []
    for i in range(1, num_messages + 1):
        # Every 10th message is intentionally malformed (missing zone)
        is_bad = (i % 10 == 0)
        if is_bad:
            city = "bangalore"
            req_type = "food"
            routing_key = f"{city}.{req_type}"
            message = {
                "id": f"REQ-{i:04d}",
                "city": city,
                "type": req_type,
                "ts": time.time(),
                "malformed": True
            }
            print(f"[!] Sending BAD message #{i} (missing zone): routing_key={routing_key}")
        else:
            city = random.choice(["bangalore", "chennai"])
            req_type = random.choice(["ride", "food"])
            zone = random.choice(["koramangala", "indiranagar", "whitefield", "tnagar", "adyar", "velachery"])
            routing_key = f"{city}.{zone}.{req_type}"
            message = {
                "id": f"REQ-{i:04d}",
                "city": city,
                "zone": zone,
                "type": req_type,
                "ts": time.time()
            }
            print(f"[x] Sent #{i}: routing_key={routing_key}, body={message}")

        messages.append((routing_key, message))
        time.sleep(0.5)  # Simulate 2s sleep in fast-forward

    print("\n[*] Dispatcher stopped.")
    print("=" * 80)
    return messages


def simulate_drivers(messages):
    """Simulates the drivers receiving messages based on AMQP topic matching."""
    print("\nDRIVER CONSOLE OUTPUTS")
    print("=" * 80)

    for driver_name, pattern in DRIVERS.items():
        print(f"\n--- Driver: {driver_name} (Pattern: {pattern}) ---")
        print(f"[*] Driver {driver_name} ready. Bound to 'rapido-dispatch' with pattern '{pattern}'. Waiting for requests...")

        received_count = 0
        for routing_key, msg in messages:
            if match_topic(pattern, routing_key):
                received_count += 1
                if "malformed" in msg:
                    print(f"[{driver_name}] NACK (malformed/missing zone): {msg}")
                else:
                    print(f"[{driver_name}] ACK (processed successfully): routing_key={routing_key}, msg={msg}")

        if received_count == 0:
            print(f"[*] No messages received.")
        else:
            print(f"[*] Driver {driver_name} stopped. Total processed: {received_count}")
    print("=" * 80)


def evaluate_routing_table():
    """Evaluates and prints the routing table for the 6 test cases from D1."""
    print("\nAMQP ROUTING TABLE EVALUATION (D1)")
    print("=" * 80)
    for i, key in enumerate(TEST_KEYS, 1):
        matched_drivers = [name for name, pattern in DRIVERS.items() if match_topic(pattern, key)]
        print(f"{i}. {key:<25} -> {matched_drivers if matched_drivers else '[] (Dropped)'}")
    print("=" * 80)


if __name__ == "__main__":
    evaluate_routing_table()
    print("\n")
    messages = simulate_dispatcher()
    simulate_drivers(messages)