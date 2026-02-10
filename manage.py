#!/usr/bin/env python3
"""
SISTEMA GESTION CESAR - Management Script
=========================================

Unified interface for development, database management, and administration.

Usage:
    python manage.py <command> [subcommand] [options]

Examples:
    python manage.py setup             # Full environment setup
    python manage.py start             # Start services
    python manage.py db migrate "msg"  # Create migration
    python manage.py db seed           # Run master seed
    python manage.py test --unit       # Run unit tests
"""

import subprocess
import sys
import os
import argparse
import time
from pathlib import Path
from typing import Optional, List

class Manager:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.backend_container = os.getenv("BACKEND_CONTAINER", "backend_FastOps")
        self.db_container = os.getenv("DB_CONTAINER", "container_DB_FastOps") 

    def _run_local(self, cmd: str, cwd: str = None) -> bool:
        """Runs a command on the local host machine."""
        print(f"📍 Executing local: {cmd}")
        work_dir = cwd if cwd else self.project_root
        try:
            subprocess.run(
                cmd,
                cwd=work_dir,
                shell=True,
                check=True,
                env=None # Inherit env vars
            )
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Error running: {cmd}")
            return False

    def _run_in_backend(self, cmd: str, interactive: bool = False) -> bool:
        """Runs a command inside the backend container."""
        flags = "-it" if interactive else ""
        full_cmd = f"docker exec {flags} {self.backend_container} {cmd}"
        print(f"🐳 Executing in backend: {cmd}")
        return self._run_local(full_cmd)

    # ==========================================
    # Environment Control
    # ==========================================
    def setup(self):
        """Full environment setup (Build -> Up -> Wait -> Migrate -> Seed)"""
        print("🚀 Starting full setup...")
        if not self._run_local("docker-compose build"): return
        if not self._run_local("docker-compose up -d"): return
        self.wait_db()
        self.db_upgrade()
        self.db_seed()
        print("\n✅ Setup complete! API: http://localhost:8000/docs")

    def start(self):
        """Start services"""
        self._run_local("docker-compose up -d")
        print("✅ Services started")

    def stop(self):
        """Stop services"""
        self._run_local("docker-compose down")
        print("✅ Services stopped")
    
    def restart(self):
        """Restart services"""
        self.stop()
        self.start()

    def logs(self, service: str = "backend"):
        """Show logs"""
        self._run_local(f"docker-compose logs -f {service}")

    def shell(self):
        """Open bash in backend container"""
        self._run_in_backend("bash", interactive=True)

    def wait_db(self):
        """Wait for DB to be potentially ready (simple sleep loop or netcat)"""
        print("⏳ Waiting for Database...")
        # A simple retry mechanism using the existing script logic inside container is best
        # effectively: while ! nc -z db 5432; do sleep 1; done
        self._run_in_backend("bash -c 'while ! nc -z db 5432; do sleep 1; done'")
        print("✅ Database is reachable")

    # ==========================================
    # Database Management
    # ==========================================
    def db_migrate(self, message: str, local: bool = False):
        """Create a new migration revision"""
        cmd = f'python -m alembic revision --autogenerate -m "{message}"'
        if local: self._run_local(cmd, cwd=os.path.join(self.project_root, 'backend'))
        else: self._run_in_backend(cmd)

    def db_upgrade(self, local: bool = False):
        """Apply migrations"""
        print("🗃️  Applying migrations...")
        cmd = "python -m alembic upgrade head"
        if local: self._run_local(cmd, cwd=os.path.join(self.project_root, 'backend'))
        else: self._run_in_backend(cmd)

    def db_downgrade(self, revision: str = "-1", local: bool = False):
        """Revert migrations"""
        cmd = f"python -m alembic downgrade {revision}"
        if local: self._run_local(cmd, cwd=os.path.join(self.project_root, 'backend'))
        else: self._run_in_backend(cmd)

    def db_reset(self):
        """Destructive: Wipe DB, Re-create, Seed"""
        print("⚠️  WARNING: This will DESTROY all data.")
        confirmation = input("Are you sure? (y/N): ")
        if confirmation.lower() != 'y':
            print("Operation cancelled.")
            return

        print("💥 Resetting database...")
        self._run_local("docker-compose down -v") # Removes volumes
        self._run_local("docker-compose up -d")
        self.wait_db()
        self.db_upgrade()
        self.db_seed()
        print("✅ Database reset complete")

    def db_seed(self, local: bool = False, genesis: bool = False):
        """Run master seed"""
        print("🌱 Seeding data...")
        cmd = "python scripts/seed/master_seed.py"
        if genesis:
            cmd += " --genesis"
        
        if local: self._run_local(cmd)
        else: self._run_in_backend(cmd)


    def admin_create(self, local: bool = False):
        """Create admin user"""
        print("👤 Creating admin user...")
        cmd = "python scripts/admin/create_admin.py"
        if local: self._run_local(cmd)
        else: self._run_in_backend(cmd)

    # ==========================================
    # Testing
    # ==========================================
    def test(self, args: List[str]):
        """Run tests. Pass args like --unit, --coverage"""
        # We forward arguments to the backend script
        # create string from args list
        args_str = " ".join(args)
        cmd = f"python scripts/run_tests.py {args_str}"
        self._run_in_backend(cmd)

    # ==========================================
    # Maintenance
    # ==========================================
    def clean(self):
        """Clean temp files"""
        print("🧹 Cleaning local temp files...")
        # Local cleanup
        patterns = ["*.pyc", "__pycache__", "*.pyo", "*.pyd", ".pytest_cache"]
        for pattern in patterns:
             # Recursive delete using python pathlib or subprocess find/del
             if sys.platform == "win32":
                 self._run_local(f'del /S /Q {pattern} 2>nul') # Simple windows cleanup attempt
             else:
                 self._run_local(f"find . -name '{pattern}' -delete")
        
        print("✅ Clean finished")


