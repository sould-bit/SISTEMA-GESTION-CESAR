import os
import logging
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
    tickets,
    uploads,
    modifiers,
    ingredients,
    menu_engineering,
    kitchen_production,
    inventory_count,
    intelligence
)
from fastapi.staticfiles import StaticFiles
from .core.websockets import sio # Import Socket.IO server
import socketio
from app.core.exceptions import RBACException, create_rbac_exception_handler

# Logger setup
logger = logging.getLogger(__name__)

# Inicializar App
app = FastAPI(
    title="SISTEMA GESTION CESAR",
    version="0.1.0"
)

# Configurar CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Handler global para excepciones RBAC
app.add_exception_handler(RBACException, create_rbac_exception_handler())

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