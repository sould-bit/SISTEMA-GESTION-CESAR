from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .company import Company
    from .branch import Branch

class CashClosureStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

class CashClosure(SQLModel, table=True):
    """
    Modelo de Arqueo/Cierre de Caja.
    Permite conciliar el dinero del sistema vs el real.
    """
    __tablename__ = "cash_closures"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    branch_id: int = Field(foreign_key="branches.id", index=True, nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = Field(default=None)
    
    # 1. Monto Inicial (Base)
    initial_cash: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    
    # 2. Totales ESPERADOS (Sistema)
    expected_cash: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    expected_card: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    expected_transfer: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    expected_total: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2) # Suma de todo + inicial
    
    # 3. Totales REALES (Usuario cuenta billetes/voucher de datafono/app banco)
    real_cash: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    real_card: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    real_transfer: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    real_total: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    
    # 4. Diferencia (Real - Esperado)
    difference: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    
    status: CashClosureStatus = Field(default=CashClosureStatus.OPEN)
    notes: Optional[str] = Field(default=None, max_length=500)

    # Relaciones
    user: "User" = Relationship()
    company: "Company" = Relationship()
    branch: "Branch" = Relationship()
