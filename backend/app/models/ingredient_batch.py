from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid
from sqlalchemy import Column, Numeric
from .branch import Branch
from .ingredient import Ingredient

class IngredientBatch(SQLModel, table=True):
    """
    Modelo de Lote de Insumos (FIFO).
    Permite registrar compras con costos específicos y controlar el agotamiento por fecha.
    """
    __tablename__ = "ingredient_batches"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ingredient_id: uuid.UUID = Field(foreign_key="ingredients.id", nullable=False, index=True)
    branch_id: int = Field(foreign_key="branches.id", nullable=False, index=True)
    
    # Cantidades
    quantity_initial: Decimal = Field(sa_column=Column(Numeric(12, 3), nullable=False))
    quantity_remaining: Decimal = Field(sa_column=Column(Numeric(12, 3), nullable=False))
    
    # Costos
    cost_per_unit: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    total_cost: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False)) # Calculado: qty * unit_cost
    
    # Metadatos
    acquired_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    is_active: bool = Field(default=True, index=True) # True si remaining > 0
    supplier: Optional[str] = Field(default=None, max_length=100)
    
    # Relaciones
    ingredient: Optional[Ingredient] = Relationship()
    branch: Optional[Branch] = Relationship()
