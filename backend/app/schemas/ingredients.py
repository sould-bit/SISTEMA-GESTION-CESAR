"""
Schemas Pydantic para el módulo de Ingredientes (Insumos).

Define las estructuras de validación para crear, actualizar
y responder con datos de ingredientes.
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class IngredientBase(BaseModel):
    """Base schema para ingredientes."""
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del ingrediente")
    sku: str = Field(..., min_length=1, max_length=50, description="Código SKU único")
    base_unit: str = Field(..., min_length=1, max_length=20, description="Unidad base: kg, lt, und")
    yield_factor: float = Field(default=1.0, ge=0.01, le=1.0, description="Factor de rendimiento (0.90 = 10% merma)")


class IngredientCreate(IngredientBase):
    """Schema para crear un ingrediente."""
    current_cost: Decimal = Field(default=Decimal(0), ge=0, description="Costo actual por unidad base")
    category_id: Optional[int] = Field(None, description="ID de categoría (opcional)")


class IngredientUpdate(BaseModel):
    """Schema para actualizar un ingrediente."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    base_unit: Optional[str] = Field(None, min_length=1, max_length=20)
    current_cost: Optional[Decimal] = Field(None, ge=0)
    yield_factor: Optional[float] = Field(None, ge=0.01, le=1.0)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class IngredientResponse(IngredientBase):
    """Schema de respuesta para ingredientes."""
    id: uuid.UUID
    company_id: int
    current_cost: Decimal
    last_cost: Decimal
    category_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class IngredientListResponse(BaseModel):
    """Schema para listar ingredientes (versión resumida)."""
    id: uuid.UUID
    name: str
    sku: str
    base_unit: str
    current_cost: Decimal
    yield_factor: float
    is_active: bool

    class Config:
        from_attributes = True


class IngredientCostUpdate(BaseModel):
    """Schema para actualizar costo desde una compra."""
    new_cost: Decimal = Field(..., gt=0, description="Nuevo costo del ingrediente")
    use_weighted_average: bool = Field(default=True, description="Usar promedio ponderado")
