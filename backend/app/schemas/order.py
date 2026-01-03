from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.order import OrderStatus, PaymentMethod, PaymentStatus

# --- Order Item Schemas ---

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0, description="Cantidad del producto")
    # unit_price y tax se calculan en backend, pero permitimos override opcional si es necesario
    # para casos especiales, aunque por defecto debería venir del producto.
    # Por ahora simple: cantidad y producto.
    notes: Optional[str] = None

class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str # Helper para frontend
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- Payment Schemas ---

class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    method: PaymentMethod
    transaction_id: Optional[str] = None

class PaymentRead(BaseModel):
    id: int
    amount: Decimal
    method: PaymentMethod
    status: PaymentStatus
    created_at: datetime

    class Config:
        from_attributes = True

# --- Order Schemas ---

class OrderCreate(BaseModel):
    branch_id: int
    items: List[OrderItemCreate]
    customer_notes: Optional[str] = None
    
    # Pagos opcionales al crear (ej: pago completo en caja o pedido web pagado)
    payments: Optional[List[PaymentCreate]] = None

    @field_validator('items')
    def validate_items_params(cls, v):
        if not v:
            raise ValueError('El pedido debe tener al menos un item')
        return v

class OrderUpdateStatus(BaseModel):
    status: OrderStatus

class OrderRead(BaseModel):
    id: int
    order_number: str
    branch_id: int
    company_id: int
    status: OrderStatus
    
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    
    customer_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    items: List[OrderItemRead] = []
    payments: List[PaymentRead] = []
    
    class Config:
        from_attributes = True
