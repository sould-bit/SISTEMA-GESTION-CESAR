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

_Este documento se actualizará a medida que avancemos._
