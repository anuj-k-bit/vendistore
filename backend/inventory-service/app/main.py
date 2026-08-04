import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from .database import engine, Base, get_db
from .models import Machine, Slot, Transaction
from .schemas import MachineInventoryResponse, RestockResponse, SlotResponse
from .kafka_consumer import start_kafka_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InventoryService")

# Initialize DB tables
Base.metadata.create_all(bind=engine)

DEFAULT_SLOTS_DATA = [
    {"slot_id": "A1", "product_name": "Nitro Cold Brew", "price": 4.50, "current_stock": 10, "max_capacity": 15},
    {"slot_id": "A2", "product_name": "Matcha Green Tea Latte", "price": 4.00, "current_stock": 12, "max_capacity": 15},
    {"slot_id": "A3", "product_name": "Electrolyte Spark Hydration", "price": 3.25, "current_stock": 8, "max_capacity": 12},
    {"slot_id": "A4", "product_name": "Dark Chocolate Almond Bar", "price": 2.75, "current_stock": 15, "max_capacity": 20},
    {"slot_id": "B1", "product_name": "Dragonfruit Sparkling Water", "price": 2.50, "current_stock": 6, "max_capacity": 12},
    {"slot_id": "B2", "product_name": "Organic Protein Crunch Bar", "price": 3.50, "current_stock": 9, "max_capacity": 15},
    {"slot_id": "B3", "product_name": "Detox Green Juice", "price": 5.00, "current_stock": 7, "max_capacity": 10},
    {"slot_id": "B4", "product_name": "Mango Passion Kombucha", "price": 4.25, "current_stock": 11, "max_capacity": 12},
]

FLEET_MACHINES = [
    {"id": "VM-101", "name": "Downtown Tech Hub", "location": "450 Market St, Floor 1 Lobby"},
    {"id": "VM-102", "name": "Airport Terminal 2", "location": "Gate B14 Concourse"},
    {"id": "VM-103", "name": "Metro Central Station", "location": "Main Mezzanine Platform"},
    {"id": "VM-104", "name": "City General Hospital", "location": "ER Entrance Waiting Area"},
    {"id": "VM-105", "name": "University Student Union", "location": "North Quad Hallway"},
    {"id": "VM-106", "name": "Financial Center Tower", "location": "Floor 28 Break Room"},
    {"id": "VM-107", "name": "Grand Luxury Hotel", "location": "2nd Floor Fitness Atrium"},
    {"id": "VM-108", "name": "Westside Shopping Mall", "location": "Food Court Level 1"},
    {"id": "VM-109", "name": "Northside Innovation Park", "location": "Building 4 Tech Corridor"},
    {"id": "VM-110", "name": "Subway Junction East", "location": "Eastbound Line Platform"}
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed 10 fleet machines in database if not present
    db = next(get_db())
    try:
        for m in FLEET_MACHINES:
            existing = db.query(Machine).filter(Machine.id == m["id"]).first()
            if not existing:
                vm = Machine(id=m["id"], name=m["name"], location=m["location"], status="Operational")
                db.add(vm)
                for s in DEFAULT_SLOTS_DATA:
                    slot = Slot(
                        machine_id=m["id"],
                        slot_id=s["slot_id"],
                        product_name=s["product_name"],
                        price=s["price"],
                        current_stock=s["current_stock"],
                        max_capacity=s["max_capacity"]
                    )
                    db.add(slot)
        db.commit()
        logger.info("Initialized fleet inventory schema for 10 machines (VM-101 to VM-110) in PostgreSQL.")
    except Exception as e:
        logger.error(f"Error seeding fleet database: {e}")
    finally:
        db.close()

    # Start Kafka Consumer Thread
    start_kafka_consumer()
    yield

app = FastAPI(
    title="IntelliVend Kafka Inventory Microservice",
    version="2.0.0",
    description="PostgreSQL inventory manager consuming streaming purchase events from Kafka topic 'purchases'",
    lifespan=lifespan
)

@app.get("/")
def root():
    return {
        "service": "IntelliVend Inventory Microservice",
        "status": "ONLINE",
        "health_check": "/health",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "inventory-service", "event_bus": "KAFKA"}

@app.get("/fleet/inventory")
def get_fleet_inventory_summary(db: Session = Depends(get_db)):
    """Returns inventory status for all 10 fleet machines in PostgreSQL."""
    machines = db.query(Machine).order_by(Machine.id).all()
    fleet_summary = []

    for m in machines:
        slots = db.query(Slot).filter(Slot.machine_id == m.id).order_by(Slot.slot_id).all()
        total_items = sum(s.current_stock for s in slots)
        total_capacity = sum(s.max_capacity for s in slots)
        fleet_summary.append({
            "machine_id": m.id,
            "name": m.name,
            "location": m.location,
            "status": m.status,
            "total_slots": len(slots),
            "total_items": total_items,
            "capacity": total_capacity,
            "stock_percentage": round((total_items / total_capacity) * 100, 1) if total_capacity else 0
        })

    return {
        "fleet_size": len(machines),
        "machines": fleet_summary
    }

@app.get("/machines/{machine_id}/inventory", response_model=MachineInventoryResponse)
def get_machine_inventory(machine_id: str, db: Session = Depends(get_db)):
    """Fetch current stock levels for a specific machine in the 10-node fleet."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID '{machine_id}' not found."
        )

    slots = db.query(Slot).filter(Slot.machine_id == machine_id).order_by(Slot.slot_id).all()
    total_items = sum(s.current_stock for s in slots)

    return MachineInventoryResponse(
        machine_id=machine.id,
        name=machine.name,
        location=machine.location,
        status=machine.status,
        total_slots=len(slots),
        total_items=total_items,
        slots=slots
    )

@app.post("/machines/{machine_id}/restock", response_model=RestockResponse)
def restock_machine(machine_id: str, db: Session = Depends(get_db)):
    """Refill all slots of a machine back to 100% max capacity."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID '{machine_id}' not found."
        )

    slots = db.query(Slot).filter(Slot.machine_id == machine_id).all()
    restocked_count = 0
    total_stock_now = 0

    for slot in slots:
        slot.current_stock = slot.max_capacity
        restocked_count += 1
        total_stock_now += slot.current_stock

    machine.status = "Operational"
    db.commit()

    return RestockResponse(
        message=f"Machine '{machine_id}' successfully restocked.",
        machine_id=machine_id,
        slots_restocked=restocked_count,
        total_stock_now=total_stock_now
    )
