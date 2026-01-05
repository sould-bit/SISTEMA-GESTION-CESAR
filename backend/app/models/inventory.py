from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint, Index
from .product import Product
from .branch import Branch
from .user import User

class Inventory(SQLModel, table=True):
    """
    Modelo de Inventario - Stock por Sucursal.
    Separamos el concepto de "Producto" (Catálogo) del "Inventario" (Existencia física).
    """
    __tablename__ = "inventory"
    
    __table_args__ = (
        UniqueConstraint("branch_id", "product_id", name="uq_inventory_branch_product"),
        Index("idx_inventory_branch", "branch_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branches.id", nullable=False)
    product_id: int = Field(foreign_key="products.id", nullable=False)
    
    # Existencia actual
    stock: Decimal = Field(default=Decimal("0.000"), max_digits=12, decimal_places=3)
    
    # Configuración de alertas y ubicación
    min_stock: Decimal = Field(default=Decimal("0.000"), max_digits=12, decimal_places=3)
    max_stock: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=3)
    bin_location: Optional[str] = Field(default=None, max_length=50) # Ubicación en estante/nevera
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    branch: Optional[Branch] = Relationship()
    product: Optional[Product] = Relationship()


class InventoryTransaction(SQLModel, table=True):
    """
    Historial de Movimientos de Inventario (Kardex).
    Cada cambio en el stock debe generar un registro aquí.
    """
    __tablename__ = "inventory_transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    inventory_id: int = Field(foreign_key="inventory.id", nullable=False)
    
    # Tipo de movimiento: IN (Entrada), OUT (Salida), ADJ (Ajuste), SALE (Venta), WASTE (Desperdicio)
    transaction_type: str = Field(max_length=20) 
    
    quantity: Decimal = Field(max_digits=12, decimal_places=3) # Positivo o negativo
    balance_after: Decimal = Field(max_digits=12, decimal_places=3) # Stock resultante
    
    # Referencias (opcionales según el tipo)
    reference_id: Optional[str] = Field(default=None, max_length=100) # ID Pedido / ID Compra
    reason: Optional[str] = Field(default=None, max_length=255)
    
    user_id: Optional[int] = Field(foreign_key="users.id", nullable=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relaciones
    inventory: Optional[Inventory] = Relationship()
    user: Optional[User] = Relationship()
