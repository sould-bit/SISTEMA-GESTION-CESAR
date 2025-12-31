# backend/app/dependencies.py
"""
📦 DEPENDENCIAS CENTRALIZADAS

Este archivo importa y reexporta todas las dependencias
para facilitar su uso en los routers.

IMPORTANTE: Todas las dependencias multi-tenant están aquí
para mantener el código organizado.
"""

# Dependencias de autenticación
from app.auth_deps import get_current_user

# Dependencias multi-tenant
from core.multi_tenant import (
    verify_current_user_company,  # ✅ Nueva: retorna company_id del usuario
    verify_company_access,        # ✅ Original: valida acceso a company_id específico
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
    "verify_current_user_company",  # ✅ Nueva dependencia
    "verify_company_access",
    "verify_branch_access",
    "verify_active_subscription",
    "verify_plan_limits",

    # Database
    "get_session"
]