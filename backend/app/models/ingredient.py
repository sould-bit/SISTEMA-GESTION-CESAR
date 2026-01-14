from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
import uuid
from datetime import datetime
from sqlalchemy import Column, Numeric

if TYPE_CHECKING:
    from .category import Category
    from .company import Company

class IngredientBase(SQLModel):
    name: str = Field(index=True)
    sku: str = Field(index=True)
    base_unit: str = Field(description="Unidad base de almacenamiento: kg, lt, und")
    current_cost: Decimal = Field(default=0, sa_column=Column(Numeric(10, 2)))
    last_cost: Decimal = Field(default=0, sa_column=Column(Numeric(10, 2)))
    yield_factor: float = Field(default=1.0, description="Factor de rendimiento (0.90 = 10% merma natural)")

    # Foreign Keys updated to int to match existing tables
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)

class Ingredient(IngredientBase, table=True):
    __tablename__ = "ingredients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    category: Optional["Category"] = Relationship()
    company: Optional["Company"] = Relationship()
