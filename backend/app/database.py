from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

# Crear el engine ASÍNCRONO
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False  # muestra las SQL en consola
)

# Crear sessionmaker ASÍNCRONO
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    """
    Generador de sesiones ASÍNCRONAS

    Esta función es una DEPENDENCIA que:
    1. Crea una sesión asíncrona
    2. La entrega al endpoint
    3. Se asegura que se cierre automáticamente
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()  # Commit si no hay errores
        except Exception:
            await session.rollback()  # Rollback si hay error
            raise
        finally:
            await session.close()  # Siempre cerrar la sesión