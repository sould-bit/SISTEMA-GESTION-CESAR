from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Index, UniqueConstraint, Column, Numeric
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .company import Company
    from .product import Product
    from .order import OrderItem

class ProductModifier(SQLModel, table=True):
    """
    Modelo de Modificador - "Extras" o variaciones de un producto.
    Ejemplo: "Queso Extra", "Termino Medio", "Sin Cebolla".
    
    A diferencia de un Producto, un Modificador:
    - No se vende solo (usualmente).
    - Se "anexa" a un producto principal.
    - Tiene su propia "Mini-Receta" para descontar inventario.
    """
    __tablename__ = "product_modifiers"
    
    __table_args__ = (
        Index("idx_modifiers_company", "company_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", nullable=False)
    
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    
    # Precio adicional (puede ser 0)
    extra_price: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    
    # Opcional: Vincular a una categoría específica o producto específico?
    # Por ahora, los hacemos globales por compañía para simplificar.
    # En el futuro podríamos añadir `category_id` si queremos filtrar "Toppings de Hamburguesa".
    
    is_active: bool = Field(default=True)
    
    # Relaciones
    company: "Company" = Relationship()
    recipe_items: List["ModifierRecipeItem"] = Relationship(back_populates="modifier", sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"})


class ModifierRecipeItem(SQLModel, table=True):
    """
    Mini-Receta del Modificador.
    Define qué ingredientes se descuentan al seleccionar este modificador.
    Ej: "Queso Extra" -> Descuenta 0.02kg de "Queso Cheddar".
    """
    __tablename__ = "modifier_recipe_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    modifier_id: int = Field(foreign_key="product_modifiers.id", nullable=False)
    ingredient_product_id: int = Field(foreign_key="products.id", nullable=False)
    
    quantity: Decimal = Field(sa_column=Column(Numeric(10, 3)))
    unit: str = Field(max_length=50)
    
    # Relaciones
    modifier: Optional["ProductModifier"] = Relationship(back_populates="recipe_items")
    ingredient: Optional["Product"] = Relationship(sa_relationship_kwargs={"lazy": "selectin"})


class OrderItemModifier(SQLModel, table=True):
    """
    Tabla intermedia para registrar los modificadores aplicados a un item de orden.
    """
    __tablename__ = "order_item_modifiers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    order_item_id: int = Field(foreign_key="order_items.id", nullable=False)
    modifier_id: int = Field(foreign_key="product_modifiers.id", nullable=False)
    
    # Snapshot del precio al momento de la venta
    unit_price: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    quantity: int = Field(default=1) # Usualmente 1, pero porsiaca "Doble Extra Queso"
    
    # Costo calculado del modificador (suma de ingredientes) - Snapshot opcional para reportes de margen
    cost_snapshot: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))

    # Relaciones
    # Nota: Definir relación en OrderItem requiere importar este modelo allá.
