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
    sku: Optional[str] = Field(None, min_length=1, max_length=50, description="Código SKU único (opcional, auto-generado si se omite)")
    base_unit: str = Field(..., min_length=1, max_length=20, description="Unidad base: kg, lt, und")
    yield_factor: float = Field(default=1.0, ge=0.01, le=1.0, description="Factor de rendimiento (0.90 = 10% merma)")
    ingredient_type: str = Field(default="RAW", pattern="^(RAW|PROCESSED|MERCHANDISE)$", description="Tipo: RAW, PROCESSED o MERCHANDISE")


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
    ingredient_type: str
    stock: Optional[Decimal] = Field(default=Decimal(0))
    total_inventory_value: Optional[Decimal] = Field(default=Decimal(0))
    calculated_cost: Optional[Decimal] = Field(default=Decimal(0))
    category_id: Optional[int] = None
    min_stock: Optional[Decimal] = Field(default=Decimal(0))


    class Config:
        from_attributes = True


class IngredientCostUpdate(BaseModel):
    """Schema para actualizar costo desde una compra."""
    new_cost: Decimal = Field(..., gt=0, description="Nuevo costo del ingrediente")
    use_weighted_average: bool = Field(default=False, description="Usar promedio ponderado (False = Costo Estático)")
    reason: Optional[str] = Field(default=None, description="Razón del cambio de precio")


class IngredientCostHistoryResponse(BaseModel):
    id: uuid.UUID
    previous_cost: Decimal
    new_cost: Decimal
    reason: Optional[str]
    created_at: datetime
    user_id: Optional[int]


class IngredientStockUpdate(BaseModel):
    """Schema para actualizar el stock de un ingrediente."""
    quantity: Decimal = Field(..., description="Cantidad a mover (positiva para IN/ADJ, positiva para OUT que será convertida)")
    transaction_type: str = Field(..., pattern="^(IN|OUT|ADJ|PURCHASE|ADJUST)$")
    reference_id: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    cost_per_unit: Optional[Decimal] = Field(default=None, gt=0, description="Costo unitario para registrar lote (Solo IN/PURCHASE)")
    supplier: Optional[str] = Field(default=None, description="Proveedor del lote")


class IngredientBatchResponse(BaseModel):
    """Schema para respuesta de Lotes (Batches)."""
    id: uuid.UUID
    quantity_initial: Decimal
    quantity_remaining: Decimal
    cost_per_unit: Decimal
    total_cost: Decimal
    current_value: Optional[Decimal] = None # Valor del stock restante (qty_remaining * cost_per_unit)
    acquired_at: datetime
    is_active: bool
    supplier: Optional[str]
    
    class Config:
        from_attributes = True


class IngredientBatchUpdate(BaseModel):
    """Schema para actualizar un Lote (Batch)."""
    quantity_initial: Optional[Decimal] = Field(default=None, ge=0, description="Cantidad inicial comprada")
    quantity_remaining: Optional[Decimal] = Field(default=None, ge=0, description="Cantidad restante")
    cost_per_unit: Optional[Decimal] = Field(default=None, ge=0, description="Costo por unidad")
    total_cost: Optional[Decimal] = Field(default=None, ge=0, description="Costo total de la compra")
    supplier: Optional[str] = Field(default=None, max_length=100, description="Proveedor")
    is_active: Optional[bool] = None


class IngredientInventorySettingsUpdate(BaseModel):
    """Schema para actualizar configuraciones de inventario (min/max stock)."""
    min_stock: Optional[Decimal] = Field(None, ge=0)
    max_stock: Optional[Decimal] = Field(None, ge=0)


class IngredientStockMovementResponse(BaseModel):
    """Schema para respuesta de movimientos de stock."""
    id: uuid.UUID
    created_at: datetime
    transaction_type: str
    quantity: Decimal
    balance_after: Optional[Decimal] = None
    reference_id: Optional[str] = None
    reason: Optional[str] = None
    user_name: Optional[str] = None
    ingredient_name: Optional[str] = None
    ingredient_unit: Optional[str] = None
    ingredient_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
