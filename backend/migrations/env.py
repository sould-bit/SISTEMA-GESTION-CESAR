from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

import os
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# ⭐ USAR LA MISMA CONFIGURACIÓN QUE LA APP (SOLUCIÓN ROBUSTA)
# Esto evita problemas de codificación y usa la misma lógica
from app.config import settings

# Sobrescribir la URL con la configuración de la app
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)



# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
from sqlmodel import SQLModel
from app.models import User, Company, Branch, Subscription, Category, Role, RolePermission, Permission, PermissionCategory, Product, Table, Order  # Tus modelos
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
