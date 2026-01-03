from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column

class OrderAudit(SQLModel, table=True):
    """
    Modelo de Auditoría de Pedidos.
    Registra cada cambio de estado, quién lo hizo y cuándo.
    """
    __tablename__ = "order_audits"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    order_id: int = Field(foreign_key="orders.id", index=True, nullable=False)
    
    old_status: str = Field(nullable=False)
    new_status: str = Field(nullable=False)
    
    changed_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Meta información (JSON) para contexto extra:
    # Ej: {"reason": "Customer cancelled", "ip": "192.168.1.1", "device": "POS-01"}
    meta: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
