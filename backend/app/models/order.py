from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Index, UniqueConstraint, String, Column
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .product import Product
    from .company import Company
    from .branch import Branch


class OrderStatus(str, Enum):
    """Estados posibles de un pedido."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Métodos de pago soportados."""
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    OTHER = "other"


class PaymentStatus(str, Enum):
    """Estados de un pago."""
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


class Payment(SQLModel, table=True):
    """
    Modelo de Pago - Registra la transacción financiera de un pedido.
    """
    __tablename__ = "payments"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", nullable=False)
    
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    method: PaymentMethod = Field(sa_column=Column(String))
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, sa_column=Column(String, default=PaymentStatus.PENDING))
    
    transaction_id: Optional[str] = Field(default=None, max_length=100)  # ID de pasarela externa si aplica
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones
    order: "Order" = Relationship(back_populates="payments")


class OrderItem(SQLModel, table=True):
    """
    Modelo de Item de Pedido - Líneas individuales de un pedido.
    """
    __tablename__ = "order_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", nullable=False)
    product_id: int = Field(foreign_key="products.id", nullable=False)

    quantity: Decimal = Field(max_digits=10, decimal_places=2)
    unit_price: Decimal = Field(max_digits=12, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    subtotal: Decimal = Field(max_digits=12, decimal_places=2)
    
    notes: Optional[str] = Field(default=None, max_length=255)

    # Relaciones
    order: "Order" = Relationship(back_populates="items")
    product: "Product" = Relationship()

    @property
    def product_name(self) -> str:
        return self.product.name if self.product else "Desconocido"


class Order(SQLModel, table=True):
    """
    Modelo de Pedido - Cabecera principal del pedido.
    
    Maneja el total, estado, y vinculación con empresa/sucursal.
    Multi-tenant: company_id y branch_id obligatorios.
    """
    __tablename__ = "orders"

    __table_args__ = (
        Index("idx_orders_company_status", "company_id", "status"),
        Index("idx_orders_branch_date", "branch_id", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    branch_id: int = Field(foreign_key="branches.id", index=True, nullable=False)
    
    # Número consecutivo único por sucursal (Generado por OrderCounter)
    order_number: str = Field(max_length=20, index=True, nullable=False)
    
    status: OrderStatus = Field(default=OrderStatus.PENDING, sa_column=Column(String, default=OrderStatus.PENDING))
    
    # Totales
    subtotal: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    tax_total: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    total: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    
    # Información del cliente (opcional para MVP)
    customer_notes: Optional[str] = Field(default=None, max_length=500)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones
    items: List[OrderItem] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    payments: List[Payment] = Relationship(back_populates="order")
    company: "Company" = Relationship()
    branch: "Branch" = Relationship()
