from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from sqlmodel import SQLModel


class ProductBase(BaseModel):
    """Campos base compartidos por todos los schemas de Product"""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    price: Decimal = Field(..., ge=0, le=999999999.99)  # >= 0, <= 999M
    tax_rate: Decimal = Field(0, ge=0, le=1)  # 0% a 100%
    stock: Optional[Decimal] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = Field(None, gt=0)
    is_active: bool = Field(True)

class ProductCreate(ProductBase):
    """Schema para crear productos - validaciones estrictas"""
    
    # Campos requeridos (heredados de ProductBase)
    # name: requerido
    # price: requerido (> 0)
    
    # Campos opcionales con valores por defecto
    # description: opcional
    # tax_rate: default 0
    # stock: opcional
    # image_url: opcional
    # category_id: opcional
    # is_active: default True
    
    @field_validator('price')
    @classmethod
    def validate_price_not_zero(cls, v):
        if v <= 0:
            raise ValueError('El precio debe ser mayor a cero')
        if v > 1000000:  # 1 millón
            raise ValueError('El precio no puede exceder $1.000.000')
        return v
    
    @field_validator('tax_rate')
    @classmethod
    def validate_tax_rate(cls, v):
        if v < 0 or v > 1:
            raise ValueError('La tasa de impuesto debe estar entre 0% y 100%')
        return v


class ProductUpdate(BaseModel):
    """Schema para actualizar productos - todos los campos opcionales"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[Decimal] = Field(None, gt=0, le=999999999.99)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    stock: Optional[Decimal] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    
    @field_validator('price')
    @classmethod
    def validate_price_update(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El precio debe ser mayor a cero')
        return v


class CategoryRead(BaseModel):
    """Schema mínimo de Category para incluir en ProductRead"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    is_active: bool


# ============================================
# 📋 SCHEMA PARA LISTADOS - Optimizado para performance
# ============================================
class ProductListRead(BaseModel):
    """
    Schema ligero para listados - evita lazy loading de relaciones.
    
    Usa `category_name` (string) en lugar de `category` (objeto)
    para evitar el error MissingGreenlet en contextos async.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    tax_rate: Decimal = Decimal('0')
    stock: Optional[Decimal] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Campo plano en lugar de relación - evita lazy loading
    category_name: Optional[str] = None
    
    # Campo calculado
    final_price: Optional[Decimal] = None
    
    @model_validator(mode='after')
    def calculate_final_price(self):
        """Calcula precio final incluyendo impuestos"""
        if self.final_price is None and self.price is not None:
            tax = self.tax_rate if self.tax_rate is not None else Decimal('0')
            self.final_price = self.price * (1 + tax)
        return self
    
    @classmethod
    def from_product_with_category_name(
        cls, 
        product, 
        category_name: Optional[str] = None
    ) -> "ProductListRead":
        """
        Factory method para crear desde Product + nombre de categoría.
        
        Args:
            product: Instancia del modelo Product
            category_name: Nombre de la categoría (opcional)
            
        Returns:
            ProductListRead: Schema listo para serialización
        """
        # Calcular precio final
        final_price = None
        if product.price and product.tax_rate is not None:
            final_price = product.price * (1 + product.tax_rate)
        
        return cls(
            id=product.id,
            company_id=product.company_id,
            name=product.name,
            description=product.description,
            price=product.price,
            tax_rate=product.tax_rate or Decimal('0'),
            stock=product.stock,
            image_url=product.image_url,
            category_id=product.category_id,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            category_name=category_name,
            final_price=final_price
        )


# ============================================
# 🔍 SCHEMA PARA DETALLE - Incluye relaciones completas
# ============================================
class ProductDetailRead(ProductBase):
    """
    Schema completo para detalle de producto.
    
    Incluye la relación `category` completa (objeto CategoryRead).
    Solo usar cuando se ha cargado la relación con selectinload/joinedload.
    """
    
    id: int
    company_id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relación completa - requiere eager loading
    category: Optional[CategoryRead] = None
    
    # Campo calculado
    final_price: Optional[Decimal] = None
    
    @model_validator(mode='after')
    def calculate_final_price(self):
        """Calcula precio final incluyendo impuestos"""
        if self.final_price is None and self.price is not None:
            tax = self.tax_rate if self.tax_rate is not None else Decimal('0')
            self.final_price = self.price * (1 + tax)
        return self


# ============================================
# 🔄 ALIAS PARA COMPATIBILIDAD - ProductRead = ProductDetailRead
# ============================================
# Mantener ProductRead como alias para compatibilidad con código existente
ProductRead = ProductDetailRead