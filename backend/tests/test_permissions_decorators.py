"""
Pruebas para decoradores de permisos.

Estas pruebas validan que los decoradores de autorización
funcionen correctamente con las dependencias FastAPI.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_permission, require_any_permission, require_all_permissions
from app.models import User


class TestPermissionDecorators:
    """Pruebas para decoradores de permisos."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_permission_grants_access_with_valid_permission(
        self,
        db_session,
        test_user,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que el decorador permite acceso cuando el usuario tiene el permiso."""
        # Arrange
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        # Crear decorador
        decorator = require_permission("test.permission")
        decorated_func = decorator(self._mock_endpoint)

        # Act
        result = await decorated_func(
            session=db_session,
            current_user=test_user
        )

        # Assert
        assert result == "success"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_permission_denies_access_without_permission(
        self,
        db_session,
        test_user
    ):
        """Test que el decorador deniega acceso cuando el usuario no tiene el permiso."""
        # Arrange
        decorator = require_permission("nonexistent.permission")
        decorated_func = decorator(self._mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=db_session,
                current_user=test_user
            )

        assert exc_info.value.status_code == 403
        assert "Permiso denegado" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_permission_denies_access_without_user(self, db_session):
        """Test que el decorador deniega acceso cuando no hay usuario autenticado."""
        # Arrange
        decorator = require_permission("any.permission")
        decorated_func = decorator(self._mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=db_session,
                current_user=None
            )

        assert exc_info.value.status_code == 401
        assert "No autenticado" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_permission_denies_access_without_session(self, test_user):
        """Test que el decorador deniega acceso cuando no hay sesión de BD."""
        # Arrange
        decorator = require_permission("any.permission")
        decorated_func = decorator(self._mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=None,
                current_user=test_user
            )

        assert exc_info.value.status_code == 500
        assert "sesión de BD no disponible" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_any_permission_grants_access_with_one_valid_permission(
        self,
        db_session,
        test_user,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que permite acceso si el usuario tiene AL MENOS uno de los permisos requeridos."""
        # Arrange
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        decorator = require_any_permission(["test.permission", "other.permission"])
        decorated_func = decorator(self._mock_endpoint)

        # Act
        result = await decorated_func(
            session=db_session,
            current_user=test_user
        )

        # Assert
        assert result == "success"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_any_permission_denies_access_without_any_permission(
        self,
        db_session,
        test_user
    ):
        """Test que deniega acceso si el usuario no tiene ninguno de los permisos requeridos."""
        # Arrange
        decorator = require_any_permission(["nonexistent.perm1", "nonexistent.perm2"])
        decorated_func = decorator(self._mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=db_session,
                current_user=test_user
            )

        assert exc_info.value.status_code == 403
        assert "se requiere uno de" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_all_permissions_grants_access_with_all_permissions(
        self,
        db_session,
        test_user,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que permite acceso solo si el usuario tiene TODOS los permisos requeridos."""
        # Arrange
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        # Solo requiere el permiso que tiene
        decorator = require_all_permissions(["test.permission"])
        decorated_func = decorator(self._mock_endpoint)

        # Act
        result = await decorated_func(
            session=db_session,
            current_user=test_user
        )

        # Assert
        assert result == "success"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_require_all_permissions_denies_access_missing_one_permission(
        self,
        db_session,
        test_user,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que deniega acceso si falta al menos uno de los permisos requeridos."""
        # Arrange
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        # Requiere un permiso que tiene y otro que no
        decorator = require_all_permissions(["test.permission", "missing.permission"])
        decorated_func = decorator(self._mock_endpoint)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await decorated_func(
                session=db_session,
                current_user=test_user
            )

        assert exc_info.value.status_code == 403
        assert "se requieren todos estos permisos" in exc_info.value.detail

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_decorator_preserves_function_metadata(self):
        """Test que los decoradores preservan los metadatos de la función original."""
        # Arrange
        decorator = require_permission("test.permission")
        decorated_func = decorator(self._mock_endpoint_with_metadata)

        # Assert
        assert decorated_func.__name__ == "mock_endpoint"
        assert decorated_func.__doc__ == "Mock endpoint for testing"

    async def _mock_endpoint(self, session: AsyncSession, current_user: User):
        """Mock endpoint for testing."""
        return "success"

    async def _mock_endpoint_with_metadata(self, session: AsyncSession, current_user: User):
        """Mock endpoint for testing."""
        return "success"
