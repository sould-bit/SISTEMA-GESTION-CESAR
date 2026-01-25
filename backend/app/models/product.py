from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy import Index, text, Column, Numeric
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .category import Category
    from .company import Company
    from .recipe import Recipe

class Product(SQLModel, table=True):
    """
    Modelo de Producto para el sistema de gestión.
    Representa items del menú (hamburguesas, bebidas, etc.).
    Multi-Tenant: Cada producto pertenece a una empresa.
    Soft Delete: Eliminación lógica para preservar integridad.
    """

    __tablename__ = "products"

    __table_args__ = (
        # NOTA: La unicidad de nombre por empresa se maneja via índice parcial
        # en la BD (uq_products_company_name_active). Este índice solo aplica
        # a productos ACTIVOS, permitiendo reutilizar nombres de productos inactivos.
        # Ver migración: b001_partial_unique_products.py
        
        # Índice: filtro por empresa + activo (listados)
        Index("idx_products_company_active", "company_id", "is_active"),
        # Índice: búsqueda por categoría
        Index("idx_products_category", "company_id", "category_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)

    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)
    price: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2)))
    tax_rate: Decimal = Field(default=0, sa_column=Column(Numeric(5, 2)))

    stock: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(10, 2)))

    image_url: Optional[str] = Field(default=None, max_length=500)

    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    category: Optional["Category"] = Relationship(back_populates="products")
    company: Optional["Company"] = Relationship()

    # Active Recipe Link
    active_recipe_id: Optional[uuid.UUID] = Field(default=None, foreign_key="recipes.id", nullable=True)

    # Relationships
    recipes: List["Recipe"] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"foreign_keys": "Recipe.product_id"}
    )