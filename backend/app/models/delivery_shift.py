"""
Modelo DeliveryShift (Turnos de Domiciliarios)
==============================================
Registra los turnos de trabajo de domiciliarios para:
- Control de horas trabajadas
- Cuadre de dinero recaudado
- Reportes de productividad
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Numeric, String, Index
from sqlmodel import SQLModel, Field, Relationship


class DeliveryShift(SQLModel, table=True):
    """
    Modelo de Turno de Domiciliario.
    
    Un turno inicia cuando el domiciliario comienza a trabajar
    y termina cuando hace su cuadre de caja.
    
    Flujo típico:
    1. Domiciliario inicia turno (start_shift)
    2. Recibe pedidos y los entrega
    3. Al final del día, cierra turno (end_shift) reportando efectivo
    4. Sistema calcula diferencia entre esperado vs real
    """
    __tablename__ = "delivery_shifts"
    
    __table_args__ = (
        Index("idx_delivery_shifts_driver", "company_id", "delivery_person_id"),
        Index("idx_delivery_shifts_date", "company_id", "started_at"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    branch_id: int = Field(foreign_key="branches.id", index=True, nullable=False)
    delivery_person_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    
    # Periodo del turno
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    
    # Contadores de pedidos
    total_orders: int = Field(default=0, description="Pedidos asignados en el turno")
    total_delivered: int = Field(default=0, description="Pedidos entregados")
    total_cancelled: int = Field(default=0, description="Pedidos cancelados")
    
    # Montos
    total_earnings: Decimal = Field(
        default=Decimal("0.00"), 
        sa_column=Column(Numeric(12, 2)),
        description="Suma del total de pedidos entregados"
    )
    expected_cash: Decimal = Field(
        default=Decimal("0.00"), 
        sa_column=Column(Numeric(12, 2)),
        description="Efectivo esperado (pedidos pagados en efectivo)"
    )
    cash_collected: Decimal = Field(
        default=Decimal("0.00"), 
        sa_column=Column(Numeric(12, 2)),
        description="Efectivo reportado por el domiciliario al cerrar"
    )
    
    # Estado del turno
    status: str = Field(
        default="active", 
        sa_column=Column(String, default="active"),
        description="active = en curso, closed = cerrado"
    )
    
    # Notas del cierre
    closing_notes: Optional[str] = Field(default=None, max_length=500)
    
    # Diferencia calculada (positivo = sobrante, negativo = faltante)
    @property
    def difference(self) -> Decimal:
        """Calcula la diferencia entre efectivo esperado y recaudado."""
        return self.cash_collected - self.expected_cash
