from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Numeric

if TYPE_CHECKING:
    from .ingredient import Ingredient
    from .user import User

class IngredientCostHistory(SQLModel, table=True):
    __tablename__ = "ingredient_cost_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ingredient_id: UUID = Field(foreign_key="ingredients.id", index=True)
    
    previous_cost: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    new_cost: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    
    reason: Optional[str] = Field(default=None)
    
    user_id: Optional[int] = Field(foreign_key="users.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    ingredient: Optional["Ingredient"] = Relationship()
    user: Optional["User"] = Relationship()
