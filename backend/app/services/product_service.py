"""
🛒 PRODUCT SERVICE - Servicio de Productos con Control de Carga

Implementa Service Layer que controla qué datos cargar según el endpoint:
- get_products_for_list() → Schema ligero para listados
- get_product_detail() → Schema completo para detalle
- create_product() / update_product() → Con invalidación de caché

Incluye:
✅ Control explícito de carga de datos
✅ Estrategia de invalidación de caché
✅ Logging de operaciones
✅ Manejo robusto de errores
"""

from typing import List, Optional, Callable, Any
from decimal import Decimal
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.category import Category
from app.repositories.product_repository import ProductRepository
from app.schemas.products import (
    ProductCreate, 
    ProductUpdate, 
    ProductRead,
    ProductListRead,
    ProductDetailRead
)

logger = logging.getLogger(__name__)


# ============================================
# 🔄 ESTRATEGIA DE INVALIDACIÓN DE CACHÉ
# ============================================
class CacheInvalidator:
    """
    Gestiona invalidación de caché para productos.
    
    Estrategia:
    - Invalidación por evento (create, update, delete)
    - Invalidación por patrón (company_id, category_id)
    - Hooks para integración con Redis
    """
    
    def __init__(self):
        self._invalidation_hooks: List[Callable] = []
    
    def register_hook(self, hook: Callable[[str, int, Optional[dict]], Any]):
        """
        Registrar hook de invalidación.
        
        Args:
            hook: Función async que recibe (event, company_id, metadata)
        """
        self._invalidation_hooks.append(hook)
    
    async def invalidate(
        self, 
        event: str, 
        company_id: int, 
        metadata: Optional[dict] = None
    ):
        """
        Disparar invalidación de caché.
        
        Events:
        - product_created
        - product_updated  
        - product_deleted
        - category_changed
        
        Args:
            event: Tipo de evento
            company_id: ID de empresa afectada
            metadata: Info adicional (product_id, category_id, etc)
        """
        logger.debug(f"🔄 Cache invalidation: {event} for company {company_id}")
        
        for hook in self._invalidation_hooks:
            try:
                if callable(hook):
                    await hook(event, company_id, metadata or {})
            except Exception as e:
                logger.warning(f"⚠️ Cache invalidation hook error: {e}")


# Instancia global del invalidador
cache_invalidator = CacheInvalidator()

# Registrar hook de Redis automáticamente
try:
    from app.core.cache import redis_product_cache_hook
    cache_invalidator.register_hook(redis_product_cache_hook)
    logger.info("✅ Redis product cache hook registrado")
except ImportError:
    logger.warning("⚠️ Redis cache hook no disponible")


