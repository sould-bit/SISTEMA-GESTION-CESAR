from fastapi import FastAPI

#crear instancias de fast 

app = FastAPI(
    title="API de gestion de cesar",
    description="SISTEMA INTEGRAL DE GESTION DE CESAR",
    version="0.0.1"
)


#RUTA RAIZ 
@app.get("/")
def read_root():
   return {"Hello": "World"}