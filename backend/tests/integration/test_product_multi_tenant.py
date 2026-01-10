"""
🧪 PRUEBAS DE AISLAMIENTO MULTI-TENANT PARA PRODUCTOS

Estas pruebas validan:
- ✅ Empresa A NO puede ver productos de Empresa B
- ✅ Empresa A NO puede modificar productos de Empresa B
- ✅ Validaciones anti-cross-tenant funcionan correctamente
- ✅ Búsquedas y filtros respetan multi-tenancy
- ✅ Relaciones (categorías) se validan por tenant
"""

import pytest
from decimal import Decimal

from app.services.product_service import ProductService
from app.schemas.products import ProductCreate, ProductUpdate
from fastapi import HTTPException


class TestProductMultiTenantIsolation:
    """🧪 Pruebas de aislamiento multi-tenant para productos."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_create_products(self, db_session, test_company, test_company_2, test_category, test_category_company_2):
        """
        ✅ TEST: Aislamiento en creación de productos

        Cada empresa puede crear productos solo con sus propias categorías.
        """
        service = ProductService(db_session)

        # Empresa 1 crea producto válido
        product_company_1 = ProductCreate(
            name="Producto Empresa 1",
            price=Decimal('25.00'),
            category_id=test_category.id  # Categoría de Empresa 1
        )
        created_1 = await service.create_product(product_company_1, test_company.id)
        assert created_1.company_id == test_company.id

        # Empresa 2 crea producto válido
        product_company_2 = ProductCreate(
            name="Producto Empresa 2",
            price=Decimal('30.00'),
            category_id=test_category_company_2.id  # Categoría de Empresa 2
        )
        created_2 = await service.create_product(product_company_2, test_company_2.id)
        assert created_2.company_id == test_company_2.id

        # Empresa 1 intenta crear producto con categoría de Empresa 2 (DEBE FALLAR)
        cross_tenant_product = ProductCreate(
            name="Producto Cross-Tenant",
            price=Decimal('20.00'),
            category_id=test_category_company_2.id  # ❌ Categoría de Empresa 2
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_product(cross_tenant_product, test_company.id)

        assert exc_info.value.status_code == 400
        assert "no pertenece a su empresa" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_list_products(self, db_session, test_company, test_company_2):
        """
        ✅ TEST: Aislamiento en listado de productos

        Cada empresa solo ve sus propios productos.
        """
        service = ProductService(db_session)

        # Crear productos para ambas empresas
        products_data = [
            ("Producto Lista 1A", test_company.id),
            ("Producto Lista 1B", test_company.id),
            ("Producto Lista 2A", test_company_2.id),
            ("Producto Lista 2B", test_company_2.id),
        ]

        for name, company_id in products_data:
            product_data = ProductCreate(name=name, price=Decimal('15.00'))
            await service.create_product(product_data, company_id)

        # Empresa 1 lista sus productos
        products_company_1 = await service.get_products(test_company.id)
        company_1_names = [p.name for p in products_company_1]

        # Empresa 2 lista sus productos
        products_company_2 = await service.get_products(test_company_2.id)
        company_2_names = [p.name for p in products_company_2]

        # Assert aislamiento
        assert len(products_company_1) == 2
        assert len(products_company_2) == 2
        assert "Producto Lista 1A" in company_1_names
        assert "Producto Lista 1B" in company_1_names
        assert "Producto Lista 2A" not in company_1_names
        assert "Producto Lista 2B" not in company_1_names

        assert "Producto Lista 2A" in company_2_names
        assert "Producto Lista 2B" in company_2_names
        assert "Producto Lista 1A" not in company_2_names
        assert "Producto Lista 1B" not in company_2_names

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_update_products(self, db_session, test_company, test_company_2):
        """
        ✅ TEST: Aislamiento en actualización de productos

        Empresa A no puede actualizar productos de Empresa B.
        """
        service = ProductService(db_session)

        # Crear producto para Empresa 1
        product_company_1 = ProductCreate(name="Producto Update 1", price=Decimal('20.00'))
        created_1 = await service.create_product(product_company_1, test_company.id)

        # Crear producto para Empresa 2
        product_company_2 = ProductCreate(name="Producto Update 2", price=Decimal('25.00'))
        created_2 = await service.create_product(product_company_2, test_company_2.id)

        # Empresa 1 actualiza su propio producto (DEBE FUNCIONAR)
        update_data = ProductUpdate(name="Producto Update 1 Modificado", price=Decimal('30.00'))
        updated_1 = await service.update_product(created_1.id, update_data, test_company.id)
        assert updated_1.name == "Producto Update 1 Modificado"

        # Empresa 1 intenta actualizar producto de Empresa 2 (DEBE FALLAR)
        with pytest.raises(HTTPException) as exc_info:
            await service.update_product(created_2.id, update_data, test_company.id)

        assert exc_info.value.status_code == 404  # No encuentra el producto

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_delete_products(self, db_session, test_company, test_company_2):
        """
        ✅ TEST: Aislamiento en eliminación de productos

        Empresa A no puede eliminar productos de Empresa B.
        """
        service = ProductService(db_session)

        # Crear productos para ambas empresas
        product_1 = ProductCreate(name="Producto Delete 1", price=Decimal('15.00'))
        product_2 = ProductCreate(name="Producto Delete 2", price=Decimal('20.00'))

        created_1 = await service.create_product(product_1, test_company.id)
        created_2 = await service.create_product(product_2, test_company_2.id)

        # Empresa 1 elimina su propio producto (DEBE FUNCIONAR)
        result_1 = await service.delete_product(created_1.id, test_company.id)
        assert "eliminado correctamente" in result_1["message"]

        # Empresa 1 intenta eliminar producto de Empresa 2 (DEBE FALLAR)
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_product(created_2.id, test_company.id)

        assert exc_info.value.status_code == 404

        # Verificar que el producto de Empresa 2 aún existe
        product_still_exists = await service.product_repo.get_by_id_or_404(created_2.id, test_company_2.id)
        assert product_still_exists.is_active is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_search_products(self, db_session, test_company, test_company_2):
        """
        ✅ TEST: Aislamiento en búsqueda de productos

        Las búsquedas solo retornan resultados de la propia empresa.
        """
        service = ProductService(db_session)

        # Crear productos con nombres similares en ambas empresas
        common_name = "Producto Común"

        product_1 = ProductCreate(name=f"{common_name} Empresa 1", price=Decimal('15.00'))
        product_2 = ProductCreate(name=f"{common_name} Empresa 2", price=Decimal('20.00'))

        await service.create_product(product_1, test_company.id)
        await service.create_product(product_2, test_company_2.id)

        # Empresa 1 busca "Producto Común"
        search_results_1 = await service.get_products(test_company.id, search=common_name)

        # Empresa 2 busca "Producto Común"
        search_results_2 = await service.get_products(test_company_2.id, search=common_name)

        # Assert aislamiento en búsqueda
        assert len(search_results_1) == 1
        assert len(search_results_2) == 1
        assert "Empresa 1" in search_results_1[0].name
        assert "Empresa 2" in search_results_2[0].name
        assert "Empresa 1" not in search_results_2[0].name
        assert "Empresa 2" not in search_results_1[0].name

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_name_uniqueness(self, db_session, test_company, test_company_2):
        """
        ✅ TEST: Unicidad de nombres por empresa

        El mismo nombre puede existir en diferentes empresas,
        pero no dentro de la misma empresa.
        """
        service = ProductService(db_session)
        duplicate_name = "Producto Nombre Duplicado"

        # Empresa 1 crea producto
        product_1 = ProductCreate(name=duplicate_name, price=Decimal('15.00'))
        await service.create_product(product_1, test_company.id)

        # Empresa 2 crea producto con mismo nombre (DEBE FUNCIONAR)
        product_2 = ProductCreate(name=duplicate_name, price=Decimal('20.00'))
        created_2 = await service.create_product(product_2, test_company_2.id)
        assert created_2.name == duplicate_name
        assert created_2.company_id == test_company_2.id

        # Empresa 1 intenta crear otro producto con mismo nombre (DEBE FALLAR)
        product_1_duplicate = ProductCreate(name=duplicate_name, price=Decimal('25.00'))
        with pytest.raises(HTTPException) as exc_info:
            await service.create_product(product_1_duplicate, test_company.id)

        assert exc_info.value.status_code == 400
        assert "Ya existe un producto" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_category_filters(self, db_session, test_company, test_company_2, test_category, test_category_company_2):
        """
        ✅ TEST: Filtros por categoría respetan multi-tenancy

        Los filtros por categoría solo funcionan dentro de la misma empresa.
        """
        service = ProductService(db_session)

        # Crear productos en ambas empresas con categorías
        product_1 = ProductCreate(
            name="Producto Cat 1",
            price=Decimal('15.00'),
            category_id=test_category.id
        )
        product_2 = ProductCreate(
            name="Producto Cat 2",
            price=Decimal('20.00'),
            category_id=test_category_company_2.id
        )

        await service.create_product(product_1, test_company.id)
        await service.create_product(product_2, test_company_2.id)

        # Empresa 1 filtra por su categoría
        filtered_1 = await service.get_products(
            company_id=test_company.id,
            category_id=test_category.id
        )

        # Empresa 2 filtra por su categoría
        filtered_2 = await service.get_products(
            company_id=test_company_2.id,
            category_id=test_category_company_2.id
        )

        # Assert aislamiento en filtros
        assert len(filtered_1) == 1
        assert len(filtered_2) == 1
        assert filtered_1[0].name == "Producto Cat 1"
        assert filtered_2[0].name == "Producto Cat 2"

        # Empresa 1 intenta filtrar por categoría de Empresa 2 (no debe retornar resultados)
        cross_filter = await service.get_products(
            company_id=test_company.id,
            category_id=test_category_company_2.id
        )
        assert len(cross_filter) == 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_inventory_operations(self, db_session, test_company, test_company_2):
        """
        ✅ TEST: Operaciones de inventario respetan multi-tenancy

        Funciones como stock bajo, rangos de precio, etc. solo operan
        dentro de la misma empresa.
        """
        service = ProductService(db_session)

        # Crear productos con stock bajo en ambas empresas
        product_1 = ProductCreate(
            name="Producto Stock Bajo 1",
            price=Decimal('10.00'),
            stock=Decimal('5.0')  # Stock bajo
        )
        product_2 = ProductCreate(
            name="Producto Stock Bajo 2",
            price=Decimal('15.00'),
            stock=Decimal('3.0')  # Stock bajo
        )

        await service.create_product(product_1, test_company.id)
        await service.create_product(product_2, test_company_2.id)

        # Obtener productos con stock bajo para Empresa 1
        low_stock_1 = await service.get_low_stock_products(test_company.id, Decimal('10.0'))

        # Obtener productos con stock bajo para Empresa 2
        low_stock_2 = await service.get_low_stock_products(test_company_2.id, Decimal('10.0'))

        # Assert aislamiento en operaciones de inventario
        assert len(low_stock_1) == 1
        assert len(low_stock_2) == 1
        assert low_stock_1[0].name == "Producto Stock Bajo 1"
        assert low_stock_2[0].name == "Producto Stock Bajo 2"

        # Verificar rangos de precio
        price_range_1 = await service.get_products_by_price_range(
            test_company.id, Decimal('5.00'), Decimal('20.00')
        )
        price_range_2 = await service.get_products_by_price_range(
            test_company_2.id, Decimal('5.00'), Decimal('20.00')
        )

        assert len(price_range_1) == 1  # Solo producto de Empresa 1
        assert len(price_range_2) == 1  # Solo producto de Empresa 2

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation_cross_company_operations(self, db_session, test_company, test_company_2, test_user_company_2):
        """
        ✅ TEST: Prevención de operaciones cross-company

        Simula escenario donde un usuario malicioso intenta acceder
        a recursos de otra empresa usando IDs conocidos.
        """
        service = ProductService(db_session)

        # Crear producto en Empresa 1
        product_company_1 = ProductCreate(name="Producto Seguro 1", price=Decimal('25.00'))
        created_1 = await service.create_product(product_company_1, test_company.id)

        # Simular que un usuario de Empresa 2 conoce el ID del producto de Empresa 1
        malicious_user_company_id = test_company_2.id
        known_product_id = created_1.id

        # Intentar leer producto de otra empresa
        with pytest.raises(HTTPException) as exc_info:
            await service.product_repo.get_by_id_or_404(known_product_id, malicious_user_company_id)
        assert exc_info.value.status_code == 404

        # Intentar actualizar producto de otra empresa
        update_data = ProductUpdate(name="Nombre Hackeado", price=Decimal('1.00'))
        with pytest.raises(HTTPException) as exc_info:
            await service.update_product(known_product_id, update_data, malicious_user_company_id)
        assert exc_info.value.status_code == 404

        # Intentar eliminar producto de otra empresa
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_product(known_product_id, malicious_user_company_id)
        assert exc_info.value.status_code == 404

        # Intentar actualizar stock de producto de otra empresa
        with pytest.raises(HTTPException) as exc_info:
            await service.update_stock(known_product_id, malicious_user_company_id, Decimal('100.0'))
        assert exc_info.value.status_code == 404

        # Verificar que el producto original no fue modificado
        original_product = await service.product_repo.get_by_id_or_404(created_1.id, test_company.id)
        assert original_product.name == "Producto Seguro 1"
        assert original_product.price == Decimal('25.00')

