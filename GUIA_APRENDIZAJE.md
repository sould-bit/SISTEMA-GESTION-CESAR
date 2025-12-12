# 🎓 Guía de Aprendizaje - Proyecto SISALCHI

## 📚 Introducción

Esta guía te llevará paso a paso en el desarrollo del sistema SISALCHI. Cada fase está diseñada para que aprendas conceptos fundamentales de desarrollo web moderno.

---

## 🗺️ Roadmap de Aprendizaje

### **FASE 0: Fundamentos y Preparación del Proyecto** ⏱️ 1-2 días

#### 🎯 Objetivos de Aprendizaje

- Entender qué es un monorepo y por qué usarlo
- Aprender sobre Docker y contenedores
- Configurar un proyecto moderno de JavaScript/TypeScript
- Dominar Git y control de versiones

#### 📝 Conceptos que Aprenderás

1. **Monorepo**: Un repositorio que contiene múltiples proyectos (backend + frontend)
2. **Docker**: Contenedores para empaquetar aplicaciones
3. **Node.js y npm**: Gestor de paquetes de JavaScript
4. **Git**: Control de versiones profesional

#### ✅ Tareas Prácticas

**Paso 1: Crear la estructura del monorepo**

```bash
# Qué hacer:
mkdir -p backend frontend
touch README.md

# Qué aprenderás:
# - Organización de proyectos
# - Separación de responsabilidades (backend/frontend)
```

**Paso 2: Inicializar Git**

```bash
# Qué hacer:
git init
git branch -m main

# Qué aprenderás:
# - Control de versiones
# - Buenas prácticas (usar 'main' en lugar de 'master')
```

**Paso 3: Crear .gitignore**

```bash
# Qué hacer:
# Crear archivo .gitignore con contenido para Python y Node.js

# Qué aprenderás:
# - Por qué NO versionar node_modules, .env, __pycache__
# - Seguridad (no subir credenciales)
```

---

### **FASE 1.5: Configuración Profesional con Docker y Variables de Entorno** ⏱️ 1 día

#### 🎯 Objetivos de Aprendizaje

- Entender la importancia de las variables de entorno (`.env`)
- Configurar servicios con Docker Compose
- Separar configuración de código (12-Factor App)

#### 📝 Conceptos que Aprenderás

**1.5.1 - El Archivo `.env` (Variables de Entorno)**

**¿Qué es?**
Es un archivo de texto plano donde guardamos "secretos" y configuraciones que cambian según el entorno (tu PC, el servidor de pruebas, producción).

**¿Por qué es vital?**
1.  **Seguridad**: Nunca debes subir contraseñas a GitHub. El archivo `.env` siempre se agrega al `.gitignore`.
2.  **Flexibilidad**: Puedes cambiar el usuario de la base de datos sin tocar el código Python.

**Tu archivo `.env` (ubicado en la raíz del proyecto):**
```env
# Credenciales de Base de Datos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=admin
POSTGRES_DB=sisalchi

# Conexión Backend -> BD
DATABASE_URL=postgresql://postgres:admin@db:5432/sisalchi
```

**1.5.2 - Docker Compose: Orquestación de Servicios**

En lugar de instalar PostgreSQL manualmente en tu Windows, usamos un contenedor.
El archivo `docker-compose.yml` es el plano de arquitectura.

-   **Servicios**: Las partes de tu app (db, backend, frontend).
-   **Volúmenes**: Discos duros virtuales para que los datos no se borren al apagar el contenedor.
-   **Redes**: Permiten que el `backend` hable con la `db` usando su nombre (`db`) en lugar de IPs complicadas.

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      # Docker lee estas variables automáticamente de tu archivo .env
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

---

### **FASE 1.5: Configuración Profesional con Docker y Variables de Entorno** ⏱️ 1 día

#### 🎯 Objetivos de Aprendizaje

- Entender la importancia de las variables de entorno (`.env`)
- Configurar servicios con Docker Compose
- Separar configuración de código (12-Factor App)

#### 📝 Conceptos que Aprenderás

**1.5.1 - El Archivo `.env` (Variables de Entorno)**

**¿Qué es?**
Es un archivo de texto plano donde guardamos "secretos" y configuraciones que cambian según el entorno (tu PC, el servidor de pruebas, producción).

