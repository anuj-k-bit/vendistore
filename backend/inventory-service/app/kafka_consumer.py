import time
import logging
import threading
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Add kafka-service directory to sys.path to import kafka_engine
KAFKA_SERVICE_PATH = Path(__file__).parent.parent.parent / "kafka-service"
sys.path.insert(0, str(KAFKA_SERVICE_PATH))

try:
    from kafka_engine import kafka_engine
except ImportError:
    # Fallback import if directory structure varies
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "backend" / "kafka-service"))
    from kafka_engine import kafka_engine

from .database import SessionLocal
from .models import Machine, Slot, Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Kafka_Inventory_Consumer")

GROUP_ID = "inventory-service-group"

def process_kafka_purchase_record(record: dict):
    """Processes a single Kafka purchase event and updates PostgreSQL inventory."""
    event_data = record.get("value", {})
    db: Session = SessionLocal()
    try:
        machine_id = event_data.get("machine_id", "VM-101")
        slot_id = event_data.get("slot_id")
        product_name = event_data.get("product_name", "Unknown Product")
        product_id = event_data.get("product_id")
        price = float(event_data.get("price", 0.0))
        remaining_stock = event_data.get("remaining_stock")
        max_cap = int(event_data.get("max_capacity", 15))
        tx_id = event_data.get("transaction_id", f"TX-KAFKA-{record.get('offset')}")
        payment_method = event_data.get("payment_method", "NFC_TAP")

        # 1. Ensure Machine exists in DB
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            machine = Machine(
                id=machine_id,
                name=f"Vending Terminal {machine_id}",
                location="Fleet Node",
                status="Operational"
            )
            db.add(machine)
            db.commit()

        # 2. Update or Create Slot stock
        if slot_id:
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

        # 3. Save Transaction record
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
        logger.info(f"✅ [KAFKA -> POSTGRES DB] Machine '{machine_id}' Slot '{slot_id}' ({product_name}) -> Stock: {remaining_stock} | Kafka Topic 'purchases' Offset {record.get('offset')}")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error processing Kafka purchase record: {e}")
    finally:
        db.close()

def start_kafka_consumer():
    """Background polling thread that consumes from Kafka topic 'purchases'."""
    def poll_kafka():
        logger.info(f"🚀 Started Kafka Consumer for group '{GROUP_ID}' on topic 'purchases'...")
        while True:
            try:
                records = kafka_engine.consume(topic="purchases", group_id=GROUP_ID, max_messages=20)
                for record in records:
                    process_kafka_purchase_record(record)
            except Exception as e:
                logger.error(f"Kafka polling error: {e}")
            time.sleep(0.5)

    thread = threading.Thread(target=poll_kafka, daemon=True)
    thread.start()
    return thread
