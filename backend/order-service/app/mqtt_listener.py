import logging
import json
import os
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrderService_MQTT")

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

def process_purchase_event_direct(payload: dict):
    """Publish purchase event to MQTT broker so inventory-service receives stock deduction."""
    try:
        topic = f"machine/{payload['machine_id']}/events"
        client_id = f"OrderSvc_Pub_{payload['transaction_id']}"
        
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        except AttributeError:
            client = mqtt.Client(client_id=client_id)

        client.connect(MQTT_BROKER, MQTT_PORT, 30)
        client.publish(topic, json.dumps(payload), qos=1)
        client.disconnect()
        logger.info(f"📡 Dispatched MQTT Purchase Event to '{topic}' for TX {payload['transaction_id']}")
    except Exception as e:
        logger.warning(f"Failed to publish MQTT purchase event: {e}")
