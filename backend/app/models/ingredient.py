from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
import uuid
from datetime import datetime
from sqlalchemy import Column, Numeric
from enum import Enum

if TYPE_CHECKING:
    from .category import Category
    from .company import Company

import sqlalchemy as sa
from sqlalchemy import Column, Numeric, Enum as SaEnum

# ... existing imports ...

class IngredientType(str, Enum):
    RAW = "RAW"
    PROCESSED = "PROCESSED"
    MERCHANDISE = "MERCHANDISE"  # Direct-sale items: Coca-Cola, Beer, etc.

class IngredientBase(SQLModel):
    name: str = Field(index=True)
    sku: str = Field(index=True, max_length=150)
    base_unit: str = Field(description="Unidad base de almacenamiento: kg, lt, und")
    current_cost: Decimal = Field(default=0, sa_column=Column(Numeric(18, 4)))
    last_cost: Decimal = Field(default=0, sa_column=Column(Numeric(18, 4)))
    yield_factor: float = Field(default=1.0, description="Factor de rendimiento (0.90 = 10% merma natural)")

    # Foreign Keys updated to int to match existing tables
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)

    ingredient_type: IngredientType = Field(
        default=IngredientType.RAW,
        sa_column=Column(SaEnum(IngredientType, name="ingredient_type_enum"), nullable=False, default=IngredientType.RAW)
    )

class Ingredient(IngredientBase, table=True):
    __tablename__ = "ingredients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    category: Optional["Category"] = Relationship()
    company: Optional["Company"] = Relationship()
