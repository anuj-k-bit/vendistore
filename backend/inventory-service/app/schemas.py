from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime

class SlotBase(BaseModel):
    slot_id: str
    product_id: Optional[str] = None
    product_name: str
    price: float
    current_stock: int
    max_capacity: int

class SlotResponse(SlotBase):
    id: int
    machine_id: str
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class MachineInventoryResponse(BaseModel):
    machine_id: str
    name: str
    location: Optional[str] = None
    status: str
    total_slots: int
    total_items: int
    slots: List[SlotResponse]

    model_config = ConfigDict(from_attributes=True)

class RestockResponse(BaseModel):
    message: str
    machine_id: str
    slots_restocked: int
    total_stock_now: int

class PurchaseEventPayload(BaseModel):
    event_type: str
    transaction_id: str
    machine_id: str
    slot_id: str
    product_id: Optional[str] = None
    product_name: str
    price: float
    remaining_stock: int
    max_capacity: Optional[int] = 15
    payment_method: Optional[str] = "UNKNOWN"
    status: Optional[str] = "SUCCESS"
    timestamp: Optional[str] = None
