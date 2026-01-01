from typing import Optional
from datetime import datetime
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field


class OrderCounter(SQLModel, table=True):
    """
    Modelo de Contador de Pedidos - Genera números consecutivos únicos.
    
    Permite tener secuencias separadas por sucursal o tipo de pedido.
    Ej: Sucursal A: Pedido 001, 002... Sucursal B: Pedido 001, 002...
    """
    __tablename__ = "order_counters"

    __table_args__ = (
        UniqueConstraint("branch_id", "counter_type", name="uq_branch_counter_type"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    branch_id: int = Field(foreign_key="branches.id", index=True, nullable=False)
    
    # Tipo de contador (ej: "delivery", "dine_in", "general")
    counter_type: str = Field(default="general", max_length=50)
    
    # Prefijo opcional (ej: "SUC1-")
    prefix: Optional[str] = Field(default=None, max_length=10)
    
    # El último número utilizado
    last_value: int = Field(default=0)
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
