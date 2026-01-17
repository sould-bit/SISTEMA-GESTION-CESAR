from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from decimal import Decimal
import uuid
from datetime import datetime
from sqlalchemy import Column, Numeric

class ProductionEvent(SQLModel, table=True):
    __tablename__ = "production_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    company_id: int = Field(index=True, nullable=False) # Tenant ID
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Origen (Input) - Legacy / Primary Input
    input_ingredient_id: Optional[uuid.UUID] = Field(default=None, foreign_key="ingredients.id", index=True)
    input_quantity: float = Field(default=0, description="Cantidad del insumo principal (Legacy)")
    input_cost_total: Decimal = Field(default=0, sa_column=Column(Numeric(18, 2)), description="Costo total de los lotes consumidos")
    
    notes: Optional[str] = Field(default=None, description="Notas de la producción")

    # Destino (Output)
    output_ingredient_id: uuid.UUID = Field(foreign_key="ingredients.id", index=True)
    output_batch_id: Optional[uuid.UUID] = Field(default=None, foreign_key="ingredient_batches.id", description="ID del lote generado por esta producción")
    output_quantity: float = Field(description="Cantidad total producida del insumo destino")
    
    # Resultado
    calculated_unit_cost: Decimal = Field(default=0, sa_column=Column(Numeric(18, 6)), description="Costo unitario resultante")
    
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    inputs: list["ProductionEventInput"] = Relationship(sa_relationship_kwargs={"cascade": "all, delete-orphan"})
