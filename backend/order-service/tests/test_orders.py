import pytest
import unittest.mock as mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

service_dir = str(Path(__file__).parent.parent.resolve())
if service_dir in sys.path:
    sys.path.remove(service_dir)
sys.path.insert(0, service_dir)

from app.main import app
from app.database import Base, get_db
from app.models import OrderRecord

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_orders.db"

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
    yield
    db = TestingSessionLocal()
    db.query(OrderRecord).delete()
    db.commit()
    db.close()
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

@mock.patch("httpx.Client.get")
@mock.patch("app.mqtt_listener.process_purchase_event_direct")
def test_create_order_success(mock_mqtt, mock_get):
    # Mock inventory service response returning stock > 0
    mock_get.return_value = mock.Mock(
        status_code=200,
        json=lambda: {
            "machine_id": "VM-101",
            "slots": [
                {
                    "slot_id": "A1",
                    "product_name": "Nitro Cold Brew",
                    "price": 4.50,
                    "current_stock": 10,
                    "max_capacity": 15
                }
            ]
        }
    )

    payload = {
        "machine_id": "VM-101",
        "slot_id": "A1",
        "payment_method": "NFC_TAP_APPLE_PAY"
    }

    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["machine_id"] == "VM-101"
    assert data["slot_id"] == "A1"
    assert data["product_name"] == "Nitro Cold Brew"
    assert data["price"] == 4.50
    assert data["status"] == "SUCCESS"
    assert data["order_id"].startswith("ORD-")

@mock.patch("httpx.Client.get")
def test_create_order_empty_slot_rejected(mock_get):
    """VERIFY EMPTY SLOT IS REJECTED WITH 400 BAD REQUEST"""
    # Mock inventory service response returning stock = 0
    mock_get.return_value = mock.Mock(
        status_code=200,
        json=lambda: {
            "machine_id": "VM-101",
            "slots": [
                {
                    "slot_id": "B1",
                    "product_name": "Dragonfruit Sparkling Water",
                    "price": 2.50,
                    "current_stock": 0,
                    "max_capacity": 12
                }
            ]
        }
    )

    payload = {
        "machine_id": "VM-101",
        "slot_id": "B1",
        "payment_method": "CREDIT_CARD"
    }

    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    assert "empty / out of stock" in error_detail.lower()

@mock.patch("httpx.Client.get")
def test_create_order_nonexistent_slot_returns_404(mock_get):
    mock_get.return_value = mock.Mock(
        status_code=200,
        json=lambda: {
            "machine_id": "VM-101",
            "slots": [
                {"slot_id": "A1", "current_stock": 5}
            ]
        }
    )

    payload = {
        "machine_id": "VM-101",
        "slot_id": "Z99",
        "payment_method": "NFC_TAP"
    }

    response = client.post("/orders", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