**¿Por qué es vital?**
1.  **Seguridad**: Nunca debes subir contraseñas a GitHub. El archivo `.env` siempre se agrega al `.gitignore`.
2.  **Flexibilidad**: Puedes cambiar el usuario de la base de datos sin tocar el código Python.

**Tu archivo `.env` (ubicado en la raíz del proyecto):**
```env
# Credenciales de Base de Datos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=admin
POSTGRES_DB=sisalchi

# Conexión Backend -> BD
DATABASE_URL=postgresql://postgres:admin@db:5432/sisalchi
```

**1.5.2 - Docker Compose: Orquestación de Servicios**

En lugar de instalar PostgreSQL manualmente en tu Windows, usamos un contenedor.
El archivo `docker-compose.yml` es el plano de arquitectura.

-   **Servicios**: Las partes de tu app (db, backend, frontend).
-   **Volúmenes**: Discos duros virtuales para que los datos no se borren al apagar el contenedor.
-   **Redes**: Permiten que el `backend` hable con la `db` usando su nombre (`db`) en lugar de IPs complicadas.

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      # Docker lee estas variables automáticamente de tu archivo .env
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

---

### **FASE 1: Backend - Fundamentos con FastAPI** ⏱️ 3-5 días

#### 🎯 Objetivos de Aprendizaje

- Entender arquitectura REST API
- Aprender Python moderno con FastAPI
- Dominar bases de datos relacionales con PostgreSQL
- Implementar autenticación JWT

#### 📝 Conceptos que Aprenderás

**1.1 - Configuración del Entorno Python**

```bash
# Qué hacer:
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install fastapi uvicorn sqlmodel psycopg2-binary python-jose passlib

# Qué aprenderás:
# - Entornos virtuales (aislar dependencias)
# - Gestión de paquetes con pip
# - Por qué usar requirements.txt
```

**1.2 - Estructura del Proyecto Backend**

```
backend/
├── app/
│   ├── __init__.py          # Convierte carpeta en módulo Python
│   ├── main.py              # Punto de entrada de FastAPI
│   ├── config.py            # Configuración (variables de entorno)
│   ├── database.py          # Conexión a PostgreSQL
│   ├── models/              # Modelos de datos (SQLModel)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   └── order.py
│   ├── routers/             # Endpoints organizados
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── products.py
│   │   └── orders.py
│   └── utils/               # Funciones auxiliares
│       ├── __init__.py
│       ├── security.py      # JWT, hashing
│       └── dependencies.py  # Inyección de dependencias
├── requirements.txt
├── .env
└── Dockerfile

# Qué aprenderás:
# - Arquitectura en capas
# - Separación de responsabilidades
# - Modularización de código
```

**1.3 - Crear tu Primera API**

**Archivo: `backend/app/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="SISALCHI API")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a SISALCHI API"}

@app.get("/health")
def health_check():
    return {"status": "OK"}

# Qué aprenderás:
# - Decoradores en Python (@app.get)
# - Rutas HTTP (endpoints)
# - Respuestas JSON
```

**Ejecutar:**

```bash
uvicorn app.main:app --reload

# Qué aprenderás:
# - Servidor de desarrollo
# - Hot reload (recarga automática)
# - Visitar http://localhost:8000/docs (Swagger UI automático!)
```

**1.4 - Base de Datos con SQLModel**

**Concepto: ORM (Object-Relational Mapping)**

- En lugar de escribir SQL manualmente, usas clases Python
- SQLModel combina Pydantic (validación) + SQLAlchemy (ORM)

**Archivo: `backend/app/models/user.py`**

```python
from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    hashed_password: str
    role: str = Field(default="cajero")  # admin, cajero, cocina, domiciliario

    class Config:
        schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@sisalchi.com",
                "role": "admin"
            }
        }

# Qué aprenderás:
# - Modelos de datos
# - Validación automática
# - Índices de base de datos
# - Type hints en Python
```

**1.5 - Autenticación JWT**

**Concepto: JSON Web Tokens**

- Token seguro que contiene información del usuario
- No necesitas guardar sesiones en el servidor
- El cliente envía el token en cada petición

**Archivo: `backend/app/utils/security.py`**

