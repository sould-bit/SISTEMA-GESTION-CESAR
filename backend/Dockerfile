#imagen base : python 3.12 version 3.12.4

FROM python:3.12.4

#establecer carpeta de trabajo

WORKDIR /app

#copiar el archivo requirements.txt

COPY requirements.txt ./requirements.txt

#instalar las dependencias de python

RUN pip install --no-cache-dir -r requirements.txt

#copiar el resto del trabajo 

COPY . . 

#exponer el puerto 8000 "donde correra fastapi"

EXPOSE 8000

#comando para ejecutar la app 


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]