from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session, SQLModel
from .database import get_session, engine
from .models import User, Company, Branch, Subscription # importar modelos para que  SQLMODEL  los detecte
from .routers import auth, category, rbac, product

from .core.logging_config import get_rbac_logger
from .core.exceptions import RBACException, create_rbac_exception_handler
import time
import os

# funcion para crear tablas al inicio
#def create_db_and_tables(): 3comentado para darle control total a alembic
#   SQLModel.metadata.create_all(engine)

# Configurar logging
logger = get_rbac_logger("app.api")

# Crear instancia de FastAPI con configuración avanzada
app = FastAPI(
    title="API de Gestión de César",
    description="SISTEMA INTEGRAL DE GESTIÓN DE CÉSAR - RBAC Avanzado",
    version="0.0.2",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging personalizado
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging detallado de requests."""
    start_time = time.time()

    # Log de entrada
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "path": request.url.path,
            "query_params": str(request.query_params)
        }
    )

    try:
        response = await call_next(request)

        # Calcular duración
        duration = time.time() - start_time

        # Log de respuesta exitosa
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "path": request.url.path
            }
        )

        return response

    except Exception as e:
        # Calcular duración
        duration = time.time() - start_time

        # Log de error
        logger.error(
            "Request failed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "duration_ms": round(duration * 1000, 2),
                "error": str(e),
                "path": request.url.path
            },
            exc_info=True
        )
        raise

# Incluir routers
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(rbac.router)
app.include_router(product.router)

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