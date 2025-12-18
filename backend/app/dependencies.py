# backend/app/dependencies.py
"""
📦 DEPENDENCIAS CENTRALIZADAS

Este archivo importa y reexporta todas las dependencias
para facilitar su uso en los routers.

IMPORTANTE: Todas las dependencias multi-tenant están aquí
para mantener el código organizado.
"""

# Dependencias de autenticación
from app.routers.auth import get_current_user

# Dependencias multi-tenant
from core.multi_tenant import (
    verify_company_access,
    verify_branch_access, 
    verify_active_subscription,
    verify_plan_limits
)

# Sesión de base de datos
from app.database import get_session

# ============================================
# RE-EXPORTACIÓN PARA FACILITAR IMPORTS
# ============================================

__all__ = [
    # Auth
    "get_current_user",
    
    # Multi-tenant
    "verify_company_access",
    "verify_branch_access",
    "verify_active_subscription", 
    "verify_plan_limits",
    
    # Database
    "get_session"
]