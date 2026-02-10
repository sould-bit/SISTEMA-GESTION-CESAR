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

**Problemas comunes con `.env`:**
- **Encoding:** Los archivos `.env` deben estar guardados en **UTF-8** sin BOM (Byte Order Mark)
- **Caracteres especiales:** Si las contraseñas contienen caracteres especiales, pueden causar problemas de encoding
- **Variables no definidas:** Si una variable de entorno no está definida, puede causar errores inesperados

**Solución para problemas de encoding:**
```bash
# Verificar el encoding del archivo .env
file -I backend/.env  # En Linux/Mac
# O en Python:
python -c "import chardet; print(chardet.detect(open('.env', 'rb').read()))"
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

## 7. Autenticación JWT en FastAPI

**Definición:**
Sistema de autenticación basado en JSON Web Tokens (JWT) que permite verificar la identidad de usuarios sin almacenar sesiones en el servidor.

**¿Por qué JWT?**
- **Sin estado**: El servidor no guarda sesiones, todo está en el token
- **Escalable**: Funciona bien en sistemas distribuidos
- **Seguro**: Los tokens son firmados y pueden expirar
- **Flexible**: Puedes incluir información adicional en el token

### 7.1 Componentes del sistema

#### **1. Modelos y Schemas**
```python
# Modelo de BD (SQLModel)
class User(SQLModel, table=True):
    id: int
    username: str
    hashed_password: str
    company_id: int  # Multi-tenant
    role: str

# Schemas para API
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: int
    company_id: int
    role: str
```

#### **2. Funciones de seguridad**
```python
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenData:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return TokenData(**payload)
```

#### **3. Dependencias de FastAPI**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Extrae usuario del token JWT"""
    try:
        payload = decode_token(token)
        user = get_user_by_id(payload.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
```

### 7.2 Flujo completo de autenticación

```
1. POST /auth/login
   Body: {"username": "admin", "password": "123"}

2. Backend:
   - Busca usuario por username
   - Verifica contraseña con bcrypt
   - Genera token JWT con datos del usuario

3. Response: {"access_token": "eyJ...", "token_type": "bearer"}

4. Cliente envía token en header:
   Authorization: Bearer eyJ...

5. Cada endpoint protegido usa Depends(get_current_user)
```

### 7.3 Multi-Tenant en autenticación

**Problema:** ¿Cómo aislar usuarios entre compañías?

**Solución:** Incluir `company_id` en el token JWT

```python
# Al crear token
token_data = {
    "user_id": user.id,
    "company_id": user.company_id,  # CRÍTICO para aislamiento
    "branch_id": user.branch_id,
    "role": user.role
}
token = create_access_token(token_data)

# Al verificar token
current_user = get_current_user(token)
# current_user.company_id se usa para filtrar queries
```

**Middleware de aislamiento:**
```python
def verify_company_access(company_id: int, current_user: User):
    if current_user.company_id != company_id:
        raise HTTPException(403, "Acceso denegado")
```

### 7.4 Endpoints de autenticación típicos

```python
@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, session: Session = Depends(get_session)):
    # 1. Buscar usuario
    user = session.exec(select(User).where(
        User.username == login_data.username,
        User.is_active == True
    )).first()

    # 2. Verificar contraseña
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(401, "Credenciales inválidas")

    # 3. Crear token
    token_data = {
        "user_id": user.id,
        "company_id": user.company_id,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = create_access_token(token_data)

    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
```

### 7.5 Consideraciones de seguridad

1. **Nunca almacenes contraseñas en texto plano**
2. **Usa HTTPS en producción**
3. **Configura tiempo de expiración razonable**
4. **Invalida tokens en logout** (aunque JWT es stateless)
5. **Rota las claves secretas periódicamente**

### 7.6 Debugging de autenticación

**Errores comunes:**
- `401 Unauthorized`: Token expirado o inválido
- `403 Forbidden`: Usuario no tiene permisos
- `500 Internal Server Error`: Problema con decode del token

**Herramientas útiles:**
```bash
# Decodificar token manualmente (para debugging)
import jwt
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
print(payload)
```

---

## 8. Permisos para Pedidos (Permission-Based RBAC)

### 8.1 Concepto

En lugar de verificar **roles** (isAdmin, isCashier, etc.) en el código, verificamos **permisos** configurados en Staff > Roles y Permisos. Esto permite:
- **Modularidad:** Un solo módulo (`order_permissions.py`) define qué permiso requiere cada transición.
- **Escalabilidad:** Cambiar quién puede aceptar pedidos sin tocar código, solo asignando `orders.update` al rol deseado.
- **Logs de monitoreo:** `log_security_event` registra denegaciones con order_id, usuario y permiso requerido.

### 8.2 Permisos usados

| Permiso | Acción |
|---------|--------|
| `orders.update` | Aceptar pedidos, enviar a cocina, marcar listo, entregar |
| `orders.cancel` | Cancelar pedidos directamente |
| `orders.manage_all` | Aprobar/rechazar solicitudes de cancelación |
| `cash.close` | Registrar pagos / cobrar mesa |

### 8.3 Backend

- **`app/core/order_permissions.py`:** Mapeo `(old_status, new_status) → permiso requerido`.
- **`OrderStateMachine.transition()`:** Usa `PermissionService.check_permission()` en lugar de roles.
- **Logs:** `log_security_event("ORDER_STATUS_DENIED", ...)` cuando se deniega el cambio.

### 8.4 Frontend

- **`useOrderPermissions` hook:** Centraliza `canAcceptOrder`, `canMarkReady`, `canDeliver`, etc. basado en `user.permissions`.
- **Componentes actualizados:** OrderDetailsModal, OrderCard, TableCard, OrderListItem usan el hook en lugar de `isAdmin || isCashier`.

### 8.5 Configuración

En `backend/data/seeds/role_permissions.json`, el rol **waiter** ya tiene `orders.update`, por lo que los meseros pueden aceptar pedidos si así se desea. Para quitarles esa capacidad, basta con remover `orders.update` del rol en Staff > Roles y Permisos.

---

_Este documento se actualizará a medida que avancemos._
