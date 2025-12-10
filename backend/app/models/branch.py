from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

class Branch(SQLModel, table=True):
    """
    Modelo de Sucursal.
    Cada negocio (Company) puede tener múltiples sucursales.
    """
    __tablename__ = "branches"
    
    # Restricción única: No pueden haber dos sucursales con el mismo código en la misma compañía
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="unique_branch_code_per_company"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    
    name: str = Field(max_length=200)
    code: str = Field(max_length=20, description="Código corto ej: CENT, SUR")
    address: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=50)
    
    is_active: bool = Field(default=True)
    is_main: bool = Field(default=False, description="Si es la sucursal principal")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones
    company: "Company" = Relationship(back_populates="branches")
