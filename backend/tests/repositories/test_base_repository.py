"""
🧪 TESTS UNITARIOS - BaseRepository

Tests para el repositorio base que cubren:
- ✅ Operaciones CRUD básicas
- ✅ Filtros multi-tenant automáticos
- ✅ Manejo de transacciones
- ✅ Validaciones de existencia
- ✅ Conteo de registros
- ✅ Paginación

Ejecutar tests:
    pytest backend/tests/repositories/test_base_repository.py -v
"""

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.repositories.base_repository import BaseRepository
from app.models.category import Category
from app.models.company import Company


class TestBaseRepository:
    """
    🏗️ Tests para BaseRepository

    Tests de operaciones CRUD con aislamiento multi-tenant.
    """

    @pytest.fixture
    async def category_repo(self, db_session):
        """Fixture para repositorio de categorías"""
        return BaseRepository(Category, db_session)

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, category_repo, test_category, test_company):
        """
        🔍 GET BY ID - Éxito

        Debe retornar el registro correcto con filtro multi-tenant.
        """
        # Act
        result = await category_repo.get_by_id(test_category.id, test_company.id)

        # Assert
        assert result is not None
        assert result.id == test_category.id
        assert result.company_id == test_company.id

    @pytest.mark.asyncio
    async def test_get_by_id_wrong_company(self, category_repo, test_category):
        """
        🔍 GET BY ID - Empresa equivocada

        Debe retornar None por aislamiento multi-tenant.
        """
        # Act
        result = await category_repo.get_by_id(test_category.id, 99999)  # Empresa diferente

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_or_404_success(self, category_repo, test_category, test_company):
        """
        🔍 GET BY ID OR 404 - Éxito

        Debe retornar el registro cuando existe.
        """
        # Act
        result = await category_repo.get_by_id_or_404(test_category.id, test_company.id)

        # Assert
        assert result.id == test_category.id

    @pytest.mark.asyncio
    async def test_get_by_id_or_404_not_found(self, category_repo, test_company):
        """
        🔍 GET BY ID OR 404 - No encontrado

        Debe lanzar HTTPException 404 cuando no existe.
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_repo.get_by_id_or_404(99999, test_company.id)

        assert exc_info.value.status_code == 404
        assert "no encontrado" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_success(self, category_repo, test_company):
        """
        📋 LIST - Éxito

        Debe retornar lista de registros con filtros.
        """
        # Act
        results = await category_repo.list(test_company.id)

        # Assert
        assert isinstance(results, list)
        assert len(results) >= 1

        # Verificar que todos los registros pertenezcan a la empresa
        for result in results:
            assert result.company_id == test_company.id

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, category_repo, test_company, db_session):
        """
        📋 LIST - Con paginación

        Debe respetar límites de paginación.
        """
        # Crear más categorías para probar paginación
        for i in range(5):
            category = Category(
                company_id=test_company.id,
                name=f"Test Category {i}",
                is_active=True
            )
            db_session.add(category)
        await db_session.commit()

        # Act - Pedir solo 3 registros
        results = await category_repo.list(test_company.id, skip=0, limit=3)

        # Assert
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_list_empty_company(self, category_repo):
        """
        📋 LIST - Empresa sin registros

        Debe retornar lista vacía.
        """
        # Act
        results = await category_repo.list(99999)  # Empresa inexistente

        # Assert
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_create_success(self, category_repo, test_company):
        """
        ➕ CREATE - Éxito

        Debe crear registro correctamente.
        """
        # Arrange
        data = {
            "company_id": test_company.id,
            "name": "Nueva Categoría",
            "description": "Descripción",
            "is_active": True
        }

        # Act
        result = await category_repo.create(data)

        # Assert
        assert result.id is not None
        assert result.name == "Nueva Categoría"
        assert result.company_id == test_company.id
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_update_success(self, category_repo, test_category, test_company):
        """
        ✏️ UPDATE - Éxito

        Debe actualizar campos correctamente.
        """
        # Act
        result = await category_repo.update(
            test_category.id,
            test_company.id,
            {"name": "Nombre Actualizado", "description": "Nueva descripción"}
        )

        # Assert
        assert result.id == test_category.id
        assert result.name == "Nombre Actualizado"
        assert result.description == "Nueva descripción"
        assert result.company_id == test_company.id

    @pytest.mark.asyncio
    async def test_update_not_found(self, category_repo, test_company):
        """
        ✏️ UPDATE - No encontrado

        Debe fallar cuando el registro no existe.
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_repo.update(99999, test_company.id, {"name": "Test"})

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_soft_success(self, category_repo, test_category, test_company):
        """
        🗑️ DELETE SOFT - Éxito

        Debe marcar como inactivo, no eliminar físicamente.
        """
        # Act
        result = await category_repo.delete(test_category.id, test_company.id, soft_delete=True)

        # Assert
        assert result == True

        # Verificar que aún existe pero está inactivo
        category = await category_repo.get_by_id(test_category.id, test_company.id)
        assert category.is_active == False

    @pytest.mark.asyncio
    async def test_delete_hard_success(self, category_repo, test_category, test_company):
        """
        🗑️ DELETE HARD - Éxito

        Debe eliminar físicamente el registro.
        """
        # Act
        result = await category_repo.delete(test_category.id, test_company.id, soft_delete=False)

        # Assert
        assert result == True

        # Verificar que ya no existe
        category = await category_repo.get_by_id(test_category.id, test_company.id)
        assert category is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, category_repo, test_company):
        """
        🗑️ DELETE - No encontrado

        Debe fallar cuando el registro no existe.
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_repo.delete(99999, test_company.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_exists_true(self, category_repo, test_category, test_company):
        """
        🔍 EXISTS - Verdadero

        Debe retornar True cuando el registro existe.
        """
        # Act
        result = await category_repo.exists(test_category.id, test_company.id)

        # Assert
        assert result == True

    @pytest.mark.asyncio
    async def test_exists_false(self, category_repo, test_company):
        """
        🔍 EXISTS - Falso

        Debe retornar False cuando el registro no existe.
        """
        # Act
        result = await category_repo.exists(99999, test_company.id)

        # Assert
        assert result == False

    @pytest.mark.asyncio
    async def test_count_success(self, category_repo, test_company, db_session):
        """
        🔢 COUNT - Éxito

        Debe contar correctamente los registros.
        """
        # Crear algunas categorías adicionales
        for i in range(3):
            category = Category(
                company_id=test_company.id,
                name=f"Count Test {i}",
                is_active=True
            )
            db_session.add(category)
        await db_session.commit()

        # Act
        count = await category_repo.count(test_company.id)

        # Assert
        assert count >= 4  # Al menos las 3 nuevas + la de prueba

    @pytest.mark.asyncio
    async def test_count_empty_company(self, category_repo):
        """
        🔢 COUNT - Empresa vacía

        Debe retornar 0 para empresa sin registros.
        """
        # Act
        count = await category_repo.count(99999)

        # Assert
        assert count == 0

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_create(self, db_session, test_company):
        """
        🔒 MULTI-TENANT - Crear en diferentes empresas

        Registros pueden tener mismos datos en empresas diferentes.
        """
        # Crear segunda empresa
        company2 = Company(
            name="Company 2",
            slug="company-2",
            owner_name="Owner 2",
            owner_email="owner2@test.com",
            plan="trial",
            is_active=True
        )
        db_session.add(company2)
        await db_session.commit()

        # Crear repositorio
        repo = BaseRepository(Category, db_session)

        # Crear categorías con mismo nombre en empresas diferentes
        data1 = {"company_id": test_company.id, "name": "Shared Name", "is_active": True}
        data2 = {"company_id": company2.id, "name": "Shared Name", "is_active": True}

        result1 = await repo.create(data1)
        result2 = await repo.create(data2)

        # Assert
        assert result1.company_id == test_company.id
        assert result2.company_id == company2.id
        assert result1.name == result2.name
        assert result1.id != result2.id

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_list(self, db_session, test_company):
        """
        🔒 MULTI-TENANT - Listar por empresa

        Cada empresa solo ve sus propios registros.
        """
        # Crear segunda empresa
        company2 = Company(
            name="Company 2",
            slug="company-2",
            owner_name="Owner 2",
            owner_email="owner2@test.com",
            plan="trial",
            is_active=True
        )
        db_session.add(company2)
        await db_session.commit()

        # Crear repositorio
        repo = BaseRepository(Category, db_session)

        # Crear datos en ambas empresas
        await repo.create({"company_id": test_company.id, "name": "Company 1 Data", "is_active": True})
        await repo.create({"company_id": company2.id, "name": "Company 2 Data", "is_active": True})

        # Listar por empresa
        results1 = await repo.list(test_company.id)
        results2 = await repo.list(company2.id)

        # Assert - Aislamiento completo
        names1 = [r.name for r in results1]
        names2 = [r.name for r in results2]

        assert "Company 1 Data" in names1
        assert "Company 2 Data" not in names1

        assert "Company 2 Data" in names2
        assert "Company 1 Data" not in names2
