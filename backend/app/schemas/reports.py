from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

class SalesSummary(BaseModel):
    """Resumen analítico de ventas."""
    gross_revenue: Decimal = Field(default=Decimal("0.00"), description="Ingreso total con impuestos")
    net_revenue: Decimal = Field(default=Decimal("0.00"), description="Ingreso neto (subtotal)")
    tax_total: Decimal = Field(default=Decimal("0.00"), description="Total de impuestos")
    
    order_count: int = Field(default=0, description="Cantidad de pedidos exitosos")
    canceled_orders_count: int = Field(default=0, description="Cantidad de pedidos cancelados")
    items_sold_count: Decimal = Field(default=Decimal("0.00"), description="Cantidad total de productos/items vendidos")
    
    average_ticket: Decimal = Field(default=Decimal("0.00"), description="Ticket promedio por pedido exitoso")
    conversion_rate: float = Field(default=0.0, description="Tasa de conversión (%)")
    growth_rate: Optional[float] = Field(default=None, description="Tasa de crecimiento vs periodo anterior (%)")
    
    period_start: datetime
    period_end: datetime

class TopProduct(BaseModel):
    """Métrica de producto más vendido."""
    product_id: int
    product_name: str
    quantity_sold: Decimal
    revenue: Decimal

class CategorySale(BaseModel):
    """Ventas por categoría."""
    category_id: Optional[int]
    category_name: str
    revenue: Decimal
    percentage: float

class PaymentMethodSale(BaseModel):
    """Ventas por método de pago."""
    method: str
    revenue: Decimal
    count: int

class ReportsCollection(BaseModel):
    """Colección completa de reportes para el dashboard."""
    summary: SalesSummary
    top_products: List[TopProduct]
    categories: List[CategorySale]
    payments: List[PaymentMethodSale]
