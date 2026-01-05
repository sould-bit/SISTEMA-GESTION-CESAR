from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from app.models.cash_closure import CashClosureStatus

class CashOpen(BaseModel):
    initial_cash: Decimal

class CashClose(BaseModel):
    real_cash: Decimal
    real_card: Decimal
    real_transfer: Decimal
    notes: Optional[str] = None

class CashClosureRead(BaseModel):
    id: int
    user_id: int
    branch_id: int
    status: CashClosureStatus
    opened_at: datetime
    closed_at: Optional[datetime] = None
    
    initial_cash: Decimal
    
    expected_cash: Decimal
    expected_card: Decimal
    expected_transfer: Decimal
    expected_total: Decimal
    
    real_cash: Decimal
    real_card: Decimal
    real_transfer: Decimal
    real_total: Decimal
    
    difference: Decimal
    notes: Optional[str] = None

    class Config:
        from_attributes = True
