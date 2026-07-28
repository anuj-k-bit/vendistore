#!/usr/bin/env python3
"""
IntelliVend MQTT Event Subscriber Test Client
Subscribes to telemetry topics `machine/+/events` and displays incoming JSON payloads.
"""

import json
import argparse
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc, properties=None):
    print("[SUBSCRIBER] Connected to MQTT Broker! Subscribing to topic pattern: 'machine/+/events'...")
    client.subscribe("machine/+/events", qos=1)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        print("\n" + "=" * 60)
        print(f"[RECEIVED EVENT] Topic: '{msg.topic}'")
        print(f"  Machine: {data.get('machine_id')} | TX: {data.get('transaction_id')}")
        print(f"  Slot: {data.get('slot_id')} | Product: {data.get('product_name')}")
        print(f"  Price: ${data.get('price'):.2f} | Payment: {data.get('payment_method')}")
        print(f"  Remaining Stock: {data.get('remaining_stock')}/{data.get('max_capacity')} ({data.get('stock_percentage')}%)")
        print(f"  Timestamp: {data.get('timestamp')}")
        print("=" * 60)
    except Exception as e:
        print(f"[RAW MSG] {msg.topic}: {msg.payload.decode('utf-8')}")

def main():
    parser = argparse.ArgumentParser(description="MQTT Subscriber for IntelliVend Events")
    parser.add_argument("--broker", type=str, default="broker.emqx.io", help="MQTT Broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT Broker port")
    args = parser.parse_args()

    client_id = f"IntelliVend_Subscriber_{hash(args.broker) % 10000}"
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        client = mqtt.Client(client_id=client_id)

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[CONNECTING] Connecting to MQTT broker at {args.broker}:{args.port}...")
    client.connect(args.broker, args.port, 60)
    
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[STOPPED] Subscriber stopped.")

if __name__ == "__main__":
    main()
