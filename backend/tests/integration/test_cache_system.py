#!/usr/bin/env python3
"""
Prueba del Sistema de Cache Redis

Esta prueba valida:
- Conexión y operaciones básicas con Redis
- Cache de permisos de usuario
- Invalidación de cache
- Métricas y health checks
- Fallback cuando Redis no está disponible
"""

import asyncio
import os
from unittest.mock import Mock, AsyncMock
from app.core.cache import RBACCache, get_rbac_cache


async def test_cache_initialization():
    """Test de inicialización del cache."""
    print("🧪 Probando inicialización del cache...")

    # Test con configuración por defecto
    cache = RBACCache()

    assert cache.redis_url == "redis://localhost:6379/0"
    assert cache.default_ttl.seconds == 900  # 15 minutos
    assert cache.max_connections == 10

    print("✅ Cache inicializado correctamente")


async def test_cache_without_redis():
    """Test del cache cuando Redis no está disponible."""
    print("🧪 Probando cache sin Redis...")

    # Crear cache con URL inválida
    cache = RBACCache(redis_url="redis://nonexistent:6379/0")

    # Todas las operaciones deberían fallar gracefully
    result = await cache.get_user_permissions(1, 1)
    assert result is None

    success = await cache.set_user_permissions(1, 1, ["test.permission"])
    assert success is False

    success = await cache.invalidate_user_permissions(1, 1)
    assert success is False

    print("✅ Cache maneja correctamente la falta de Redis")


async def test_cache_operations_mock():
    """Test de operaciones del cache con mock."""
    print("🧪 Probando operaciones del cache con mock...")

    # Crear cache con mock
    cache = RBACCache()

    # Mock del cliente Redis
    mock_client = AsyncMock()
    cache._redis_client = mock_client
    cache._is_connected = True

    # Test get_user_permissions - cache hit
    mock_client.get.return_value = '["test.permission", "admin.access"]'
    permissions = await cache.get_user_permissions(1, 1)

    assert permissions == ["test.permission", "admin.access"]
    mock_client.get.assert_called_with("rbac:user_permissions:1:1")

    # Test get_user_permissions - cache miss
    mock_client.get.return_value = None
    permissions = await cache.get_user_permissions(1, 1)

    assert permissions is None

    # Test set_user_permissions
    mock_client.setex.return_value = True
    success = await cache.set_user_permissions(1, 1, ["test.permission"])

    assert success is True
    mock_client.setex.assert_called_once()

    # Test invalidate_user_permissions
    mock_client.delete.return_value = 1
    success = await cache.invalidate_user_permissions(1, 1)

    assert success is True
    mock_client.delete.assert_called_with("rbac:user_permissions:1:1")

    print("✅ Operaciones del cache funcionan correctamente")


async def test_cache_metrics():
    """Test de métricas del cache."""
    print("🧪 Probando métricas del cache...")

    cache = RBACCache()

    # Mock del cliente
    mock_client = AsyncMock()
    cache._redis_client = mock_client
    cache._is_connected = True

    # Simular operaciones
    mock_client.get.return_value = '["test.permission"]'
    await cache.get_user_permissions(1, 1)  # Hit

    mock_client.get.return_value = None
    await cache.get_user_permissions(2, 1)  # Miss

    mock_client.setex.return_value = True
    await cache.set_user_permissions(1, 1, ["test.permission"])  # Set

    mock_client.delete.return_value = 1
    await cache.invalidate_user_permissions(1, 1)  # Invalidation

    # Verificar métricas
    metrics = cache.get_metrics()

    assert metrics["hits"] == 1
    assert metrics["misses"] == 1
    assert metrics["sets"] == 1
    assert metrics["invalidations"] == 1
    assert metrics["hit_ratio"] == 50.0
    assert "timestamp" in metrics

    print("✅ Métricas del cache funcionan correctamente")


async def test_health_check():
    """Test del health check del cache."""
    print("🧪 Probando health check del cache...")

    # Test sin Redis
    cache = RBACCache(redis_url="redis://nonexistent:6379/0")
    health = await cache.health_check()

    assert health["status"] == "degraded"
    assert health["redis_connected"] is False
    assert "metrics" in health

    # Test con mock Redis
    cache = RBACCache()
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    cache._redis_client = mock_client
    cache._is_connected = True

    health = await cache.health_check()

    assert health["status"] == "healthy"
    assert health["redis_connected"] is True

    print("✅ Health check funciona correctamente")


