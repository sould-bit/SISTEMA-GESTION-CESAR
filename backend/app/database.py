from sqlmodel import create_engine, Session
from .config import settings

#crear el engine (mmotoe de coneccion)

engine = create_engine(
    settings.DATABASE_URL,
    echo= True # muestra las sql en consola 
)


def get_session():
    """generador de sesiones"""
    
    with Session(engine) as session:
        yield session