```python
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Convierte contraseña en hash seguro"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña es correcta"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Crea un JWT con tiempo de expiración"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Qué aprenderás:
# - Seguridad de contraseñas (nunca guardar en texto plano)
# - Hashing con bcrypt
# - Tokens JWT
# - Expiración de sesiones
```

---

### **FASE 2: Frontend - React Moderno** ⏱️ 4-6 días

#### 🎯 Objetivos de Aprendizaje

- Dominar React con Hooks
- TypeScript para código más seguro
- Estado global con Redux Toolkit
- Diseño moderno con TailwindCSS

#### 📝 Conceptos que Aprenderás

**2.1 - Inicializar Proyecto con Vite**

```bash
# Qué hacer:
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install

# Qué aprenderás:
# - Vite (build tool moderno, más rápido que Webpack)
# - React 18 con TypeScript
# - Hot Module Replacement (HMR)
```

**2.2 - Componentes en React**

**Concepto: Componentes Funcionales**

- Todo en React es un componente
- Componentes = funciones que retornan JSX (HTML + JavaScript)

**Archivo: `frontend/src/components/Button.tsx`**

```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary";
}

export function Button({ label, onClick, variant = "primary" }: ButtonProps) {
  const baseClasses = "px-4 py-2 rounded-lg font-semibold";
  const variantClasses =
    variant === "primary"
      ? "bg-blue-600 text-white hover:bg-blue-700"
      : "bg-gray-200 text-gray-800 hover:bg-gray-300";

  return (
    <button className={`${baseClasses} ${variantClasses}`} onClick={onClick}>
      {label}
    </button>
  );
}

// Qué aprenderás:
// - Props (pasar datos entre componentes)
// - TypeScript interfaces
// - TailwindCSS clases utilitarias
// - Composición de componentes
```

**2.3 - Hooks de React**

**useState - Manejo de Estado Local**

```typescript
import { useState } from "react";

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Contador: {count}</p>
      <button onClick={() => setCount(count + 1)}>Incrementar</button>
    </div>
  );
}

// Qué aprenderás:
// - Estado local del componente
// - Re-renderizado cuando cambia el estado
// - Inmutabilidad
```

**useEffect - Efectos Secundarios**

```typescript
import { useEffect, useState } from "react";

function ProductList() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    // Se ejecuta al montar el componente
    fetch("http://localhost:8000/products")
      .then((res) => res.json())
      .then((data) => setProducts(data));
  }, []); // [] = solo se ejecuta una vez

  return (
    <ul>
      {products.map((product) => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}

// Qué aprenderás:
// - Ciclo de vida de componentes
// - Llamadas a API
// - Dependencias de useEffect
```

**2.4 - Redux Toolkit - Estado Global**

**Concepto: Por qué Redux?**

- Compartir estado entre componentes sin "prop drilling"
- Un solo lugar para toda la lógica de estado
- Debugging más fácil con Redux DevTools

**Archivo: `frontend/src/store/slices/authSlice.ts`**

```typescript
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface AuthState {
  user: { id: number; username: string; role: string } | null;
  token: string | null;
  isAuthenticated: boolean;
}

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    login: (state, action: PayloadAction<{ user: any; token: string }>) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.isAuthenticated = true;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
    },
  },
});

export const { login, logout } = authSlice.actions;
export default authSlice.reducer;

// Qué aprenderás:
// - Slices (pedazos de estado)
// - Actions (acciones que modifican el estado)
// - Reducers (funciones puras que actualizan estado)
// - Inmutabilidad con Immer (incluido en Redux Toolkit)
```

---

### **FASE 3: Integración Backend-Frontend** ⏱️ 2-3 días

#### 🎯 Objetivos de Aprendizaje

- Conectar frontend con backend
- Manejo de autenticación
- CORS y seguridad
- Axios para peticiones HTTP

#### 📝 Conceptos que Aprenderás

**3.1 - Configurar CORS en Backend**

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Qué aprenderás:
# - CORS (Cross-Origin Resource Sharing)
# - Por qué el navegador bloquea peticiones
# - Seguridad web
```

**3.2 - Servicio de API en Frontend**

```typescript
// frontend/src/services/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

// Interceptor para agregar token a todas las peticiones
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (username: string, password: string) =>
    api.post("/auth/token", { username, password }),

  getMe: () => api.get("/auth/me"),
};

