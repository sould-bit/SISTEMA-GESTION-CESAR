from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal

import uuid

# --- Base Schemas ---
class ModifierRecipeItemBase(BaseModel):
    ingredient_product_id: Optional[int] = None
    ingredient_id: Optional[uuid.UUID] = None
    quantity: Decimal
    unit: str

class ProductModifierBase(BaseModel):
    name: str
    description: Optional[str] = None
    extra_price: Decimal = Decimal("0.00")
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

# --- Create Schemas ---
class ModifierRecipeItemCreate(ModifierRecipeItemBase):
    pass

class ProductModifierCreate(ProductModifierBase):
    pass

# --- Update Schemas ---
class ProductModifierUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    extra_price: Optional[Decimal] = None
    is_active: Optional[bool] = None

# --- Response Schemas ---
from app.schemas.products import ProductBase
from app.schemas.ingredients import IngredientResponse

class ModifierRecipeItemRead(ModifierRecipeItemBase):
    id: int
    modifier_id: int
    ingredient: Optional[ProductBase] = None
    ingredient_ref: Optional[IngredientResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProductModifierRead(ProductModifierBase):
    id: int
    company_id: int
    recipe_items: List[ModifierRecipeItemRead] = []
    
    model_config = ConfigDict(from_attributes=True)
