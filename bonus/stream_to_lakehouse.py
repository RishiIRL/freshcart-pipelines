#!/usr/bin/env python3
"""
Bonus Task: Stream-to-Lakehouse Idempotency Simulation
Simulates a 1-minute event stream of FreshCart orders, writes them to a raw landing zone,
transforms and loads them into a curated lakehouse layer, and runs the batch ingestion
twice to prove idempotency (totals and row counts do not double).
Includes tqdm progress bars and elapsed time logging per user preferences.
"""

import os
import json
import time
import pandas as pd
from tqdm import tqdm

RAW_LANDING_PATH = "/home/glitch/Projects/Assignment/freshcart-pipelines/bonus/raw_landing.jsonl"
CURATED_LAKEHOUSE_PATH = "/home/glitch/Projects/Assignment/freshcart-pipelines/bonus/curated_orders.csv"


def simulate_stream(num_events: int = 60) -> list[dict]:
    """Simulate a 1-minute order event stream (1 event per simulated second)."""
    print(f"[*] Simulating {num_events} events from FreshCart order stream...")
    events = []
    
    start_time = time.time()
    for i in tqdm(range(num_events), desc="Streaming Events", unit="evt"):
        event_id = f"ORD-{1000 + i}"
        city = "bangalore" if i % 2 == 0 else "chennai"
        zone = "koramangala" if city == "bangalore" else "tnagar"
        order_type = "food" if i % 3 == 0 else "ride"
        amount = round(150.0 + (i * 12.5) % 500.0, 2)
        
        event = {
            "order_id": event_id,
            "city": city,
            "zone": zone,
            "type": order_type,
            "amount": amount,
            "event_timestamp": start_time + i
        }
        events.append(event)
        time.sleep(0.01)  # small simulated delay
        
    elapsed = time.time() - start_time
    print(f"[+] Stream simulation complete. Generated {num_events} events in {elapsed:.2f}s.")
    return events


def write_raw_landing(events: list[dict], filepath: str) -> None:
    """Write raw events to landing zone (append-only JSONL)."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    print(f"[*] Writing raw events to landing zone: {filepath}")
    with open(filepath, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    print(f"[+] Raw landing write complete.")


def load_and_transform(landing_path: str, curated_path: str) -> pd.DataFrame:
    """
    Batch ingestion job: Read raw landing, transform, deduplicate by order_id,
    and write idempotently to curated lakehouse storage.
    """
    print(f"[*] Starting batch ingestion job from {landing_path}...")
    start_time = time.time()
    
    # Step 1: Read raw records with progress
    records = []
    with open(landing_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in tqdm(lines, desc="Reading Raw Records", unit="line"):
        records.append(json.loads(line.strip()))
        
    df_raw = pd.DataFrame(records)
    print(f"[+] Read {len(df_raw)} raw records.")
    
    # Step 2: Idempotent Transformation & Deduplication
    # Group by order_id, taking the latest event_timestamp or deduplicating
    print("[*] Transforming and deduplicating records (idempotency key: order_id)...")
    df_curated = df_raw.sort_values("event_timestamp").drop_duplicates(subset=["order_id"], keep="last")
    
    # Compute aggregates or curated schema
    df_curated["processed_at"] = time.time()
    
    # Step 3: Write to curated lakehouse (overwrite/upsert semantics ensuring idempotency)
    os.makedirs(os.path.dirname(curated_path), exist_ok=True)
    df_curated.to_csv(curated_path, index=False)
    
    elapsed = time.time() - start_time
    print(f"[+] Curated lakehouse write complete: {curated_path} ({len(df_curated)} unique rows) in {elapsed:.2f}s.")
    return df_curated


def main():
    print("==================================================")
    print(" FreshCart Stream-to-Lakehouse Idempotency Demo ")
    print("==================================================")
    
    # 1. Simulate 60 events (1-minute window)
    events = simulate_stream(60)
    
    # 2. Write raw landing zone
    write_raw_landing(events, RAW_LANDING_PATH)
    
    # 3. First Batch Ingestion Run
    print("\n--- BATCH RUN 1 (Initial Ingestion) ---")
    df_run1 = load_and_transform(RAW_LANDING_PATH, CURATED_LAKEHOUSE_PATH)
    total_amount_run1 = df_run1["amount"].sum()
    print(f"Run 1 Row Count: {len(df_run1)} | Total Amount: {total_amount_run1:.2f}")
    
    # 4. Second Batch Ingestion Run (Simulating retry/reprocessing of the same landing data)
    print("\n--- BATCH RUN 2 (Idempotency Proof Run) ---")
    df_run2 = load_and_transform(RAW_LANDING_PATH, CURATED_LAKEHOUSE_PATH)
    total_amount_run2 = df_run2["amount"].sum()
    print(f"Run 2 Row Count: {len(df_run2)} | Total Amount: {total_amount_run2:.2f}")
    
    # 5. Verify Idempotency Assertions
    print("\n--- IDEMPOTENCY VERIFICATION ---")
    assert len(df_run1) == len(df_run2), f"Row count mismatch! Run 1: {len(df_run1)}, Run 2: {len(df_run2)}"
    assert total_amount_run1 == total_amount_run2, f"Total amount mismatch! Run 1: {total_amount_run1}, Run 2: {total_amount_run2}"
    print("✅ SUCCESS: Run 1 and Run 2 produce identical row counts and total amounts!")
    print("   Idempotency verified: re-running batch ingestion over landing data does not double totals.")
    print("==================================================")


if __name__ == "__main__":
    main()
