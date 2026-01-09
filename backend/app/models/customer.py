from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from .company import Company
    from .customer_address import CustomerAddress
    from .order import Order

class Customer(SQLModel, table=True):
    """
    Modelo de Cliente (CRM).
    Representa al comprador final.
    """
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("company_id", "phone", name="uq_customer_phone_company"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    
    phone: str = Field(index=True, max_length=20, description="Identificador principal del usuario")
    full_name: str = Field(max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, description="Notas internas sobre el cliente")
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones
    company: "Company" = Relationship()
    addresses: List["CustomerAddress"] = Relationship(back_populates="customer", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    orders: List["Order"] = Relationship(back_populates="customer")
