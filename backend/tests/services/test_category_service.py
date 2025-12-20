"""
🧪 TESTS UNITARIOS - CategoryService

Tests para el servicio de categorías que cubren:
- ✅ Listar categorías por empresa
- ✅ Crear categoría con validación de unicidad
- ✅ Crear categoría duplicada (debe fallar)
- ✅ Obtener categoría por ID
- ✅ Obtener categoría inexistente (debe fallar)
- ✅ Actualizar categoría
- ✅ Eliminar categoría (soft delete)
- ✅ Validaciones multi-tenant

Ejecutar tests:
    pytest backend/tests/services/test_category_service.py -v
"""

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead
from app.models.category import Category


class TestCategoryService:
    """
    🗂️ Tests para CategoryService

    Cada test es independiente y usa fixtures limpias.
    """

    @pytest.mark.asyncio
    async def test_get_categories_success(self, category_service: CategoryService, test_company):
        """
        📋 LISTAR CATEGORÍAS - Éxito

        Debe retornar lista de categorías de la empresa.
        """
        # Act
        categories = await category_service.get_categories(test_company.id)

        # Assert
        assert isinstance(categories, list)
        assert len(categories) >= 1  # Al menos la categoría de prueba

        # Verificar que todas las categorías pertenezcan a la empresa correcta
        for category in categories:
            assert category.company_id == test_company.id
            assert category.is_active == True

    @pytest.mark.asyncio
    async def test_get_categories_empty_company(self, category_service: CategoryService):
        """
        📋 LISTAR CATEGORÍAS - Empresa sin categorías

        Debe retornar lista vacía para empresa sin categorías.
        """
        # Act
        categories = await category_service.get_categories(99999)  # ID inexistente

        # Assert
        assert isinstance(categories, list)
        assert len(categories) == 0

    @pytest.mark.asyncio
    async def test_create_category_success(self, category_service: CategoryService, test_company):
        """
        ➕ CREAR CATEGORÍA - Éxito

        Debe crear categoría correctamente con validaciones.
        """
        # Arrange
        category_data = CategoryCreate(
            name="Nueva Categoría Test",
            description="Descripción de prueba",
            is_active=True
        )

        # Act
        result = await category_service.create_category(category_data, test_company.id)

        # Assert
        assert isinstance(result, CategoryRead)
        assert result.name == category_data.name
        assert result.description == category_data.description
        assert result.is_active == category_data.is_active
        assert result.company_id == test_company.id
        assert result.id is not None
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_category_duplicate_name(self, category_service: CategoryService, test_company):
        """
        ➕ CREAR CATEGORÍA - Nombre duplicado

        Debe fallar al intentar crear categoría con nombre existente.
        """
        # Arrange
        category_data = CategoryCreate(
            name="Test Category",  # Este nombre ya existe en test data
            description="Duplicada",
            is_active=True
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_service.create_category(category_data, test_company.id)

        assert exc_info.value.status_code == 400
        assert "Ya existe una categoría" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_category_different_companies(self, category_service: CategoryService, db_session):
        """
        ➕ CREAR CATEGORÍA - Unicidad por empresa

        El mismo nombre puede existir en diferentes empresas.
        """
        # Crear segunda empresa
        from app.models.company import Company
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

        # Crear categoría con mismo nombre en empresa diferente
        category_data = CategoryCreate(
            name="Test Category",  # Ya existe en test_company
            description="En otra empresa",
            is_active=True
        )

        # Act - Debe funcionar porque es empresa diferente
        result = await category_service.create_category(category_data, company2.id)

        # Assert
        assert result.name == category_data.name
        assert result.company_id == company2.id

    @pytest.mark.asyncio
    async def test_get_category_by_id_success(self, category_service: CategoryService, test_category, test_company):
        """
        🔍 OBTENER CATEGORÍA POR ID - Éxito

        Debe retornar la categoría correcta.
        """
        # Act
        result = await category_service.get_category_by_id(test_category.id, test_company.id)

        # Assert
        assert isinstance(result, CategoryRead)
        assert result.id == test_category.id
        assert result.name == test_category.name
        assert result.company_id == test_company.id

    @pytest.mark.asyncio
    async def test_get_category_by_id_not_found(self, category_service: CategoryService, test_company):
        """
        🔍 OBTENER CATEGORÍA POR ID - No encontrada

        Debe fallar cuando la categoría no existe.
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_service.get_category_by_id(99999, test_company.id)

        assert exc_info.value.status_code == 404
        assert "Categoría no encontrada" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_category_by_id_wrong_company(self, category_service: CategoryService, test_category):
        """
        🔍 OBTENER CATEGORÍA POR ID - Empresa equivocada

        Debe fallar cuando la categoría pertenece a otra empresa (seguridad multi-tenant).
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_service.get_category_by_id(test_category.id, 99999)  # Empresa diferente

        assert exc_info.value.status_code == 404
        assert "Categoría no encontrada" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_category_success(self, category_service: CategoryService, test_category, test_company):
        """
        ✏️ ACTUALIZAR CATEGORÍA - Éxito

        Debe actualizar correctamente los campos proporcionados.
        """
        # Arrange
        update_data = CategoryUpdate(
            name="Categoría Actualizada",
            description="Descripción actualizada"
            # is_active no se proporciona, debe mantenerse
        )

        # Act
        result = await category_service.update_category(test_category.id, update_data, test_company.id)

        # Assert
        assert isinstance(result, CategoryRead)
        assert result.id == test_category.id
        assert result.name == "Categoría Actualizada"
        assert result.description == "Descripción actualizada"
        assert result.is_active == test_category.is_active  # No cambió
        assert result.company_id == test_company.id

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, category_service: CategoryService, test_company):
        """
        ✏️ ACTUALIZAR CATEGORÍA - No encontrada

        Debe fallar cuando la categoría no existe.
        """
        update_data = CategoryUpdate(name="Nuevo nombre")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_service.update_category(99999, update_data, test_company.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_duplicate_name(self, category_service: CategoryService, test_category, test_company, db_session):
        """
        ✏️ ACTUALIZAR CATEGORÍA - Nombre duplicado

        Debe fallar al actualizar con nombre que ya existe.
        """
        # Crear segunda categoría
        category2 = Category(
            company_id=test_company.id,
            name="Otra Categoría",
            description="Segunda categoría",
            is_active=True
        )
        db_session.add(category2)
        await db_session.commit()

        # Intentar actualizar primera categoría con nombre de la segunda
        update_data = CategoryUpdate(name="Otra Categoría")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_service.update_category(test_category.id, update_data, test_company.id)

        assert exc_info.value.status_code == 400
        assert "Ya existe una categoría" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_category_success(self, category_service: CategoryService, test_category, test_company):
        """
        🗑️ ELIMINAR CATEGORÍA - Éxito (Soft Delete)

        Debe marcar la categoría como inactiva, no eliminarla.
        """
        # Act
        result = await category_service.delete_category(test_category.id, test_company.id)

        # Assert
        assert isinstance(result, dict)
        assert "message" in result
        assert "eliminada correctamente" in result["message"]

        # Verificar que la categoría aún existe pero está inactiva
        category = await category_service.get_category_by_id(test_category.id, test_company.id)
        assert category.is_active == False

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, category_service: CategoryService, test_company):
        """
        🗑️ ELIMINAR CATEGORÍA - No encontrada

        Debe fallar cuando la categoría no existe.
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await category_service.delete_category(99999, test_company.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_check_category_exists_found(self, category_service: CategoryService, test_company):
        """
        🔍 VERIFICAR EXISTENCIA - Encontrada

        Debe retornar la categoría cuando existe.
        """
        # Act
        result = await category_service._check_category_exists("Test Category", test_company.id)

        # Assert
        assert result is not None
        assert result.name == "Test Category"
        assert result.company_id == test_company.id

    @pytest.mark.asyncio
    async def test_check_category_exists_not_found(self, category_service: CategoryService, test_company):
        """
        🔍 VERIFICAR EXISTENCIA - No encontrada

        Debe retornar None cuando no existe.
        """
        # Act
        result = await category_service._check_category_exists("No Existe", test_company.id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_create(self, category_service: CategoryService, db_session):
        """
        🔒 AISLAMIENTO MULTI-TENANT - Crear

        Categorías de diferentes empresas deben estar completamente aisladas.
        """
        # Crear segunda empresa
        from app.models.company import Company
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

        # Crear categoría con mismo nombre en empresa diferente
        category_data = CategoryCreate(
            name="Shared Name",
            description="En company 1",
            is_active=True
        )

        # Crear en primera empresa
        result1 = await category_service.create_category(category_data, 1)  # test_company.id

        # Crear en segunda empresa (mismo nombre)
        category_data.description = "En company 2"
        result2 = await category_service.create_category(category_data, company2.id)

        # Assert - Ambas deben existir
        assert result1.company_id == 1
        assert result2.company_id == company2.id
        assert result1.name == result2.name  # Mismo nombre
        assert result1.id != result2.id      # IDs diferentes

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_list(self, category_service: CategoryService, db_session):
        """
        🔒 AISLAMIENTO MULTI-TENANT - Listar

        Cada empresa solo debe ver sus propias categorías.
        """
        # Crear segunda empresa
        from app.models.company import Company
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

        # Crear categorías en ambas empresas
        cat1 = Category(company_id=1, name="Company 1 Only", is_active=True)
        cat2 = Category(company_id=company2.id, name="Company 2 Only", is_active=True)
        db_session.add(cat1)
        db_session.add(cat2)
        await db_session.commit()

        # Listar categorías de cada empresa
        categories_company1 = await category_service.get_categories(1)
        categories_company2 = await category_service.get_categories(company2.id)

        # Assert - Cada empresa solo ve sus categorías
        company1_names = [c.name for c in categories_company1]
        company2_names = [c.name for c in categories_company2]

        assert "Company 1 Only" in company1_names
        assert "Company 2 Only" not in company1_names  # No debe ver la de company 2

        assert "Company 2 Only" in company2_names
        assert "Company 1 Only" not in company2_names  # No debe ver la de company 1
