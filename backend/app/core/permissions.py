"""
🔐 DECORADORES DE AUTORIZACIÓN - Sistema RBAC

Este módulo proporciona decoradores para proteger endpoints con permisos.

Decoradores disponibles:
- @require_permission("permission.code") - Requiere un permiso específico
- @require_any_permission(["perm1", "perm2"]) - Requiere al menos uno
- @require_all_permissions(["perm1", "perm2"]) - Requiere todos
- @require_role("role_code") - Requiere un rol específico
- @require_branch_access() - Verifica acceso a sucursal

Uso:
    from app.core.permissions import require_permission

    @router.post("/products")
    @require_permission("products.create")
    async def create_product(...):
        ...
"""

from functools import wraps
from typing import List, Callable, Optional, TypeVar, ParamSpec
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.services.permission_service import PermissionService
from app.database import get_session
from app.dependencies import get_current_user

# Type hints para preservar firmas de función
P = ParamSpec('P')
R = TypeVar('R')


def _get_session(kwargs: dict) -> Optional[AsyncSession]:
    """Extrae la sesión de BD de los argumentos de la función."""
    # 1. Buscar 'session' directamente
    if 'session' in kwargs:
        return kwargs['session']

    # 2. Buscar 'db' directamente
    if 'db' in kwargs:
        return kwargs['db']

    # 3. Buscar en servicios que tengan atributo .session o .db
    for val in kwargs.values():
        if hasattr(val, 'session'):
            return val.session
        if hasattr(val, 'db'):
            return val.db

    return None


def require_permission(permission_code: str):
    """
    Decorador que requiere un permiso específico.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Extraer current_user de kwargs
            current_user = kwargs.get('current_user')

            # Validar que el usuario esté autenticado
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )

            # Obtener sesión
            session = _get_session(kwargs)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error interno: sesión de BD no disponible en la función decorada"
                )

            # Verificar permiso
            print(f"DEBUG: Creando PermissionService con sesión {id(session)}")
            permission_service = PermissionService(session)
            print(f"DEBUG: Llamando a check_permission para {permission_code}")
            has_permission = await permission_service.check_permission(
                user_id=current_user.id,
                permission_code=permission_code,
                company_id=current_user.company_id
            )

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permiso denegado: se requiere '{permission_code}'"
                )

            # Ejecutar función original
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_any_permission(permission_codes: List[str]):
    """
    Decorador que requiere AL MENOS UNO de los permisos especificados.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Extraer current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )

            # Obtener sesión
            session = _get_session(kwargs)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error interno: sesión de BD no disponible"
                )

            permission_service = PermissionService(session)

            # Verificar si tiene al menos uno
            for perm_code in permission_codes:
                has_permission = await permission_service.check_permission(
                    user_id=current_user.id,
                    permission_code=perm_code,
                    company_id=current_user.company_id
                )

                if has_permission:
                    return await func(*args, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado: se requiere uno de {permission_codes}"
            )

        return wrapper
    return decorator


def require_all_permissions(permission_codes: List[str]):
    """
    Decorador que requiere TODOS los permisos especificados.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Extraer current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )

            # Obtener sesión
            session = _get_session(kwargs)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error interno: sesión de BD no disponible"
                )

            permission_service = PermissionService(session)

            # Verificar todos
            for perm_code in permission_codes:
                has_permission = await permission_service.check_permission(
                    user_id=current_user.id,
                    permission_code=perm_code,
                    company_id=current_user.company_id
                )

                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permiso denegado: se requieren todos estos permisos {permission_codes}"
                    )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(role_code: str):
    """
    Decorador que requiere un rol específico.

    IMPORTANTE: La función decorada DEBE tener este parámetro:
    - current_user: User = Depends(get_current_user)
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Extraer dependencias de kwargs
            current_user = kwargs.get('current_user')

            # Validar que el usuario esté autenticado
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )

            if not current_user.user_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuario sin rol asignado"
                )

            if current_user.user_role.code != role_code:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permiso denegado: se requiere rol '{role_code}'"
                )

            # Ejecutar función original
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_branch_access(branch_id_param: str = "branch_id"):
    """
    Decorador que verifica acceso a una sucursal específica.
    Corregido para funcionar correctamente con dependencias FastAPI.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(
            *args: P.args,
            current_user: User = Depends(get_current_user),
            **kwargs: P.kwargs
        ) -> R:
            # Validar que el usuario esté autenticado
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )

            branch_id = kwargs.get(branch_id_param)

            if branch_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parámetro '{branch_id_param}' no encontrado"
                )

            if not hasattr(current_user, 'can_access_branch') or not current_user.can_access_branch(branch_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene acceso a esta sucursal"
                )

            # Ejecutar función original con dependencias inyectadas
            return await func(
                *args,
                current_user=current_user,
                **kwargs
            )

        return wrapper
    return decorator


# ============================================================================
# DEPENDENCIAS DE FASTAPI (alternativa a decoradores)
# ============================================================================

def verify_permission(permission_code: str):
    """
    Factory de dependencias de FastAPI para verificar permisos.
    Versión mejorada con mejor manejo de errores.

    Uso:
        @router.get("/some-path")
        async def some_endpoint(
            _=Depends(verify_permission("some.permission"))
        ):
            ...
    """
    async def _verify(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
    ):
        # Validar que el usuario esté autenticado
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no autenticado"
            )

        # Validar que la sesión esté disponible
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno: sesión de base de datos no disponible"
            )

        permission_service = PermissionService(session)
        has_permission = await permission_service.check_permission(
            user_id=current_user.id,
            permission_code=permission_code,
            company_id=current_user.company_id
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado: se requiere '{permission_code}'"
            )
        return True

    return _verify
