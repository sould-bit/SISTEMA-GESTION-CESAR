from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Index, UniqueConstraint, Column, Numeric
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .product import Product


class RecipeItem(SQLModel, table=True):
    """
    Modelo de Item de Receta - Ingredientes individuales.
    
    Representa un ingrediente en una receta con su cantidad y costo unitario.
    El costo unitario se guarda como snapshot al momento de la creación.
    """

    __tablename__ = "recipe_items"

    __table_args__ = (
        # Índice: búsqueda por receta
        Index("idx_recipe_items_recipe", "recipe_id"),
        # Unicidad: un ingrediente solo puede aparecer una vez por receta
        UniqueConstraint("recipe_id", "ingredient_product_id", name="uq_recipe_item_ingredient"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipes.id", nullable=False)
    ingredient_product_id: int = Field(foreign_key="products.id", nullable=False)

    # Cantidad del ingrediente
    quantity: Decimal = Field(sa_column=Column(Numeric(10, 3)))
    unit: str = Field(max_length=50)  # kg, unidad, litro, gramo, etc.

    # Snapshot del costo al momento de agregar (para histórico)
    unit_cost: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2)))

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones (lazy='selectin' para async)
    recipe: Optional["Recipe"] = Relationship(back_populates="items")
    ingredient: Optional["Product"] = Relationship()


class Recipe(SQLModel, table=True):
    """
    Modelo de Receta - Define los ingredientes de un producto.
    
    Una receta contiene múltiples items (ingredientes) con sus cantidades.
    El costo total se calcula automáticamente sumando los costos de los items.
    Multi-Tenant: Cada receta pertenece a una empresa.
    """

    __tablename__ = "recipes"

    __table_args__ = (
        # Unicidad: un producto solo puede tener una receta
        UniqueConstraint("product_id", name="uq_recipe_product"),
        # Índice: filtro por empresa + activo
        Index("idx_recipes_company_active", "company_id", "is_active"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    product_id: int = Field(foreign_key="products.id", nullable=False)

    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)

    # Costo total calculado (suma de items)
    total_cost: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2)))

    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relaciones (lazy='selectin' para async)
    items: List["RecipeItem"] = Relationship(back_populates="recipe")
    product: Optional["Product"] = Relationship(back_populates="recipe")
    company: Optional["Company"] = Relationship()


# Importar para evitar circular imports
from .company import Company
