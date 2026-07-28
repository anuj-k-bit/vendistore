import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add app directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.database import Base, get_db
from app.models import Machine, Slot, Transaction
from app.mqtt_listener import process_purchase_event

# In-memory SQLite DB for isolated unit testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_inventory.db"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Clean previous records
    db.query(Slot).delete()
    db.query(Machine).delete()
    db.query(Transaction).delete()
    db.commit()
    
    # Seed VM-101 for testing
    vm = Machine(id="VM-101", name="Downtown Tech Hub", location="450 Market St")
    db.add(vm)
    
    s1 = Slot(machine_id="VM-101", slot_id="A1", product_name="Nitro Cold Brew", price=4.50, current_stock=10, max_capacity=15)
    s2 = Slot(machine_id="VM-101", slot_id="A2", product_name="Matcha Green Tea", price=4.00, current_stock=12, max_capacity=15)
    db.add_all([s1, s2])
    db.commit()
    db.close()
    
    yield
    
    db = TestingSessionLocal()
    db.query(Slot).delete()
    db.query(Machine).delete()
    db.query(Transaction).delete()
    db.commit()
    db.close()
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

def test_get_machine_inventory():
    response = client.get("/machines/VM-101/inventory")
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "VM-101"
    assert data["total_slots"] == 2
    assert data["total_items"] == 22
    assert len(data["slots"]) == 2
    assert data["slots"][0]["slot_id"] == "A1"
    assert data["slots"][0]["current_stock"] == 10

def test_purchase_event_decrements_stock_in_db():
    purchase_payload = {
        "event_type": "PURCHASE",
        "transaction_id": "TX-TEST-001",
        "machine_id": "VM-101",
        "slot_id": "A1",
        "product_name": "Nitro Cold Brew",
        "price": 4.50,
        "remaining_stock": 9,
        "max_capacity": 15,
        "payment_method": "NFC_TAP_APPLE_PAY"
    }
    
    # Process event using test database session
    db = TestingSessionLocal()
    process_purchase_event(purchase_payload, db_session=db)
    db.close()
    
    # Query GET endpoint to verify stock was updated to 9
    response = client.get("/machines/VM-101/inventory")
    assert response.status_code == 200
    data = response.json()
    
    slot_a1 = next(s for s in data["slots"] if s["slot_id"] == "A1")
    assert slot_a1["current_stock"] == 9

def test_restock_machine():
    restock_resp = client.post("/machines/VM-101/restock")
    assert restock_resp.status_code == 200
    r_data = restock_resp.json()
    assert r_data["machine_id"] == "VM-101"
    assert r_data["slots_restocked"] == 2
    
    # Check inventory is refilled to 15 + 15 = 30
    inv_resp = client.get("/machines/VM-101/inventory")
    data = inv_resp.json()
    assert data["slots"][0]["current_stock"] == 15
    assert data["slots"][1]["current_stock"] == 15

def test_get_nonexistent_machine_returns_404():
    response = client.get("/machines/VM-999/inventory")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
