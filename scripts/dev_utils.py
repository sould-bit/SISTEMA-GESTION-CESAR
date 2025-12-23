#!/usr/bin/env python3
"""
Development Utilities - Herramientas para desarrollo
===================================================

Utilidades comunes para facilitar el desarrollo y testing.

Uso:
    python scripts/dev_utils.py <comando>

Comandos disponibles:
    setup       : Setup completo del entorno de desarrollo
    seed        : Ejecutar seeding de datos
    test        : Ejecutar tests
    clean       : Limpiar archivos temporales
    reset-db    : Resetear base de datos completamente
    logs        : Ver logs de la aplicación
"""

import subprocess
import sys
import argparse
from pathlib import Path


class DevUtils:
    """Utilidades para desarrollo"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    def run_command(self, cmd: str, cwd=None):
        """Ejecuta un comando y retorna el resultado"""
        try:
            result = subprocess.run(
                cmd.split(),
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ Error ejecutando '{cmd}': {e}")
            print(f"stderr: {e.stderr}")
            return None

    def setup(self):
        """Setup completo del entorno"""
        print("🚀 Iniciando setup completo...")

        # Verificar Docker
        print("🐳 Verificando Docker...")
        if not self.run_command("docker --version"):
            print("❌ Docker no está instalado")
            return False

        # Verificar Docker Compose
        print("🐳 Verificando Docker Compose...")
        if not self.run_command("docker-compose --version"):
            print("❌ Docker Compose no está instalado")
            return False

        # Construir imágenes
        print("🏗️  Construyendo imágenes...")
        if not self.run_command("docker-compose build"):
            return False

        # Iniciar servicios
        print("▶️  Iniciando servicios...")
        if not self.run_command("docker-compose up -d"):
            return False

        # Esperar a que la DB esté lista
        print("⏳ Esperando base de datos...")
        self.run_command("docker-compose exec backend bash -c 'while ! nc -z db 5432; do sleep 1; done'")

        # Ejecutar migraciones
        print("🗃️  Ejecutando migraciones...")
        if not self.run_command("docker-compose exec backend alembic upgrade head"):
            return False

        # Seed de datos
        print("🌱 Poblando datos iniciales...")
        if not self.run_command("docker-compose exec backend python scripts/seed/master_seed.py"):
            return False

        print("✅ Setup completado exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Verificar aplicación: http://localhost:8000/docs")
        print("2. Login admin: admin/admin123")
        print("3. Ejecutar tests: python scripts/dev_utils.py test")

        return True

    def seed(self):
        """Ejecutar seeding de datos"""
        print("🌱 Ejecutando seeding de datos...")
        result = self.run_command("docker-compose exec backend python scripts/seed/master_seed.py")
        return result is not None

    def test(self):
        """Ejecutar tests"""
        print("🧪 Ejecutando tests...")
        result = self.run_command("docker-compose exec backend pytest tests/ -v")
        return result is not None

    def clean(self):
        """Limpiar archivos temporales"""
        print("🧹 Limpiando archivos temporales...")

        # Archivos Python
        patterns = ["*.pyc", "__pycache__", "*.pyo", "*.pyd"]
        for pattern in patterns:
            self.run_command(f"find . -name '{pattern}' -delete")

        # Logs
        self.run_command("find . -name '*.log' -delete")

        # Docker
        self.run_command("docker-compose down -v")
        self.run_command("docker system prune -f")

        print("✅ Limpieza completada")
        return True

    def reset_db(self):
        """Resetear base de datos"""
        print("💥 Reseteando base de datos...")

        # Detener servicios
        self.run_command("docker-compose down -v")

        # Recrear servicios
        self.run_command("docker-compose up -d db")

        # Esperar DB
        self.run_command("docker-compose exec backend bash -c 'while ! nc -z db 5432; do sleep 1; done'")

        # Migraciones
        self.run_command("docker-compose exec backend alembic upgrade head")

        # Seed
        self.seed()

        print("✅ Base de datos reseteada")
        return True

    def logs(self):
        """Ver logs de la aplicación"""
        print("📋 Logs de la aplicación:")
        self.run_command("docker-compose logs -f backend")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Development Utilities")
    parser.add_argument("command", choices=[
        "setup", "seed", "test", "clean", "reset-db", "logs"
    ], help="Comando a ejecutar")

    args = parser.parse_args()

    utils = DevUtils()

    commands = {
        "setup": utils.setup,
        "seed": utils.seed,
        "test": utils.test,
        "clean": utils.clean,
        "reset-db": utils.reset_db,
        "logs": utils.logs
    }

    success = commands[args.command]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