async def test_role_permissions_cache():
    """Test del cache de permisos de rol."""
    print("🧪 Probando cache de permisos de rol...")

    cache = RBACCache()
    mock_client = AsyncMock()
    cache._redis_client = mock_client
    cache._is_connected = True

    # Test set_role_permissions
    mock_client.setex.return_value = True
    success = await cache.set_role_permissions("role-123", 1, ["perm1", "perm2"])

    assert success is True
    mock_client.setex.assert_called_with(
        "rbac:role_permissions:1:role-123",
        900,  # TTL por defecto
        '["perm1", "perm2"]'
    )

    # Test get_role_permissions
    mock_client.get.return_value = '["perm1", "perm2"]'
    permissions = await cache.get_role_permissions("role-123", 1)

    assert permissions == ["perm1", "perm2"]

    # Test invalidate_role_permissions
    mock_client.delete.return_value = 1
    success = await cache.invalidate_role_permissions("role-123", 1)

    assert success is True

    print("✅ Cache de permisos de rol funciona correctamente")


async def test_mass_invalidation():
    """Test de invalidación masiva."""
    print("🧪 Probando invalidación masiva...")

    cache = RBACCache()
    mock_client = AsyncMock()
    cache._redis_client = mock_client
    cache._is_connected = True

    # Test invalidate_company_permissions
    mock_client.keys.return_value = ["key1", "key2", "key3"]
    mock_client.delete.return_value = 3

    deleted_count = await cache.invalidate_company_permissions(1)

    assert deleted_count == 3
    mock_client.keys.assert_called_with("rbac:*:permissions:1:*")

    # Test invalidate_all_permissions
    mock_client.keys.return_value = ["key1", "key2"]
    mock_client.delete.return_value = 2

    deleted_count = await cache.invalidate_all_permissions()

    assert deleted_count == 2

    print("✅ Invalidación masiva funciona correctamente")


async def test_error_handling():
    """Test de manejo de errores."""
    print("🧪 Probando manejo de errores...")

    cache = RBACCache()
    mock_client = AsyncMock()
    cache._redis_client = mock_client
    cache._is_connected = True

    # Simular error de Redis
    mock_client.get.side_effect = Exception("Redis connection error")
    mock_client.setex.side_effect = Exception("Redis connection error")
    mock_client.delete.side_effect = Exception("Redis connection error")

    # Operaciones deberían manejar el error gracefully
    result = await cache.get_user_permissions(1, 1)
    assert result is None

    success = await cache.set_user_permissions(1, 1, ["test"])
    assert success is False

    success = await cache.invalidate_user_permissions(1, 1)
    assert success is False

    # Verificar que se registraron errores en métricas
    metrics = cache.get_metrics()
    assert metrics["errors"] >= 3  # Al menos 3 errores registrados

    print("✅ Manejo de errores funciona correctamente")


def test_factory_function():
    """Test de la función factory."""
    print("🧪 Probando función factory...")

    # Limpiar instancia global para test
    import app.core.cache
    app.core.cache._rbac_cache_instance = None

    # Obtener instancia
    cache = get_rbac_cache()

    assert isinstance(cache, RBACCache)

    # Obtener nuevamente debería retornar la misma instancia
    cache2 = get_rbac_cache()
    assert cache is cache2

    print("✅ Función factory funciona correctamente")


async def main():
    """Función principal de pruebas."""
    print("🔌 PRUEBA DEL SISTEMA DE CACHE REDIS")
    print("=" * 50)

    tests = [
        ("Inicialización", test_cache_initialization),
        ("Sin Redis", test_cache_without_redis),
        ("Operaciones Mock", test_cache_operations_mock),
        ("Métricas", test_cache_metrics),
        ("Health Check", test_health_check),
        ("Permisos de Rol", test_role_permissions_cache),
        ("Invalidación Masiva", test_mass_invalidation),
        ("Manejo de Errores", test_error_handling),
        ("Factory", test_factory_function),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        try:
            if test_name == "Factory":
                test_func()  # Síncrono
            else:
                await test_func()
            results.append((test_name, True))
            print(f"✅ {test_name} completado")
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))

    # Resultados
    print(f"\n{'='*50}")
    print("📊 RESULTADOS:")
    print('='*50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"   {test_name:20} : {status}")
        if not passed:
            all_passed = False

    print('='*50)

    if all_passed:
        print("🎉 ¡Sistema de cache Redis validado!")
        print("\n✨ Características confirmadas:")
        print("   • Conexión y operaciones básicas")
        print("   • Cache de permisos de usuario y rol")
        print("   • Invalidación automática y masiva")
        print("   • Métricas de rendimiento")
        print("   • Health checks")
        print("   • Manejo de errores robusto")
        print("   • Fallback cuando Redis no está disponible")
    else:
        print("⚠️  Algunas pruebas fallaron.")
        print("🔧 Revisa los errores arriba.")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n🚀 Estado final: {'✅ EXITOSO' if success else '❌ FALLIDO'}")
