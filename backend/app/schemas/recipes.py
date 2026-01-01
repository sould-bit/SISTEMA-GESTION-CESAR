"""
Schemas Pydantic para el Sistema de Recetas.

Define las estructuras de validación para crear, actualizar
y responder con datos de recetas y sus ingredientes.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ============================================
# SCHEMAS PARA RECIPE ITEMS (Ingredientes)
# ============================================

class RecipeItemBase(BaseModel):
    """Base schema para items de receta."""
    ingredient_product_id: int = Field(..., description="ID del producto ingrediente")
    quantity: Decimal = Field(..., gt=0, description="Cantidad del ingrediente")
    unit: str = Field(..., min_length=1, max_length=50, description="Unidad de medida")


class RecipeItemCreate(RecipeItemBase):
    """Schema para crear un item de receta."""
    pass


class RecipeItemUpdate(BaseModel):
    """Schema para actualizar un item de receta."""
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)


class RecipeItemResponse(RecipeItemBase):
    """Schema de respuesta para items de receta."""
    id: int
    recipe_id: int
    unit_cost: Decimal = Field(description="Costo unitario del ingrediente")
    subtotal: Decimal = Field(description="Costo total del item (quantity * unit_cost)")
    ingredient_name: Optional[str] = Field(None, description="Nombre del ingrediente")
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
    """Schema para crear una receta con ingredientes."""
    product_id: int = Field(..., description="ID del producto al que pertenece la receta")
    items: List[RecipeItemCreate] = Field(..., min_length=1, description="Lista de ingredientes")

    @field_validator('items')
    @classmethod
    def validate_unique_ingredients(cls, items: List[RecipeItemCreate]) -> List[RecipeItemCreate]:
        """Validar que no haya ingredientes duplicados."""
        ingredient_ids = [item.ingredient_product_id for item in items]
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
    """Schema de respuesta para recetas."""
    id: int
    company_id: int
    product_id: int
    product_name: Optional[str] = Field(None, description="Nombre del producto")
    total_cost: Decimal = Field(description="Costo total calculado")
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[RecipeItemResponse] = Field(default_factory=list)
    items_count: int = Field(0, description="Número de ingredientes")

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    """Schema para listar recetas (sin items detallados)."""
    id: int
    company_id: int
    product_id: int
    product_name: Optional[str] = None
    name: str
    total_cost: Decimal
    is_active: bool
    items_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeCostRecalculateResponse(BaseModel):
    """Schema de respuesta al recalcular costos."""
    recipe_id: int
    old_total_cost: Decimal
    new_total_cost: Decimal
    difference: Decimal
    items_updated: int
