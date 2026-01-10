"""
🧪 PRUEBAS DE CONCURRENCIA PARA PRODUCTOS

Estas pruebas validan:
- ✅ Stress testing con asyncio.gather (simula múltiples usuarios)
- ✅ Race conditions en decremento de stock
- ✅ Concurrencia en creación de productos
- ✅ Isolation de transacciones
- ✅ Performance bajo carga
"""

import asyncio
import pytest
from decimal import Decimal
from typing import List

from app.services.product_service import ProductService
from app.schemas.products import ProductCreate, ProductUpdate
from fastapi import HTTPException


class TestProductConcurrency:
    """🧪 Pruebas de concurrencia para operaciones de productos."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_product_creation(self, db_session_factory):
        """
        ✅ TEST: Creación concurrente de productos

        Simula múltiples usuarios creando productos al mismo tiempo.
        Valida que no hay conflictos de unicidad o race conditions.
        """
        # Arrange - Setup manual con su propia sesión para evitar bloqueos de fixture
        import time
        ts = int(time.time())
        async with db_session_factory() as session:
            # Crear compañía y categoría para este test específico
            from app.models import Company, Category
            company = Company(name=f"Co Concurrente {ts}", slug=f"co-con-{ts}", email=f"co{ts}@test.com")
            session.add(company)
            await session.commit()
            await session.refresh(company)
            company_id = company.id

            category = Category(name=f"Cat Concurrente {ts}", company_id=company_id)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            category_id = category.id

        num_concurrent = 10

        async def create_product_task(task_id: int):
            """Tarea para crear un producto de forma concurrente."""
            async with db_session_factory() as session:
                service = ProductService(session)
                product_data = ProductCreate(
                    name=f"Producto Concurrente {task_id}",
                    description=f"Descripción tarea {task_id}",
                    price=Decimal(f'{(task_id + 1) * 5}.00'),
                    tax_rate=Decimal('0.10'),
                    category_id=category_id
                )
                return await service.create_product(product_data, company_id)

        # Act - Ejecutar múltiples creaciones concurrentemente
        tasks = [create_product_task(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        successful_creations = [r for r in results if not isinstance(r, Exception)]
        failed_creations = [r for r in results if isinstance(r, Exception)]

        # Todas las creaciones deben ser exitosas (nombres únicos)
        assert len(successful_creations) == num_concurrent
        assert len(failed_creations) == 0

        # Verificar que todos los productos se crearon
        async with db_session_factory() as session:
            service = ProductService(session)
            all_products = await service.get_products(company_id)
            concurrent_names = [p.name for p in all_products if "Producto Concurrente" in p.name]
            assert len(concurrent_names) == num_concurrent

        # Verificar unicidad de nombres
        assert len(set(concurrent_names)) == num_concurrent

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_stock_update_race_condition(self, db_session_factory):
        """
        ✅ TEST: Race condition en actualización de stock

        Simula múltiples usuarios intentando actualizar el stock del mismo producto.
        Valida que no hay pérdida de actualizaciones.
        """
        # Arrange - Setup manual
        import time
        ts = int(time.time())
        async with db_session_factory() as session:
            from app.models import Company, Category
            company = Company(name=f"Co Stock {ts}", slug=f"co-stock-{ts}", email=f"stock{ts}@test.com")
            session.add(company)
            await session.commit()
            await session.refresh(company)
            company_id = company.id

            category = Category(name=f"Cat Stock {ts}", company_id=company_id)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            category_id = category.id

            service = ProductService(session)
            # Crear producto con stock inicial
            product_data = ProductCreate(
                name="Producto Stock Concurrencia",
                price=Decimal('20.00'),
                stock=Decimal('100.0'),
                category_id=category_id
            )
            product = await service.create_product(product_data, company_id)
            product_id = product.id

        # Act - Múltiples actualizaciones concurrentes
        num_updates = 5
        stock_increments = [Decimal('10.0'), Decimal('15.0'), Decimal('-5.0'), Decimal('8.0'), Decimal('-12.0')]

        async def update_stock_task(increment: Decimal):
            """Tarea para actualizar stock de forma atómica."""
            async with db_session_factory() as session:
                service = ProductService(session)
                # Usar la nueva función atómica add_stock
                return await service.add_stock(product_id, company_id, increment)

        # Ejecutar actualizaciones concurrentemente
        tasks = [update_stock_task(inc) for inc in stock_increments]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        successful_updates = [r for r in results if not isinstance(r, Exception)]
        failed_updates = [r for r in results if isinstance(r, Exception)]

        # Todas las actualizaciones deben ser exitosas
        if failed_updates:
            print("\n❌ FALLOS EN UPDATES:")
            for e in failed_updates:
                print(f"  - {type(e).__name__}: {e}")
        
        assert len(successful_updates) == num_updates
        assert len(failed_updates) == 0

        # Verificar stock final
        async with db_session_factory() as session:
            service = ProductService(session)
            final_product = await service.product_repo.get_by_id_or_404(product_id, company_id)
            expected_final_stock = Decimal('100.0') + sum(stock_increments)
            assert final_product.stock == expected_final_stock

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_read_operations(self, db_session_factory):
        """
        ✅ TEST: Operaciones de lectura concurrentes

        Simula múltiples usuarios leyendo datos al mismo tiempo.
        Valida que las lecturas son consistentes.
        """
        # Arrange - Setup manual
        import time
        ts = int(time.time())
        async with db_session_factory() as session:
            from app.models import Company, Category, Product
            company = Company(name=f"Co Read {ts}", slug=f"co-read-{ts}", email=f"read{ts}@test.com")
            session.add(company)
            await session.commit()
            await session.refresh(company)
            company_id = company.id

            category = Category(name=f"Cat Read {ts}", company_id=company_id)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            category_id = category.id

            # Batch de productos
            for i in range(5):
                product = Product(
                    name=f"Prod Read {i} {ts}",
                    price=Decimal('10.0'),
                    company_id=company_id,
                    category_id=category_id
                )
                session.add(product)
            await session.commit()

        num_reads = 20

        async def read_products_task(task_id: int):
            """Tarea para leer productos."""
            async with db_session_factory() as session:
                service = ProductService(session)
                products = await service.get_products(company_id)
                return {
                    'task_id': task_id,
                    'count': len(products),
                    'names': [p.name for p in products]
                }

        # Act - Ejecutar múltiples lecturas concurrentemente
        tasks = [read_products_task(i) for i in range(num_reads)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        successful_reads = [r for r in results if not isinstance(r, Exception)]
        failed_reads = [r for r in results if isinstance(r, Exception)]

        # Todas las lecturas deben ser exitosas
        assert len(successful_reads) == num_reads
        assert len(failed_reads) == 0

        # Todas las lecturas deben retornar los mismos datos
        first_result = successful_reads[0]
        for result in successful_reads[1:]:
            assert result['count'] == first_result['count']
            assert set(result['names']) == set(first_result['names'])

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_mixed_operations(self, db_session_factory):
        """
        ✅ TEST: Operaciones mixtas concurrentes

        Simula escenario real: usuarios creando, leyendo y actualizando productos simultáneamente.
        """
        # Arrange - Setup manual
        import time
        ts = int(time.time())
        async with db_session_factory() as session:
            from app.models import Company, Category, Product
            company = Company(name=f"Co Mixed {ts}", slug=f"co-mixed-{ts}", email=f"mixed{ts}@test.com")
            session.add(company)
            await session.commit()
            await session.refresh(company)
            company_id = company.id

            category = Category(name=f"Cat Mixed {ts}", company_id=company_id)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            category_id = category.id

            # Crear productos base
            base_product_ids = []
            for i in range(3):
                product = Product(
                    name=f"Prod Mix Base {i} {ts}",
                    price=Decimal('10.0'),
                    stock=Decimal('50.0'),
                    company_id=company_id,
                    category_id=category_id
                )
                session.add(product)
                await session.flush()
                base_product_ids.append(product.id)
            await session.commit()

        # Funciones para operaciones concurrentes
        async def create_operation(task_id: int):
            async with db_session_factory() as session:
                service = ProductService(session)
                product_data = ProductCreate(
                    name=f"Prod Mix New {task_id}",
                    price=Decimal('25.00'),
                    category_id=category_id
                )
                return await service.create_product(product_data, company_id)

        async def read_operation(task_id: int):
            async with db_session_factory() as session:
                service = ProductService(session)
                return await service.get_products(company_id)

        async def update_operation(task_id: int, product_id: int):
            async with db_session_factory() as session:
                service = ProductService(session)
                update_data = ProductUpdate(
                    name=f"Prod Mix Upd {task_id}",
                    price=Decimal('30.00')
                )
                return await service.update_product(product_id, update_data, company_id)

        # Act - Ejecutar operaciones mixtas concurrentemente
        tasks = []
        for i in range(5): tasks.append(create_operation(i))
        for i in range(10): tasks.append(read_operation(i))
        for i, pid in enumerate(base_product_ids): tasks.append(update_operation(i, pid))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        successful_operations = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_operations) >= 10

        # Verificar creaciones
        async with db_session_factory() as session:
            service = ProductService(session)
            final_products = await service.get_products(company_id)
            created_concurrent = [p for p in final_products if "Prod Mix New" in p.name]
            assert len(created_concurrent) == 5

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_name_uniqueness_validation(self, db_session_factory):
        """
        ✅ TEST: Validación de unicidad de nombre bajo concurrencia

        Simula múltiples usuarios intentando crear productos con el mismo nombre.
        Solo uno debe tener éxito.
        """
        # Arrange - Setup manual
        import time
        ts = int(time.time())
        async with db_session_factory() as session:
            from app.models import Company, Category
            company = Company(name=f"Co Unique {ts}", slug=f"co-uni-{ts}", email=f"uni{ts}@test.com")
            session.add(company)
            await session.commit()
            await session.refresh(company)
            company_id = company.id

            category = Category(name=f"Cat Unique {ts}", company_id=company_id)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            category_id = category.id

        product_name = f"Prod Unique {ts}"
        num_concurrent_creations = 5

        async def create_same_name_task(task_id: int):
            """Intentar crear producto con mismo nombre."""
            async with db_session_factory() as session:
                service = ProductService(session)
                product_data = ProductCreate(
                    name=product_name,
                    price=Decimal('15.00'),
                    category_id=category_id
                )
                try:
                    return await service.create_product(product_data, company_id)
                except Exception as e:
                    return e

        # Act - Intentar crear múltiples productos con mismo nombre concurrentemente
        tasks = [create_same_name_task(i) for i in range(num_concurrent_creations)]
        results = await asyncio.gather(*tasks)

        # Assert
        successful_creations = [r for r in results if not isinstance(r, Exception)]
        failed_creations = [r for r in results if isinstance(r, Exception)]

        assert len(successful_creations) == 1
        assert len(failed_creations) == 4

        async with db_session_factory() as session:
            service = ProductService(session)
            products_with_name = await service.product_repo.search_by_name(company_id, product_name)
            assert len(products_with_name) == 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_high_concurrency_performance(self, db_session_factory):
        """
        ✅ TEST: Performance bajo alta concurrencia

        Ejecuta muchas operaciones concurrentemente para validar performance.
        """
        # Arrange - Setup manual
        import time
        ts = int(time.time())
        async with db_session_factory() as session:
            from app.models import Company, Category
            company = Company(name=f"Co Perf {ts}", slug=f"co-perf-{ts}", email=f"perf{ts}@test.com")
            session.add(company)
            await session.commit()
            await session.refresh(company)
            company_id = company.id

            category = Category(name=f"Cat Perf {ts}", company_id=company_id)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            category_id = category.id

        num_operations = 50

        async def quick_create_task(task_id: int):
            async with db_session_factory() as session:
                service = ProductService(session)
                product_data = ProductCreate(
                    name=f"Prod Perf {task_id:03d}",
                    price=Decimal('1.00'),
                    category_id=category_id
                )
                return await service.create_product(product_data, company_id)

        # Act - Medir tiempo de ejecución
        import time
        start_time = time.time()
        tasks = [quick_create_task(i) for i in range(num_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = time.time() - start_time

        # Assert
        successful_creations = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_creations) == num_operations
        assert execution_time < 15.0

        async with db_session_factory() as session:
            service = ProductService(session)
            final_products = await service.get_products(company_id)
            perf_products = [p for p in final_products if "Prod Perf" in p.name]
            assert len(perf_products) == num_operations


