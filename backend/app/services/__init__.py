"""
🛠️ CAPA DE SERVICIOS - Lógica de Negocio Centralizada

Esta capa contiene toda la lógica de negocio del sistema, separada de los routers HTTP.
Cada servicio maneja una entidad o módulo específico del negocio.

Servicios disponibles:
- AuthService: Autenticación, login, tokens JWT
- CategoryService: Gestión de categorías
- UserService: Gestión de usuarios
- CompanyService: Gestión de empresas

Principios:
- ✅ Separación de responsabilidades
- ✅ Lógica reutilizable
- ✅ Fácil testing
- ✅ Multi-tenant por defecto
"""

from .auth_service import AuthService
from .category_service import CategoryService
from .product_service import ProductService

__all__ = ["AuthService", "CategoryService", "ProductService"]
