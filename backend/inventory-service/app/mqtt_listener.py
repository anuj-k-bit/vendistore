import json
import logging
import threading
import time
import os
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Machine, Slot, Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MQTT_Listener")

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = "machine/+/events"

def process_purchase_event(event_data: dict, db_session: Session = None):
    """Process incoming purchase event and update database inventory."""
    db: Session = db_session or SessionLocal()
    should_close = db_session is None
    try:
        machine_id = event_data.get("machine_id", "VM-101")
        slot_id = event_data.get("slot_id")
        product_name = event_data.get("product_name", "Unknown Product")
        product_id = event_data.get("product_id")
        price = float(event_data.get("price", 0.0))
        remaining_stock = event_data.get("remaining_stock")
        max_cap = int(event_data.get("max_capacity", 15))
        tx_id = event_data.get("transaction_id", f"TX-LOCAL-{int(time.time())}")
        payment_method = event_data.get("payment_method", "NFC_TAP")

        # 1. Ensure Machine exists
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            machine = Machine(
                id=machine_id,
                name=f"Vending Terminal {machine_id}",
                location="Automated Fleet Node",
                status="Operational"
            )
            db.add(machine)
            db.commit()

        # 2. Find or Create Slot
        slot = db.query(Slot).filter(Slot.machine_id == machine_id, Slot.slot_id == slot_id).first()
        if slot:
            if remaining_stock is not None:
                slot.current_stock = max(0, remaining_stock)
            else:
                slot.current_stock = max(0, slot.current_stock - 1)
            slot.product_name = product_name
            slot.price = price
        else:
            initial_stock = max(0, remaining_stock) if remaining_stock is not None else 9
            slot = Slot(
                machine_id=machine_id,
                slot_id=slot_id,
                product_id=product_id,
                product_name=product_name,
                price=price,
                current_stock=initial_stock,
                max_capacity=max_cap
            )
            db.add(slot)

        # 3. Record Audit Transaction
        existing_tx = db.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
        if not existing_tx:
            tx = Transaction(
                transaction_id=tx_id,
                machine_id=machine_id,
                slot_id=slot_id,
                product_name=product_name,
                price=price,
                payment_method=payment_method
            )
            db.add(tx)

        db.commit()
        logger.info(
            f"✅ DB UPDATED [{machine_id}] Slot {slot_id} ({product_name}) -> Stock decremented to {slot.current_stock}/{slot.max_capacity} | TX: {tx_id}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ DB update error processing event: {e}")
    finally:
        if should_close:
            db.close()

def on_connect(client, userdata, flags, rc, properties=None):
    logger.info(f"📡 MQTT Connected to broker [{MQTT_BROKER}:{MQTT_PORT}]. Subscribing to '{TOPIC}'...")
    client.subscribe(TOPIC, qos=1)

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        event_data = json.loads(payload_str)
        if event_data.get("event_type") == "PURCHASE":
            process_purchase_event(event_data)
    except Exception as e:
        logger.error(f"Error parsing MQTT message from {msg.topic}: {e}")

def start_mqtt_listener():
    client_id = f"IntelliVend_Inventory_Svc_{int(time.time())}"
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        client = mqtt.Client(client_id=client_id)

    client.on_connect = on_connect
    client.on_message = on_message

    def run():
        try:
            logger.info(f"Connecting to MQTT broker tcp://{MQTT_BROKER}:{MQTT_PORT}...")
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.loop_forever()
        except Exception as e:
            logger.warning(f"MQTT Listener connection error: {e}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return client
