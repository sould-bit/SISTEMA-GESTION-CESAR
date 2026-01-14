from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
import uuid
from datetime import datetime
from sqlalchemy import Column, Numeric

if TYPE_CHECKING:
    from .product import Product
    from .company import Company
    from .ingredient import Ingredient

class RecipeItem(SQLModel, table=True):
    __tablename__ = "recipe_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # FKs
    recipe_id: uuid.UUID = Field(foreign_key="recipes.id", index=True, nullable=False)
    ingredient_id: uuid.UUID = Field(foreign_key="ingredients.id", index=True, nullable=False)

    # Data
    gross_quantity: float = Field(description="Cantidad bruta retirada del almacén")
    net_quantity: float = Field(description="Cantidad neta usada en el plato")
    measure_unit: str = Field(description="Unidad usada en la receta (ej. gramos vs kg del insumo)")

    calculated_cost: Decimal = Field(default=0, sa_column=Column(Numeric(10, 2)), description="Snapshot del costo")

    # Relationships
    recipe: Optional["Recipe"] = Relationship(back_populates="items")
    ingredient: Optional["Ingredient"] = Relationship()


class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # FKs
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    product_id: int = Field(foreign_key="products.id", index=True, nullable=False)

    name: str = Field(max_length=200)
    version: int = Field(default=1)
    is_active: bool = Field(default=True)

    batch_yield: float = Field(default=1.0, description="Rendimiento de la receta (ej. 1 olla de salsa)")
    total_cost: Decimal = Field(default=0, sa_column=Column(Numeric(10, 2))) # Cache del costo calculado
    preparation_time: int = Field(default=0, description="minutos")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    items: List["RecipeItem"] = Relationship(back_populates="recipe")
    product: Optional["Product"] = Relationship(
        back_populates="recipes",
        sa_relationship_kwargs={"foreign_keys": "Recipe.product_id"}
    )
    company: Optional["Company"] = Relationship()
