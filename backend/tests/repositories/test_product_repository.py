"""
🧪 PRUEBAS UNITARIAS PARA PRODUCT REPOSITORY

Estas pruebas validan:
- ✅ Operaciones CRUD básicas del repositorio
- ✅ Consultas específicas (por categoría, búsqueda, stock bajo)
- ✅ Multi-tenancy (filtrado por company_id)

Todas las pruebas usan mocks para evitar conflictos de concurrencia async.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from sqlalchemy.ext.asyncio import AsyncSession


class TestProductRepository:
    """🧪 Pruebas unitarias para ProductRepository usando mocks."""

    # ==================== TESTS CRUD BÁSICOS ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product(self):
        """✅ Test creación básica de producto."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        product_data = {
            "name": "Producto Repo Test",
            "description": "Producto creado por repository",
            "price": Decimal('20.00'),
            "tax_rate": Decimal('0.10'),
            "stock": Decimal('30.0'),
            "company_id": 1,
            "category_id": 1,
            "is_active": True
        }
        
        # Mock the refresh to set the id
        async def mock_refresh(obj):
            obj.id = 1
            obj.created_at = datetime.now()
        
        mock_session.refresh = mock_refresh

        # Act
        product = await repo.create(product_data)

        # Assert
        assert product.name == "Producto Repo Test"
        assert product.company_id == 1
        assert product.category_id == 1
        assert product.price == Decimal('20.00')
        assert mock_session.add.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_by_id_found(self):
        """✅ Test obtener producto existente."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_product = Product(
            id=1,
            name="Producto Test",
            price=Decimal('25.00'),
            company_id=1,
            is_active=True
        )
        mock_product.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_product
        mock_session.execute.return_value = mock_result

        # Act
        product = await repo.get_by_id(1, 1)

        # Assert
        assert product is not None
        assert product.id == 1
        assert product.name == "Producto Test"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_by_id_not_found(self):
        """✅ Test obtener producto inexistente retorna None."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        product = await repo.get_by_id(99999, 1)

        # Assert
        assert product is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_by_id_or_404_found(self):
        """✅ Test get_by_id_or_404 encuentra producto."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_product = Product(
            id=1,
            name="Producto Test",
            price=Decimal('25.00'),
            company_id=1,
            is_active=True
        )
        mock_product.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_product
        mock_session.execute.return_value = mock_result

        # Act
        product = await repo.get_by_id_or_404(1, 1)

        # Assert
        assert product.id == 1
        assert product.name == "Producto Test"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_by_id_or_404_not_found(self):
        """❌ Test get_by_id_or_404 lanza 404 si no existe."""
        from fastapi import HTTPException
        
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await repo.get_by_id_or_404(99999, 1)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_products(self):
        """✅ Test listar productos de una empresa."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_products = [
            Product(id=1, name="Producto 1", price=Decimal('10.00'), company_id=1, is_active=True),
            Product(id=2, name="Producto 2", price=Decimal('20.00'), company_id=1, is_active=True),
        ]
        for p in mock_products:
            p.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_products
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        products = await repo.list(company_id=1)

        # Assert
        assert len(products) == 2
        assert all(p.company_id == 1 for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_product(self):
        """✅ Test actualizar producto."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_product = Product(
            id=1,
            name="Producto Original",
            price=Decimal('25.00'),
            company_id=1,
            is_active=True
        )
        mock_product.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_product
        mock_session.execute.return_value = mock_result

        update_data = {"name": "Nombre Actualizado", "price": Decimal('35.00')}

        # Act
        updated = await repo.update(1, 1, update_data)

        # Assert
        assert updated.name == "Nombre Actualizado"
        assert updated.price == Decimal('35.00')
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_product_soft_delete(self):
        """✅ Test eliminación (soft delete) de producto."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_product = Product(
            id=1,
            name="Producto a Eliminar",
            price=Decimal('25.00'),
            company_id=1,
            is_active=True
        )
        mock_product.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_product
        mock_session.execute.return_value = mock_result

        # Act
        result = await repo.delete(1, 1, soft_delete=True)

        # Assert
        assert result is True
        assert mock_product.is_active is False
        assert mock_session.commit.called

    # ==================== TESTS DE CONSULTAS ESPECÍFICAS ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_active_by_category(self):
        """✅ Test obtener productos activos por categoría."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_products = [
            Product(id=1, name="Producto 1", category_id=1, company_id=1, price=Decimal('10.00'), is_active=True),
            Product(id=2, name="Producto 2", category_id=1, company_id=1, price=Decimal('20.00'), is_active=True),
        ]
        for p in mock_products:
            p.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_products
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        products = await repo.get_active_by_category(1, 1)

        # Assert
        assert len(products) == 2
        assert all(p.category_id == 1 for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_name(self):
        """✅ Test búsqueda por nombre."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_products = [
            Product(id=1, name="Hamburguesa", company_id=1, price=Decimal('15.00'), is_active=True),
        ]
        for p in mock_products:
            p.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_products
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        products = await repo.search_by_name(1, "hambur")

        # Assert
        assert len(products) == 1
        assert "Hamburguesa" in products[0].name

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_name_empty_query(self):
        """✅ Test búsqueda con query vacío retorna lista vacía."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)

        # Act
        products = await repo.search_by_name(1, "")

        # Assert
        assert products == []
        assert not mock_session.execute.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_with_category(self):
        """✅ Test obtener producto con categoría."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_product = Product(
            id=1,
            name="Producto Test",
            price=Decimal('25.00'),
            company_id=1,
            category_id=1,
            is_active=True
        )
        mock_product.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_product
        mock_session.execute.return_value = mock_result

        # Act
        product = await repo.get_with_category(1, 1)

        # Assert
        assert product is not None
        assert product.id == 1

    # ==================== TESTS DE STOCK ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_stock(self):
        """✅ Test actualizar stock de producto."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_product = Product(
            id=1,
            name="Producto Test",
            price=Decimal('25.00'),
            stock=Decimal('100.0'),
            company_id=1,
            is_active=True
        )
        mock_product.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_product
        mock_session.execute.return_value = mock_result

        # Act
        updated = await repo.update_stock(1, 1, Decimal('150.0'))

        # Assert
        assert updated.stock == Decimal('150.0')
        assert mock_session.commit.called

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_low_stock_products(self):
        """✅ Test obtener productos con stock bajo."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_products = [
            Product(id=1, name="Producto Bajo", stock=Decimal('5.0'), company_id=1, price=Decimal('10.00'), is_active=True),
            Product(id=2, name="Producto Muy Bajo", stock=Decimal('2.0'), company_id=1, price=Decimal('15.00'), is_active=True),
        ]
        for p in mock_products:
            p.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_products
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        low_stock = await repo.get_low_stock_products(1, Decimal('10'))

        # Assert
        assert len(low_stock) == 2
        assert all(p.stock <= Decimal('10') for p in low_stock)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_by_price_range(self):
        """✅ Test obtener productos en rango de precios."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_products = [
            Product(id=1, name="Producto 20", price=Decimal('20.00'), company_id=1, is_active=True),
            Product(id=2, name="Producto 25", price=Decimal('25.00'), company_id=1, is_active=True),
        ]
        for p in mock_products:
            p.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_products
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        products = await repo.get_products_by_price_range(1, Decimal('15'), Decimal('30'))

        # Assert
        assert len(products) == 2
        assert all(Decimal('15') <= p.price <= Decimal('30') for p in products)

    # ==================== TESTS MULTI-TENANT ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multi_tenant_isolation(self):
        """✅ Test que list filtra por company_id."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        # Solo productos de company 1
        mock_products = [
            Product(id=1, name="Producto C1", price=Decimal('10.00'), company_id=1, is_active=True),
        ]
        for p in mock_products:
            p.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_products
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Act
        products = await repo.list(company_id=1)

        # Assert
        assert len(products) == 1
        assert all(p.company_id == 1 for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_exists(self):
        """✅ Test verificar existencia."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_product = Product(id=1, name="Producto", company_id=1, price=Decimal('10.00'), is_active=True)
        mock_product.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_product
        mock_session.execute.return_value = mock_result

        # Act
        exists = await repo.exists(1, 1)

        # Assert
        assert exists is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_count(self):
        """✅ Test contar productos."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        repo = ProductRepository(mock_session)
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        # Act
        count = await repo.count(1)

        # Assert
        assert count == 5
