"""
Schemas de Delivery (Domiciliarios)
===================================
Define los modelos Pydantic para validación de requests/responses
del módulo de control de domiciliarios.

Estructura:
- Requests: Lo que el cliente envía al servidor
- Responses: Lo que el servidor devuelve al cliente
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# =============================================================================
# REQUEST SCHEMAS (Entrada de datos)
# =============================================================================

class AssignDriverRequest(BaseModel):
    """
    Request para asignar un domiciliario a un pedido.
    
    Ejemplo de uso:
    POST /orders/123/assign-delivery
    Body: {"driver_id": 5}
    """
    driver_id: int = Field(..., description="ID del usuario domiciliario a asignar")


class CloseShiftRequest(BaseModel):
    """
    Request para cerrar el turno de un domiciliario con cuadre de caja.
    
    El domiciliario reporta cuánto dinero en efectivo recaudó.
    El sistema calcula lo esperado y muestra la diferencia.
    """
    cash_collected: Decimal = Field(
        ..., 
        ge=0, 
        description="Monto en efectivo que el domiciliario entrega"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Notas del cierre")


# =============================================================================
# RESPONSE SCHEMAS (Salida de datos)
# =============================================================================

class DriverRead(BaseModel):
    """
    Información básica de un domiciliario.
    
    Se usa para listar domiciliarios disponibles.
    """
    id: int
    full_name: str
    username: str
    is_available: bool = True  # True si no tiene pedidos activos
    active_orders_count: int = 0  # Cuántos pedidos tiene asignados ahora
    
    class Config:
        from_attributes = True


class DeliveryOrderRead(BaseModel):
    """
    Pedido visto desde la perspectiva del domiciliario.
    
    Incluye solo la información relevante para entregas.
    """
    id: int
    order_number: str
    
    # Información del cliente
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    
    # Dirección de entrega
    delivery_address: str
    delivery_notes: Optional[str] = None
    
    # Estado y tracking
    status: str
    total: Decimal
    delivery_fee: Decimal = Decimal("0.00")
    
    # Timestamps de seguimiento
    created_at: datetime
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeliveryOrderList(BaseModel):
    """Lista de pedidos para el domiciliario."""
    orders: List[DeliveryOrderRead]
    total_count: int


class ShiftSummary(BaseModel):
    """
    Resumen de un turno de domiciliario.
    
    Se genera al cerrar el turno para cuadre.
    """
    id: int
    driver_name: str
    
    # Conteo
    total_orders: int = 0
    total_delivered: int = 0
    
    # Dinero
    total_earnings: Decimal = Decimal("0.00")  # Total en ventas
    expected_cash: Decimal = Decimal("0.00")   # Efectivo esperado
    cash_collected: Decimal = Decimal("0.00")  # Efectivo reportado
    difference: Decimal = Decimal("0.00")      # Diferencia (+ sobrante, - faltante)
    
    # Estado
    status: str  # "active" o "closed"
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# RESPONSE GENERALES
# =============================================================================

class AssignmentResponse(BaseModel):
    """Respuesta después de asignar un domiciliario."""
    message: str
    order_id: int
    driver_id: int
    driver_name: str
    assigned_at: datetime


class DeliveryStatusUpdate(BaseModel):
    """Respuesta después de actualizar estado de entrega."""
    message: str
    order_id: int
    order_number: str
    new_status: str
    timestamp: datetime
