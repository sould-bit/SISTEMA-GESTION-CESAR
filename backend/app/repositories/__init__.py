"""
🗃️ CAPA DE REPOSITORIOS - Acceso a Datos Centralizado

Esta capa contiene los repositorios que manejan el acceso a datos de manera
centralizada y con filtros multi-tenant automáticos.

Repositorios disponibles:
- BaseRepository: Clase base con operaciones comunes
- CategoryRepository: Acceso específico a categorías
- UserRepository: Acceso específico a usuarios

Características:
- ✅ Multi-tenant automático
- ✅ Operaciones CRUD genéricas
- ✅ Filtros de seguridad
- ✅ Manejo de transacciones
"""

from .base_repository import BaseRepository

__all__ = ["BaseRepository"]
