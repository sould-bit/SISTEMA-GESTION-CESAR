"""
Sistema de Excepciones Personalizadas para RBAC

Este módulo define excepciones específicas para el sistema de roles y permisos,
proporcionando mejor manejo de errores, logging detallado y respuestas HTTP apropiadas.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException


class RBACException(HTTPException):
    """Excepción base para errores del sistema RBAC."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        error_type: str = "rbac_error",
        extra_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code or "RBAC_ERROR"
        self.error_type = error_type
        self.extra_data = extra_data or {}


# ========== EXCEPCIONES DE PERMISOS ==========

class PermissionDeniedException(RBACException):
    """Se lanza cuando un usuario no tiene un permiso requerido."""

    def __init__(
        self,
        permission_code: str,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        required_role: Optional[str] = None
    ):
        super().__init__(
            status_code=403,
            detail=f"Permiso denegado: se requiere '{permission_code}'",
            error_code="PERMISSION_DENIED",
            error_type="authorization_error",
            extra_data={
                "permission_code": permission_code,
                "user_id": user_id,
                "company_id": company_id,
                "required_role": required_role,
                "action": "access_denied"
            }
        )


class PermissionNotFoundException(RBACException):
    """Se lanza cuando se solicita un permiso que no existe."""

    def __init__(self, permission_code: str, company_id: Optional[int] = None):
        super().__init__(
            status_code=404,
            detail=f"Permiso no encontrado: '{permission_code}'",
            error_code="PERMISSION_NOT_FOUND",
            error_type="resource_error",
            extra_data={
                "permission_code": permission_code,
                "company_id": company_id
            }
        )


class InsufficientPermissionsException(RBACException):
    """Se lanza cuando se requieren múltiples permisos y faltan algunos."""

    def __init__(
        self,
        required_permissions: list,
        granted_permissions: list,
        user_id: Optional[int] = None
    ):
        missing = set(required_permissions) - set(granted_permissions)

        super().__init__(
            status_code=403,
            detail=f"Permisos insuficientes. Faltan: {list(missing)}",
            error_code="INSUFFICIENT_PERMISSIONS",
            error_type="authorization_error",
            extra_data={
                "required_permissions": required_permissions,
                "granted_permissions": granted_permissions,
                "missing_permissions": list(missing),
                "user_id": user_id
            }
        )


# ========== EXCEPCIONES DE ROLES ==========

class RoleNotFoundException(RBACException):
    """Se lanza cuando se solicita un rol que no existe."""

    def __init__(self, role_id: Optional[str] = None, role_code: Optional[str] = None, company_id: Optional[int] = None):
        detail = "Rol no encontrado"
        if role_code:
            detail = f"Rol no encontrado: '{role_code}'"
        elif role_id:
            detail = f"Rol no encontrado: ID '{role_id}'"

        super().__init__(
            status_code=404,
            detail=detail,
            error_code="ROLE_NOT_FOUND",
            error_type="resource_error",
            extra_data={
                "role_id": role_id,
                "role_code": role_code,
                "company_id": company_id
            }
        )


class RoleAlreadyExistsException(RBACException):
    """Se lanza cuando se intenta crear un rol con código duplicado."""

    def __init__(self, role_code: str, company_id: int):
        super().__init__(
            status_code=409,
            detail=f"Ya existe un rol con el código '{role_code}' en esta empresa",
            error_code="ROLE_ALREADY_EXISTS",
            error_type="validation_error",
            extra_data={
                "role_code": role_code,
                "company_id": company_id
            }
        )


class SystemRoleModificationException(RBACException):
    """Se lanza cuando se intenta modificar un rol del sistema."""

    def __init__(self, role_code: str, action: str):
        super().__init__(
            status_code=403,
            detail=f"No se puede {action} el rol del sistema '{role_code}'",
            error_code="SYSTEM_ROLE_MODIFICATION",
            error_type="authorization_error",
            extra_data={
                "role_code": role_code,
                "action": action
            }
        )


class InvalidRoleHierarchyException(RBACException):
    """Se lanza cuando hay problemas con la jerarquía de roles."""

    def __init__(self, current_level: int, required_level: int, action: str = "perform_action"):
        super().__init__(
            status_code=403,
            detail=f"Nivel jerárquico insuficiente. Actual: {current_level}, Requerido: {required_level}",
            error_code="INVALID_ROLE_HIERARCHY",
            error_type="authorization_error",
            extra_data={
                "current_level": current_level,
                "required_level": required_level,
                "action": action
            }
        )


# ========== EXCEPCIONES DE USUARIOS ==========