export const productsAPI = {
  getAll: () => api.get("/products"),
  create: (data: any) => api.post("/products", data),
};

// Qué aprenderás:
// - Axios interceptors
// - LocalStorage para persistencia
// - Headers HTTP
// - Organización de servicios
```

---

### **FASE 4: Características Avanzadas** ⏱️ 5-7 días

#### 🎯 Objetivos de Aprendizaje

- WebSockets para tiempo real
- Transacciones de base de datos
- Testing
- Docker Compose

#### 📝 Conceptos que Aprenderás

**4.1 - WebSockets con Socket.IO**

```python
# backend/app/websockets.py
import socketio

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

@sio.on('connect')
async def connect(sid, environ):
    print(f'Cliente conectado: {sid}')

@sio.on('new_order')
async def handle_new_order(sid, data):
    # Emitir a todos los clientes en el canal de cocina
    await sio.emit('order_created', data, room='kitchen')

# Qué aprenderás:
# - Comunicación bidireccional en tiempo real
# - Rooms y namespaces
# - Eventos personalizados
```

**4.2 - Transacciones en Base de Datos**

```python
from sqlmodel import Session, select

async def create_order_with_inventory_deduction(order_data, session: Session):
    try:
        # Iniciar transacción
        # 1. Crear pedido
        order = Order(**order_data)
        session.add(order)

        # 2. Descontar inventario
        for item in order.items:
            product = session.get(Product, item.product_id)
            if product.stock < item.quantity:
                raise ValueError(f"Stock insuficiente para {product.name}")
            product.stock -= item.quantity

        # 3. Confirmar todo o nada
        session.commit()
        return order
    except Exception as e:
        session.rollback()
        raise e

# Qué aprenderás:
# - ACID (Atomicidad, Consistencia, Aislamiento, Durabilidad)
# - Rollback en caso de error
# - Integridad de datos
```

---

## 🛠️ Herramientas que Necesitas Instalar

### Esenciales

1. **Python 3.10+**: https://www.python.org/downloads/
2. **Node.js 20+**: https://nodejs.org/
3. **PostgreSQL**: https://www.postgresql.org/download/
4. **Git**: https://git-scm.com/downloads
5. **Docker** (opcional): https://www.docker.com/get-started

### Editores Recomendados

- **VS Code**: https://code.visualstudio.com/
  - Extensiones: Python, ESLint, Prettier, Tailwind CSS IntelliSense

---

## 📖 Recursos de Aprendizaje

### Documentación Oficial

- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Redux Toolkit: https://redux-toolkit.js.org/
- TailwindCSS: https://tailwindcss.com/docs

### Tutoriales Recomendados

- FastAPI Tutorial: https://fastapi.tiangolo.com/tutorial/
- React Beta Docs: https://react.dev/learn
- TypeScript Handbook: https://www.typescriptlang.org/docs/

---

## ✅ Checklist de Progreso

### Fase 0: Preparación

- [ ] Estructura de carpetas creada
- [ ] Git inicializado
- [ ] README.md creado
- [ ] .gitignore configurado

### Fase 1: Backend Básico

- [ ] Entorno virtual Python creado
- [ ] FastAPI instalado y corriendo
- [ ] Primera ruta GET funcionando
- [ ] PostgreSQL instalado y configurado
- [ ] Primer modelo SQLModel creado
- [ ] Autenticación JWT implementada

### Fase 2: Frontend Básico

- [ ] Vite + React + TypeScript inicializado
- [ ] TailwindCSS configurado
- [ ] Primer componente creado
- [ ] Redux Toolkit configurado
- [ ] Primer slice creado

### Fase 3: Integración

- [ ] CORS configurado
- [ ] Login funcionando
- [ ] Peticiones autenticadas funcionando
- [ ] Manejo de errores implementado

### Fase 4: Avanzado

- [ ] WebSockets funcionando
- [ ] Transacciones de DB implementadas
- [ ] Tests básicos escritos
- [ ] Docker Compose configurado

---

## 🎯 Próximo Paso

**¡Empecemos con la Fase 0!**

¿Estás listo para comenzar? Dime y te guiaré paso a paso en cada comando y concepto.
