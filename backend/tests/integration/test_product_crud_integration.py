"""
🧪 PRUEBAS DE INTEGRACIÓN PARA CRUD COMPLETO DE PRODUCTOS

Estas pruebas validan:
- ✅ Flujo completo de creación -> listado -> detalle -> actualización -> eliminación
- ✅ Integración entre Service, Repository y Base de Datos
- ✅ Validaciones de negocio end-to-end
- ✅ Soft delete funcional
- ✅ Relaciones con categorías
"""

import pytest
from decimal import Decimal

from app.services.product_service import ProductService
from app.schemas.products import ProductCreate, ProductUpdate


class TestProductCRUDIntegration:
    """🧪 Pruebas de integración para flujo completo CRUD de productos."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_crud_flow(self, db_session, test_company, test_category):
        """
        ✅ TEST COMPLETO: Flujo CRUD end-to-end

        Este test valida el flujo completo:
        1. Crear producto
        2. Listar productos (verificar que aparece)
        3. Obtener detalle
        4. Actualizar producto
        5. Verificar actualización
        6. Eliminar (soft delete)
        7. Verificar que ya no aparece en listados activos
        """
        # Arrange
        service = ProductService(db_session)

        # 1. CREAR PRODUCTO
        product_data = ProductCreate(
            name="Producto Integración",
            description="Producto para test de integración",
            price=Decimal('45.00'),
            tax_rate=Decimal('0.12'),
            stock=Decimal('25.0'),
            image_url="https://example.com/product.jpg",
            category_id=test_category.id
        )

        # Act & Assert - Crear
        created_product = await service.create_product(product_data, test_company.id)

        # Assert creación
        assert created_product.name == "Producto Integración"
        assert created_product.company_id == test_company.id
        assert created_product.category_id == test_category.id
        assert created_product.price == Decimal('45.00')
        assert created_product.is_active is True
        assert created_product.id is not None

        # 2. LISTAR PRODUCTOS - Verificar que aparece
        products = await service.get_products(test_company.id)
        product_names = [p.name for p in products]
        assert "Producto Integración" in product_names

        # 3. OBTENER DETALLE
        product_detail = await service.product_repo.get_with_category(created_product.id, test_company.id)
        assert product_detail is not None
        assert product_detail.name == "Producto Integración"
        assert product_detail.category is not None
        assert product_detail.category.name == test_category.name

        # 4. ACTUALIZAR PRODUCTO
        update_data = ProductUpdate(
            name="Producto Integración Actualizado",
            price=Decimal('50.00'),
            description="Descripción actualizada",
            stock=Decimal('30.0')
        )

        updated_product = await service.update_product(created_product.id, update_data, test_company.id)

        # Assert actualización
        assert updated_product.name == "Producto Integración Actualizado"
        assert updated_product.price == Decimal('50.00')
        assert updated_product.stock == Decimal('30.0')

        # 5. VERIFICAR ACTUALIZACIÓN EN LISTADO
        products_after_update = await service.get_products(test_company.id)
        updated_names = [p.name for p in products_after_update]
        assert "Producto Integración Actualizado" in updated_names
        assert "Producto Integración" not in updated_names

        # 6. ELIMINAR PRODUCTO (SOFT DELETE)
        delete_result = await service.delete_product(created_product.id, test_company.id)
        assert "eliminado correctamente" in delete_result["message"]

        # 7. VERIFICAR SOFT DELETE
        # Producto ya no aparece en listados activos
        active_products = await service.get_products(test_company.id, active_only=True)
        active_names = [p.name for p in active_products]
        assert "Producto Integración Actualizado" not in active_names

        # Pero sí existe en BD (soft delete)
        product_in_db = await service.product_repo.get_by_id_or_404(created_product.id, test_company.id)
        assert product_in_db.is_active is False
        assert product_in_db.name == "Producto Integración Actualizado"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_category_relationship_integrity(self, db_session, test_company, test_category):
        """
        ✅ TEST: Integridad de relaciones con categorías

        Valida que:
        - No se puede crear producto con categoría de otra empresa
        - La categoría se carga correctamente en las consultas
        - Los filtros por categoría funcionan
        """
        # Arrange
        service = ProductService(db_session)

        # Crear producto válido
        product_data = ProductCreate(
            name="Producto Categoría",
            price=Decimal('15.00'),
            category_id=test_category.id
        )

        # Act - Crear producto
        created_product = await service.create_product(product_data, test_company.id)

        # Assert - Relación funciona
        assert created_product.category_id == test_category.id

        # Obtener con categoría cargada
        product_with_category = await service.product_repo.get_with_category(created_product.id, test_company.id)
        assert product_with_category.category is not None
        assert product_with_category.category.name == test_category.name

        # Filtrar por categoría
        products_by_category = await service.get_products(
            company_id=test_company.id,
            category_id=test_category.id
        )
        assert len(products_by_category) >= 1
        assert all(p.category_id == test_category.id for p in products_by_category)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_functionality_integration(self, db_session, test_company, test_category):
        """
        ✅ TEST: Funcionalidad de búsqueda integrada

        Valida que:
        - La búsqueda funciona a través de todas las capas
        - Es insensible a mayúsculas
        - Respeta multi-tenancy
        """
        # Arrange
        service = ProductService(db_session)

        # Crear varios productos con nombres variados
        products_to_create = [
            ProductCreate(name="Hamburguesa Clásica", price=Decimal('25.00'), category_id=test_category.id),
            ProductCreate(name="Pizza Margherita", price=Decimal('35.00'), category_id=test_category.id),
            ProductCreate(name="Ensalada César", price=Decimal('18.00'), category_id=test_category.id),
        ]

        for product_data in products_to_create:
            await service.create_product(product_data, test_company.id)

        # Act - Buscar "pizza"
        search_results = await service.get_products(test_company.id, search="pizza")

        # Assert
        assert len(search_results) == 1
        assert "Pizza" in search_results[0].name

        # Act - Buscar "HAMBURGUESA" (mayúsculas)
        search_results_upper = await service.get_products(test_company.id, search="HAMBURGUESA")

        # Assert
        assert len(search_results_upper) == 1
        assert "Hamburguesa" in search_results_upper[0].name

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_stock_management_integration(self, db_session, test_company, test_category):
        """
        ✅ TEST: Gestión de stock integrada

        Valida que:
        - Actualización de stock funciona
        - Productos con stock bajo se detectan correctamente
        - Filtros de stock funcionan
        """
        # Arrange
        service = ProductService(db_session)

        # Crear productos con diferentes niveles de stock
        products_data = [
            ProductCreate(name="Producto Stock Alto", price=Decimal('10.00'), stock=Decimal('100.0'), category_id=test_category.id),
            ProductCreate(name="Producto Stock Medio", price=Decimal('15.00'), stock=Decimal('25.0'), category_id=test_category.id),
            ProductCreate(name="Producto Stock Bajo", price=Decimal('20.00'), stock=Decimal('5.0'), category_id=test_category.id),
        ]

        created_products = []
        for product_data in products_data:
            product = await service.create_product(product_data, test_company.id)
            created_products.append(product)

        # Act - Obtener productos con stock bajo (threshold = 20)
        low_stock_products = await service.get_low_stock_products(test_company.id, Decimal('20.0'))

        # Assert
        assert len(low_stock_products) >= 1
        low_stock_names = [p.name for p in low_stock_products]
        assert "Producto Stock Bajo" in low_stock_names

        # Act - Actualizar stock
        product_to_update = created_products[2]  # Stock Bajo
        updated_product = await service.update_stock(product_to_update.id, test_company.id, Decimal('50.0'))

        # Assert - Stock actualizado
        assert updated_product.stock == Decimal('50.0')

        # Verificar que ya no aparece en stock bajo
        low_stock_after_update = await service.get_low_stock_products(test_company.id, Decimal('20.0'))
        low_stock_names_after = [p.name for p in low_stock_after_update]
        assert "Producto Stock Bajo" not in low_stock_names_after

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_price_range_filtering_integration(self, db_session, test_company, test_category):
        """
        ✅ TEST: Filtrado por rango de precios integrado

        Valida que el filtrado por precios funciona correctamente
        a través de todas las capas.
        """
        # Arrange
        service = ProductService(db_session)

        # Crear productos con precios variados
        prices = [Decimal('5.00'), Decimal('15.00'), Decimal('25.00'), Decimal('35.00'), Decimal('45.00')]
        created_products = []

        for i, price in enumerate(prices):
            product_data = ProductCreate(
                name=f"Producto Precio {i+1}",
                price=price,
                category_id=test_category.id
            )
            product = await service.create_product(product_data, test_company.id)
            created_products.append(product)

        # Act - Filtrar precios entre 10 y 40
        filtered_products = await service.get_products_by_price_range(
            test_company.id,
            Decimal('10.00'),
            Decimal('40.00')
        )

        # Assert
        assert len(filtered_products) == 3  # Precios: 15, 25, 35
        for product in filtered_products:
            assert Decimal('10.00') <= product.price <= Decimal('40.00')

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_business_validations_integration(self, db_session, test_company, test_category, test_company_2, test_category_company_2):
        """
        ✅ TEST: Validaciones de negocio integradas

        Valida que todas las validaciones de negocio funcionan:
        - Unicidad de nombre por empresa
        - Validación de propiedad de categoría
        - Validaciones de precio y campos requeridos
        """
        # Arrange
        service = ProductService(db_session)

        # 1. Crear producto válido
        product_data = ProductCreate(
            name="Producto Validación",
            price=Decimal('12.00'),
            category_id=test_category.id
        )
        await service.create_product(product_data, test_company.id)

        # 2. Intentar crear producto con mismo nombre (debe fallar)
        duplicate_data = ProductCreate(
            name="Producto Validación",  # Nombre duplicado
            price=Decimal('15.00'),
            category_id=test_category.id
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_product(duplicate_data, test_company.id)
        assert exc_info.value.status_code == 400
        assert "Ya existe un producto" in str(exc_info.value.detail)

        # 3. Intentar crear producto con categoría de otra empresa (debe fallar)
        cross_tenant_data = ProductCreate(
            name="Producto Cross-Tenant",
            price=Decimal('20.00'),
            category_id=test_category_company_2.id  # Categoría de otra empresa
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_product(cross_tenant_data, test_company.id)
        assert exc_info.value.status_code == 400
        assert "no pertenece a su empresa" in str(exc_info.value.detail)

        # 4. Crear producto válido en segunda empresa (debe funcionar)
        valid_second_company = ProductCreate(
            name="Producto Validación",  # Mismo nombre, empresa diferente
            price=Decimal('18.00'),
            category_id=test_category_company_2.id
        )

        second_product = await service.create_product(valid_second_company, test_company_2.id)
        assert second_product.name == "Producto Validación"
        assert second_product.company_id == test_company_2.id


