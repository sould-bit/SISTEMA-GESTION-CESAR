📘 FastOps - Arquitectura de Frontend (Panel Administrativo y Operativo)Versión: 1.0 - InicialFecha: Enero 2026Módulo: Cliente Web "Manager" (Admin, Caja, Cocina)Arquitecto: Robert1. Visión Técnica y Stack TecnológicoEl frontend debe soportar operaciones críticas en tiempo real (Caja y Cocina) y gestión administrativa compleja (Admin). No podemos permitirnos recargas de página innecesarias ni lentitud.1.1 Stack Principal (La "Santa Trinidad" del Frontend Moderno)TecnologíaElecciónJustificaciónFramework BaseReact 18 + TypeScriptEstándar de la industria, tipado estático para evitar errores en props y modelos de datos.Build ToolViteVelocidad de compilación instantánea (esencial para DX).Estilos / UITailwind CSS + Shadcn/UIComponentes accesibles, ligeros y altamente personalizables. Evitamos el peso de Material UI.Estado Global (UI)Zustand o Redux ToolkitRedux Toolkit es preferible si el equipo ya lo conoce; Zustand es más ligero. Recomendación: Redux Toolkit para escalabilidad empresarial.Estado ServidorTanStack Query (React Query)CRÍTICO. Maneja caché, re-intentos, y estados de carga automáticamente. Elimina el 80% del código de useEffect.RoutingReact Router v6Manejo de rutas protegidas y layouts anidados.FormulariosReact Hook Form + ZodValidación de esquemas TypeScript (sincronizados con los schemas del backend).Tiempo RealSocket.io-clientPara escuchar eventos de cocina y caja sin polling.2. Arquitectura de Carpetas (Feature-Based)Evitaremos organizar por "tipo" (no queremos una carpeta con 50 componentes mezclados). Usaremos una arquitectura basada en Módulos (Features). Esto permite que el proyecto escale a cientos de archivos sin volverse un caos.Plaintextsrc/
├── assets/                  # Imágenes, fuentes, svgs
├── components/              # Componentes "tontos" (UI pura) compartidos
│   ├── ui/                  # Componentes base (Botones, Inputs - Shadcn)
│   ├── layout/              # Sidebar, Header, AuthLayout
│   └── common/              # Loaders, Modales genéricos
├── config/                  # Variables de entorno, constantes globales
├── hooks/                   # Custom hooks globales (useAuth, useSocket)
├── lib/                     # Utilidades (axios client, cn, formatters)
├── stores/                  # Estado global (AuthStore, UIStore)
├── types/                   # Interfaces TS globales (User, Company, etc.)
├── features/                # 🧠 EL NÚCLEO DEL NEGOCIO
│   ├── auth/                # Login, Recuperar pass, Selección de Tenant
│   ├── admin/               # Panel Administrativo
│   │   ├── products/        # CRUD Productos (Componentes + Hooks + API)
│   │   ├── users/           # Gestión Usuarios
│   │   └── reports/         # Gráficos y reportes
│   ├── pos/                 # ⚡ CAJA (Punto de venta)
│   │   ├── components/      # Grid productos, Carrito, Modal Pago
│   │   └── hooks/           # Lógica de cálculo de totales
│   ├── kitchen/             # 🍳 KDS (Pantalla Cocina)
│   └── dispatcher/          # 🛵 Gestión Domicilios
├── routes/                  # Definición de rutas y Guards (Protección)
└── main.tsx                 # Punto de entrada
3. Estrategia de Conexión con Backend (Multi-Tenant)Dado que el backend es Multi-Tenant, el frontend debe ser inteligente al manejar las peticiones.3.1 El Cliente HTTP (Axios Interceptor)No haremos fetch directo. Crearemos una instancia de Axios centralizada en src/lib/api.ts.Requisito: Cada petición debe inyectar automáticamente:El Token JWT (Authorization: Bearer ...).(Opcional según diseño backend) El X-Tenant-ID si el usuario gestiona múltiples empresas, aunque usualmente el token ya lleva esta info.TypeScript// Ejemplo conceptual
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
3.2 Manejo de Errores GlobalSi el backend responde 401 Unauthorized (token expirado), el frontend debe automáticamente redirigir al Login sin que el componente tenga que manejarlo.4. Diseño de Módulos Clave4.1 Módulo 1: Autenticación y LayoutLogin: Debe ser limpio.Persistencia: Guardar token en localStorage o cookies seguras.Layout Shell: Sidebar colapsable a la izquierda, Header con perfil usuario y selector de sucursal (si aplica).4.2 Módulo 2: Panel Administrativo (CRUDs)Patrón de Diseño: Tablas de datos potentes (filtrado, paginación server-side).Herramienta: TanStack Table (Headless UI) para las tablas de inventario y productos.UX: Formularios en Modales (Slide-over) o páginas dedicadas para creación de productos complejos (recetas).4.3 Módulo 3: El POS (Caja) - Alta Prioridad ⚡Este es el módulo más crítico. Debe funcionar rápido.Diseño:Izquierda: Grid de categorías y productos (Buscador rápido).Derecha: Ticket virtual (Carrito), selector de cliente, botón de pago.Lógica Local: El cálculo de subtotales, impuestos y descuentos se hace en el frontend (estado local) para velocidad, y se valida en backend al enviar.Accesibilidad: Soporte para teclado (ej. F5 para cobrar).4.4 Módulo 4: Operativo (Cocina/KDS) - Tiempo RealTecnología: WebSockets.Comportamiento:Al cargar: GET /orders/active.Al recibir evento ws:new_order: Agregar tarjeta al tablero (Kanban o Grid) con sonido de alerta.Al cambiar estado: Optimistic UI (cambia color inmediatamente mientras avisa al backend).5. Plan de Desarrollo Frontend (Fases)Para mantener la alineación con el Backend, desarrollaremos en este orden:FASE 1: Andamiaje y Seguridad (Semanas 1-2)[ ] Configuración inicial Vite + Tailwind + Shadcn.[ ] Configuración de Axios e Interceptors.[ ] Implementación de useAuth (Login, Logout, Refresh Token).[ ] Estructura de Rutas Protegidas (PrivateRoutes).[ ] Layout Principal (Sidebar + Header).FASE 2: Gestión de Datos Maestros (Semanas 2-3)[ ] Usuarios y Roles: Tabla de usuarios, asignación de permisos.[ ] Catálogo: CRUD de Categorías y Productos.Reto: Formulario de Recetas (Ingredientes dinámicos).[ ] Configuración: Datos de la empresa (Logo, impuestos).FASE 3: El POS (Caja) (Semanas 4-5)[ ] Diseño visual del POS (Grid vs Lista).[ ] Lógica del Carrito (Redux/Zustand slice específico).[ ] Integración de búsqueda de clientes.[ ] Flujo de cierre de venta (Selección método de pago).[ ] Impresión: Integración con servicio de impresión local (o llamada al backend para que imprima).FASE 4: Operaciones en Tiempo Real (Semanas 6-7)[ ] KDS (Cocina): Tablero de comandas.[ ] Conexión WebSocket: Hook useSocket para escuchar eventos.[ ] Dispatcher: Vista para asignar motorizados.6. Consideraciones de "Arquitecto" (Riesgos y Soluciones)Bloqueo de UI:Riesgo: Traer 5000 productos bloquea el navegador.Solución: Implementar Virtualización en las listas (usar react-window) y paginación en el backend.Estado Desincronizado:Riesgo: Caja dice que hay stock, Backend dice que no.Solución: Usar React Query para invalidar caché de inventario cada vez que se hace una venta.Manejo de Internet Intermitente (Caja):Riesgo: Se va internet a mitad de un pedido.Solución: Redux Persist para guardar el carrito actual en local. Si falla la petición, guardar en cola de "pendientes por sincronizar" (Estrategia Offline First básica).7. Entregables Esperados del FrontendRepositorio Git (fastops-frontend-manager).Storybook (Opcional, pero recomendado): Catálogo de componentes UI.Variables de entorno .env.production y .env.development.Build optimizado en Docker (Nginx sirviendo los estáticos).



