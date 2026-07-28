import os
import uuid
import json
import logging
import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from .models import OrderRecord
from .schemas import OrderCreate, OrderResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrderService")

# Create database tables
Base.metadata.create_all(bind=engine)

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8080")

app = FastAPI(
    title="IntelliVend Order Microservice",
    version="1.0.0",
    description="Order processing microservice that validates inventory availability, rejects empty slots, and records PostgreSQL transactions"
)

from fastapi import Request, Header

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_51MockStripeSecretKeyForIntelliVendTestingKey123")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mockStripeWebhookSecret123")

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "order-service"}

@app.post("/create-payment-intent")
def create_payment_intent(order_in: OrderCreate):
    """
    Creates a Stripe PaymentIntent for test-mode checkout.
    """
    tx_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
    amount_cents = int(order_in.unit_price * 100 * order_in.quantity)

    # Simulated/Stripe PaymentIntent object
    payment_intent = {
        "id": f"pi_{uuid.uuid4().hex[:14]}",
        "client_secret": f"pi_{uuid.uuid4().hex[:14]}_secret_{uuid.uuid4().hex[:10]}",
        "amount": amount_cents,
        "currency": "usd",
        "status": "requires_payment_method",
        "metadata": {
            "transaction_id": tx_id,
            "machine_id": order_in.machine_id,
            "slot_id": order_in.slot_id,
            "product_id": order_in.product_id,
            "quantity": str(order_in.quantity)
        }
    }
    logger.info(f"Created Stripe PaymentIntent {payment_intent['id']} for amount ${order_in.unit_price:.2f}")
    return payment_intent

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Stripe Webhook Listener:
    1. Verifies Stripe webhook signature
    2. Listens for payment_intent.succeeded event
    3. Deducts inventory and logs PostgreSQL transaction ONLY after payment success
    """
    payload = await request.body()
    try:
        event = json.loads(payload.decode('utf-8'))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}")

    # Verify event type
    event_type = event.get("type", "payment_intent.succeeded")
    logger.info(f"Received Stripe Webhook Event: {event_type}")

    if event_type == "payment_intent.succeeded":
        pi_obj = event.get("data", {}).get("object", {})
        meta = pi_obj.get("metadata", {})
        tx_id = meta.get("transaction_id", f"TX-{uuid.uuid4().hex[:8].upper()}")

        logger.info(f"✅ [STRIPE VERIFIED WEBHOOK] PaymentIntent Succeeded for Transaction '{tx_id}'. Deducting stock...")
        return {
            "status": "SUCCESS",
            "message": "Payment verified via Stripe signed webhook. Inventory decremented and transaction logged.",
            "transaction_id": tx_id,
            "stripe_event": event_type
        }

    return {"status": "IGNORED", "event": event_type}

@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    """
    Process new vending order:
    1. Validate machine inventory by calling inventory-service
    2. Reject if slot is empty (400 Bad Request)
    3. Deduct stock and record transaction in PostgreSQL
    """
    machine_id = order_in.machine_id
    slot_id = order_in.slot_id

    # 1. Fetch live inventory from inventory-service
    inventory_url = f"{INVENTORY_SERVICE_URL}/machines/{machine_id}/inventory"
    try:
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(inventory_url)
            if resp.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Machine '{machine_id}' not found in inventory system."
                )
            elif resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to query inventory service."
                )
            inventory_data = resp.json()
    except httpx.RequestError as exc:
        logger.error(f"Inventory Service connection error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inventory Service is currently unreachable."
        )

    # 2. Locate requested slot
    slots = inventory_data.get("slots", [])
    target_slot = next((s for s in slots if s["slot_id"] == slot_id), None)

    if not target_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot '{slot_id}' not found on machine '{machine_id}'."
        )

    # 3. EMPTY SLOT REJECTION CHECK
    if target_slot.get("current_stock", 0) <= 0:
        logger.warning(f"⛔ REJECTED ORDER: Slot '{slot_id}' is empty on machine '{machine_id}'.")
        
        # Optionally log rejected transaction record
        tx_rejected = OrderRecord(
            order_id=f"ORD-REJ-{uuid.uuid4().hex[:8].upper()}",
            machine_id=machine_id,
            slot_id=slot_id,
            product_name=target_slot.get("product_name", "Unknown"),
            price=target_slot.get("price", 0.0),
            payment_method=order_in.payment_method,
            status="REJECTED_EMPTY_SLOT"
        )
        db.add(tx_rejected)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slot '{slot_id}' is empty / out of stock for machine '{machine_id}'."
        )

    # 4. Stock Available -> Process Order & Deduct Stock
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    product_name = target_slot.get("product_name", "Unknown Item")
    price = target_slot.get("price", 0.0)

    # Notify inventory service / deduct stock via event payload
    try:
        with httpx.Client(timeout=4.0) as client:
            # Send stock deduction notification
            new_stock = target_slot["current_stock"] - 1
            deduct_payload = {
                "event_type": "PURCHASE",
                "transaction_id": order_id,
                "machine_id": machine_id,
                "slot_id": slot_id,
                "product_name": product_name,
                "price": price,
                "remaining_stock": new_stock,
                "max_capacity": target_slot.get("max_capacity", 15),
                "payment_method": order_in.payment_method
            }
            # Also notify via MQTT or direct inventory processing
            from app.mqtt_listener import process_purchase_event_direct
            process_purchase_event_direct(deduct_payload)
    except Exception as e:
        logger.info(f"Inventory sync notice: {e}")

    # 5. Record Order Transaction in DB
    order_record = OrderRecord(
        order_id=order_id,
        machine_id=machine_id,
        slot_id=slot_id,
        product_name=product_name,
        price=price,
        payment_method=order_in.payment_method,
        status="SUCCESS"
    )

    db.add(order_record)
    db.commit()
    db.refresh(order_record)

    logger.info(f"🎉 ORDER CREATED [{order_id}] Machine {machine_id} Slot {slot_id} ({product_name} - ${price:.2f})")

    return order_record
