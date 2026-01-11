"""
🏪 PRODUCT REPOSITORY - Operaciones de Base de Datos Optimizadas

Implementa múltiples estrategias de carga para diferentes casos de uso:
- get_products_basic() → Sin joins, máxima performance
- get_products_with_category_name() → Join ligero, solo nombre categoría
- get_all_with_category() → Con selectinload para relaciones completas
- get_with_category() → Detalle individual con relación

Incluye:
✅ Query monitoring con timing
✅ Logging de performance
✅ Manejo robusto de errores
"""

from typing import List, Optional, Tuple
from decimal import Decimal
import time
import logging
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.category import Category
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


# ============================================
# 📊 DECORATOR PARA MONITOREO DE QUERIES
# ============================================
def monitor_query(operation_name: str):
    """
    Decorator para monitorear tiempo de ejecución de queries.
    
    Registra en logs:
    - Nombre de operación
    - Tiempo de ejecución en ms
    - Warning si excede 100ms
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                # Log performance
                if elapsed_ms > 100:
                    logger.warning(
                        f"⚠️ SLOW QUERY [{operation_name}]: {elapsed_ms:.2f}ms"
                    )
                else:
                    logger.debug(
                        f"📊 Query [{operation_name}]: {elapsed_ms:.2f}ms"
                    )
                
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"❌ Query ERROR [{operation_name}]: {elapsed_ms:.2f}ms - {str(e)}"
                )
                raise
        return wrapper
    return decorator


class ProductRepository(BaseRepository[Product]):
    """
    🏪 Repository optimizado para operaciones con Productos
    
    Implementa múltiples estrategias de carga según el caso de uso
    para evitar errores de lazy loading (MissingGreenlet) y optimizar performance.
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)

    # ============================================
    # 📋 LISTADOS OPTIMIZADOS
    # ============================================

    @monitor_query("get_products_basic")
    async def get_products_basic(
        self, 
        company_id: int, 
        active_only: bool = True
    ) -> List[Product]:
        """
        📋 Listado básico sin joins - máxima performance.
        
        Usar cuando NO se necesita información de categoría.
        Ideal para: autocomplete, conteos, validaciones.
        
        Args:
            company_id: ID de la empresa (multi-tenant)
            active_only: Si True, solo productos activos
            
        Returns:
            List[Product]: Productos sin relaciones cargadas
        """
        query = select(Product).where(Product.company_id == company_id)
        
        if active_only:
            query = query.where(Product.is_active == True)
        
        query = query.order_by(Product.name)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        logger.info(f"✅ get_products_basic: {len(products)} productos")
        return products

    @monitor_query("get_products_with_category_name")
    async def get_products_with_category_name(
        self, 
        company_id: int, 
        active_only: bool = True,
        category_id: Optional[int] = None
    ) -> List[Tuple[Product, Optional[str]]]:
        """
        📋 Productos con nombre de categoría (JOIN ligero).
        
        Usar para listados donde se muestra el nombre de categoría
        sin necesitar el objeto completo. Evita lazy loading.
        
        Args:
            company_id: ID de la empresa (multi-tenant)
            active_only: Si True, solo productos activos
            category_id: Filtrar por categoría específica
            
        Returns:
            List[Tuple[Product, str|None]]: Tuplas (producto, nombre_categoria)
        """
        query = (
            select(Product, Category.name.label("category_name"))
            .outerjoin(Category, Product.category_id == Category.id)
            .where(Product.company_id == company_id)
        )
        
        if active_only:
            query = query.where(Product.is_active == True)
        
        if category_id:
            query = query.where(Product.category_id == category_id)
        
        query = query.order_by(Product.name)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        logger.info(f"✅ get_products_with_category_name: {len(rows)} productos")
        return [(row[0], row[1]) for row in rows]

    @monitor_query("get_all_with_category")
    async def get_all_with_category(
        self, 
        company_id: int, 
        active_only: bool = True
    ) -> List[Product]:
        """
        📋 Lista con categorías completas cargadas (selectinload).
        
        Usar cuando se necesita el objeto Category completo.
        Más pesado que get_products_with_category_name pero
        proporciona acceso a todos los campos de Category.
        
        Args:
            company_id: ID de la empresa (multi-tenant)
            active_only: Si True, solo productos activos
            
        Returns:
            List[Product]: Productos con relación category cargada
        """
        query = (
            select(Product)
            .where(Product.company_id == company_id)
            .options(selectinload(Product.category))
        )
        
        if active_only:
            query = query.where(Product.is_active == True)
        
        query = query.order_by(Product.name)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        logger.info(f"✅ get_all_with_category: {len(products)} productos")
        return products

    # ============================================
    # 🔍 BÚSQUEDAS Y FILTROS
    # ============================================

    @monitor_query("get_active_by_category")
    async def get_active_by_category(
        self, 
        company_id: int, 
        category_id: int
    ) -> List[Product]:
        """Obtener productos activos de una categoría específica"""
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.company_id == company_id,
                    Product.category_id == category_id,
                    Product.is_active == True
                )
            )
            .order_by(Product.name)
        )
        return result.scalars().all()

    @monitor_query("search_by_name")
    async def search_by_name(
        self, 
        company_id: int, 
        query: str, 
        limit: int = 50
    ) -> List[Product]:
        """
        🔍 Buscar productos por nombre (case-insensitive).
        
        Usa índice funcional LOWER(name) para performance.
        """
        if not query or not query.strip():
            return []
        
        search_pattern = f"%{query.strip()}%"
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.company_id == company_id,
                    Product.is_active == True,
                    func.lower(Product.name).like(func.lower(search_pattern))
                )
            )
            .order_by(Product.name)
            .limit(limit)
        )
        products = result.scalars().all()
        logger.info(f"🔍 search_by_name '{query}': {len(products)} resultados")
        return products

    @monitor_query("search_with_category_name")
    async def search_with_category_name(
        self,
        company_id: int,
        query: str,
        limit: int = 50
    ) -> List[Tuple[Product, Optional[str]]]:
        """
        🔍 Buscar productos con nombre de categoría incluido.
        
        Combina búsqueda con JOIN ligero para listados.
        """
        if not query or not query.strip():
            return []
        
        search_pattern = f"%{query.strip()}%"
        stmt = (
            select(Product, Category.name.label("category_name"))
            .outerjoin(Category, Product.category_id == Category.id)
            .where(
                and_(
                    Product.company_id == company_id,
                    Product.is_active == True,
                    func.lower(Product.name).like(func.lower(search_pattern))
                )
            )
            .order_by(Product.name)
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        logger.info(f"🔍 search_with_category_name '{query}': {len(rows)} resultados")
        return [(row[0], row[1]) for row in rows]

    # ============================================
    # 🔍 DETALLE INDIVIDUAL
    # ============================================

    @monitor_query("get_with_category")
    async def get_with_category(
        self, 
        product_id: int, 
        company_id: int
    ) -> Optional[Product]:
        """
        🔍 Obtener producto con su categoría cargada.
        
        Usa selectinload para cargar la relación de forma segura
        en contexto async (evita MissingGreenlet).
        """
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.id == product_id,
                    Product.company_id == company_id
                )
            )
            .options(selectinload(Product.category))
        )
        return result.scalar_one_or_none()

    # ============================================
    # 📦 OPERACIONES DE STOCK
    # ============================================

    @monitor_query("update_stock")
    async def update_stock(
        self, 
        product_id: int, 
        company_id: int, 
        new_stock: Decimal
    ) -> Product:
        """
        📦 Actualizar stock de un producto con bloqueo pesimista.
        """
        # Usar with_for_update() para evitar race conditions en Postgres
        stmt = select(Product).where(
            and_(Product.id == product_id, Product.company_id == company_id)
        ).with_for_update()
        
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {product_id} no encontrado"
            )
            
        old_stock = product.stock
        product.stock = new_stock
        
        await self.db.commit()
        await self.db.refresh(product)
        
        return product

    @monitor_query("add_stock")
    async def add_stock(
        self, 
        product_id: int, 
        company_id: int, 
        increment: Decimal
    ) -> Product:
        """
        📦 Incrementar/decrementar stock de forma atómica.
        """
        stmt = update(Product).where(
            and_(Product.id == product_id, Product.company_id == company_id)
        ).values(stock=Product.stock + increment).returning(Product)
        
        result = await self.db.execute(stmt)
        product = result.scalar_one()
        await self.db.commit()
        return product

    @monitor_query("get_low_stock_products")
    async def get_low_stock_products(
        self, 
        company_id: int, 
        threshold: Decimal = Decimal('10')
    ) -> List[Product]:
        """📉 Obtener productos con stock bajo"""
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.company_id == company_id,
                    Product.is_active == True,
                    Product.stock <= threshold,
                    Product.stock.isnot(None)
                )
            )
            .order_by(Product.stock)
        )
        products = result.scalars().all()
        logger.info(f"📉 Productos con stock bajo (≤{threshold}): {len(products)}")
        return products

    @monitor_query("get_products_by_price_range")
    async def get_products_by_price_range(
        self, 
        company_id: int, 
        min_price: Decimal, 
        max_price: Decimal
    ) -> List[Product]:
        """💰 Obtener productos en un rango de precios"""
        result = await self.db.execute(
            select(Product)
            .where(
                and_(
                    Product.company_id == company_id,
                    Product.is_active == True,
                    Product.price.between(min_price, max_price)
                )
            )
            .order_by(Product.price)
        )
        return result.scalars().all()
