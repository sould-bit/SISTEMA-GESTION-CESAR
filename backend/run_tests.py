#!/usr/bin/env python3
"""
🧪 EJECUTOR DE TESTS - FastOps SaaS

Script para ejecutar tests con diferentes configuraciones y reportes.

Uso:
    python run_tests.py              # Tests básicos
    python run_tests.py --coverage   # Con coverage
    python run_tests.py --html       # Reporte HTML
    python run_tests.py --verbose    # Modo verbose
    python run_tests.py --unit       # Solo unit tests
    python run_tests.py --integration # Solo integration tests
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd: list, description: str) -> int:
    """Ejecutar comando y mostrar resultado"""
    print(f"\n🔄 {description}")
    print(f"📝 Comando: {' '.join(cmd)}")
    print("-" * 50)

    result = subprocess.run(cmd, cwd=Path(__file__).parent)

    if result.returncode == 0:
        print(f"✅ {description} - ÉXITO")
    else:
        print(f"❌ {description} - FALLÓ")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Ejecutor de tests para FastOps")
    parser.add_argument("--coverage", action="store_true", help="Ejecutar con coverage")
    parser.add_argument("--html", action="store_true", help="Generar reporte HTML")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")
    parser.add_argument("--unit", action="store_true", help="Solo tests unitarios")
    parser.add_argument("--integration", action="store_true", help="Solo tests de integración")
    parser.add_argument("--services", action="store_true", help="Solo tests de servicios")
    parser.add_argument("--routers", action="store_true", help="Solo tests de routers")
    parser.add_argument("--fast", action="store_true", help="Solo tests rápidos")

    args = parser.parse_args()

    # Base command
    cmd = [sys.executable, "-m", "pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
        if args.html:
            cmd.append("--cov-report=html")

    # Add HTML report
    if args.html:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])

    # Filter by type
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.services:
        cmd.append("tests/services/")
    elif args.routers:
        cmd.append("tests/routers/")
    elif args.fast:
        cmd.extend(["-m", "not slow"])

    # Run tests
    exit_code = run_command(cmd, "EJECUTANDO TESTS")

    # Show results
    if exit_code == 0:
        print("\n🎉 TODOS LOS TESTS PASARON!")
        if args.coverage:
            print("📊 Reporte de coverage generado")
        if args.html:
            print("📄 Reporte HTML generado en: test_report.html")
            print("📈 Reporte de coverage HTML en: htmlcov/index.html")
    else:
        print(f"\n💥 {exit_code} TEST(S) FALLARON!")
        print("🔍 Revisa los logs arriba para más detalles")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
