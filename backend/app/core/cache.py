"""
Sistema de Cache Redis para el Sistema RBAC

Este módulo proporciona:
- Cache de permisos de usuario para alto rendimiento
- Invalidación automática de cache
- Configuración de TTL personalizable
- Manejo de errores y fallbacks
- Métricas de cache
"""

import json
import redis.asyncio as redis
from typing import Optional, List, Dict, Any, Union
from datetime import timedelta, datetime, timezone
import asyncio
import logging

from app.core.logging_config import get_rbac_logger


class RBACCache:
    """
    Sistema de cache Redis para RBAC con alta disponibilidad.

    Características:
    - Cache de permisos por usuario
    - Cache de permisos por rol
    - Invalidación automática
    - TTL configurable
    - Métricas de rendimiento
    - Fallback a base de datos si Redis falla
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 900,  # 15 minutos
        max_connections: int = 10,
        enable_metrics: bool = True
    ):
        """
        Inicializar cache Redis.

        Args:
            redis_url: URL de conexión a Redis
            default_ttl: TTL por defecto en segundos
            max_connections: Máximo número de conexiones
            enable_metrics: Habilitar métricas de rendimiento
        """
        self.redis_url = redis_url
        self.default_ttl = timedelta(seconds=default_ttl)
        self.max_connections = max_connections
        self.enable_metrics = enable_metrics

        # Cliente Redis (lazy initialization)
        self._redis_client: Optional[redis.Redis] = None
        self._is_connected = False

        # Logger
        self.logger = get_rbac_logger("cache")

        # Métricas
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "invalidations": 0,
            "sets": 0
        }

        # Locks para operaciones atómicas
        self._locks: Dict[str, asyncio.Lock] = {}

    async def _get_client(self) -> redis.Redis:
        """Obtener cliente Redis (con inicialización lazy)."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    decode_responses=True
                )

                # Verificar conexión
                await self._redis_client.ping()
                self._is_connected = True
                self.logger.info("Redis cache conectado exitosamente")

            except Exception as e:
                self._is_connected = False
                self.logger.warning(f"No se pudo conectar a Redis: {e}")
                raise

        return self._redis_client

    async def _ensure_connection(self) -> bool:
        """Asegurar que Redis esté disponible."""
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception:
            self._is_connected = False
            return False

    # ========== CACHE DE PERMISOS DE USUARIO ==========

    async def get_user_permissions(self, user_id: int, company_id: int) -> Optional[List[str]]:
        """
        Obtener permisos de usuario desde cache.

        Returns:
            Lista de códigos de permisos o None si no está en cache
        """
        if not await self._ensure_connection():
            return None

        try:
            client = await self._get_client()
            key = f"rbac:user_permissions:{company_id}:{user_id}"

            cached_data = await client.get(key)

            if cached_data:
                permissions = json.loads(cached_data)
                self._record_metric("hits")
                self.logger.debug(f"Cache hit para usuario {user_id}", extra={
                    "user_id": user_id,
                    "company_id": company_id,
                    "permissions_count": len(permissions)
                })
                return permissions
            else:
                self._record_metric("misses")
                return None

        except Exception as e:
            self._record_metric("errors")
            self.logger.warning(f"Error obteniendo permisos de usuario desde cache: {e}")
            return None

    async def set_user_permissions(
        self,
        user_id: int,
        company_id: int,
        permissions: List[str],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Guardar permisos de usuario en cache.

        Args:
            user_id: ID del usuario
            company_id: ID de la empresa
            permissions: Lista de códigos de permisos
            ttl: TTL personalizado (opcional)

        Returns:
            True si se guardó exitosamente
        """
        if not await self._ensure_connection():
            return False

        try:
            client = await self._get_client()
            key = f"rbac:user_permissions:{company_id}:{user_id}"

            ttl_seconds = int((ttl or self.default_ttl).total_seconds())

            await client.setex(key, ttl_seconds, json.dumps(permissions))

            self._record_metric("sets")
            self.logger.debug(f"Permisos guardados en cache para usuario {user_id}", extra={
                "user_id": user_id,
                "company_id": company_id,
                "permissions_count": len(permissions),
                "ttl_seconds": ttl_seconds
            })

            return True

        except Exception as e:
            self._record_metric("errors")
            self.logger.warning(f"Error guardando permisos de usuario en cache: {e}")
            return False

    async def invalidate_user_permissions(self, user_id: int, company_id: int) -> bool:
        """
        Invalidar cache de permisos de un usuario específico.

        Returns:
            True si se invalidó exitosamente
        """
        if not await self._ensure_connection():
            return False

        try:
            client = await self._get_client()
            key = f"rbac:user_permissions:{company_id}:{user_id}"

            deleted = await client.delete(key)

            if deleted:
                self._record_metric("invalidations")
                self.logger.info(f"Cache invalidado para usuario {user_id}", extra={
                    "user_id": user_id,
                    "company_id": company_id,
                    "action": "invalidate_user_permissions"
                })

            return bool(deleted)

        except Exception as e:
            self._record_metric("errors")
            self.logger.warning(f"Error invalidando cache de usuario: {e}")
            return False

    # ========== CACHE DE PERMISOS DE ROL ==========

    async def get_role_permissions(self, role_id: str, company_id: int) -> Optional[List[str]]:
        """
        Obtener permisos de rol desde cache.

        Returns:
            Lista de códigos de permisos o None si no está en cache
        """
        if not await self._ensure_connection():
            return None

        try:
            client = await self._get_client()
            key = f"rbac:role_permissions:{company_id}:{role_id}"

            cached_data = await client.get(key)

            if cached_data:
                permissions = json.loads(cached_data)
                self._record_metric("hits")
                return permissions
            else:
                self._record_metric("misses")
                return None

        except Exception as e:
            self._record_metric("errors")
            self.logger.warning(f"Error obteniendo permisos de rol desde cache: {e}")
            return None

    async def set_role_permissions(
        self,
        role_id: str,
        company_id: int,
        permissions: List[str],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Guardar permisos de rol en cache.

        Returns:
            True si se guardó exitosamente
        """
        if not await self._ensure_connection():
            return False

        try:
            client = await self._get_client()
            key = f"rbac:role_permissions:{company_id}:{role_id}"

            ttl_seconds = int((ttl or self.default_ttl).total_seconds())

            await client.setex(key, ttl_seconds, json.dumps(permissions))

            self._record_metric("sets")
            return True

        except Exception as e:
            self._record_metric("errors")
            self.logger.warning(f"Error guardando permisos de rol en cache: {e}")
            return False

    async def invalidate_role_permissions(self, role_id: str, company_id: int) -> bool:
        """
        Invalidar cache de permisos de un rol específico.

        Returns:
            True si se invalidó exitosamente
        """
        if not await self._ensure_connection():
            return False

        try:
            client = await self._get_client()
            key = f"rbac:role_permissions:{company_id}:{role_id}"

            deleted = await client.delete(key)

            if deleted:
                self._record_metric("invalidations")
                self.logger.info(f"Cache invalidado para rol {role_id}", extra={
                    "role_id": role_id,
                    "company_id": company_id,
                    "action": "invalidate_role_permissions"
                })

            return bool(deleted)

        except Exception as e:
            self._record_metric("errors")
            self.logger.warning(f"Error invalidando cache de rol: {e}")
            return False

    # ========== INVALIDACIÓN MASIVA ==========

    async def invalidate_company_permissions(self, company_id: int) -> int:
        """
        Invalidar todo el cache de permisos de una empresa.

        Returns:
            Número de claves eliminadas
        """
        if not await self._ensure_connection():
            return 0

        try:
            client = await self._get_client()

            # Patrón para buscar todas las claves de la empresa
            pattern = f"rbac:*:permissions:{company_id}:*"

            # Obtener todas las claves que coinciden
            keys = await client.keys(pattern)

            if keys:
                # Eliminar todas las claves
                deleted_count = await client.delete(*keys)

                self.metrics["invalidations"] += deleted_count

                self.logger.info(f"Cache masivo invalidado para empresa {company_id}", extra={
                    "company_id": company_id,
                    "keys_deleted": deleted_count,
                    "action": "invalidate_company_permissions"
                })

                return deleted_count

            return 0

        except Exception as e:
            self._record_metric("errors")
            self.logger.warning(f"Error en invalidación masiva: {e}")
            return 0

    async def invalidate_all_permissions(self) -> int:
        """
        Invalidar TODO el cache de permisos (usar con cuidado).

        Returns:
            Número de claves eliminadas
        """
        if not await self._ensure_connection():
            return 0

        try:
            client = await self._get_client()

            # Eliminar todas las claves RBAC
            keys = await client.keys("rbac:*:permissions:*")

            if keys:
                deleted_count = await client.delete(*keys)

                self.metrics["invalidations"] += deleted_count

                self.logger.warning("Cache completo de permisos invalidado", extra={
                    "keys_deleted": deleted_count,
                    "action": "invalidate_all_permissions",
                    "severity": "high"
                })

                return deleted_count

            return 0

        except Exception as e:
            self._record_metric("errors")
            self.logger.error(f"Error en invalidación completa: {e}")
            return 0

    # ========== MÉTRICAS Y MONITORING ==========

    def _record_metric(self, metric: str):
        """Registrar métrica interna."""
        if metric in self.metrics:
            self.metrics[metric] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtener métricas de rendimiento del cache.

        Returns:
            Diccionario con métricas actuales
        """
        metrics = self.metrics.copy()

        # Calcular ratios
        total_requests = metrics["hits"] + metrics["misses"]
        if total_requests > 0:
            metrics["hit_ratio"] = round(metrics["hits"] / total_requests * 100, 2)
        else:
            metrics["hit_ratio"] = 0.0

        # Estado de conexión
        metrics["redis_connected"] = self._is_connected

        # Timestamp
        metrics["timestamp"] = datetime.now(timezone.utc).isoformat()

        return metrics

    async def health_check(self) -> Dict[str, Any]:
        """
        Verificar salud del sistema de cache.

        Returns:
            Estado de salud con métricas
        """
        health = {
            "service": "rbac_cache",
            "status": "healthy",
            "redis_connected": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            # Verificar conexión Redis
            if await self._ensure_connection():
                client = await self._get_client()
                await client.ping()
                health["redis_connected"] = True
            else:
                health["status"] = "degraded"
                health["message"] = "Redis no disponible"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        # Agregar métricas
        health["metrics"] = self.get_metrics()

        return health

    # ========== LIMPIEZA Y MANTENIMIENTO ==========

    async def cleanup_expired_keys(self) -> int:
        """
        Forzar limpieza de claves expiradas (Redis lo hace automáticamente,
        pero este método puede ser útil para mantenimiento).

        Returns:
            Número de claves limpiadas (siempre 0 en Redis normal)
        """
        # En Redis, las claves expiradas se limpian automáticamente
        # Este método está aquí por si se necesita lógica adicional
        return 0

    async def close(self):
        """Cerrar conexiones Redis."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            self._is_connected = False
            self.logger.info("Conexiones Redis cerradas")


# Instancia global del cache
_rbac_cache_instance: Optional[RBACCache] = None


def get_rbac_cache() -> RBACCache:
    """Factory para obtener instancia del cache RBAC."""
    global _rbac_cache_instance

    if _rbac_cache_instance is None:
        # Configurar desde variables de entorno
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "900"))  # 15 minutos por defecto
        max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))

        _rbac_cache_instance = RBACCache(
            redis_url=redis_url,
            default_ttl=cache_ttl,
            max_connections=max_connections
        )

    return _rbac_cache_instance


