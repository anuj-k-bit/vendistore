from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime

class OrderCreate(BaseModel):
    machine_id: str
    slot_id: str
    payment_method: Optional[str] = "NFC_TAP_APPLE_PAY"

class OrderResponse(BaseModel):
    id: int
    order_id: str
    machine_id: str
    slot_id: str
    product_name: str
    price: float
    payment_method: str
    status: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