. Desglose Atómico (Atomic Design)
Para que el equipo de desarrollo no cree un "código espagueti", debemos romper tus bocetos en componentes reutilizables.

Supongamos que tu boceto de Caja (POS) tiene estas zonas. Así es como se deben llamar los componentes en el código:

Zona Visual (Boceto)	Nombre del Componente (React)	Responsabilidad Técnica
Contenedor Principal	POSLayout.tsx	Maneja el grid principal (sidebar vs contenido), no tiene lógica de negocio.
Grid de Productos	ProductGrid.tsx	Recibe la lista de productos y renderiza las tarjetas. Implementa virtualización si son muchos ítems.
Tarjeta de Producto	ProductCard.tsx	Muestra foto, precio y nombre. Maneja el evento onClick -> addToCart().
Ticket / Carrito	CurrentOrderTicket.tsx	Muestra la lista de ítems seleccionados, cantidades y subtotales.
Fila del Ticket	TicketItemRow.tsx	Input para cambiar cantidad (+/-), botón de eliminar, notas (ej. "sin cebolla").
Barra de Totales	OrderSummaryFooter.tsx	Calcula impuestos, descuentos y Total Final. Botón "COBRAR".
Buscador	QuickSearchInput.tsx	Búsqueda global con debounce (espera a que dejes de escribir para buscar).
Arquitectura del Estado Global (El "Cerebro" del Frontend)
Como decidimos usar Redux Toolkit (para escalabilidad empresarial), no podemos dejar que cada componente haga lo que quiera. Definiremos los "Slices" (pedazos de memoria) necesarios.