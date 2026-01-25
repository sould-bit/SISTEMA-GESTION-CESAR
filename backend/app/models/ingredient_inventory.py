from typing import Optional
from decimal import Decimal
from datetime import datetime
import uuid
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint, Index
from sqlalchemy import Column, Numeric
from .branch import Branch
from .ingredient import Ingredient
from .user import User

class IngredientInventory(SQLModel, table=True):
    """
    Modelo de Inventario de Insumos - Stock por Sucursal.
    Nivel C: La Realidad Física para Ingredientes.
    """
    __tablename__ = "ingredient_inventory"

    __table_args__ = (
        UniqueConstraint("branch_id", "ingredient_id", name="uq_ingredient_inventory_branch"),
        Index("idx_ingredient_inventory_branch", "branch_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    branch_id: int = Field(foreign_key="branches.id", nullable=False)
    ingredient_id: uuid.UUID = Field(foreign_key="ingredients.id", nullable=False)

    # Existencia actual
    stock: Decimal = Field(default=0, sa_column=Column(Numeric(12, 3)))

    # Configuración de alertas
    min_stock: Decimal = Field(default=0, sa_column=Column(Numeric(12, 3)))
    max_stock: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(12, 3)))

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    branch: Optional[Branch] = Relationship()
    ingredient: Optional[Ingredient] = Relationship()


class IngredientTransaction(SQLModel, table=True):
    """
    Historial de Movimientos de Insumos (Kardex).
    """
    __tablename__ = "ingredient_transactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    inventory_id: uuid.UUID = Field(foreign_key="ingredient_inventory.id", nullable=False)

    # Tipo de movimiento: IN (Compra), OUT (Uso/Explosión), WASTE (Merma/Desperdicio), ADJ (Ajuste)
    transaction_type: str = Field(max_length=20)

    quantity: Decimal = Field(sa_column=Column(Numeric(12, 3))) # Positivo o negativo
    balance_after: Decimal = Field(sa_column=Column(Numeric(12, 3))) # Stock resultante

    # Referencias
    reference_id: Optional[str] = Field(default=None, max_length=100) # ID Compra / ID Orden
    reason: Optional[str] = Field(default=None, max_length=255)

    user_id: Optional[int] = Field(foreign_key="users.id", nullable=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    inventory: Optional[IngredientInventory] = Relationship()
    user: Optional[User] = Relationship()
