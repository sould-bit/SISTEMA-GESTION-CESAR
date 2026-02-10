
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.order import Order, OrderStatus
from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.modifier import ProductModifierBase

# --- Order Item Schemas ---

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0, description="Cantidad del producto")
    # unit_price y tax se calculan en backend, pero permitimos override opcional si es necesario
    # para casos especiales, aunque por defecto debería venir del producto.
    # Por ahora simple: cantidad y producto.
    notes: Optional[str] = None
    modifiers: Optional[List[int]] = []
    removed_ingredients: Optional[List[str]] = []

class OrderItemUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0, description="Nueva cantidad")
    notes: Optional[str] = None
    modifiers: Optional[List[int]] = None # IDs de modificadores
    removed_ingredients: Optional[List[str]] = None

# Define minimal read schema for nested usage
class OrderItemModifierRead(BaseModel):
    id: int
    modifier_id: int
    quantity: int
    unit_price: Decimal
    # Nested info from ProductModifier
    modifier: Optional[ProductModifierBase] = None

    model_config = ConfigDict(from_attributes=True)

class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str # Helper para frontend
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal
    notes: Optional[str] = None
    removed_ingredients: List[str] = []
    modifiers: List[OrderItemModifierRead] = []
    
    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)

# --- Order Schemas ---

class OrderCreate(BaseModel):
    branch_id: int
    items: List[OrderItemCreate]
    customer_notes: Optional[str] = None
    
    # Pagos opcionales al crear (ej: pago completo en caja o pedido web pagado)
    payments: Optional[List[PaymentCreate]] = None

    # CRM Fields (V5.0)
    # CRM Fields (V5.0)
    customer_id: Optional[int] = None
    delivery_type: str = "dine_in" # dine_in, takeaway, delivery
    delivery_address: Optional[str] = None
    delivery_notes: Optional[str] = None

    # Nuevos campos V5.1: Datos de cliente para domicilio
    delivery_customer_name: Optional[str] = None
    delivery_customer_phone: Optional[str] = None

    # Mesas (V7.0)
    table_id: Optional[int] = None

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

    # CRM Fields
    customer_id: Optional[int] = None
    delivery_type: str = "dine_in"
    delivery_address: Optional[str] = None
    delivery_notes: Optional[str] = None
    delivery_fee: Decimal = Decimal("0.00")
    
    delivery_customer_name: Optional[str] = None
    delivery_customer_phone: Optional[str] = None
    
    table_id: Optional[int] = None
    created_by_name: Optional[str] = None
    
    # Cancellation fields (V8.0)
    cancellation_status: Optional[str] = None  # pending, approved, denied
    cancellation_reason: Optional[str] = None
    cancellation_requested_at: Optional[datetime] = None
    cancellation_denied_reason: Optional[str] = None  # Why cancellation was denied
    
    items: List[OrderItemRead] = []
    payments: List[PaymentRead] = []
    
    model_config = ConfigDict(from_attributes=True)


class OrderCancelRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=255)

class OrderCancelProcess(BaseModel):
    approved: bool
    notes: Optional[str] = None

