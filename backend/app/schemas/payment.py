from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from app.models.payment import PaymentMethod, PaymentStatus

class PaymentBase(BaseModel):
    amount: Decimal
    method: PaymentMethod
    transaction_id: Optional[str] = None

class PaymentCreate(PaymentBase):
    order_id: int

class PaymentRead(PaymentBase):
    id: int
    company_id: int
    branch_id: int
    order_id: int
    status: PaymentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
