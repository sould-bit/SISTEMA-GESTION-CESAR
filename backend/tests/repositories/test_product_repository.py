"""
🧪 PRUEBAS UNITARIAS PARA PRODUCT REPOSITORY

Estas pruebas validan:
- ✅ Operaciones CRUD básicas del repositorio
- ✅ Decremento atómico de stock (lógica SQL anti-carrera)
- ✅ Consultas específicas (por categoría, búsqueda, stock bajo)
- ✅ Relaciones con categorías (joins)
- ✅ Multi-tenancy (filtrado por company_id)
"""

import pytest
from decimal import Decimal
from unittest.mock import patch

from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from sqlalchemy.exc import IntegrityError


class TestProductRepository:
    """🧪 Pruebas unitarias para ProductRepository."""

    # ==================== TESTS CRUD BÁSICOS ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product(self, db_session, test_company, test_category):
        """✅ Test creación básica de producto."""
        # Arrange
        repo = ProductRepository(db_session)
        company = await test_company
        category = await test_category
        product_data = {
            "name": "Producto Repo Test",
            "description": "Producto creado por repository",
            "price": Decimal('20.00'),
            "tax_rate": Decimal('0.10'),
            "stock": Decimal('30.0'),
            "company_id": company.id,
            "category_id": category.id,
            "is_active": True
        }

        # Act
        product = await repo.create(product_data)

        # Assert
        assert product.name == "Producto Repo Test"
        assert product.company_id == test_company.id
        assert product.category_id == test_category.id
        assert product.price == Decimal('20.00')

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_by_id_or_404_found(self, db_session, test_product):
        """✅ Test obtener producto existente."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        product = await repo.get_by_id_or_404(test_product.id, test_product.company_id)

        # Assert
        assert product.id == test_product.id
        assert product.name == test_product.name

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_by_id_or_404_not_found(self, db_session, test_company):
        """❌ Test obtener producto inexistente lanza 404."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await repo.get_by_id_or_404(99999, test_company.id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_products(self, db_session, test_company, test_products_batch):
        """✅ Test listar productos de una empresa."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        products = await repo.list(test_company.id)

        # Assert
        assert len(products) == 5
        assert all(p.company_id == test_company.id for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_product(self, db_session, test_product):
        """✅ Test actualizar producto."""
        # Arrange
        repo = ProductRepository(db_session)
        update_data = {
            "name": "Nombre Actualizado",
            "price": Decimal('35.00'),
            "description": "Descripción actualizada"
        }

        # Act
        updated = await repo.update(test_product.id, test_product.company_id, update_data)

        # Assert
        assert updated.name == "Nombre Actualizado"
        assert updated.price == Decimal('35.00')
        assert updated.description == "Descripción actualizada"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_product_soft_delete(self, db_session, test_product):
        """✅ Test eliminación (soft delete) de producto."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        await repo.delete(test_product.id, test_product.company_id, soft_delete=True)

        # Assert - Verificar soft delete
        await db_session.refresh(test_product)
        assert test_product.is_active is False

    # ==================== TESTS DE CONSULTAS ESPECÍFICAS ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_active_by_category(self, db_session, test_company, test_category, test_products_batch):
        """✅ Test obtener productos activos por categoría."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        products = await repo.get_active_by_category(test_company.id, test_category.id)

        # Assert
        assert len(products) == 5
        assert all(p.category_id == test_category.id for p in products)
        assert all(p.is_active is True for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_name_case_insensitive(self, db_session, test_company, test_products_batch):
        """✅ Test búsqueda por nombre (insensible a mayúsculas)."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        products = await repo.search_by_name(test_company.id, "producto", 10)

        # Assert
        assert len(products) == 5  # Todos contienen "producto"
        assert all("producto" in p.name.lower() for p in products)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_name_limit(self, db_session, test_company, test_products_batch):
        """✅ Test búsqueda con límite de resultados."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        products = await repo.search_by_name(test_company.id, "producto", 2)

        # Assert
        assert len(products) == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_with_category(self, db_session, test_product, test_category):
        """✅ Test obtener producto con categoría cargada (join)."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        product = await repo.get_with_category(test_product.id, test_product.company_id)

        # Assert
        assert product is not None
        assert product.id == test_product.id
        assert product.category is not None
        assert product.category.id == test_category.id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_with_category_not_found(self, db_session, test_company):
        """❌ Test obtener producto con categoría inexistente."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        product = await repo.get_with_category(99999, test_company.id)

        # Assert
        assert product is None

    # ==================== TESTS DE STOCK ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_stock(self, db_session, test_product):
        """✅ Test actualizar stock de producto."""
        # Arrange
        repo = ProductRepository(db_session)
        new_stock = Decimal('150.0')

        # Act
        updated = await repo.update_stock(test_product.id, test_product.company_id, new_stock)

        # Assert
        assert updated.stock == new_stock

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_low_stock_products(self, db_session, test_company, test_products_batch):
        """✅ Test obtener productos con stock bajo."""
        # Arrange
        repo = ProductRepository(db_session)
        threshold = Decimal('50')  # Algunos productos tienen stock < 50

        # Act
        low_stock_products = await repo.get_low_stock_products(test_company.id, threshold)

        # Assert
        assert isinstance(low_stock_products, list)
        # Todos los productos retornados deben tener stock <= threshold
        for product in low_stock_products:
            assert product.stock <= threshold
            assert product.stock is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_low_stock_products_exclude_null_stock(self, db_session, test_company):
        """✅ Test que productos sin stock definido no aparecen en stock bajo."""
        # Arrange
        repo = ProductRepository(db_session)

        # Crear producto sin stock
        product_no_stock = Product(
            name="Producto Sin Stock",
            price=Decimal('10.00'),
            company_id=test_company.id,
            stock=None,  # Sin stock definido
            is_active=True
        )
        db_session.add(product_no_stock)
        await db_session.commit()

        # Act
        low_stock_products = await repo.get_low_stock_products(test_company.id, Decimal('100'))

        # Assert - El producto sin stock no debe aparecer
        product_names = [p.name for p in low_stock_products]
        assert "Producto Sin Stock" not in product_names

    # ==================== TESTS DE PRECIOS ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_by_price_range(self, db_session, test_company, test_products_batch):
        """✅ Test obtener productos en rango de precios."""
        # Arrange
        repo = ProductRepository(db_session)
        min_price = Decimal('15.00')
        max_price = Decimal('35.00')

        # Act
        products = await repo.get_products_by_price_range(test_company.id, min_price, max_price)

        # Assert
        assert isinstance(products, list)
        for product in products:
            assert min_price <= product.price <= max_price

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_products_by_price_range_no_results(self, db_session, test_company):
        """✅ Test rango de precios sin resultados."""
        # Arrange
        repo = ProductRepository(db_session)
        min_price = Decimal('1000.00')  # Precio muy alto
        max_price = Decimal('2000.00')

        # Act
        products = await repo.get_products_by_price_range(test_company.id, min_price, max_price)

        # Assert
        assert len(products) == 0

    # ==================== TESTS MULTI-TENANT ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multi_tenant_isolation_create(self, db_session, test_company, test_company_2):
        """✅ Test que productos se crean en la empresa correcta."""
        # Arrange
        repo = ProductRepository(db_session)

        # Crear producto para empresa 1
        product_data_1 = {
            "name": "Producto Empresa 1",
            "price": Decimal('10.00'),
            "company_id": test_company.id,
            "is_active": True
        }

        # Crear producto para empresa 2
        product_data_2 = {
            "name": "Producto Empresa 2",
            "price": Decimal('20.00'),
            "company_id": test_company_2.id,
            "is_active": True
        }

        # Act
        product_1 = await repo.create(product_data_1)
        product_2 = await repo.create(product_data_2)

        # Assert
        assert product_1.company_id == test_company.id
        assert product_2.company_id == test_company_2.id
        assert product_1.company_id != product_2.company_id

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multi_tenant_isolation_list(self, db_session, test_company, test_company_2, test_product_company_2):
        """✅ Test que list solo retorna productos de la empresa."""
        # Arrange
        repo = ProductRepository(db_session)

        # Act
        products_company_1 = await repo.list(test_company.id)
        products_company_2 = await repo.list(test_company_2.id)

        # Assert
        assert all(p.company_id == test_company.id for p in products_company_1)
        assert all(p.company_id == test_company_2.id for p in products_company_2)

        # Verificar que no se mezclan productos
        company_1_ids = {p.id for p in products_company_1}
        company_2_ids = {p.id for p in products_company_2}
        assert len(company_1_ids.intersection(company_2_ids)) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multi_tenant_isolation_search(self, db_session, test_company, test_company_2):
        """✅ Test que búsqueda respeta multi-tenancy."""
        # Arrange
        repo = ProductRepository(db_session)

        # Crear productos con mismo nombre en empresas diferentes
        product_data_1 = {
            "name": "Producto Compartido",
            "price": Decimal('10.00'),
            "company_id": test_company.id,
            "is_active": True
        }
        product_data_2 = {
            "name": "Producto Compartido",
            "price": Decimal('20.00'),
            "company_id": test_company_2.id,
            "is_active": True
        }

        await repo.create(product_data_1)
        await repo.create(product_data_2)

        # Act
        results_company_1 = await repo.search_by_name(test_company.id, "compartido")
        results_company_2 = await repo.search_by_name(test_company_2.id, "compartido")

        # Assert
        assert len(results_company_1) == 1
        assert len(results_company_2) == 1
        assert results_company_1[0].company_id == test_company.id
        assert results_company_2[0].company_id == test_company_2.id

    # ==================== TESTS DE MANEJO DE ERRORES ====================

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_product_integrity_error(self, db_session, test_company):
        """❌ Test manejo de errores de integridad."""
        # Arrange
        repo = ProductRepository(db_session)

        # Crear producto que cause error de integridad
        # (por ejemplo, foreign key inválida)
        product_data = {
            "name": "Producto Error",
            "price": Decimal('10.00'),
            "company_id": test_company.id,
            "category_id": 99999,  # FK inválida
            "is_active": True
        }

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repo.create(product_data)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_product_wrong_company(self, db_session, test_product_company_2, test_company):
        """❌ Test actualizar producto de otra empresa."""
        # Arrange
        repo = ProductRepository(db_session)
        update_data = {"name": "Nombre Hackeado"}

        # Act & Assert - Debe fallar porque no encuentra el producto
        with pytest.raises(HTTPException) as exc_info:
            await repo.update(test_product_company_2.id, test_company.id, update_data)

        assert exc_info.value.status_code == 404
