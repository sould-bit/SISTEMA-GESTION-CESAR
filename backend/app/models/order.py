from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Index, UniqueConstraint, String, Column, Numeric, JSON
from sqlmodel import SQLModel, Field, Relationship


if TYPE_CHECKING:
    from .product import Product
    from .company import Company
    from .branch import Branch
    from .payment import Payment
    from .customer import Customer
    from .modifier import OrderItemModifier


class OrderStatus(str, Enum):
    """Estados posibles de un pedido."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem(SQLModel, table=True):
    """
    Modelo de Item de Pedido - Líneas individuales de un pedido.
    """
    __tablename__ = "order_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", nullable=False)
    product_id: int = Field(foreign_key="products.id", nullable=False)

    quantity: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    unit_price: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    tax_amount: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2)))
    subtotal: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    
    notes: Optional[str] = Field(default=None, max_length=255)

    # Relaciones
    order: "Order" = Relationship(back_populates="items")
    product: "Product" = Relationship()
    modifiers: List["OrderItemModifier"] = Relationship(sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    modifiers: List["OrderItemModifier"] = Relationship(sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    # New V9.0: Recipe Customization
    # Almacenamos lista de IDs (Strings o Ints) de ingredientes removidos de la receta base
    removed_ingredients: List[str] = Field(default=[], sa_column=Column(JSON))


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
    subtotal: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2)))
    tax_total: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2)))
    total: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2)))
    
    # CRM & Delivery (V5.0)
    customer_id: Optional[int] = Field(default=None, foreign_key="customers.id", index=True)
    delivery_type: str = Field(default="dine_in", sa_column=Column(String, default="dine_in")) # dine_in, takeaway, delivery, eat_here
    
    # Mesas
    table_id: Optional[int] = Field(default=None, foreign_key="tables.id", index=True)
    
    # Snapshot de Datos de Entrega
    delivery_address: Optional[str] = Field(default=None, description="Dirección snapshot al momento del pedido")
    delivery_notes: Optional[str] = Field(default=None, max_length=500, description="Notas de entrega")
    delivery_fee: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    
    # Asignación de Domiciliario
    delivery_person_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    assigned_at: Optional[datetime] = Field(default=None, description="Cuándo se asignó el domiciliario")
    picked_up_at: Optional[datetime] = Field(default=None, description="Cuándo recogió el pedido")
    delivered_at: Optional[datetime] = Field(default=None, description="Cuándo lo entregó")
    
    # Información del cliente (Legacy/Notes)
    customer_notes: Optional[str] = Field(default=None, max_length=500)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones
    # Relaciones
    items: List[OrderItem] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    payments: List["Payment"] = Relationship(back_populates="order")
    company: "Company" = Relationship()
    branch: "Branch" = Relationship()
    customer: Optional["Customer"] = Relationship(back_populates="orders")
    # table: Optional["Table"] = Relationship(back_populates="orders")