class ProductService:
    """
    🛒 Servicio de Productos con Control de Carga
    
    Gestiona operaciones CRUD con estrategias de carga optimizadas:
    - Listados: Schema ligero (ProductListRead) sin relaciones completas
    - Detalle: Schema completo (ProductDetailRead) con relaciones
    - Mutaciones: Invalidan caché automáticamente
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self._cache_invalidator = cache_invalidator

    # ============================================
    # 📋 LISTADOS OPTIMIZADOS
    # ============================================

    async def get_products_for_list(
        self, 
        company_id: int, 
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> List[ProductListRead]:
        """
        📋 LISTADO OPTIMIZADO PARA UI
        
        Devuelve ProductListRead (schema ligero) con category_name
        en lugar de la relación completa. Evita MissingGreenlet.
        
        Args:
            company_id: ID de empresa (multi-tenant)
            category_id: Filtrar por categoría
            search: Buscar por nombre
            active_only: Solo activos
            
        Returns:
            List[ProductListRead]: Productos con category_name
        """
        try:
            if search and search.strip():
                # Búsqueda con nombre de categoría
                rows = await self.product_repo.search_with_category_name(
                    company_id, 
                    search.strip()
                )
            else:
                # Listado con nombre de categoría
                rows = await self.product_repo.get_products_with_category_name(
                    company_id,
                    active_only=active_only,
                    category_id=category_id
                )
            
            # Convertir a schema usando factory method
            results = [
                ProductListRead.from_product_with_category_name(product, category_name)
                for product, category_name in rows
            ]
            
            logger.info(f"📋 get_products_for_list: {len(results)} productos")
            return results
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error en get_products_for_list: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno listando productos"
            )

    async def get_product_detail(
        self, 
        product_id: int, 
        company_id: int
    ) -> ProductDetailRead:
        """
        🔍 DETALLE COMPLETO DE PRODUCTO
        
        Devuelve ProductDetailRead con relación Category cargada.
        Usa selectinload para evitar MissingGreenlet.
        
        Args:
            product_id: ID del producto
            company_id: ID de empresa (multi-tenant)
            
        Returns:
            ProductDetailRead: Producto con categoría completa
            
        Raises:
            HTTPException 404: Si no existe
        """
        product = await self.product_repo.get_with_category(product_id, company_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        logger.info(f"🔍 get_product_detail: {product.name} (ID: {product_id})")
        return ProductDetailRead.model_validate(product)

    # ============================================
    # 📋 LISTADO LEGACY (compatibilidad)
    # ============================================

    async def get_products(
        self, 
        company_id: int, 
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> List[ProductRead]:
        """
        📋 LISTAR PRODUCTOS (método legacy)
        
        ⚠️ DEPRECATED: Usar get_products_for_list() para listados.
        Este método mantiene compatibilidad pero puede causar
        MissingGreenlet si se accede a relaciones.
        """
        try:
            if search:
                products = await self.product_repo.search_by_name(company_id, search)
            elif category_id:
                products = await self.product_repo.get_active_by_category(company_id, category_id)
            else:
                products = await self.product_repo.get_products_basic(company_id, active_only)
            
            return products
        
        except Exception as e:
            logger.error(f"❌ Error listando productos: {e}")
            raise HTTPException(500, "Error interno listando productos")

    # ============================================
    # ➕ CREAR PRODUCTO
    # ============================================

    async def create_product(
        self, 
        product_data: ProductCreate, 
        company_id: int
    ) -> ProductDetailRead:
        """
        ➕ CREAR PRODUCTO CON VALIDACIONES
        
        Invalida caché de productos después de crear.
        
        Returns:
            ProductDetailRead: Producto creado con categoría
        """
        try:
            # 1. Validar categoría si se especifica
            if product_data.category_id is not None:
                await self._validate_category_ownership(
                    product_data.category_id, 
                    company_id
                )
            
            # 2. Verificar unicidad del nombre
            await self._check_product_name_unique(product_data.name, company_id)
            
            # 3. Crear producto
            product_dict = product_data.model_dump()
            product_dict["company_id"] = company_id
            
            product = await self.product_repo.create(product_dict)
            
            # 4. Cargar con categoría para respuesta
            if product.category_id:
                product = await self.product_repo.get_with_category(
                    product.id, 
                    company_id
                )
            
            # 5. Invalidar caché
            await self._cache_invalidator.invalidate(
                "product_created",
                company_id,
                {"product_id": product.id, "category_id": product.category_id}
            )
            
            logger.info(f"✅ Producto creado: '{product.name}' (ID: {product.id})")
            return ProductDetailRead.model_validate(product)

        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(400, "Producto con este nombre ya existe")
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error creando producto: {e}")
            raise HTTPException(500, "Error interno creando producto")

    # ============================================
    # ✏️ ACTUALIZAR PRODUCTO
    # ============================================

    async def update_product(
        self, 
        product_id: int, 
        product_data: ProductUpdate, 
        company_id: int
    ) -> ProductDetailRead:
        """
        ✏️ ACTUALIZAR PRODUCTO CON VALIDACIONES
        
        Invalida caché después de actualizar.
        """
        try:
            # 1. Verificar ownership
            existing = await self.product_repo.get_by_id_or_404(product_id, company_id)
            old_category_id = existing.category_id
            
            # 2. Validar categoría si cambia
            if (product_data.category_id is not None and 
                product_data.category_id != existing.category_id):
                await self._validate_category_ownership(
                    product_data.category_id, 
                    company_id
                )
            
            # 3. Validar unicidad si cambia nombre
            if product_data.name and product_data.name != existing.name:
                await self._check_product_name_unique(
                    product_data.name, 
                    company_id, 
                    exclude_id=product_id
                )
            
            # 4. Actualizar
            update_dict = product_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            product = await self.product_repo.update(product_id, company_id, update_dict)
            
            # 5. Recargar con categoría
            product = await self.product_repo.get_with_category(product_id, company_id)
            
            # 6. Invalidar caché
            await self._cache_invalidator.invalidate(
                "product_updated",
                company_id,
                {
                    "product_id": product_id,
                    "old_category_id": old_category_id,
                    "new_category_id": product.category_id
                }
            )
            
            logger.info(f"✅ Producto actualizado: '{product.name}' (ID: {product.id})")
            return ProductDetailRead.model_validate(product)
        
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error actualizando producto {product_id}: {e}")
            raise HTTPException(500, "Error interno actualizando producto")

    # ============================================
    # 🗑️ ELIMINAR PRODUCTO
    # ============================================

    async def delete_product(self, product_id: int, company_id: int) -> dict:
        """
        🗑️ ELIMINAR PRODUCTO (SOFT DELETE)
        
        Invalida caché después de eliminar.
        """
        try:
            product = await self.product_repo.get_by_id_or_404(product_id, company_id)
            
            await self.product_repo.delete(product_id, company_id, soft_delete=True)
            
            # Invalidar caché
            await self._cache_invalidator.invalidate(
                "product_deleted",
                company_id,
                {"product_id": product_id, "category_id": product.category_id}
            )
            
            logger.info(f"✅ Producto eliminado: '{product.name}' (ID: {product.id})")
            return {"message": f"Producto '{product.name}' eliminado correctamente"}
        
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error eliminando producto {product_id}: {e}")
            raise HTTPException(500, "Error interno eliminando producto")

    # ============================================
    # 🔍 VALIDACIONES PRIVADAS
    # ============================================

    async def _validate_category_ownership(
        self, 
        category_id: int, 
        company_id: int
    ):
        """Validar que la categoría pertenece a la empresa"""
        result = await self.db.execute(
            select(Category).where(
                Category.id == category_id,
                Category.company_id == company_id,
                Category.is_active == True
            )
        )
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La categoría especificada no existe o no pertenece a su empresa"
            )

    async def _check_product_name_unique(
        self, 
        name: str, 
        company_id: int, 
        exclude_id: Optional[int] = None
    ):
        """Verificar unicidad del nombre del producto"""
        query = select(Product).where(
            Product.name == name,
            Product.company_id == company_id
        )
        
        if exclude_id:
            query = query.where(Product.id != exclude_id)
        
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un producto con el nombre '{name}' en esta empresa"
            )

    # ============================================
    # 📊 OPERACIONES ADICIONALES
    # ============================================

    async def get_low_stock_products(
        self, 
        company_id: int, 
        threshold: Decimal = Decimal('10')
    ) -> List[ProductListRead]:
        """📉 Obtener productos con stock bajo"""
        products = await self.product_repo.get_low_stock_products(company_id, threshold)
        return [ProductListRead.model_validate(p) for p in products]

    async def get_products_by_price_range(
        self, 
        company_id: int, 
        min_price: Decimal, 
        max_price: Decimal
    ) -> List[ProductListRead]:
        """💰 Filtrar productos por rango de precios"""
        products = await self.product_repo.get_products_by_price_range(
            company_id, 
            min_price, 
            max_price
        )
        return [ProductListRead.model_validate(p) for p in products]

    async def update_stock(
        self, 
        product_id: int, 
        company_id: int, 
        new_stock: Decimal
    ) -> ProductDetailRead:
        """📦 Actualizar stock de producto con bloqueo pesimista"""
        product = await self.product_repo.update_stock(product_id, company_id, new_stock)
        
        # Invalidar caché
        await self._cache_invalidator.invalidate(
            "product_updated",
            company_id,
            {"product_id": product_id, "field": "stock"}
        )
        
        return ProductDetailRead.model_validate(product)

    async def add_stock(
        self, 
        product_id: int, 
        company_id: int, 
        increment: Decimal
    ) -> ProductDetailRead:
        """📦 Incrementar/decrementar stock de forma atómica"""
        # Actualización atómica (no devuelve relaciones)
        await self.product_repo.add_stock(product_id, company_id, increment)
        
        # Recargar con relaciones para cumplir con ProductDetailRead
        product = await self.product_repo.get_with_category(product_id, company_id)
        
        # Invalidar caché
        await self._cache_invalidator.invalidate(
            "product_updated",
            company_id,
            {"product_id": product_id, "field": "stock"}
        )
        
        return ProductDetailRead.model_validate(product)
