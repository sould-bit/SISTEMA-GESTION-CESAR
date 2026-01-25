"""
Financial Calculation Utilities
================================

Módulo centralizado para cálculos financieros de inventario.
Garantiza consistencia y precisión decimal en toda la aplicación.

Author: Sistema
Version: 1.0.0
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple, TYPE_CHECKING, Any
from sqlalchemy import func, select

# TYPE_CHECKING evita importación circular en runtime
if TYPE_CHECKING:
    from app.models.inventory import IngredientBatch


# Constants for precision
DEFAULT_PRICE_PRECISION = Decimal("0.01")  # 2 decimal places
DEFAULT_QUANTITY_PRECISION = Decimal("0.001")  # 3 decimal places
DEFAULT_WAC_PRECISION = Decimal("0.0001")  # 4 decimal places for WAC calculations


def round_currency(value: Decimal, precision: Decimal = DEFAULT_PRICE_PRECISION) -> Decimal:
    """
    Redondea un valor monetario con precisión estándar.
    
    Args:
        value: Valor decimal a redondear
        precision: Precisión de redondeo (default: 0.01 para 2 decimales)
    
    Returns:
        Valor redondeado como Decimal
    
    Example:
        >>> round_currency(Decimal("1666.6666"))
        Decimal("1666.67")
    """
    if value is None:
        return Decimal("0.00")
    return value.quantize(precision, rounding=ROUND_HALF_UP)


def calculate_proportional_value(
    total_cost: Decimal,
    quantity_remaining: Decimal,
    quantity_initial: Decimal
) -> Decimal:
    """
    Calcula el valor proporcional de un lote basado en el consumo.
    
    IMPORTANTE: Esta fórmula evita errores de precisión decimal al usar
    el total_cost original en lugar de recalcular desde cost_per_unit.
    
    Fórmula: total_cost * (quantity_remaining / quantity_initial)
    
    Args:
        total_cost: Costo total original del lote
        quantity_remaining: Cantidad restante en el lote
        quantity_initial: Cantidad inicial del lote
    
    Returns:
        Valor actual del inventario restante
    
    Example:
        >>> calculate_proportional_value(
        ...     total_cost=Decimal("50000"),
        ...     quantity_remaining=Decimal("20"),
        ...     quantity_initial=Decimal("30")
        ... )
        Decimal("33333.33")  # Exacto, sin error de redondeo
    """
    if quantity_initial is None or quantity_initial == 0:
        return Decimal("0.00")
    
    if total_cost is None:
        return Decimal("0.00")
    
    proportion = quantity_remaining / quantity_initial
    raw_value = total_cost * proportion
    
    return round_currency(raw_value)


def calculate_wac(
    total_value: Decimal,
    total_quantity: Decimal,
    fallback_cost: Optional[Decimal] = None
) -> Decimal:
    """
    Calcula el Costo Promedio Ponderado (WAC - Weighted Average Cost).
    
    Fórmula: WAC = Total Value / Total Quantity
    
    Args:
        total_value: Suma del valor de todos los lotes activos
        total_quantity: Suma de la cantidad restante de todos los lotes
        fallback_cost: Costo de respaldo si no hay stock (usa current_cost)
    
    Returns:
        WAC redondeado a 4 decimales
    
    Example:
        >>> calculate_wac(
        ...     total_value=Decimal("85000"),
        ...     total_quantity=Decimal("50")
        ... )
        Decimal("1700.0000")
    """
    if total_quantity is None or total_quantity <= 0:
        return round_currency(fallback_cost or Decimal("0.00"), DEFAULT_WAC_PRECISION)
    
    if total_value is None or total_value <= 0:
        return round_currency(fallback_cost or Decimal("0.00"), DEFAULT_WAC_PRECISION)
    
    wac = total_value / total_quantity
    return round_currency(wac, DEFAULT_WAC_PRECISION)


def build_proportional_value_expression(batch_table: Any):
    """
    Construye una expresión SQLAlchemy para calcular valor proporcional.
    
    Uso en queries:
        from app.models.inventory import IngredientBatch
        value_expr = build_proportional_value_expression(IngredientBatch)
        stmt = select(func.sum(value_expr).label("total_value"))
    
    Args:
        batch_table: La tabla/modelo de IngredientBatch (requerido)
    
    Returns:
        Expression SQLAlchemy con manejo de NULL y división por cero
    """
    return batch_table.total_cost * (
        batch_table.quantity_remaining / 
        func.nullif(batch_table.quantity_initial, 0)
    )


def build_stock_value_subquery(
    batch_table,
    company_id: int,
    branch_id: Optional[int] = None,
    ingredient_relation=None
):
    """
    Construye subquery para calcular stock y valor de inventario.
    
    Centraliza la lógica de cálculo para evitar duplicación.
    
    Args:
        batch_table: Tabla de lotes (IngredientBatch)
        company_id: ID de la empresa
        branch_id: ID de sucursal (None para todas)
        ingredient_relation: Relación a Ingredient para filtro por company
    
    Returns:
        Tuple de (stock_subquery, value_subquery)
    """
    value_expression = build_proportional_value_expression(batch_table)
    
    # Base filters
    base_filters = [batch_table.is_active == True]
    
    if branch_id:
        base_filters.append(batch_table.branch_id == branch_id)
    
    # Stock subquery
    stock_stmt = select(
        batch_table.ingredient_id,
        func.sum(batch_table.quantity_remaining).label("stock")
    ).where(*base_filters).group_by(batch_table.ingredient_id)
    
    # Value subquery
    value_stmt = select(
        batch_table.ingredient_id,
        func.sum(value_expression).label("total_value")
    ).where(*base_filters).group_by(batch_table.ingredient_id)
    
    # Add company filter via join if needed (global query)
    if not branch_id and ingredient_relation:
        from app.models.product import Ingredient
        stock_stmt = stock_stmt.join(ingredient_relation).where(
            Ingredient.company_id == company_id
        )
        value_stmt = value_stmt.join(ingredient_relation).where(
            Ingredient.company_id == company_id
        )
    
    return stock_stmt.subquery(), value_stmt.subquery()


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_batch_consistency(
    total_cost: Decimal,
    quantity_initial: Decimal,
    cost_per_unit: Decimal,
    tolerance: Decimal = Decimal("0.50")
) -> Tuple[bool, Decimal]:
    """
    Valida que un lote tenga datos consistentes.
    
    Verifica que: |total_cost - (quantity_initial * cost_per_unit)| < tolerance
    
    Args:
        total_cost: Costo total del lote
        quantity_initial: Cantidad inicial
        cost_per_unit: Costo por unidad
        tolerance: Diferencia máxima permitida
    
    Returns:
        Tuple de (is_valid, difference)
    
    Example:
        >>> validate_batch_consistency(
        ...     total_cost=Decimal("50000"),
        ...     quantity_initial=Decimal("30"),
        ...     cost_per_unit=Decimal("1666.67")
        ... )
        (True, Decimal("0.10"))  # Diferencia pequeña, aceptable
    """
    expected_total = quantity_initial * cost_per_unit
    difference = abs(total_cost - expected_total)
    is_valid = difference <= tolerance
    
    return is_valid, round_currency(difference)


def calculate_margin(
    sale_price: Decimal,
    cost: Decimal
) -> Tuple[Decimal, Decimal]:
    """
    Calcula margen de ganancia en valor absoluto y porcentaje.
    
    Args:
        sale_price: Precio de venta
        cost: Costo del producto (WAC o cost_per_unit)
    
    Returns:
        Tuple de (margin_absolute, margin_percentage)
    
    Example:
        >>> calculate_margin(Decimal("5000"), Decimal("1666.67"))
        (Decimal("3333.33"), Decimal("66.67"))
    """
    if sale_price is None or sale_price <= 0:
        return Decimal("0.00"), Decimal("0.00")
    
    margin_absolute = sale_price - (cost or Decimal("0"))
    margin_percentage = (margin_absolute / sale_price) * 100
    
    return (
        round_currency(margin_absolute),
        round_currency(margin_percentage)
    )
