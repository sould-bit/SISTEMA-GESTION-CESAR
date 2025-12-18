from fastapi import FastAPI, Depends
from sqlmodel import select, Session, SQLModel
from .database import get_session, engine 
from .models import User, Company, Branch, Subscription # importar modelos para que  SQLMODEL  los detecte 
from .routers import auth, category

import logging
logging.basicConfig(level=logging.INFO)

# funcion para crear tablas al inicio
#def create_db_and_tables(): 3comentado para darle control total a alembic
#   SQLModel.metadata.create_all(engine)

#crear instancias de fast 

app = FastAPI(
    title="API de gestion de cesar",
    description="SISTEMA INTEGRAL DE GESTION DE CESAR",
    version="0.0.1"
)

app.include_router(auth.router)
app.include_router(category.router)


#Evento que se ejecuta al arramncar la app 
@app.on_event("startup")
async def on_startup():
    #create_db_and_tables()
    logging.info("Aplicacion iniciada - Async mode")




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