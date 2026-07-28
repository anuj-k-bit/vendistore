import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class OrderRecord(Base):
    __tablename__ = "order_records"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True) # e.g. "ORD-98214"
    machine_id = Column(String, index=True)
    slot_id = Column(String)
    product_name = Column(String)
    price = Column(Float)
    payment_method = Column(String, default="NFC_TAP")
    status = Column(String, default="SUCCESS") # "SUCCESS", "REJECTED_EMPTY_SLOT", "FAILED"
    created_at = Column(DateTime, default=utc_now)
