"""
Audit Log Model
===============
Modelo para registrar acciones críticas del sistema.

Acciones auditables:
- Autenticación (login/logout)
- Cambios de inventario
- Cierres de caja
- Cambios de usuarios/roles
- Eliminación/modificación de productos
"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
from sqlalchemy import Column, String, Index
from sqlmodel import SQLModel, Field, JSON


class AuditAction(str, Enum):
    """Tipos de acciones auditables."""
    
    # Autenticación
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    
    # Inventario
    STOCK_ADJUST = "stock_adjust"
    STOCK_ENTRY = "stock_entry"
    STOCK_EXIT = "stock_exit"
    
    # Caja
    CASH_OPEN = "cash_open"
    CASH_CLOSE = "cash_close"
    PAYMENT_RECEIVED = "payment_received"
    
    # Usuarios/Roles
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_ASSIGN = "role_assign"
    PERMISSION_CHANGE = "permission_change"
    
    # Productos
    PRODUCT_CREATE = "product_create"
    PRODUCT_UPDATE = "product_update"
    PRODUCT_DELETE = "product_delete"
    PRODUCT_PRICE_CHANGE = "product_price_change"
    
    # Pedidos (complementa OrderAudit)
    ORDER_CANCEL = "order_cancel"
    ORDER_REFUND = "order_refund"
    
    # Sistema
    CONFIG_CHANGE = "config_change"


class AuditLog(SQLModel, table=True):
    """
    Registro de auditoría general.
    
    Captura quién hizo qué, cuándo y desde dónde.
    Multi-tenant por company_id.
    """
    __tablename__ = "audit_logs"
    
    __table_args__ = (
        Index("idx_audit_company_created", "company_id", "created_at"),
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Multi-tenant
    company_id: int = Field(foreign_key="companies.id", index=True, nullable=False)
    
    # Quién realizó la acción
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    username: Optional[str] = Field(default=None, max_length=100)  # Snapshot del username
    
    # Qué acción se realizó
    action: str = Field(sa_column=Column(String, nullable=False, index=True))
    
    # Sobre qué entidad
    entity_type: Optional[str] = Field(default=None, max_length=50)  # "order", "product", "user"
    entity_id: Optional[int] = Field(default=None)
    
    # Valores antes/después del cambio (JSON)
    old_value: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    new_value: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Descripción legible
    description: Optional[str] = Field(default=None, max_length=500)
    
    # Contexto de la petición
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 max
    user_agent: Optional[str] = Field(default=None, max_length=500)
    
    # Sucursal (si aplica)
    branch_id: Optional[int] = Field(default=None, foreign_key="branches.id")
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