def main():
    parser = argparse.ArgumentParser(description="System Management Script")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup / Env
    subparsers.add_parser("setup", help="Full setup (build, up, migrate, seed)")
    subparsers.add_parser("start", help="Start services")
    subparsers.add_parser("stop", help="Stop services")
    subparsers.add_parser("restart", help="Restart services")
    logs_p = subparsers.add_parser("logs", help="View logs")
    logs_p.add_argument("service", nargs="?", default="backend", help="Service name (default: backend)")
    subparsers.add_parser("shell", help="Open bash in backend")

    # DB Group
    db_parser = subparsers.add_parser("db", help="Database commands")
    db_parser.add_argument("--local", action="store_true", help="Run command on local host instead of Docker")
    db_subs = db_parser.add_subparsers(dest="db_command")
    
    mig_p = db_subs.add_parser("migrate", help="Create migration")
    mig_p.add_argument("message", help="Migration message")
    
    db_subs.add_parser("upgrade", help="Apply migrations")
    
    down_p = db_subs.add_parser("downgrade", help="Revert migration")
    down_p.add_argument("revision", nargs="?", default="-1", help="Revision (default -1)")
    
    db_subs.add_parser("reset", help="Reset DB (Destructive)")
    seed_p = db_subs.add_parser("seed", help="Run master seed")
    seed_p.add_argument("--genesis", action="store_true", help="Genesis Mode: System config only")
    seed_p.add_argument("--local", action="store_true", help="Run command on local host")

    # Admin Group
    admin_parser = subparsers.add_parser("admin", help="Admin commands")
    admin_parser.add_argument("--local", action="store_true", help="Run command on local host instead of Docker")
    admin_subs = admin_parser.add_subparsers(dest="admin_command")
    admin_subs.add_parser("create", help="Create default admin user")

    # Test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--unit", action="store_true", help="Unit tests only")
    test_parser.add_argument("--integration", action="store_true", help="Integration tests only")
    test_parser.add_argument("--rbac", action="store_true", help="RBAC tests only")
    test_parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    test_parser.add_argument("--file", help="Specific test file")

    # Clean
    subparsers.add_parser("clean", help="Clean temp files")

    # Parse
    args = parser.parse_args()
    
    mgr = Manager()

    if args.command == "setup":
        mgr.setup()
    elif args.command == "start":
        mgr.start()
    elif args.command == "stop":
        mgr.stop()
    elif args.command == "restart":
        mgr.restart()
    elif args.command == "logs":
        mgr.logs(args.service)
    elif args.command == "shell":
        mgr.shell()
    
    elif args.command == "db":
        local_mode = getattr(args, 'local', False)
        if args.db_command == "migrate":
            mgr.db_migrate(args.message, local=local_mode)
        elif args.db_command == "upgrade":
            mgr.db_upgrade(local=local_mode)
        elif args.db_command == "downgrade":
            mgr.db_downgrade(args.revision, local=local_mode)
        elif args.db_command == "reset":
            mgr.db_reset() # This is destructive and interactive, keep as is
        elif args.db_command == "seed":
            genesis_mode = getattr(args, 'genesis', False)
            mgr.db_seed(local=local_mode, genesis=genesis_mode)
        else:
            db_parser.print_help()

    elif args.command == "admin":
        local_mode = getattr(args, 'local', False)
        if args.admin_command == "create":
            mgr.admin_create(local=local_mode)
        else:
            admin_parser.print_help()

    elif args.command == "test":
        # Reconstruct args for the backend script
        forward_args = []
        if args.unit: forward_args.append("--unit")
        if args.integration: forward_args.append("--integration")
        if args.rbac: forward_args.append("--rbac")
        if args.coverage: forward_args.append("--coverage")
        if args.file: forward_args.extend(["--file", args.file])
        mgr.test(forward_args)

    elif args.command == "clean":
        mgr.clean()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
