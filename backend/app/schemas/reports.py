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


# =============================================================================
# NUEVOS SCHEMAS - Reportes Adicionales
# =============================================================================

class InventoryReportItem(BaseModel):
    """Item de reporte de inventario."""
    product_id: int
    product_name: str
    category_name: Optional[str] = None
    current_stock: Decimal = Field(default=Decimal("0"), description="Stock actual")
    min_stock: Decimal = Field(default=Decimal("0"), description="Stock mínimo")
    max_stock: Decimal = Field(default=Decimal("0"), description="Stock máximo")
    stock_status: str = Field(description="Estado: LOW, OK, EXCESS")
    unit_cost: Decimal = Field(default=Decimal("0"), description="Costo unitario")
    total_value: Decimal = Field(default=Decimal("0"), description="Valor total en inventario")


class InventoryReport(BaseModel):
    """Reporte completo de inventario."""
    items: List[InventoryReportItem]
    total_value: Decimal = Field(description="Valor total del inventario")
    low_stock_count: int = Field(description="Productos con stock bajo")
    out_of_stock_count: int = Field(description="Productos sin stock")
    generated_at: datetime


class DeliveryReportItem(BaseModel):
    """Estadísticas de un domiciliario."""
    user_id: int
    user_name: str
    deliveries_completed: int = 0
    deliveries_canceled: int = 0
    total_revenue: Decimal = Field(default=Decimal("0"))
    avg_delivery_time_minutes: Optional[float] = None
    rating: Optional[float] = None


class DeliveryReport(BaseModel):
    """Reporte de domiciliarios."""
    delivery_persons: List[DeliveryReportItem]
    total_deliveries: int
    total_revenue: Decimal
    avg_delivery_time_minutes: Optional[float] = None
    period_start: datetime
    period_end: datetime


class RecipeConsumptionItem(BaseModel):
    """Consumo de ingrediente por receta."""
    ingredient_id: int
    ingredient_name: str
    total_consumed: Decimal = Field(description="Cantidad consumida en el periodo")
    unit: str = Field(default="unidad")
    avg_cost_per_unit: Decimal = Field(default=Decimal("0"))
    total_cost: Decimal = Field(default=Decimal("0"))


class RecipeConsumptionReport(BaseModel):
    """Reporte de consumo por recetas."""
    ingredients: List[RecipeConsumptionItem]
    total_cost: Decimal
    top_consumed: List[str] = Field(description="Top 5 ingredientes más consumidos")
    period_start: datetime
    period_end: datetime