class UserNotFoundException(RBACException):
    """Se lanza cuando se solicita un usuario que no existe."""

    def __init__(self, user_id: Optional[int] = None, username: Optional[str] = None, company_id: Optional[int] = None):
        detail = "Usuario no encontrado"
        if username:
            detail = f"Usuario no encontrado: '{username}'"
        elif user_id:
            detail = f"Usuario no encontrado: ID {user_id}"

        super().__init__(
            status_code=404,
            detail=detail,
            error_code="USER_NOT_FOUND",
            error_type="resource_error",
            extra_data={
                "user_id": user_id,
                "username": username,
                "company_id": company_id
            }
        )


class UserRoleAssignmentException(RBACException):
    """Se lanza cuando hay problemas asignando roles a usuarios."""

    def __init__(self, user_id: int, role_id: str, reason: str):
        super().__init__(
            status_code=400,
            detail=f"No se puede asignar rol al usuario: {reason}",
            error_code="USER_ROLE_ASSIGNMENT_ERROR",
            error_type="business_logic_error",
            extra_data={
                "user_id": user_id,
                "role_id": role_id,
                "reason": reason
            }
        )


# ========== EXCEPCIONES DE CATEGORÍAS ==========

class CategoryNotFoundException(RBACException):
    """Se lanza cuando se solicita una categoría que no existe."""

    def __init__(self, category_id: Optional[str] = None, category_code: Optional[str] = None, company_id: Optional[int] = None):
        detail = "Categoría de permisos no encontrada"
        if category_code:
            detail = f"Categoría no encontrada: '{category_code}'"
        elif category_id:
            detail = f"Categoría no encontrada: ID '{category_id}'"

        super().__init__(
            status_code=404,
            detail=detail,
            error_code="CATEGORY_NOT_FOUND",
            error_type="resource_error",
            extra_data={
                "category_id": category_id,
                "category_code": category_code,
                "company_id": company_id
            }
        )


class CategoryDeletionException(RBACException):
    """Se lanza cuando no se puede eliminar una categoría."""

    def __init__(self, category_code: str, reason: str, permission_count: int = 0):
        super().__init__(
            status_code=409,
            detail=f"No se puede eliminar la categoría '{category_code}': {reason}",
            error_code="CATEGORY_DELETION_ERROR",
            error_type="business_logic_error",
            extra_data={
                "category_code": category_code,
                "reason": reason,
                "permission_count": permission_count
            }
        )


# ========== EXCEPCIONES DE SEGURIDAD ==========

class MultiTenantViolationException(RBACException):
    """Se lanza cuando hay violaciones de aislamiento multi-tenant."""

    def __init__(self, resource_type: str, requested_company: int, user_company: int, user_id: int):
        super().__init__(
            status_code=403,
            detail=f"Acceso denegado: {resource_type} pertenece a otra empresa",
            error_code="MULTI_TENANT_VIOLATION",
            error_type="security_error",
            extra_data={
                "resource_type": resource_type,
                "requested_company": requested_company,
                "user_company": user_company,
                "user_id": user_id,
                "severity": "high"
            }
        )


class ExpiredPermissionException(RBACException):
    """Se lanza cuando se intenta usar un permiso expirado."""

    def __init__(self, permission_code: str, expires_at, user_id: int):
        super().__init__(
            status_code=403,
            detail=f"Permiso expirado: '{permission_code}'",
            error_code="EXPIRED_PERMISSION",
            error_type="authorization_error",
            extra_data={
                "permission_code": permission_code,
                "expires_at": str(expires_at),
                "user_id": user_id
            }
        )


# ========== HANDLER GLOBAL PARA FASTAPI ==========

def create_rbac_exception_handler():
    """
    Crea un handler global para excepciones RBAC en FastAPI.

    Uso:
        app.add_exception_handler(RBACException, create_rbac_exception_handler())
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from app.core.logging_config import log_security_event

    async def rbac_exception_handler(request: Request, exc: RBACException):
        """Handler global para excepciones RBAC."""

        # Log de seguridad para errores de autorización
        if exc.error_type in ["authorization_error", "security_error"]:
            log_security_event(
                event="rbac_exception",
                user_id=exc.extra_data.get("user_id"),
                company_id=exc.extra_data.get("company_id"),
                details={
                    "error_code": exc.error_code,
                    "error_type": exc.error_type,
                    "status_code": exc.status_code,
                    "path": str(request.url),
                    "method": request.method,
                    **exc.extra_data
                },
                level="WARNING" if exc.status_code < 500 else "ERROR"
            )

        # Respuesta estructurada
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "type": exc.error_type,
                    "message": exc.detail,
                    "details": exc.extra_data
                },
                "path": str(request.url),
                "method": request.method
            }
        )

    return rbac_exception_handler
