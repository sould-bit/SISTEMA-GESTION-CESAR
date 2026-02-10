import os
import logging
# Trigger reload for schema update
from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session, SQLModel
from .database import get_session, engine
from .models import User, Company, Branch, Subscription # importar modelos para que  SQLMODEL  los detecte
from app.routers import (
    auth,
    rbac,
    product,
    recipe,
    category,
    inventory,
    order,
    payment,
    cash,
    reports,
    customers,
    storefront,
    delivery,
    audit,
    tickets,
    uploads,
    modifiers,
    ingredients,
    menu_engineering,
    kitchen_production,
    inventory_count,
    intelligence,
    users,
    branches,
    tables
)
from fastapi.staticfiles import StaticFiles
from .core.websockets import sio # Import Socket.IO server
import socketio
from app.core.exceptions import RBACException, create_rbac_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Logger setup
logger = logging.getLogger(__name__)

# Inicializar App
app = FastAPI(
    title="SISTEMA GESTION CESAR",
    version="0.1.0"
)

# Configurar CORS (Permitir todo en desarrollo para acceso móvil)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Cambiado a False para permitir "*" en desarrollo
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(rbac.router)
app.include_router(product.router)
app.include_router(recipe.router)
app.include_router(order.router)
app.include_router(inventory.router)
app.include_router(payment.router)
app.include_router(cash.router)
app.include_router(reports.router)
app.include_router(customers.router)
app.include_router(storefront.router)
app.include_router(delivery.router)
app.include_router(audit.router)
app.include_router(tickets.router)
app.include_router(uploads.router)
app.include_router(modifiers.router)
app.include_router(ingredients.router)
app.include_router(menu_engineering.router)
app.include_router(kitchen_production.router)
app.include_router(inventory_count.router)
app.include_router(intelligence.router)
app.include_router(users.router)
app.include_router(branches.router)
app.include_router(tables.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Handler global para excepciones RBAC
app.add_exception_handler(RBACException, create_rbac_exception_handler())

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors for easier debugging."""
    logger.error(f"❌ Validation Error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.on_event("startup")
async def on_startup():
    """Inicialización de la aplicación."""
    logger.info(
        "Aplicación iniciada - Sistema RBAC Avanzado",
        extra={
            "version": "0.1.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "features": ["RBAC", "JWT", "PostgreSQL", "FastAPI", "Storefront"]
        }
    )
    
    # Auto-create schema if missing (Fallback for Alembic issues in dev)
    try:
        async with engine.begin() as conn:
            # Importar todos los modelos para asegurar que se registren en metadata
            # Esto ya se hace arriba con "from .models import ...", pero aseguramos
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("✅ Schema auto-created (if needed)")
    except Exception as e:
        logger.error(f"❌ Schema auto-creation failed: {e}")
    
    # Auto-sync RBAC global metadata on startup
    try:
        from sqlalchemy import text
        from app.database import async_session
        from app.services.rbac_sync_service import RBACSyncService
        
        async with async_session() as session:
            # Verificar si las tablas existen antes de intentar sync
            try:
                await session.execute(text("SELECT 1 FROM permission_categories LIMIT 1"))
            except Exception:
                logger.info("⏳ RBAC Sync omitido: Tablas no existen aún. Ejecute 'alembic upgrade head' primero.")
                return
            
            # Tablas existen, ejecutar sync
            rbac_service = RBACSyncService(session)
            stats = await rbac_service.sync_global_metadata()
            
            total_changes = stats['categories_created'] + stats['permissions_created'] + stats['permissions_updated']
            if total_changes > 0:
                logger.info(
                    f"✅ RBAC Sync: {stats['categories_created']} categorías, "
                    f"{stats['permissions_created']} permisos creados, "
                    f"{stats['permissions_updated']} actualizados"
                )
            else:
                logger.info("✅ RBAC Sync: Datos globales ya sincronizados")
    except Exception as e:
        logger.warning(f"⚠️ RBAC Sync error inesperado: {e}")

@app.get("/")
def read_root():
    return {
        "message": "Bienvenido a SISALCHI API",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/bd-test")
async def test_database(session = Depends(get_session)):
    """prueba de la conexión bd """
    try:
        await session.execute(select(1))
        return {"status": "ok", "message": "Conexión a BD exitosa"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Socket.IO ASGI wrapper - combines FastAPI with Socket.IO
# This enables WebSocket connections on the same port as the HTTP API
combined_asgi_app = socketio.ASGIApp(sio, app)
