"""
RecipeItem Model - Aligned with existing database schema

The actual database uses:
- INTEGER ids (not UUID)
- ingredient_product_id pointing to products table (not separate ingredients)
- quantity, unit, unit_cost columns
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, Numeric

if TYPE_CHECKING:
    from .recipe import Recipe
    from .product import Product


class RecipeItem(SQLModel, table=True):
    """
    Represents an item in a recipe - aligned with existing DB schema.
    Uses product IDs as "ingredients" since the table references products.
    """
    __tablename__ = "recipe_items"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign Keys - matching actual DB types (INTEGER)
    recipe_id: int = Field(foreign_key="recipes.id", index=True, nullable=False)
    ingredient_product_id: int = Field(foreign_key="products.id", index=True, nullable=False)

    # Data - matching actual DB columns
    quantity: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(10, 3)))
    unit: str = Field(max_length=50)
    unit_cost: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(12, 2)))

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    recipe: Optional["Recipe"] = Relationship(back_populates="items")
    ingredient_product: Optional["Product"] = Relationship()
