from typing import Optional
from enum import Enum
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class TableStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    ATTENTION = "attention"

class Table(SQLModel, table=True):
    """
    Modelo de Mesa.
    Representa una mesa física en una sucursal.
    """
    __tablename__ = "tables"

    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branches.id", index=True, nullable=False)
    
    table_number: int = Field(nullable=False)
    seat_count: int = Field(default=4)
    
    status: TableStatus = Field(default=TableStatus.AVAILABLE)
    
    # Coordenadas opcionales para layout visual en el futuro
    pos_x: Optional[int] = Field(default=None)
    pos_y: Optional[int] = Field(default=None)

    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones
    # branch: "Branch" = Relationship(back_populates="tables")
    # orders: List["Order"] = Relationship(back_populates="table")
