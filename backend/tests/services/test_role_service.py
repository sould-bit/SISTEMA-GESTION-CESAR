"""
Pruebas unitarias para RoleService.

Estas pruebas validan:
- CRUD de roles
- Asignación de roles a usuarios
- Clonación de roles
- Validaciones de jerarquía y multi-tenancy
"""

import pytest
from uuid import uuid4

from app.services.role_service import RoleService
from app.models import Role, User


class TestRoleService:
    """Pruebas para RoleService."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_role(
        self,
        db_session,
        test_company,
        test_permission
    ):
        """Test que crea un rol correctamente."""
        # Arrange
        service = RoleService(db_session)

        # Act
        role = await service.create_role(
            company_id=test_company.id,
            name="Rol de Prueba",
            code="test_role",
            description="Descripción de prueba",
            hierarchy_level=50,
            permission_ids=[test_permission.id]
        )

        # Assert
        assert role.name == "Rol de Prueba"
        assert role.code == "test_role"
        assert role.company_id == test_company.id
        assert role.hierarchy_level == 50
        assert role.is_system is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_role_without_permissions(
        self,
        db_session,
        test_company
    ):
        """Test que crea un rol sin permisos asignados."""
        # Arrange
        service = RoleService(db_session)

        # Act
        role = await service.create_role(
            company_id=test_company.id,
            name="Rol Simple",
            code="simple_role"
        )

        # Assert
        assert role.name == "Rol Simple"
        assert role.code == "simple_role"
        assert role.company_id == test_company.id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_duplicate_role_fails(
        self,
        db_session,
        test_company,
        test_role
    ):
        """Test que falla al crear un rol con código duplicado."""
        # Arrange
        service = RoleService(db_session)

        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe un rol"):
            await service.create_role(
                company_id=test_company.id,
                name="Rol Duplicado",
                code=test_role.code  # Código duplicado
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_role(
        self,
        db_session,
        test_role,
        test_company
    ):
        """Test que actualiza un rol correctamente."""
        # Arrange
        service = RoleService(db_session)
        new_name = "Nombre Actualizado"
        new_description = "Descripción actualizada"

        # Act
        updated = await service.update_role(
            role_id=test_role.id,
            company_id=test_company.id,
            name=new_name,
            description=new_description
        )

        # Assert
        assert updated.name == new_name
        assert updated.description == new_description

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_system_role_fails(
        self,
        db_session,
        test_company
    ):
        """Test que falla al intentar actualizar un rol del sistema."""
        # Arrange
        service = RoleService(db_session)

        # Crear rol del sistema
        system_role = Role(
            name="Rol Sistema",
            code="system_role",
            company_id=test_company.id,
            is_system=True,
            is_active=True
        )
        db_session.add(system_role)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="No se pueden modificar roles del sistema"):
            await service.update_role(
                role_id=system_role.id,
                company_id=test_company.id,
                name="Nuevo Nombre"
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_role(
        self,
        db_session,
        test_role,
        test_company
    ):
        """Test que elimina (soft delete) un rol correctamente."""
        # Arrange
        service = RoleService(db_session)

        # Act
        success = await service.delete_role(
            role_id=test_role.id,
            company_id=test_company.id
        )

        # Assert
        assert success is True

        # Verificar soft delete
        await db_session.refresh(test_role)
        assert test_role.is_active is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_system_role_fails(
        self,
        db_session,
        test_company
    ):
        """Test que falla al intentar eliminar un rol del sistema."""
        # Arrange
        service = RoleService(db_session)

        # Crear rol del sistema
        system_role = Role(
            name="Rol Sistema",
            code="system_role",
            company_id=test_company.id,
            is_system=True,
            is_active=True
        )
        db_session.add(system_role)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="No se pueden eliminar roles del sistema"):
            await service.delete_role(
                role_id=system_role.id,
                company_id=test_company.id
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_role_with_users_fails(
        self,
        db_session,
        test_role,
        test_company,
        test_user
    ):
        """Test que falla al intentar eliminar un rol con usuarios asignados."""
        # Arrange
        service = RoleService(db_session)
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="tiene.*usuario"):
            await service.delete_role(
                role_id=test_role.id,
                company_id=test_company.id
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_role(
        self,
        db_session,
        test_role,
        test_company
    ):
        """Test que obtiene un rol correctamente."""
        # Arrange
        service = RoleService(db_session)

        # Act
        role = await service.get_role(
            role_id=test_role.id,
            company_id=test_company.id
        )

        # Assert
        assert role.id == test_role.id
        assert role.name == test_role.name

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_role_with_permissions(
        self,
        db_session,
        test_role,
        test_company,
        test_role_permission
    ):
        """Test que obtiene un rol con sus permisos."""
        # Arrange
        service = RoleService(db_session)

        # Act
        role = await service.get_role(
            role_id=test_role.id,
            company_id=test_company.id,
            include_permissions=True
        )

        # Assert
        assert role.id == test_role.id
        assert len(role.role_permissions) == 1
        assert role.role_permissions[0].permission_id == test_role_permission.permission_id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_roles(
        self,
        db_session,
        test_company,
        test_role
    ):
        """Test que lista roles de una empresa."""
        # Arrange
        service = RoleService(db_session)

        # Act
        roles = await service.list_roles(
            company_id=test_company.id
        )

        # Assert
        assert len(roles) >= 1
        assert any(r.id == test_role.id for r in roles)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_assign_role_to_user(
        self,
        db_session,
        test_user,
        test_role,
        test_company
    ):
        """Test que asigna un rol a un usuario correctamente."""
        # Arrange
        service = RoleService(db_session)

        # Act
        user = await service.assign_role_to_user(
            user_id=test_user.id,
            role_id=test_role.id,
            company_id=test_company.id
        )

        # Assert
        assert user.role_id == test_role.id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_assign_nonexistent_role_fails(
        self,
        db_session,
        test_user,
        test_company
    ):
        """Test que falla al asignar un rol inexistente."""
        # Arrange
        service = RoleService(db_session)
        fake_role_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="Rol no encontrado"):
            await service.assign_role_to_user(
                user_id=test_user.id,
                role_id=fake_role_id,
                company_id=test_company.id
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_assign_role_to_nonexistent_user_fails(
        self,
        db_session,
        test_role,
        test_company
    ):
        """Test que falla al asignar rol a usuario inexistente."""
        # Arrange
        service = RoleService(db_session)
        fake_user_id = 99999

        # Act & Assert
        with pytest.raises(ValueError, match="Usuario no encontrado"):
            await service.assign_role_to_user(
                user_id=fake_user_id,
                role_id=test_role.id,
                company_id=test_company.id
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_clone_role(
        self,
        db_session,
        test_role,
        test_company,
        test_permission,
        test_role_permission
    ):
        """Test que clona un rol con todos sus permisos."""
        # Arrange
        service = RoleService(db_session)
        new_name = "Rol Clonado"
        new_code = "cloned_role"

        # Act
        cloned_role = await service.clone_role(
            role_id=test_role.id,
            company_id=test_company.id,
            new_name=new_name,
            new_code=new_code
        )

        # Assert
        assert cloned_role.name == new_name
        assert cloned_role.code == new_code
        assert cloned_role.hierarchy_level == test_role.hierarchy_level
        assert cloned_role.company_id == test_company.id

        # Verificar que tiene los mismos permisos
        cloned_permissions = await service.get_role_permissions(
            role_id=cloned_role.id,
            company_id=test_company.id
        )
        assert len(cloned_permissions) == 1
        assert cloned_permissions[0].id == test_permission.id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_role_by_code(
        self,
        db_session,
        test_role,
        test_company
    ):
        """Test que obtiene un rol por código."""
        # Arrange
        service = RoleService(db_session)

        # Act
        role = await service.get_role_by_code(
            code=test_role.code,
            company_id=test_company.id
        )

        # Assert
        assert role.id == test_role.id
        assert role.code == test_role.code

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_users_with_role(
        self,
        db_session,
        test_role,
        test_company,
        test_user
    ):
        """Test que obtiene usuarios con un rol específico."""
        # Arrange
        service = RoleService(db_session)
        test_user.role_id = test_role.id
        db_session.add(test_user)
        await db_session.commit()

        # Act
        users = await service.get_users_with_role(
            role_id=test_role.id,
            company_id=test_company.id
        )

        # Assert
        assert len(users) == 1
        assert users[0].id == test_user.id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_can_inherit_from_higher_level(
        self,
        db_session,
        test_role
    ):
        """Test que verifica herencia de permisos por nivel jerárquico."""
        # Arrange
        higher_role = Role(
            name="Rol Superior",
            code="higher_role",
            company_id=test_role.company_id,
            hierarchy_level=80,  # Nivel más alto
            is_active=True
        )

        # Act
        can_inherit = test_role.can_inherit_from(higher_role)

        # Assert
        assert can_inherit is True  # 50 puede heredar de 80

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_cannot_inherit_from_lower_level(
        self,
        db_session,
        test_role
    ):
        """Test que verifica que no se puede heredar de niveles inferiores."""
        # Arrange
        lower_role = Role(
            name="Rol Inferior",
            code="lower_role",
            company_id=test_role.company_id,
            hierarchy_level=30,  # Nivel más bajo
            is_active=True
        )

        # Act
        can_inherit = test_role.can_inherit_from(lower_role)

        # Assert
        assert can_inherit is False  # 50 NO puede heredar de 30
