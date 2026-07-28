import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class Machine(Base):
    __tablename__ = "machines"

    id = Column(String, primary_key=True, index=True) # e.g. "VM-101"
    name = Column(String, nullable=False, default="IntelliVend Terminal")
    location = Column(String, nullable=True)
    status = Column(String, default="Operational")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    slots = relationship("Slot", back_populates="machine", cascade="all, delete-orphan")

class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, ForeignKey("machines.id"), nullable=False, index=True)
    slot_id = Column(String, nullable=False) # e.g. "A1"
    product_id = Column(String, nullable=True)
    product_name = Column(String, nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    current_stock = Column(Integer, nullable=False, default=10)
    max_capacity = Column(Integer, nullable=False, default=15)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    machine = relationship("Machine", back_populates="slots")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    machine_id = Column(String, index=True)
    slot_id = Column(String)
    product_name = Column(String)
    price = Column(Float)
    payment_method = Column(String)
    created_at = Column(DateTime, default=utc_now)
