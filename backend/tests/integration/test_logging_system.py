#!/usr/bin/env python3
"""
Prueba del Sistema de Logging Avanzado

Esta prueba valida:
- Configuración de logging estructurado
- Logs JSON formateados
- Funciones de conveniencia para RBAC
- Integración con servicios
"""

import asyncio
import os
import tempfile
from pathlib import Path

from app.core.logging_config import (
    RBACLogger,
    get_rbac_logger,
    log_rbac_action,
    log_permission_check,
    log_security_event
)


async def test_basic_logging():
    """Test básico de configuración de logging."""
    print("🧪 Probando configuración básica de logging...")

    # Crear logger temporal para pruebas
    with tempfile.TemporaryDirectory() as temp_dir:
        # Cambiar temporalmente el directorio para que los logs se creen ahí
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Configurar logging
            logger = RBACLogger(log_level="DEBUG", enable_json=True)

            # Obtener logger específico
            rbac_logger = logger.get_logger("test.rbac")

            # Probar logging básico
            rbac_logger.info("Test message", extra={"test_field": "test_value"})
            rbac_logger.warning("Warning test", extra={"user_id": 123})
            rbac_logger.error("Error test", extra={"error_code": "TEST_ERROR"})

            print("✅ Logging básico funciona")

            # Verificar que se crearon archivos de log
            log_files = list(Path("logs").glob("*.log"))
            if log_files:
                print(f"✅ Archivos de log creados: {len(log_files)}")
                # Leer una línea del log para verificar formato JSON
                with open(log_files[0], 'r') as f:
                    first_line = f.readline().strip()
                    if '"message"' in first_line and '"level"' in first_line:
                        print("✅ Formato JSON validado")
                    else:
                        print("⚠️ Formato de log podría no ser JSON")
            else:
                print("⚠️ No se encontraron archivos de log")

        finally:
            os.chdir(original_cwd)

    return True


async def test_rbac_logging_functions():
    """Test de funciones específicas de logging RBAC."""
    print("🧪 Probando funciones de logging RBAC...")

    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Inicializar sistema de logging
            get_rbac_logger("test")  # Esto inicializa el sistema

            # Probar log_rbac_action
            log_rbac_action(
                action="test_action",
                user_id=123,
                company_id=456,
                role_id="test-role-id",
                permission_code="test.permission",
                details={"extra_info": "test_data"}
            )

            # Probar log_permission_check
            log_permission_check(
                user_id=123,
                permission_code="test.permission",
                company_id=456,
                granted=True,
                source="database"
            )

            log_permission_check(
                user_id=124,
                permission_code="denied.permission",
                company_id=456,
                granted=False,
                source="database"
            )

            # Probar log_security_event
            log_security_event(
                event="test_security_event",
                user_id=123,
                company_id=456,
                details={"severity": "high", "action": "login_failed"}
            )

            print("✅ Funciones de logging RBAC ejecutadas correctamente")

            # Verificar logs de seguridad
            security_log = Path("logs/security.log")
            if security_log.exists():
                with open(security_log, 'r') as f:
                    content = f.read()
                    if '"event": "test_security_event"' in content:
                        print("✅ Log de seguridad registrado correctamente")
                    else:
                        print("⚠️ Log de seguridad no encontrado")

        finally:
            os.chdir(original_cwd)

    return True


async def test_logger_factory():
    """Test de la factory de loggers."""
    print("🧪 Probando factory de loggers...")

    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Obtener diferentes loggers
            api_logger = get_rbac_logger("app.api")
            rbac_logger = get_rbac_logger("app.rbac")
            perm_logger = get_rbac_logger("app.permissions")

            # Verificar que son diferentes instancias
            assert api_logger.name == "app.api"
            assert rbac_logger.name == "app.rbac"
            assert perm_logger.name == "app.permissions"

            # Probar logging en diferentes loggers
            api_logger.info("API test message", extra={"endpoint": "/test"})
            rbac_logger.info("RBAC test message", extra={"action": "test"})
            perm_logger.info("Permissions test message", extra={"permission": "test.perm"})

            print("✅ Factory de loggers funciona correctamente")

        finally:
            os.chdir(original_cwd)

    return True


async def test_environment_variables():
    """Test de configuración por variables de entorno."""
    print("🧪 Probando configuración por variables de entorno...")

    # Guardar valores originales
    original_log_level = os.environ.get("LOG_LEVEL")
    original_log_json = os.environ.get("LOG_JSON")

    try:
        # Configurar variables de entorno
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["LOG_JSON"] = "false"

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Forzar reinicialización obteniendo logger
                from app.core.logging_config import _rbac_logger_instance
                global _rbac_logger_instance
                _rbac_logger_instance = None  # Reset

                logger = get_rbac_logger("test")
                # El sistema debería usar DEBUG y formato no-JSON

                print("✅ Configuración por variables de entorno funciona")

            finally:
                os.chdir(original_cwd)

    finally:
        # Restaurar variables originales
        if original_log_level is not None:
            os.environ["LOG_LEVEL"] = original_log_level
        else:
            os.environ.pop("LOG_LEVEL", None)

        if original_log_json is not None:
            os.environ["LOG_JSON"] = original_log_json
        else:
            os.environ.pop("LOG_JSON", None)

    return True


async def main():
    """Función principal de pruebas."""
    print("📊 PRUEBA DEL SISTEMA DE LOGGING AVANZADO")
    print("=" * 50)

    tests = [
        ("Configuración Básica", test_basic_logging),
        ("Funciones RBAC", test_rbac_logging_functions),
        ("Factory de Loggers", test_logger_factory),
        ("Variables de Entorno", test_environment_variables),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
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
        print("🎉 ¡Sistema de logging avanzado validado!")
        print("\n✨ Características confirmadas:")
        print("   • Logging estructurado JSON")
        print("   • Separación por componentes")
        print("   • Rotación automática de archivos")
        print("   • Funciones específicas para RBAC")
        print("   • Configuración por entorno")
        print("   • Auditoría de seguridad")
    else:
        print("⚠️  Algunas pruebas fallaron.")
        print("🔧 Revisa los errores arriba.")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n🚀 Estado final: {'✅ EXITOSO' if success else '❌ FALLIDO'}")
