"""
RecipeItem Model - V4.1 Aligned with Ingredients Table

Uses ingredients table (UUID) for proper cost calculation and yield tracking.
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
import uuid
from sqlalchemy import Column, Numeric

if TYPE_CHECKING:
    from .recipe import Recipe
    from .ingredient import Ingredient
    from .company import Company


class RecipeItem(SQLModel, table=True):
    """
    Represents an ingredient item in a recipe.
    
    V4.1 Design:
    - Uses ingredients table (UUID) for proper yield/cost tracking
    - Calculates net_quantity based on ingredient's yield_factor
    - Snapshots calculated_cost for historical accuracy
    """
    __tablename__ = "recipe_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Foreign Keys
    recipe_id: uuid.UUID = Field(foreign_key="recipes.id", index=True, nullable=False)
    ingredient_id: uuid.UUID = Field(foreign_key="ingredients.id", index=True, nullable=False)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)

    # Quantities
    gross_quantity: Decimal = Field(
        sa_column=Column(Numeric(10, 4), nullable=False),
        description="Cantidad bruta retirada del almacén"
    )
    net_quantity: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(10, 4)),
        description="Cantidad neta usada (después de merma/yield)"
    )
    
    # Units and Cost
    measure_unit: str = Field(
        max_length=50,
        description="Unidad usada en la receta (g, kg, ml, und)"
    )
    calculated_cost: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(12, 2)),
        description="Snapshot del costo al momento de creación/actualización"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    recipe: Optional["Recipe"] = Relationship(back_populates="items")
    ingredient: Optional["Ingredient"] = Relationship()

    def calculate_cost(self, ingredient_cost: Decimal, yield_factor: float = 1.0) -> Decimal:
        """
        Calculate the cost of this recipe item.
        
        Args:
            ingredient_cost: Current cost per base_unit of the ingredient
            yield_factor: Ingredient's yield factor (e.g., 0.8 means 20% waste)
        
        Returns:
            Calculated cost for this item
        """
        # Apply yield factor to get net quantity
        self.net_quantity = self.gross_quantity * Decimal(str(yield_factor))
        # Calculate cost based on net usage
        self.calculated_cost = self.net_quantity * ingredient_cost
        return self.calculated_cost
