#!/usr/bin/env python3
"""
Script de ejecución de pruebas para el sistema RBAC.

Este script permite ejecutar diferentes tipos de pruebas:
- Pruebas unitarias completas
- Pruebas de integración
- Pruebas específicas de RBAC
- Pruebas con coverage

Uso:
    python run_tests.py                    # Todas las pruebas
    python run_tests.py --unit            # Solo pruebas unitarias
    python run_tests.py --integration     # Solo pruebas de integración
    python run_tests.py --rbac            # Solo pruebas RBAC
    python run_tests.py --coverage        # Con reporte de cobertura
    python run_tests.py --verbose         # Modo verbose
    python run_tests.py --file test_file  # Prueba específica
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Ejecuta un comando y retorna si fue exitoso."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print('='*60)

    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n❌ Ejecución interrumpida por el usuario")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False


def main():
    """Función principal del script de pruebas."""
    parser = argparse.ArgumentParser(description="Ejecutar pruebas del sistema RBAC")
    parser.add_argument("--unit", action="store_true", help="Solo pruebas unitarias")
    parser.add_argument("--integration", action="store_true", help="Solo pruebas de integración")
    parser.add_argument("--rbac", action="store_true", help="Solo pruebas RBAC")
    parser.add_argument("--coverage", action="store_true", help="Ejecutar con coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")
    parser.add_argument("--file", help="Ejecutar prueba específica (ej: test_role_service.py)")

    args = parser.parse_args()

    # Verificar que estamos en el directorio correcto
    if not Path("pytest.ini").exists():
        print("❌ Error: Debe ejecutar este script desde el directorio backend/")
        sys.exit(1)

    print("🧪 SISTEMA DE PRUEBAS - SISTEMA RBAC")
    print("="*60)

    # Base command
    cmd = ["python", "-m", "pytest"]

    # Configurar opciones
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term-missing"])

    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Configurar marcadores
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.rbac:
        markers.append("rbac")

    if markers:
        cmd.extend(["-m", " or ".join(markers)])

    # Archivo específico
    if args.file:
        if not args.file.startswith("tests/"):
            args.file = f"tests/{args.file}"
        cmd.append(args.file)

    # Ejecutar pruebas
    success = run_command(cmd, "EJECUTANDO PRUEBAS")

    # Mostrar resultados
    print(f"\n{'='*60}")
    if success:
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        if args.coverage:
            print("📊 Reporte de cobertura generado en htmlcov/")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("🔍 Revisa los errores arriba para más detalles")

    print('='*60)

    # Comandos adicionales útiles
    print("\n📝 COMANDOS ÚTILES:")
    print("• python run_tests.py --coverage    # Pruebas con cobertura")
    print("• python run_tests.py --rbac        # Solo pruebas RBAC")
    print("• python run_tests.py --file tests/services/test_role_service.py  # Prueba específica")
    print("• python -m pytest --collect-only   # Ver todas las pruebas disponibles")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
