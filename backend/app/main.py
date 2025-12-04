from fastapi import FastAPI, Depends
from sqlmodel import select, Session
from .database import get_session


#crear instancias de fast 

app = FastAPI(
    title="API de gestion de cesar",
    description="SISTEMA INTEGRAL DE GESTION DE CESAR",
    version="0.0.1"
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
def test_database(session:Session = Depends(get_session)):
    """preuba de la conceccion bd """

    try: 
        #ejecutar una query simple 
        result = session.exec(select(1)).one()
        return {
            "status": "success",
            "message": "Conexión a PostgreSQL exitosa",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Error al conectar a la base de datos",
            "error": str(e)
        }