# Guía de Configuración y Ejecución del Proyecto

Esta guía detalla los pasos para levantar el proyecto, poblar la base de datos y administrarlos utilizando el script unificado `manage.py`.

## 📋 Prerrequisitos

*   **Docker Desktop** instalado y corriendo.
*   **Python 3.9+** instalado (para ejecutar el script de gestión).

## ⚙️ Configuración Inicial

### 1. Variables de Entorno (`.env`)
Asegúrate de tener el archivo `.env` en la raíz con las credenciales necesarias (ver ejemplo en repositorio).

## 🚀 Inicio Rápido (Recomendado)

El proyecto utiliza un script maestro `manage.py` en la raíz para todas las tareas.

### Levantar todo desde cero (Setup Completo)
Construye contenedores, levanta servicios, espera a la BD, migra y puebla datos:

```bash
python manage.py setup
```

### Comandos Comunes

```bash
# Iniciar servicios
python manage.py start

# Detener servicios
python manage.py stop

# Ver logs
python manage.py logs

# Resetear base de datos (Destructivo: borra y recrea todo)
python manage.py db reset

# Poblar datos (Seed)
python manage.py db seed
```

## 🧪 Testing

Para ejecutar las pruebas del sistema:

```bash
# Correr todos los tests
python manage.py test

# Correr solo unitarios
python manage.py test --unit

# Correr con coverage
python manage.py test --coverage
```

## 🐳 Estructura del Proyecto

*   `manage.py`: Script maestro de orquestación.
*   `backend/`: Código fuente de la API (FastAPI).
    *   `backend/scripts/`: Scripts internos (admin, seed) ejecutados por manage.py.
    *   `backend/tests/`: Suite de pruebas.
*   `docker-compose.yml`: Definición de servicios.

## 🔍 Verificación

1.  **Documentación API (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
2.  **pgAdmin (Gestión BD)**: [http://localhost:5050](http://localhost:5050)
