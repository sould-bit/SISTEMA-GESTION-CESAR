"""
Pruebas unitarias para PermissionService.

Estas pruebas validan:
- Verificación de permisos de usuario
- Gestión de permisos por rol
- Cache de permisos (cuando se implemente)
- Validaciones de seguridad multi-tenant
"""

import pytest
from uuid import uuid4

from app.services.permission_service import PermissionService
from app.models import Permission, RolePermission


class TestPermissionService:
    """Pruebas para PermissionService."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_permission_user_has_permission(
        self,
        db_session,
        test_user,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que verifica correctamente cuando un usuario tiene un permiso."""
        # Arrange
        service = PermissionService(db_session)

        # Asignar rol al usuario
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        # Act
        has_permission = await service.check_permission(
            user_id=test_user.id,
            permission_code=test_permission.code,
            company_id=test_user.company_id
        )

        # Assert
        assert has_permission is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_permission_user_no_permission(
        self,
        db_session,
        test_user,
        test_company
    ):
        """Test que verifica correctamente cuando un usuario NO tiene un permiso."""
        # Arrange
        service = PermissionService(db_session)

        # Act
        has_permission = await service.check_permission(
            user_id=test_user.id,
            permission_code="nonexistent.permission",
            company_id=test_company.id
        )

        # Assert
        assert has_permission is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_permission_user_without_role(
        self,
        db_session,
        test_user,
        test_company
    ):
        """Test que verifica permisos para usuario sin rol asignado."""
        # Arrange
        service = PermissionService(db_session)
        test_user.role_id = None
        db_session.add(test_user)
        await db_session.commit()

        # Act
        has_permission = await service.check_permission(
            user_id=test_user.id,
            permission_code="any.permission",
            company_id=test_company.id
        )

        # Assert
        assert has_permission is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_permissions(
        self,
        db_session,
        test_user,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que obtiene correctamente los permisos de un usuario."""
        # Arrange
        service = PermissionService(db_session)
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        # Act
        permissions = await service.get_user_permissions(
            user_id=test_user.id,
            company_id=test_user.company_id
        )

        # Assert
        assert len(permissions) == 1
        assert permissions[0].id == test_permission.id
        assert permissions[0].code == test_permission.code

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user_permission_codes(
        self,
        db_session,
        test_user,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que obtiene solo los códigos de permisos de un usuario."""
        # Arrange
        service = PermissionService(db_session)
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        # Act
        permission_codes = await service.get_user_permission_codes(
            user_id=test_user.id,
            company_id=test_user.company_id
        )

        # Assert
        assert len(permission_codes) == 1
        assert permission_codes[0] == test_permission.code

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_grant_permission_to_role(
        self,
        db_session,
        test_role,
        test_permission
    ):
        """Test que otorga un permiso a un rol correctamente."""
        # Arrange
        service = PermissionService(db_session)
        granted_by = 1

        # Act
        role_permission = await service.grant_permission_to_role(
            role_id=test_role.id,
            permission_id=test_permission.id,
            granted_by=granted_by
        )

        # Assert
        assert role_permission.role_id == test_role.id
        assert role_permission.permission_id == test_permission.id
        assert role_permission.granted_by == granted_by

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_grant_duplicate_permission_fails(
        self,
        db_session,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que falla al intentar otorgar un permiso duplicado."""
        # Arrange
        service = PermissionService(db_session)

        # Act & Assert
        with pytest.raises(ValueError, match="El permiso ya está asignado"):
            await service.grant_permission_to_role(
                role_id=test_role.id,
                permission_id=test_permission.id,
                granted_by=1
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_revoke_permission_from_role(
        self,
        db_session,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que revoca un permiso de un rol correctamente."""
        # Arrange
        service = PermissionService(db_session)

        # Act
        success = await service.revoke_permission_from_role(
            role_id=test_role.id,
            permission_id=test_permission.id
        )

        # Assert
        assert success is True

        # Verificar que se eliminó
        result = await db_session.execute(
            db_session.query(RolePermission).filter_by(
                role_id=test_role.id,
                permission_id=test_permission.id
            )
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_revoke_nonexistent_permission(
        self,
        db_session,
        test_role
    ):
        """Test que maneja correctamente la revocación de permiso inexistente."""
        # Arrange
        service = PermissionService(db_session)
        fake_permission_id = uuid4()

        # Act
        success = await service.revoke_permission_from_role(
            role_id=test_role.id,
            permission_id=fake_permission_id
        )

        # Assert
        assert success is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_role_permissions(
        self,
        db_session,
        test_role,
        test_permission,
        test_role_permission
    ):
        """Test que obtiene permisos de un rol correctamente."""
        # Arrange
        service = PermissionService(db_session)

        # Act
        permissions = await service.get_role_permissions(
            role_id=test_role.id,
            company_id=test_role.company_id
        )

        # Assert
        assert len(permissions) == 1
        assert permissions[0].id == test_permission.id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_permissions(
        self,
        db_session,
        test_company,
        test_permission
    ):
        """Test que lista todos los permisos de una empresa."""
        # Arrange
        service = PermissionService(db_session)

        # Act
        permissions = await service.list_permissions(
            company_id=test_company.id
        )

        # Assert
        assert len(permissions) >= 1
        assert any(p.id == test_permission.id for p in permissions)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_permission(
        self,
        db_session,
        test_company,
        test_permission_category
    ):
        """Test que crea un permiso correctamente."""
        # Arrange
        service = PermissionService(db_session)

        # Act
        permission = await service.create_permission(
            company_id=test_company.id,
            category_id=test_permission_category.id,
            code="new.test.permission",
            name="Nuevo Permiso de Prueba",
            resource="new",
            action="test"
        )

        # Assert
        assert permission.code == "new.test.permission"
        assert permission.name == "Nuevo Permiso de Prueba"
        assert permission.company_id == test_company.id
        assert permission.category_id == test_permission_category.id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_duplicate_permission_fails(
        self,
        db_session,
        test_company,
        test_permission_category,
        test_permission
    ):
        """Test que falla al crear un permiso con código duplicado."""
        # Arrange
        service = PermissionService(db_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe un permiso"):
            await service.create_permission(
                company_id=test_company.id,
                category_id=test_permission_category.id,
                code=test_permission.code,  # Código duplicado
                name="Duplicado",
                resource="test",
                action="duplicate"
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_permission(
        self,
        db_session,
        test_permission,
        test_company
    ):
        """Test que actualiza un permiso correctamente."""
        # Arrange
        service = PermissionService(db_session)
        new_name = "Nombre Actualizado"

        # Act
        updated = await service.update_permission(
            permission_id=test_permission.id,
            company_id=test_company.id,
            name=new_name
        )

        # Assert
        assert updated.name == new_name
        assert updated.id == test_permission.id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_system_permission_fails(
        self,
        db_session,
        test_company
    ):
        """Test que falla al intentar actualizar un permiso del sistema."""
        # Arrange
        service = PermissionService(db_session)

        # Crear permiso del sistema
        system_perm = Permission(
            name="Permiso Sistema",
            code="system.permission",
            resource="system",
            action="permission",
            company_id=test_company.id,
            category_id=test_permission_category.id,
            is_system=True,
            is_active=True
        )
        db_session.add(system_perm)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="No se pueden modificar permisos del sistema"):
            await service.update_permission(
                permission_id=system_perm.id,
                company_id=test_company.id,
                name="Nuevo Nombre"
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_permission(
        self,
        db_session,
        test_permission,
        test_company
    ):
        """Test que elimina (soft delete) un permiso correctamente."""
        # Arrange
        service = PermissionService(db_session)

        # Act
        success = await service.delete_permission(
            permission_id=test_permission.id,
            company_id=test_company.id
        )

        # Assert
        assert success is True

        # Verificar soft delete
        await db_session.refresh(test_permission)
        assert test_permission.is_active is False
