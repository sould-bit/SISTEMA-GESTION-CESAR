from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Index

class Category(SQLModel, table=True):
    """
    Categorías de productos (Menú).
    Ej: Bebidas, Hamburguesas, Adicionales.
    Multi-Tenant: Cada categoría pertenece a una empresa.
    """
    __tablename__ = "categories"

    # Restricción: No permitir dos categorías con el mismo nombre en la misma empresa
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="unique_category_name_per_company"),
        Index("idx_categories_company_active", "company_id","is_active")
    )


    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Contexto Multi-Tenant
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    
    # Auditoría
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones (Futuro: Productos)
    # products: List["Product"] = Relationship(back_populates="category")