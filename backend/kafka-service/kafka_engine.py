#!/usr/bin/env python3
"""
IntelliVend Kafka Event Streaming Engine & MQTT Bridge
Provides durable event log management for Kafka topics:
- `purchases`
- `restocks`
- `sensor-readings`

Includes consumer group offset tracking and MQTT-to-Kafka streaming bridge.
"""

import json
import os
import time
import logging
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Kafka_Engine")

DATA_DIR = Path(__file__).parent / "kafka_data"
DATA_DIR.mkdir(exist_ok=True)

TOPICS = ["purchases", "restocks", "sensor-readings"]

class KafkaBrokerEngine:
    """Durable Kafka Log Engine storing topic partitions and consumer group offsets."""
    def __init__(self):
        self._lock = threading.Lock()
        self.topics: Dict[str, List[Dict[str, Any]]] = {topic: [] for topic in TOPICS}
        self.consumer_offsets: Dict[str, Dict[str, int]] = {} # group_id -> {topic: offset}
        self._load_persisted_logs()

    def _load_persisted_logs(self):
        with self._lock:
            for topic in TOPICS:
                log_file = DATA_DIR / f"{topic}.log"
                if log_file.exists():
                    try:
                        with open(log_file, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    msg = json.loads(line)
                                    self.topics[topic].append(msg)
                    except Exception as e:
                        logger.error(f"Error reading log file for {topic}: {e}")

    def produce(self, topic: str, key: str, value: Dict[str, Any]) -> int:
        if topic not in self.topics:
            raise ValueError(f"Unknown topic: {topic}. Supported: {TOPICS}")

        with self._lock:
            offset = len(self.topics[topic])
            record = {
                "topic": topic,
                "partition": 0,
                "offset": offset,
                "key": key,
                "timestamp": int(time.time() * 1000),
                "value": value
            }
            self.topics[topic].append(record)

            # Append to durable log file
            log_file = DATA_DIR / f"{topic}.log"
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
            except Exception as e:
                logger.error(f"Error persisting to {log_file}: {e}")

            logger.info(f"📥 [KAFKA PRODUCER] Topic: '{topic}' | Offset: {offset} | Key: {key}")
            return offset

    def consume(self, topic: str, group_id: str, max_messages: int = 10) -> List[Dict[str, Any]]:
        if topic not in self.topics:
            return []

        with self._lock:
            if group_id not in self.consumer_offsets:
                self.consumer_offsets[group_id] = {t: 0 for t in TOPICS}

            current_offset = self.consumer_offsets[group_id].get(topic, 0)
            available_records = self.topics[topic][current_offset:current_offset + max_messages]

            if available_records:
                new_offset = current_offset + len(available_records)
                self.consumer_offsets[group_id][topic] = new_offset
                logger.info(f"📤 [KAFKA CONSUMER] Group '{group_id}' consumed {len(available_records)} msg(s) from '{topic}' (Offset {current_offset} -> {new_offset})")

            return available_records

    def get_topic_metadata(self) -> Dict[str, Any]:
        with self._lock:
            return {
                topic: {
                    "partition_count": 1,
                    "total_messages": len(self.topics[topic]),
                    "latest_offset": max(0, len(self.topics[topic]) - 1)
                }
                for topic in TOPICS
            }

# Singleton Kafka Broker Engine Instance
kafka_engine = KafkaBrokerEngine()

class MQTT_Kafka_Bridge:
    """Subscribes to MQTT machine/+/telemetry and produces messages into Kafka topics."""
    def __init__(self, mqtt_broker: str = "broker.emqx.io", mqtt_port: int = 1883):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.client = None

    def start(self):
        client_id = f"IntelliVend_MQTT_Kafka_Bridge_{int(time.time())}"
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        except AttributeError:
            self.client = mqtt.Client(client_id=client_id)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        def run():
            try:
                logger.info(f"🌐 MQTT-Kafka Bridge connecting to tcp://{self.mqtt_broker}:{self.mqtt_port}...")
                self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
                self.client.loop_forever()
            except Exception as e:
                logger.warning(f"Bridge connection warning: {e}")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logger.info("📡 MQTT-Kafka Bridge Connected to MQTT Broker! Subscribing to 'machine/+/telemetry'...")
        client.subscribe("machine/+/telemetry", qos=1)
        client.subscribe("machine/+/events", qos=1)

    def on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8")
            event_data = json.loads(payload_str)
            event_type = event_data.get("event_type", "PURCHASE")
            machine_id = event_data.get("machine_id", "UNKNOWN")

            # Route to Kafka topic
            if event_type == "PURCHASE":
                kafka_engine.produce(topic="purchases", key=machine_id, value=event_data)
            elif event_type == "RESTOCK":
                kafka_engine.produce(topic="restocks", key=machine_id, value=event_data)
            elif event_type == "SENSOR_READING":
                kafka_engine.produce(topic="sensor-readings", key=machine_id, value=event_data)
            else:
                kafka_engine.produce(topic="purchases", key=machine_id, value=event_data)
        except Exception as e:
            logger.error(f"Bridge failed to route MQTT msg to Kafka: {e}")

if __name__ == "__main__":
    bridge = MQTT_Kafka_Bridge()
    bridge.start()
    print("Kafka Engine & MQTT Bridge running... Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Kafka Engine stopped.")
