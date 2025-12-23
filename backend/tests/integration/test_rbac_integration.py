#!/usr/bin/env python3
"""
Script de Pruebas de Integración para el Sistema RBAC.

Este script combina las pruebas existentes con las nuevas funcionalidades
para validar que todo el sistema funcione correctamente.

Ejecuta:
1. Pruebas unitarias de servicios
2. Pruebas de integración de endpoints
3. Pruebas del sistema completo RBAC
4. Validación de decoradores
5. Verificación de seguridad

Uso:
    python test_rbac_integration.py
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from test_rbac import test_rbac_system
from run_tests import run_command


async def run_integration_tests():
    """Ejecuta todas las pruebas de integración del sistema RBAC."""

    print("🔬 PRUEBAS DE INTEGRACIÓN COMPLETA - SISTEMA RBAC")
    print("="*70)

    results = []

    # 1. Ejecutar pruebas unitarias de servicios
    print("\n📋 PASO 1: Ejecutando pruebas unitarias de servicios...")
    success_unit = run_command(
        ["python", "-m", "pytest", "tests/services/", "-v", "--tb=short"],
        "PRUEBAS UNITARIAS DE SERVICIOS"
    )
    results.append(("Pruebas Unitarias", success_unit))

    # 2. Ejecutar pruebas de decoradores
    print("\n📋 PASO 2: Ejecutando pruebas de decoradores...")
    success_decorators = run_command(
        ["python", "-m", "pytest", "tests/test_permissions_decorators.py", "-v", "--tb=short"],
        "PRUEBAS DE DECORADORES"
    )
    results.append(("Decoradores", success_decorators))

    # 3. Ejecutar pruebas del sistema RBAC existente
    print("\n📋 PASO 3: Ejecutando pruebas del sistema RBAC existente...")
    try:
        await test_rbac_system()
        success_rbac = True
        print("✅ Pruebas del sistema RBAC completadas")
    except Exception as e:
        print(f"❌ Error en pruebas del sistema RBAC: {e}")
        success_rbac = False
    results.append(("Sistema RBAC", success_rbac))

    # 4. Ejecutar todas las pruebas con coverage si las anteriores pasaron
    if all(result[1] for result in results):
        print("\n📋 PASO 4: Ejecutando pruebas con coverage...")
        success_coverage = run_command(
            ["python", "-m", "pytest", "--cov=app", "--cov-report=html", "--cov-report=term-missing"],
            "PRUEBAS CON COVERAGE"
        )
        results.append(("Coverage", success_coverage))
    else:
        print("\n⚠️  PASO 4: Saltando coverage debido a fallos anteriores")
        results.append(("Coverage", False))

    # Resultados finales
    print(f"\n{'='*70}")
    print("📊 RESULTADOS FINALES:")
    print('='*70)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"   {test_name:20} : {status}")
        if not passed:
            all_passed = False

    print('='*70)

    if all_passed:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        print("\n✨ El sistema RBAC está funcionando correctamente.")
        print("\n📈 Próximos pasos recomendados:")
        print("   • Implementar cache Redis para mejorar performance")
        print("   • Agregar logging avanzado con JSON formatter")
        print("   • Configurar CI/CD con estas pruebas")
        print("   • Actualizar documentación de API")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
        print("\n🔧 Para ejecutar pruebas específicas:")
        print("   • python run_tests.py --rbac")
        print("   • python run_tests.py --file tests/services/test_role_service.py")
        print("   • python -m pytest tests/test_permissions_decorators.py -v")

    return all_passed


async def run_quick_validation():
    """Validación rápida del sistema RBAC sin coverage."""
    print("⚡ VALIDACIÓN RÁPIDA - SISTEMA RBAC")
    print("="*50)

    # Solo ejecutar la prueba básica del sistema
    try:
        await test_rbac_system()
        print("\n✅ Validación rápida completada exitosamente")
        return True
    except Exception as e:
        print(f"\n❌ Error en validación rápida: {e}")
        return False


def main():
    """Función principal."""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Validación rápida
        success = asyncio.run(run_quick_validation())
    else:
        # Pruebas completas
        success = asyncio.run(run_integration_tests())

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
