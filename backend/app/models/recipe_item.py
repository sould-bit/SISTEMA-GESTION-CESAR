from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
import uuid
from sqlalchemy import Column, Numeric

if TYPE_CHECKING:
    from .recipe import Recipe
    from .ingredient import Ingredient
    from .company import Company

class RecipeItem(SQLModel, table=True):
    __tablename__ = "recipe_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # FKs
    recipe_id: uuid.UUID = Field(foreign_key="recipes.id", index=True, nullable=False)
    ingredient_id: uuid.UUID = Field(foreign_key="ingredients.id", index=True, nullable=False)
    
    # Multi-tenant
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)

    # Data
    gross_quantity: float = Field(description="Cantidad bruta retirada del almacén")
    net_quantity: float = Field(description="Cantidad neta usada en el plato")
    measure_unit: str = Field(description="Unidad usada en la receta (ej. gramos vs kg del insumo)")

    calculated_cost: Decimal = Field(default=0, sa_column=Column(Numeric(10, 2)), description="Snapshot del costo")

    # Relationships
    recipe: Optional["Recipe"] = Relationship(back_populates="items")
    ingredient: Optional["Ingredient"] = Relationship()
