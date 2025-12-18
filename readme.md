# 🍔 SISALCHI - Sistema Integral de Pedidos

Sistema de gestión para salchipaperías que incluye:

- 📝 Gestión de pedidos (Mesa, Para llevar, Domicilio)
- 👨‍🍳 Comandas para cocina
- 🏍️ Control de domiciliarios
- 💰 Caja y cierres
- 📦 Inventario con recetas
- 📊 Reportes

## 🏗️ Arquitectura

### Backend

- **Stack**: FastAPI + SQLModel + PostgreSQL
- **Puerto**: 8000

### Frontend

- **Stack**: React + TypeScript + TailwindCSS + Redux Toolkit
- **Puerto**: 5173

## 📁 Estructura del Proyecto

## 🚀 Estado del Proyecto

- ✅ Fase 0: Estructura básica
- ⏳ Fase 1: Backend (próximo)
- ⏳ Fase 2: Frontend
- ⏳ Fase 3: Integración

## 🚀 Inicio Rápido

### 1. Clonar y configurar entorno
```bash
git clone <url-del-repo>
cd SISTEMA-GESTION-CESAR

# Crear entorno virtual
python -m venv el_rincon_env
el_rincon_env\Scripts\activate  # Windows
# source el_rincon_env/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r backend/requirements.txt
```

### 2. Configurar variables de entorno
```bash
# Copiar archivo de ejemplo
cp backend/.env.example backend/.env

# Editar con tus credenciales
# DATABASE_URL=postgresql://usuario:password@localhost:5432/dbname
# SECRET_KEY=tu-clave-secreta
```

### 3. Iniciar servicios con Docker
```bash
# Construir e iniciar contenedores
docker-compose up -d

# Verificar que estén corriendo
docker ps
```

### 4. Ejecutar migraciones de base de datos
```bash
# Opción 1: Usar script helper (recomendado)
./backend/scripts/run_migrations.sh current
./backend/scripts/run_migrations.sh upgrade

# Opción 2: Ejecutar directamente en Docker
docker exec -it backend_FastOps python -m alembic current
docker exec -it backend_FastOps python -m alembic upgrade head
```

### 5. Cargar datos de prueba
```bash
# Ejecutar script de seed
docker exec -it backend_FastOps python seed_data_script.py
```

### 6. Acceder a la aplicación
- **API Backend:** http://localhost:8000
- **Documentación API:** http://localhost:8000/docs
- **Base de datos:** localhost:5432 (desde fuera de Docker)

## 🛠️ Comandos Útiles

### Gestión de Base de Datos
```bash
# Ver estado de migraciones
./backend/scripts/run_migrations.sh current

# Aplicar todas las migraciones
./backend/scripts/run_migrations.sh upgrade

# Crear nueva migración
./backend/scripts/run_migrations.sh revision --autogenerate -m "Descripción"

# Rollback una migración
./backend/scripts/run_migrations.sh downgrade -1
```

### Gestión de Contenedores
```bash
# Ver logs
docker logs backend_FastOps
docker logs container_DB_FastOps

# Reiniciar servicios
docker-compose restart

# Reconstruir contenedores
docker-compose build --no-cache

# Limpiar todo
docker-compose down -v
docker system prune -a
```

## 📁 Estructura del Proyecto

```
SISTEMA-GESTION-CESAR/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── config.py          # Configuración centralizada
│   │   ├── database.py        # Conexión a BD
│   │   ├── main.py           # Punto de entrada
│   │   ├── models/           # Modelos SQLModel
│   │   ├── routers/          # Endpoints API
│   │   └── utils/            # Utilidades
│   ├── migrations/           # Migraciones Alembic
│   ├── scripts/              # Scripts helper
│   ├── requirements.txt      # Dependencias Python
│   └── Dockerfile           # Configuración Docker
├── frontend/                  # PWA React (futuro)
├── docker-compose.yml        # Orquestación de servicios
├── .env                      # Variables de entorno
└── .gitignore               # Archivos ignorados por Git
```

## 📚 Documentación
