# Conceptos Clave de Desarrollo - SISALCHI

Este documento sirve como guía de aprendizaje para dominar los conceptos técnicos implementados en el proyecto.

## 1. Multi-Tenancy (Arquitectura Multitenencia)

**Definición:**  
Es una arquitectura de software donde una sola instancia de la aplicación sirve a múltiples clientes (tenants o inquilinos). En SISALCHI, cada "Negocio" (ej: "Salchipapas El Rincón", "Comidas Rápidas Juan") es un tenant.

**Implementación en SISALCHI:**

- **Base de Datos Compartida:** Todos los datos viven en la misma base de datos.
- **Aislamiento Lógico:** Cada tabla crítica (usuarios, productos, pedidos) tiene una columna `company_id`.
- **Seguridad:** Cada consulta (Query) a la base de datos _debe_ filtrar obligatoriamente por `company_id`. Esto evita que el Negocio A vea los datos del Negocio B.
- **Sucursales:** Dentro de un Tenant (`company_id`), existen Sucursales (`branch_id`) para manejar inventarios y ventas separadas.

**Por qué es importante:**
Nos permite escalar el SaaS. Con un solo servidor podemos atender a cientos de negocios, en lugar de desplegar un servidor nuevo para cada cliente.

## 2. Pydantic & SQLModel

**Definición:**

- **Pydantic:** Librería para validación de datos en Python usando anotaciones de tipo.
- **SQLModel:** Librería construida sobre Pydantic y SQLAlchemy que permite definir modelos que sirven tanto para interactuar con la Base de Datos (SQL) como para validar datos en la API (FastAPI).

**Uso:**
Definimos clases que representan tablas y validaciones al mismo tiempo.

---

## 3. Variables de Entorno y Archivos `.env`

**Definición:**
Los archivos `.env` contienen configuración sensible (contraseñas, URLs de base de datos, claves secretas) que **NO deben subirse a Git**. Cada desarrollador tiene su propio `.env` con sus credenciales.

**¿Por qué usar `.env`?**
- **Seguridad:** No exponemos contraseñas en el código
- **Flexibilidad:** Cada entorno (desarrollo, producción) tiene su propia configuración
- **Buenas prácticas:** Separar configuración del código

**Formato correcto:**
```env
# ✅ CORRECTO - Sin espacios alrededor del =
DATABASE_URL=postgresql://usuario:password@localhost:5432/dbname
SECRET_KEY=mi-clave-secreta-super-larga

# ❌ INCORRECTO - Con espacios
DATABASE_URL = postgresql://...  # Error: espacios causan problemas
```

**Codificación importante:**
- El archivo `.env` **DEBE** estar guardado en **UTF-8 sin BOM**
- En Windows, al guardar en VS Code, seleccionar "UTF-8" (NO "UTF-8 with BOM")
- Si hay caracteres especiales mal codificados, obtendrás `UnicodeDecodeError`

**Problema común encontrado:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xab in position 8
```

**Solución:**
1. Abrir el `.env` en VS Code
2. Click en la esquina inferior derecha donde dice la codificación
3. Seleccionar "Save with Encoding" → "UTF-8"
4. Guardar el archivo

---

## 4. Pydantic Settings y Lectura de `.env`

**Definición:**
`Pydantic Settings` es una clase que lee automáticamente variables de entorno desde un archivo `.env`.

**Ejemplo en nuestro proyecto:**
```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str  # Variable requerida
    SECRET_KEY: str    # Variable requerida
    
    class Config:
        # Ruta al archivo .env
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"
        env_file_encoding = 'utf-8'  # Codificación del archivo
```

**¿Cómo funciona?**
1. Al crear `Settings()`, Pydantic busca el archivo `.env` en la ruta especificada
2. Lee todas las variables del archivo
3. Valida que las variables requeridas existan
4. Si falta una variable requerida → Lanza error

**Ruta calculada:**
```python
Path(__file__)  # backend/app/config.py
.resolve()      # Ruta absoluta
.parent         # backend/app/
.parent         # backend/
.parent         # raíz del proyecto (SISTEMA-GESTION-CESAR/)
/ ".env"        # SISTEMA-GESTION-CESAR/.env
```

**Variables requeridas en nuestro proyecto:**
```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/nombre_db

# Seguridad JWT
SECRET_KEY=clave-secreta-minimo-32-caracteres-aleatorios
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 5. Docker Compose y Variables de Entorno

**Definición:**
Docker Compose lee variables de entorno desde un archivo `.env` en la **raíz del proyecto** (donde está el `docker-compose.yml`).

**¿Cómo funciona?**
```yaml
# docker-compose.yml
services:
  db:
    environment:
      POSTGRES_USER: ${POSTGRES_USER}      # Lee de .env
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Lee de .env
      POSTGRES_DB: ${POSTGRES_DB}          # Lee de .env
```

```env
# .env (en la raíz del proyecto)
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123456789
POSTGRES_DB=bdfastops
```

**Proceso:**
1. Docker Compose lee `.env` en la raíz
2. Reemplaza `${VARIABLE}` con el valor del `.env`
3. Pasa las variables al contenedor como variables de entorno

**Problema común:**
Si el contenedor se reinicia constantemente con error:
```
Error: Database is uninitialized and superuser password is not specified.
```

**Causas posibles:**
1. El archivo `.env` no existe en la raíz
2. Las variables están vacías o mal formateadas
3. Docker Compose no está leyendo el archivo

**Solución:**
```powershell
# Verificar que Docker Compose lee las variables
docker-compose config | Select-String POSTGRES

# Si no aparecen, verificar que .env existe
Test-Path .env

# Reiniciar contenedor
docker-compose down
docker-compose up -d db
```

---

## 6. Dos Archivos `.env` en el Proyecto

**¿Por qué dos archivos `.env`?**

En nuestro proyecto tenemos:
1. **`.env` en la raíz** → Para Docker Compose
2. **`.env` en `backend/app/`** → Para la aplicación Python (opcional)

**Explicación:**
- **Docker Compose** busca `.env` en la raíz (donde está `docker-compose.yml`)
- **Pydantic Settings** busca `.env` donde le indiquemos en `config.py`

**En nuestro caso:**
- `config.py` busca en la raíz: `Path(__file__).resolve().parent.parent.parent / ".env"`
- Entonces podemos usar **un solo archivo `.env` en la raíz** para ambos

**Variables necesarias en `.env` (raíz):**
```env
# Para Docker Compose
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123456789
POSTGRES_DB=bdfastops

# Para Python (Pydantic Settings)
DATABASE_URL=postgresql://admin:admin123456789@localhost:5432/bdfastops
SECRET_KEY=tu-clave-secreta-super-segura-minimo-32-caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 7. FastAPI Dependencies (`Depends`)

**Definición:**
`Depends` es un sistema de inyección de dependencias de FastAPI. Permite reutilizar lógica común (como obtener el usuario actual) en múltiples endpoints.

**Ejemplo básico:**
```python
from fastapi import Depends

def get_current_user():
    # Lógica para obtener usuario
    return user

@app.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return current_user
```

**Uso en nuestro proyecto (futuro):**
```python
# Obtener sesión de base de datos
@app.get("/orders")
def get_orders(session: Session = Depends(get_session)):
    # session ya está disponible
    orders = session.exec(select(Order)).all()
    return orders
```

**Ventajas:**
- Código reutilizable
- Fácil de testear
- Separación de responsabilidades

---

_Este documento se actualizará a medida que avancemos._