# Función de conveniencia para cerrar el cache al salir
async def close_rbac_cache():
    """Cerrar el cache RBAC (para limpieza al salir)."""
    global _rbac_cache_instance

    if _rbac_cache_instance:
        await _rbac_cache_instance.close()
        _rbac_cache_instance = None


# ============================================
# 🛒 CACHE DE PRODUCTOS
# ============================================

class ProductCache:
    """
    Sistema de cache Redis para productos.
    
    Prefijos:
    - products:list:{company_id} → Lista de productos
    - products:detail:{company_id}:{product_id} → Detalle de producto
    - categories:active:{company_id} → Categorías activas
    """
    
    PREFIX_LIST = "products:list"
    PREFIX_DETAIL = "products:detail"
    PREFIX_CATEGORIES = "categories:active"
    
    DEFAULT_TTL = 300  # 5 minutos
    
    def __init__(self):
        self._cache = get_rbac_cache()  # Reutilizar conexión existente
    
    async def get_list(self, company_id: int) -> Optional[List[Dict[str, Any]]]:
        """Obtener lista de productos cacheada"""
        client = self._cache._redis_client
        if not client or not self._cache._is_connected:
            if not await self._cache._ensure_connection():
                return None
            client = self._cache._redis_client
        
        try:
            key = f"{self.PREFIX_LIST}:{company_id}"
            data = await client.get(key)
            if data:
                self._cache._record_metric("hits")
                return json.loads(data)
            self._cache._record_metric("misses")
            return None
        except Exception as e:
            self._cache._record_metric("errors")
            self._cache.logger.warning(f"Error leyendo cache productos: {e}")
            return None
    
    async def set_list(
        self, 
        company_id: int, 
        products: List[Dict[str, Any]], 
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """Guardar lista de productos en cache"""
        if not await self._cache._ensure_connection():
            return False
        
        try:
            client = await self._cache._get_client()
            key = f"{self.PREFIX_LIST}:{company_id}"
            data = json.dumps(products, default=str)
            await client.setex(key, ttl, data)
            self._cache._record_metric("sets")
            self._cache.logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            self._cache._record_metric("errors")
            self._cache.logger.warning(f"Error escribiendo cache productos: {e}")
            return False
    
    async def get_detail(
        self, 
        company_id: int, 
        product_id: int
    ) -> Optional[Dict[str, Any]]:
        """Obtener detalle de producto cacheado"""
        if not await self._cache._ensure_connection():
            return None
        
        try:
            client = await self._cache._get_client()
            key = f"{self.PREFIX_DETAIL}:{company_id}:{product_id}"
            data = await client.get(key)
            if data:
                self._cache._record_metric("hits")
                return json.loads(data)
            self._cache._record_metric("misses")
            return None
        except Exception as e:
            self._cache._record_metric("errors")
            return None
    
    async def set_detail(
        self, 
        company_id: int, 
        product_id: int, 
        product: Dict[str, Any],
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """Guardar detalle de producto en cache"""
        if not await self._cache._ensure_connection():
            return False
        
        try:
            client = await self._cache._get_client()
            key = f"{self.PREFIX_DETAIL}:{company_id}:{product_id}"
            data = json.dumps(product, default=str)
            await client.setex(key, ttl, data)
            self._cache._record_metric("sets")
            return True
        except Exception as e:
            self._cache._record_metric("errors")
            return False
    
    async def invalidate_company(self, company_id: int) -> int:
        """
        Invalidar todo el cache de productos de una empresa.
        """
        if not await self._cache._ensure_connection():
            return 0
        
        try:
            client = await self._cache._get_client()
            deleted = 0
            
            # Invalidar lista
            list_key = f"{self.PREFIX_LIST}:{company_id}"
            deleted += await client.delete(list_key)
            
            # Invalidar detalles (usando scan para evitar bloqueo)
            pattern = f"{self.PREFIX_DETAIL}:{company_id}:*"
            keys = await client.keys(pattern)
            if keys:
                deleted += await client.delete(*keys)
            
            # Invalidar categorías
            cat_key = f"{self.PREFIX_CATEGORIES}:{company_id}"
            deleted += await client.delete(cat_key)
            
            self._cache.metrics["invalidations"] += deleted
            self._cache.logger.info(f"Cache productos invalidado: empresa {company_id}, {deleted} keys")
            return deleted
        except Exception as e:
            self._cache._record_metric("errors")
            self._cache.logger.warning(f"Error invalidando cache productos: {e}")
            return 0
    
    async def invalidate_product(self, company_id: int, product_id: int) -> int:
        """Invalidar cache de un producto específico"""
        if not await self._cache._ensure_connection():
            return 0
        
        try:
            client = await self._cache._get_client()
            deleted = 0
            
            # Invalidar lista (contiene el producto)
            list_key = f"{self.PREFIX_LIST}:{company_id}"
            deleted += await client.delete(list_key)
            
            # Invalidar detalle
            detail_key = f"{self.PREFIX_DETAIL}:{company_id}:{product_id}"
            deleted += await client.delete(detail_key)
            
            self._cache.metrics["invalidations"] += deleted
            return deleted
        except Exception as e:
            self._cache._record_metric("errors")
            return 0


# Instancia global de ProductCache
_product_cache_instance: Optional[ProductCache] = None


def get_product_cache() -> ProductCache:
    """Factory para obtener instancia del cache de productos."""
    global _product_cache_instance
    
    if _product_cache_instance is None:
        _product_cache_instance = ProductCache()
    
    return _product_cache_instance


# ============================================
# 🎯 HOOK PARA CACHE INVALIDATOR
# ============================================

async def redis_product_cache_hook(
    event: str, 
    company_id: int, 
    metadata: dict
):
    """
    Hook para CacheInvalidator de ProductService.
    
    Registrar este hook en ProductService para invalidar
    cache automáticamente cuando cambian productos.
    
    Events:
    - product_created
    - product_updated
    - product_deleted
    - category_changed
    """
    cache = get_product_cache()
    
    if event in ("product_created", "product_deleted", "category_changed"):
        await cache.invalidate_company(company_id)
    
    elif event == "product_updated":
        product_id = metadata.get("product_id")
        if product_id:
            await cache.invalidate_product(company_id, product_id)
        else:
            await cache.invalidate_company(company_id)

