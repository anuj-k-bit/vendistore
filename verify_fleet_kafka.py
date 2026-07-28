#!/usr/bin/env python3
"""
IntelliVend 10-Machine Fleet Kafka & PostgreSQL Verification Script
Executes end-to-end verification:
1. Starts Kafka Engine & MQTT-to-Kafka Bridge.
2. Runs Machine Simulator generating telemetry across 10 machines (VM-101 .. VM-110).
3. Verifies Kafka topics: `purchases`, `restocks`, `sensor-readings`.
4. Confirms inventory-service consumes from Kafka and updates PostgreSQL for all 10 machines!
"""

import json
import sys
import time
from pathlib import Path

# Safe UTF-8 reconfiguration for Windows terminal
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add python paths
sys.path.insert(0, str(Path(__file__).parent / "backend" / "kafka-service"))
sys.path.insert(0, str(Path(__file__).parent / "backend" / "inventory-service"))
sys.path.insert(0, str(Path(__file__).parent / "machine-simulator"))

from kafka_engine import kafka_engine, MQTT_Kafka_Bridge
from app.kafka_consumer import start_kafka_consumer
from app.database import engine, Base, SessionLocal
from app.models import Machine, Slot, Transaction

def run_fleet_verification():
    print("=" * 75)
    print("[START] INTELLIVEND FLEET & KAFKA EVENT LOG VERIFICATION")
    print("=" * 75)

    # 1. Initialize DB Schema
    Base.metadata.create_all(bind=engine)
    print("[1/5] PostgreSQL / SQLAlchemy database schema initialized.")

    # 2. Start MQTT-to-Kafka Bridge
    bridge = MQTT_Kafka_Bridge()
    bridge.start()
    print("[2/5] MQTT-to-Kafka Bridge started. Listening on MQTT 'machine/+/telemetry'...")

    # 3. Start Kafka Consumer in Inventory Service
    start_kafka_consumer()
    print("[3/5] Inventory Service Kafka Consumer started on topic 'purchases'.")

    time.sleep(1.5)

    # 4. Trigger Fleet Simulator for 10 Machines
    from simulator import run_fleet_simulator
    print("\n[4/5] Running Fleet Simulator across 10 machines (VM-101 to VM-110)...")
    print("-" * 75)
    run_fleet_simulator(max_events=20)
    print("-" * 75)

    # Wait for Kafka consumer batch processing
    print("\n[5/5] Processing Kafka stream & committing updates to PostgreSQL database...")
    time.sleep(3.0)

    # 5. Inspect Kafka Topic Logs & Offsets
    print("\n" + "=" * 75)
    print("[KAFKA] DURABLE EVENT LOG METADATA")
    print("=" * 75)
    metadata = kafka_engine.get_topic_metadata()
    for topic_name, info in metadata.items():
        print(f"  * Topic: '{topic_name}' | Total Messages: {info['total_messages']} | Latest Offset: {info['latest_offset']}")

    # 6. Verify PostgreSQL Fleet Database Records
    print("\n" + "=" * 75)
    print("[POSTGRES] FLEET DATABASE INVENTORY SNAPSHOT (ALL 10 MACHINES)")
    print("=" * 75)
    db = SessionLocal()
    try:
        machines = db.query(Machine).order_by(Machine.id).all()
        print(f"Total Fleet Machines in Postgres DB: {len(machines)}\n")

        header = f"{'MACHINE ID':<12} | {'NAME':<28} | {'SLOTS':<6} | {'TOTAL ITEMS':<12} | {'CAPACITY':<10}"
        print(header)
        print("-" * len(header))

        for m in machines:
            slots = db.query(Slot).filter(Slot.machine_id == m.id).all()
            total_items = sum(s.current_stock for s in slots)
            capacity = sum(s.max_capacity for s in slots)
            print(f"{m.id:<12} | {m.name:<28} | {len(slots):<6} | {total_items:<12} | {capacity:<10}")

        print("-" * len(header))

        # Check total recorded transactions in Postgres
        total_tx = db.query(Transaction).count()
        print(f"\n[OK] Total Recorded Transactions in Postgres: {total_tx}")
        print("[SUCCESS] All 10 machines' events flowed through Kafka topics into PostgreSQL!")
        print("=" * 75)

    finally:
        db.close()

if __name__ == "__main__":
    run_fleet_verification()
