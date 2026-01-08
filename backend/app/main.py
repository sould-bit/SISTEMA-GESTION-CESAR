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
    cash
)
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

# Handler global para excepciones RBAC
app.add_exception_handler(RBACException, create_rbac_exception_handler())


# Evento que se ejecuta al arrancar la app
@app.on_event("startup")
async def on_startup():
    """Inicialización de la aplicación."""
    # create_db_and_tables()  # Comentado: usar Alembic

    logger.info(
        "Aplicación iniciada - Sistema RBAC Avanzado",
        extra={
            "version": "0.0.2",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "features": ["RBAC", "JWT", "PostgreSQL", "FastAPI"]
        }
    )




#RUTA RAIZ 
@app.get("/")
def read_root():
    return {
    "message": "Bienvenido a SISALCHI API",
    "status": "running",
    "version": "0.1.0"}


#RUTA DE SALUD
@app.get("/health")
def health_check():
    return {"status": "ok"}


#ruta para probar coneccion con bd
@app.get("/bd-test")
async def test_database(session = Depends(get_session)):
    """prueba de la conexión bd """

    try:
        #ejecutar una query simple
        result = await session.execute(select(1))
        value = result.scalar_one()
        return {
            "status": "success",
            "message": "Conexión a PostgreSQL exitosa (Async)",
            "result": value
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Error al conectar a la base de datos",
            "error": str(e)
        }

# DEBUG: Listar todas las compañías (temporal)
@app.get("/debug/companies")
async def debug_companies(session = Depends(get_session)):
    """Listar todas las compañías para debug"""
    try:
        result = await session.execute(select(Company))
        companies = result.scalars().all()
        return {
            "count": len(companies),
            "companies": [
                {
                    "id": c.id,
                    "name": c.name,
                    "slug": c.slug,
                    "is_active": c.is_active
                } for c in companies
            ]
        }
    except Exception as e:
        return {"error": str(e)}

# DEBUG: Listar usuarios por compañía
@app.get("/debug/users/{company_slug}")
async def debug_users(company_slug: str, session = Depends(get_session)):
    """Listar usuarios de una compañía para debug"""
    try:
        # Buscar compañía
        result = await session.execute(select(Company).where(Company.slug == company_slug))
        company = result.scalar_one_or_none()
        if not company:
            return {"error": f"Compañía '{company_slug}' no encontrada"}

        # Buscar usuarios
        result = await session.execute(select(User).where(User.company_id == company.id))
        users = result.scalars().all()

        return {
            "company": company.name,
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                    "is_active": u.is_active
                } for u in users
            ]
        }
    except Exception as e:
        return {"error": str(e)}

# MOUNT SOCKET.IO
# Esto permite que la app maneje tanto HTTP (FastAPI) como WebSockets (Socket.IO)
# socket_path default es 'socket.io', debe coincidir con el cliente
app = socketio.ASGIApp(sio, app)