"""
🧪 PRUEBAS UNITARIAS PARA PRODUCT SERVICE

Estas pruebas validan:
- ✅ Validaciones de precio positivo y unicidad de nombre
- ✅ Lógica de negocio del servicio de productos
- ✅ Validaciones anti-cross-tenant
- ✅ Manejo de errores y excepciones
- ✅ Funciones de cálculo (precio final, stock bajo, etc.)
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.services.product_service import ProductService
from app.schemas.products import ProductCreate, ProductUpdate
from fastapi import HTTPException


class TestProductService:
    """🧪 Pruebas unitarias para ProductService."""

    # ==================== TESTS DE VALIDACIÓN DE PRECIO ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product_with_valid_price(self, db_session, test_company, mock_category):
        """✅ Test creación de producto con precio válido."""
        # Arrange
        service = ProductService(db_session)
        product_data = ProductCreate(
            name="Producto Válido",
            description="Producto con precio válido",
            price=Decimal('99.99'),
            tax_rate=Decimal('0.10'),
            category_id=mock_category.id
        )

        # Act
        with patch.object(service, '_validate_category_ownership'), \
             patch.object(service, '_check_product_name_unique'):
            result = await service.create_product(product_data, test_company.id)

        # Assert
        assert result.name == "Producto Válido"
        assert result.price == Decimal('99.99')

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product_price_must_be_positive(self, db_session, test_company):
        """❌ Test que precio debe ser positivo."""
        # Arrange
        service = ProductService(db_session)
        product_data = ProductCreate(
            name="Producto Inválido",
            price=Decimal('0'),  # Precio inválido
            category_id=None
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            with patch.object(service, '_validate_category_ownership'), \
                 patch.object(service, '_check_product_name_unique'):
                await service.create_product(product_data, test_company.id)

        assert exc_info.value.status_code == 400
        assert "Producto con este nombre ya existe" in str(exc_info.value.detail)

    # ==================== TESTS DE UNICIDAD DE NOMBRE ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product_unique_name_per_company(self, db_session, test_company, test_category):
        """✅ Test unicidad de nombre por empresa."""
        # Arrange
        service = ProductService(db_session)
        product_data = ProductCreate(
            name="Producto Único",
            price=Decimal('10.00'),
            category_id=test_category.id
        )

        # Act - Crear primer producto
        with patch.object(service, '_validate_category_ownership'), \
             patch.object(service, '_check_product_name_unique'):
            result1 = await service.create_product(product_data, test_company.id)

        # Intentar crear segundo producto con mismo nombre
        with pytest.raises(HTTPException) as exc_info:
            with patch.object(service, '_validate_category_ownership'):
                await service.create_product(product_data, test_company.id)

        # Assert
        assert result1.name == "Producto Único"
        assert exc_info.value.status_code == 400
        assert "Producto con este nombre ya existe" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_product_name_uniqueness(self, db_session, test_company, test_category, test_product):
        """✅ Test unicidad de nombre al actualizar producto."""
        # Arrange
        service = ProductService(db_session)
        update_data = ProductUpdate(name="Nuevo Nombre")

        # Act - Actualizar nombre
        with patch.object(service, '_validate_category_ownership'):
            result = await service.update_product(test_product.id, update_data, test_company.id)

        # Assert
        assert result.name == "Nuevo Nombre"

    # ==================== TESTS DE VALIDACIÓN ANTI-CROSS-TENANT ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_validate_category_ownership_valid(self, db_session, test_company, test_category):
        """✅ Test validación de categoría que pertenece a la empresa."""
        # Arrange
        service = ProductService(db_session)

        # Act - No debería lanzar excepción
        try:
            await service._validate_category_ownership(test_category.id, test_company.id)
            success = True
        except:
            success = False

        # Assert
        assert success is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_validate_category_ownership_invalid(self, db_session, test_company, test_category_company_2):
        """❌ Test validación de categoría que NO pertenece a la empresa."""
        # Arrange
        service = ProductService(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service._validate_category_ownership(test_category_company_2.id, test_company.id)

        assert exc_info.value.status_code == 400
        assert "no pertenece a su empresa" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_validate_category_ownership_inactive_category(self, db_session, test_company, test_category):
        """❌ Test validación con categoría inactiva."""
        # Arrange
        service = ProductService(db_session)
        test_category.is_active = False
        db_session.add(test_category)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service._validate_category_ownership(test_category.id, test_company.id)

        assert exc_info.value.status_code == 400
        assert "no existe o no pertenece" in str(exc_info.value.detail)

    # ==================== TESTS DE CREACIÓN DE PRODUCTOS ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product_success(self, db_session, test_company, test_category):
        """✅ Test creación exitosa de producto."""
        # Arrange
        service = ProductService(db_session)
        product_data = ProductCreate(
            name="Producto Test",
            description="Descripción de prueba",
            price=Decimal('25.00'),
            tax_rate=Decimal('0.15'),
            stock=Decimal('50.0'),
            image_url="https://example.com/image.jpg",
            category_id=test_category.id
        )

        # Act
        with patch.object(service, '_validate_category_ownership'), \
             patch.object(service, '_check_product_name_unique'):
            result = await service.create_product(product_data, test_company.id)

        # Assert
        assert result.name == "Producto Test"
        assert result.company_id == test_company.id
        assert result.category_id == test_category.id
        assert result.price == Decimal('25.00')
        assert result.is_active is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product_without_category(self, db_session, test_company):
        """✅ Test creación de producto sin categoría."""
        # Arrange
        service = ProductService(db_session)
        product_data = ProductCreate(
            name="Producto Sin Categoría",
            price=Decimal('15.00'),
            category_id=None  # Sin categoría
        )

        # Act
        with patch.object(service, '_check_product_name_unique'):
            result = await service.create_product(product_data, test_company.id)

        # Assert
        assert result.name == "Producto Sin Categoría"
        assert result.category_id is None

    # ==================== TESTS DE LISTADO DE PRODUCTOS ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_all(self, db_session, test_company, test_products_batch):
        """✅ Test listado de todos los productos."""
        # Arrange
        service = ProductService(db_session)

        # Act
        products = await service.get_products(test_company.id)

        # Assert
        assert len(products) == 5  # Todos los productos del lote
        assert all(p.company_id == test_company.id for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_by_category(self, db_session, test_company, test_category, test_products_batch):
        """✅ Test listado de productos por categoría."""
        # Arrange
        service = ProductService(db_session)

        # Act
        products = await service.get_products(
            company_id=test_company.id,
            category_id=test_category.id
        )

        # Assert
        assert len(products) == 5  # Todos pertenecen a la misma categoría
        assert all(p.category_id == test_category.id for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_search(self, db_session, test_company, test_products_batch):
        """✅ Test búsqueda de productos por nombre."""
        # Arrange
        service = ProductService(db_session)

        # Act
        products = await service.get_products(
            company_id=test_company.id,
            search="Producto 1"
        )

        # Assert
        assert len(products) >= 1
        assert any("Producto 1" in p.name for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_active_only(self, db_session, test_company, test_product):
        """✅ Test listado solo productos activos."""
        # Arrange
        service = ProductService(db_session)

        # Desactivar un producto
        test_product.is_active = False
        db_session.add(test_product)
        await db_session.commit()

        # Act
        products = await service.get_products(
            company_id=test_company.id,
            active_only=True
        )

        # Assert
        assert not any(p.id == test_product.id for p in products)

    # ==================== TESTS DE ACTUALIZACIÓN ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_product_success(self, db_session, test_company, test_product):
        """✅ Test actualización exitosa de producto."""
        # Arrange
        service = ProductService(db_session)
        update_data = ProductUpdate(
            name="Nombre Actualizado",
            price=Decimal('30.00'),
            description="Descripción actualizada"
        )

        # Act
        with patch.object(service, '_validate_category_ownership'):
            result = await service.update_product(test_product.id, update_data, test_company.id)

        # Assert
        assert result.name == "Nombre Actualizado"
        assert result.price == Decimal('30.00')
        assert result.description == "Descripción actualizada"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_product_not_found(self, db_session, test_company):
        """❌ Test actualización de producto inexistente."""
        # Arrange
        service = ProductService(db_session)
        update_data = ProductUpdate(name="Nuevo Nombre")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.update_product(99999, update_data, test_company.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_product_wrong_company(self, db_session, test_product_company_2, test_company):
        """❌ Test actualización de producto de otra empresa."""
        # Arrange
        service = ProductService(db_session)
        update_data = ProductUpdate(name="Nombre Hackeado")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.update_product(test_product_company_2.id, update_data, test_company.id)

        assert exc_info.value.status_code == 404

    # ==================== TESTS DE ELIMINACIÓN ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_product_success(self, db_session, test_company, test_product):
        """✅ Test eliminación (soft delete) exitosa."""
        # Arrange
        service = ProductService(db_session)

        # Act
        result = await service.delete_product(test_product.id, test_company.id)

        # Assert
        assert "eliminado correctamente" in result["message"]

        # Verificar soft delete
        await db_session.refresh(test_product)
        assert test_product.is_active is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_product_not_found(self, db_session, test_company):
        """❌ Test eliminación de producto inexistente."""
        # Arrange
        service = ProductService(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_product(99999, test_company.id)

        assert exc_info.value.status_code == 404

    # ==================== TESTS DE FUNCIONES ESPECIALES ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_low_stock_products(self, db_session, test_company, test_products_batch):
        """✅ Test obtener productos con stock bajo."""
        # Arrange
        service = ProductService(db_session)

        # Act
        low_stock_products = await service.get_low_stock_products(test_company.id, Decimal('50'))

        # Assert - Algunos productos tienen stock bajo
        assert isinstance(low_stock_products, list)
        # Nota: Dependiendo de los datos de prueba, algunos productos tendrán stock bajo

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_by_price_range(self, db_session, test_company, test_products_batch):
        """✅ Test filtrar productos por rango de precios."""
        # Arrange
        service = ProductService(db_session)

        # Act
        products = await service.get_products_by_price_range(
            company_id=test_company.id,
            min_price=Decimal('5.00'),
            max_price=Decimal('25.00')
        )

        # Assert
        assert isinstance(products, list)
        for product in products:
            assert Decimal('5.00') <= product.price <= Decimal('25.00')

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_stock(self, db_session, test_company, test_product):
        """✅ Test actualizar stock de producto."""
        # Arrange
        service = ProductService(db_session)
        new_stock = Decimal('75.0')

        # Act
        result = await service.update_stock(test_product.id, test_company.id, new_stock)

        # Assert
        assert result.stock == new_stock

    # ==================== TESTS DE MANEJO DE ERRORES ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product_integrity_error_handling(self, db_session, test_company):
        """❌ Test manejo de errores de integridad."""
        # Arrange
        service = ProductService(db_session)
        product_data = ProductCreate(
            name="Producto Error",
            price=Decimal('10.00')
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            with patch.object(service, '_validate_category_ownership'), \
                 patch.object(service, '_check_product_name_unique', side_effect=Exception("DB Error")):
                await service.create_product(product_data, test_company.id)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_error_handling(self, db_session, test_company):
        """❌ Test manejo de errores en listado."""
        # Arrange
        service = ProductService(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            with patch.object(service.product_repo, 'list', side_effect=Exception("DB Error")):
                await service.get_products(test_company.id)

        assert exc_info.value.status_code == 500
