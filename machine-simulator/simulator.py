#!/usr/bin/env python3
"""
IntelliVend Fleet Event Simulator (10 Vending Machines)
Simulates VM-101 through VM-110 generating telemetry events over MQTT:
- PURCHASES -> machine/{id}/telemetry
- RESTOCKS -> machine/{id}/telemetry
- SENSOR_READINGS -> machine/{id}/telemetry
"""

import json
import random
import time
import uuid
import datetime
import argparse
import sys
import copy
import threading
from pathlib import Path

# Safe UTF-8 output formatting for Windows terminal
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import paho.mqtt.client as mqtt

CONFIG_PATH = Path(__file__).parent / "fleet_config.json"

def load_fleet_config():
    if not CONFIG_PATH.exists():
        print(f"[ERROR] Fleet config file not found at {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

PAYMENT_METHODS = ["NFC_TAP_APPLE_PAY", "NFC_TAP_GOOGLE_PAY", "CREDIT_CARD_CHIP", "QR_CODE_MOBILE"]

def create_mqtt_client():
    client_id = f"IntelliVend_FleetSim_{random.randint(1000, 9999)}"
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        client = mqtt.Client(client_id=client_id)
    return client

def simulate_machine(machine, slots_template, mqtt_client, broker, topic_template, max_events_per_machine=None):
    machine_id = machine["id"]
    topic = topic_template.format(id=machine_id)
    slots = copy.deepcopy(slots_template)

    event_count = 0
    while True:
        # Determine event type to emit: 70% PURCHASE, 20% SENSOR_READING, 10% RESTOCK (or on empty)
        available_slots = [s for s in slots if s["stock"] > 0]
        event_roll = random.random()

        if not available_slots or event_roll < 0.10:
            # RESTOCK EVENT
            for s in slots:
                s["stock"] = s["max_capacity"]
            payload = {
                "event_type": "RESTOCK",
                "transaction_id": f"RST-{uuid.uuid4().hex[:8].upper()}",
                "machine_id": machine_id,
                "machine_name": machine["name"],
                "slots_refilled": len(slots),
                "total_stock_capacity": sum(s["max_capacity"] for s in slots),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        elif event_roll < 0.30:
            # SENSOR_READING EVENT
            payload = {
                "event_type": "SENSOR_READING",
                "machine_id": machine_id,
                "machine_name": machine["name"],
                "chiller_temperature_c": round(random.uniform(3.2, 4.4), 1),
                "door_status": "CLOSED",
                "cash_canister_percent": random.randint(30, 92),
                "signal_strength_dbm": random.randint(-75, -50),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        else:
            # PURCHASE EVENT
            slot = random.choice(available_slots)
            slot["stock"] -= 1
            transaction_id = f"TX-{uuid.uuid4().hex[:8].upper()}"

            payload = {
                "event_type": "PURCHASE",
                "transaction_id": transaction_id,
                "machine_id": machine_id,
                "slot_id": slot["slot_id"],
                "product_id": slot["product_id"],
                "product_name": slot["product_name"],
                "price": slot["price"],
                "remaining_stock": slot["stock"],
                "max_capacity": slot["max_capacity"],
                "stock_percentage": round((slot["stock"] / slot["max_capacity"]) * 100, 1),
                "payment_method": random.choice(PAYMENT_METHODS),
                "status": "SUCCESS",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

        # Publish to MQTT topic
        try:
            mqtt_client.publish(topic, json.dumps(payload), qos=1)
            pub_status = "Published to MQTT"
        except Exception as e:
            pub_status = f"Local Error ({e})"

        event_count += 1
        print(f"[{machine_id}] {payload['event_type']} -> {topic} | Details: {payload.get('product_name', payload.get('chiller_temperature_c', 'Refilled'))} | Status: {pub_status}")

        if max_events_per_machine and event_count >= max_events_per_machine:
            break

        time.sleep(random.uniform(0.3, 1.0))

def run_fleet_simulator(max_events=None, override_broker=None):
    config = load_fleet_config()
    mqtt_config = config["mqtt"]
    broker = override_broker or mqtt_config["broker"]
    port = mqtt_config["port"]
    topic_template = mqtt_config["topic_template"]
    machines = config["machines"]
    default_slots = config["default_slots"]

    print("=" * 70)
    print(f"🤖 INTELLIVEND FLEET SIMULATOR (10 VENDING NODES)")
    print(f"🌐 MQTT Broker: tcp://{broker}:{port}")
    print(f"📡 Fleet Machines: {[m['id'] for m in machines]}")
    print("=" * 70)

    client = create_mqtt_client()
    try:
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        print(f"[OK] Connected to MQTT Broker [{broker}:{port}] successfully!\n")
    except Exception as e:
        print(f"[WARN] MQTT Connection error: {e}")

    threads = []
    events_per_m = (max_events // len(machines)) if max_events else None

    for m in machines:
        t = threading.Thread(
            target=simulate_machine,
            args=(m, default_slots, client, broker, topic_template, events_per_m),
            daemon=True
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    client.loop_stop()
    client.disconnect()
    print("[COMPLETE] Fleet simulation batch completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IntelliVend 10-Machine Fleet Simulator")
    parser.add_argument("--events", type=int, default=None, help="Total number of events across fleet before exiting")
    parser.add_argument("--broker", type=str, default=None, help="Override MQTT broker host")
    args = parser.parse_args()

    run_fleet_simulator(max_events=args.events, override_broker=args.broker)
