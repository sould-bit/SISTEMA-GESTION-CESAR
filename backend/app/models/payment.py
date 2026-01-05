from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Index, String, Column
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .order import Order
    from .company import Company
    from .branch import Branch

class PaymentMethod(str, Enum):
    """Métodos de pago soportados."""
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    NEQUI = "nequi"
    DAVIPLATA = "daviplata"
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
    
    __table_args__ = (
        Index("idx_payments_company_date", "company_id", "created_at"),
        Index("idx_payments_order", "order_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    branch_id: int = Field(foreign_key="branches.id", index=True, nullable=False)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    order_id: int = Field(foreign_key="orders.id", nullable=False)
    
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    method: PaymentMethod = Field(sa_column=Column(String))
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, sa_column=Column(String, default=PaymentStatus.PENDING))
    
    transaction_id: Optional[str] = Field(default=None, max_length=100)  # ID de pasarela externa si aplica
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones
    order: "Order" = Relationship(back_populates="payments")
    company: "Company" = Relationship()
    branch: "Branch" = Relationship()
