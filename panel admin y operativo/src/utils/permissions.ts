/**
 * Mapeo centralizado de códigos técnicos de permisos a sus nombres amigables 
 * tal como aparecen en la base de datos y en la interfaz de administración de roles.
 * 
 * Basado en la base de datos de producción (FastOps).
 */
export const PERMISSION_LABELS: Record<string, string> = {
    // Sucursales (Branches)
    'branches.read': 'Ver sucursales',
    'branches.create': 'Crear sucursales',
    'branches.update': 'Editar sucursales',
    'branches.delete': 'Eliminar sucursales',
    'branches read': 'Ver sucursales', // Fallback por si llega sin punto
    'branches': 'Gestión de sucursales',

    // Pedidos / Ventas (Orders)
    'orders.read': 'Ver pedidos',
    'orders.create': 'Crear pedidos',
    'orders.update': 'Actualizar pedidos',
    'orders.cancel': 'Cancelar pedidos',

    // Productos (Products)
    'products.read': 'Ver productos',
    'products.create': 'Crear productos',
    'products.update': 'Editar productos',
    'products.delete': 'Eliminar productos',

    // Categorías (Categories)
    'categories.read': 'Ver categorías',
    'categories.create': 'Crear categorías',
    'categories.update': 'Editar categorías',
    'categories.delete': 'Eliminar categorías',

    // Operaciones de Caja (Cash)
    'cash.open': 'Abrir caja',
    'cash.close': 'Cerrar caja',
    'cash.read': 'Ver movimientos de caja',

    // Usuarios / Personal (Users/Staff)
    'users.read': 'Ver usuarios',
    'users.create': 'Crear usuarios',
    'users.update': 'Editar usuarios',
    'users.delete': 'Eliminar usuarios',
    'users read': 'Ver usuarios',
    'staff': 'Gestión de personal',

    // Roles y Permisos (Roles/Permissions)
    'roles.read': 'Ver roles',
    'roles.create': 'Crear roles',
    'roles.update': 'Editar roles',
    'roles.delete': 'Eliminar roles',
    'permissions.read': 'Ver permisos',
    'permissions.update': 'Asignar permisos',

    // Inventario (Inventory)
    'inventory.read': 'Ver inventario',
    'inventory.adjust': 'Ajustar inventario',

    // Reportes (Reports)
    'reports.sales': 'Ver reportes de ventas',
    'reports.financial': 'Ver reportes financieros',

    // Configuración (Settings)
    'settings.read': 'Ver configuración',
    'settings.update': 'Modificar configuración',
};

/**
 * Retorna el nombre amigable del permiso o el código original si no se encuentra mapeo.
 */
export const getPermissionLabel = (code: string | undefined): string => {
    if (!code) return 'Permiso requerido';

    // Limpieza profunda: quitar espacios, convertir a minúsculas y normalizar puntos
    const cleanCode = code.trim().toLowerCase();

    // Intentar lookup directo
    if (PERMISSION_LABELS[cleanCode]) return PERMISSION_LABELS[cleanCode];

    // Intentar lookup reemplazando espacios por puntos si el usuario lo transcribió así
    const dottedCode = cleanCode.replace(/\s+/g, '.');
    if (PERMISSION_LABELS[dottedCode]) return PERMISSION_LABELS[dottedCode];

    return code; // Fallback al código original si nada funciona
};
