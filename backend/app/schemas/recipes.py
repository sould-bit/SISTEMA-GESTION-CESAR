"""
Schemas Pydantic para el Sistema de Recetas V4.1.

Define las estructuras de validación para crear, actualizar
y responder con datos de recetas y sus ingredientes.

V4.1 Changes:
- RecipeItems now use ingredient_id (UUID) instead of ingredient_product_id (INT)
- Added gross_quantity and net_quantity for yield tracking
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, field_validator


# ============================================
# SCHEMAS PARA RECIPE ITEMS (Ingredientes)
# ============================================

class RecipeItemBase(BaseModel):
    """Base schema para items de receta V4.1."""
    ingredient_id: uuid.UUID = Field(..., description="ID del ingrediente (UUID)")
    gross_quantity: Decimal = Field(..., gt=0, description="Cantidad bruta del ingrediente")
    measure_unit: str = Field(..., min_length=1, max_length=50, description="Unidad de medida")


class RecipeItemCreate(RecipeItemBase):
    """Schema para crear un item de receta."""
    pass


class RecipeItemUpdate(BaseModel):
    """Schema para actualizar un item de receta."""
    gross_quantity: Optional[Decimal] = Field(None, gt=0)
    measure_unit: Optional[str] = Field(None, min_length=1, max_length=50)


class RecipeItemResponse(BaseModel):
    """Schema de respuesta para items de receta V4.1."""
    id: uuid.UUID
    recipe_id: uuid.UUID
    ingredient_id: uuid.UUID
    
    gross_quantity: Decimal = Field(description="Cantidad bruta (almacén)")
    net_quantity: Optional[Decimal] = Field(None, description="Cantidad neta (post-merma)")
    measure_unit: str = Field(description="Unidad de medida")
    calculated_cost: Optional[Decimal] = Field(None, description="Costo calculado del item")
    
    # Denormalized from ingredient for convenience
    ingredient_name: Optional[str] = Field(None, description="Nombre del ingrediente")
    ingredient_unit: Optional[str] = Field(None, description="Unidad base del ingrediente")
    
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# SCHEMAS PARA RECIPES (Recetas)
# ============================================

class RecipeBase(BaseModel):
    """Base schema para recetas."""
    name: str = Field(..., min_length=1, max_length=200, description="Nombre de la receta")
    description: Optional[str] = Field(None, max_length=500)


class RecipeCreate(RecipeBase):
    """Schema para crear una receta con ingredientes V4.1."""
    product_id: int = Field(..., description="ID del producto al que pertenece la receta")
    items: List[RecipeItemCreate] = Field(..., min_length=1, description="Lista de ingredientes")

    @field_validator('items')
    @classmethod
    def validate_unique_ingredients(cls, items: List[RecipeItemCreate]) -> List[RecipeItemCreate]:
        """Validar que no haya ingredientes duplicados."""
        ingredient_ids = [item.ingredient_id for item in items]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValueError("No se permiten ingredientes duplicados en una receta")
        return items


class RecipeUpdate(BaseModel):
    """Schema para actualizar una receta."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class RecipeItemAddOrUpdate(BaseModel):
    """Schema para agregar o actualizar items de una receta existente."""
    items: List[RecipeItemCreate] = Field(..., min_length=1)


class RecipeResponse(RecipeBase):
    """Schema de respuesta para recetas V4.1."""
    id: uuid.UUID
    company_id: int
    product_id: int
    product_name: Optional[str] = Field(None, description="Nombre del producto")
    total_cost: Decimal = Field(description="Costo total calculado")
    is_active: bool
    recipe_type: str = Field(description="Tipo de receta: REAL, AUTO, PROCESSED")
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[RecipeItemResponse] = Field(default_factory=list)
    items_count: int = Field(0, description="Número de ingredientes")

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    """Schema para listar recetas (sin items detallados)."""
    id: uuid.UUID
    company_id: int
    product_id: int
    product_name: Optional[str] = None
    name: str

    total_cost: Decimal
    is_active: bool
    recipe_type: str
    items_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeCostRecalculateResponse(BaseModel):
    """Schema de respuesta al recalcular costos."""
    recipe_id: uuid.UUID
    old_total_cost: Decimal
    new_total_cost: Decimal
    difference: Decimal
    items_updated: int
