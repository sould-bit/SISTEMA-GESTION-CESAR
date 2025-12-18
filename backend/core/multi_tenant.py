"""
🛡️ MIDDLEWARE MULTI-TENANT - AISLAMIENTO AUTOMÁTICO

Este módulo garantiza que:
1. Cada usuario solo vea datos de SU empresa
2. Los permisos se verifiquen automáticamente  
3. Las suscripciones estén activas
4. Los límites del plan se respeten

Conceptos clave:
- Dependency Injection: Inyección automática de validaciones
- HTTP Exceptions: Errores específicos para diferentes casos
- Async validation: Validaciones asíncronas eficientes
"""


from datetime import datetime
from select import select
from fastapi import HTTPException, status, Depends

from app.routers.auth import get_current_user
from app.models import User, Company, Branch, Subscription

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session


COMPANY_ACCESS_DENIED = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Acceso denegado a esta empresa"
)

BRANCH_ACCESS_DENIED = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, 
    detail="Acceso denegado a esta sucursal"
)

SUBSCRIPTION_EXPIRED = HTTPException(
    status_code=status.HTTP_402_PAYMENT_REQUIRED,
    detail="Suscripción expirada. Por favor renueva tu plan."
)

PLAN_LIMIT_EXCEEDED = HTTPException(
    status_code=status.HTTP_402_PAYMENT_REQUIRED,
    detail="Límite del plan excedido. Actualiza tu suscripción."
)

# ============================================
# DEPENDENCIA: VERIFICAR ACCESO A EMPRESA
# ============================================

async def verify_company_acces(
    company_id :int, 
    current_user: User = Depends(get_current_user)
)-> bool:
    """
    🏢 VERIFICACIÓN DE ACCESO A EMPRESA
    
    Esta función DEPENDENCIA asegura que el usuario autenticado
    tenga acceso a la empresa solicitada.
    
    EJEMPLOS DE USO:
    
    1. Endpoint que recibe company_id en URL:
   
    @router.get("/companies/{company_id}/users")
    async def get_company_users(
        company_id: int,
        verified: bool = Depends(verify_company_access),  # <-- DEPENDENCIA
        session: AsyncSession = Depends(get_session)
    ):
        # Solo se ejecuta si el usuario pertenece a esa empresa
        pass
        
    2. Endpoint que recibe company_id en body:
   
    @router.post("/products")
    async def create_product(
        product: ProductCreate,
        current_user: User = Depends(get_current_user),
        verified: bool = Depends(verify_company_access(product.company_id)),  # <-- CON PARÁMETRO
        session: AsyncSession = Depends(get_session)
    ):
        pass
        
    Args:
        company_id: ID de la empresa a verificar
        current_user: Usuario inyectado por get_current_user()
    
    Returns:
        bool: True si tiene acceso
    
    Raises:
        HTTPException 403: Si no tiene acceso a la empresa
    """
    if current_user.company_id != company_id:
        raise COMPANY_ACCESS_DENIED
    
    return True

# ============================================
# DEPENDENCIA: VERIFICAR ACCESO A SUCURSAL
# ============================================

async def verify_branch_access(
    branch_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
)-> bool:
    """
    🏪 VERIFICACIÓN DE ACCESO A SUCURSAL
    
    Esta función valida acceso a sucursales específicas.
    Las reglas de negocio son:
    
    - ADMIN: Puede acceder a TODAS las sucursales de su empresa
    - OTROS ROLES: Solo pueden acceder a su sucursal asignada
    
    EJEMPLO DE USO:
   
    @router.get("/branches/{branch_id}/orders")
    async def get_branch_orders(
        branch_id: int,
        verified: bool = Depends(verify_branch_access),  # <-- DEPENDENCIA
        session: AsyncSession = Depends(get_session)
    ):
        # Solo se ejecuta si el usuario tiene acceso a esa sucursal
        pass
        
    Args:
        branch_id: ID de la sucursal a verificar
        current_user: Usuario autenticado
        session: Sesión de BD
    
    Returns:
        bool: True si tiene acceso
    
    Raises:
        HTTPException 403: Si no tiene acceso a la sucursal
    """

# 1. Validar que la sucursal pertenece a la empresa del usuario
    branch_result = await session.execute(
        select(Branch).where(
            Branch.id == branch_id,
            Branch.company == current_user.company_id
        )
     )

    branch =  branch_result.scalar_one_or_none()


    if not branch:
     raise BRANCH_ACCESS_DENIED

    
# 2. Para admins: acceso total a todas las sucursales
    if current_user.role =="admin":
        return True

# 3. Para otros roles: solo su sucursal asignada
    if current_user.branch_id != branch_id:
        raise BRANCH_ACCESS_DENIED
    
    return True



# ============================================
# DEPENDENCIA: VERIFICAR SUSCRIPCIÓN ACTIVA
# ============================================
async def verify_active_subscription(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> Company:
    """
    💳 VERIFICACIÓN DE SUSCRIPCIÓN ACTIVA
    
    Esta dependencia valida que la empresa del usuario tenga
    una suscripción activa y no expirada.
    
    EJEMPLO DE USO:
   
    @router.post("/orders")
    async def create_order(
        order: OrderCreate,
        company: Company = Depends(verify_active_subscription),  # <-- DEPENDENCIA
        session: AsyncSession = Depends(get_session)
    ):
        # Solo se ejecuta si la suscripción está activa
        pass
        
    Args:
        current_user: Usuario autenticado
        session: Sesión de BD
    
    Returns:
        Company: La empresa con suscripción válida
    
    Raises:
        HTTPException 402: Si la suscripción está expirada
    """
    # Buscar suscripción activa de la empresa
    subscription_result = await session.execute(
        select(Subscription).where(
            Subscription.company_id == current_user.company_id,
            Subscription.status == "active",
            Subscription.current_period_end > datetime.utcnow()
        )
    )
    subscription = subscription_result.scalar_one_or_none()
    
    if not subscription:
        raise SUBSCRIPTION_EXPIRED

    # Devolver la empresa para uso posterior
    company_result = await session.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = company_result.scalar_one_or_none()
    
    return company


# ============================================
# DEPENDENCIA: VERIFICAR LÍMITES DEL PLAN
# ============================================
async def verify_plan_limits(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> Company:
    """
    📊 VERIFICACIÓN DE LÍMITES DEL PLAN
    
    Esta dependencia valida que la empresa no haya excedido
    los límites de su plan actual (usuarios, productos, etc.)
    
    EJEMPLO DE USO:
   
    @router.post("/users")
    async def create_user(
        user: UserCreate,
        company: Company = Depends(verify_plan_limits),  # <-- DEPENDENCIA
        session: AsyncSession = Depends(get_session)
    ):
        # Solo se ejecuta si no se excede el límite de usuarios
        pass
        
    NOTA: Esta función necesita ser adaptada según qué acción
    se va a validar (crear usuario, producto, etc.)
    
    Args:
        current_user: Usuario autenticado
        session: Sesión de BD
    
    Returns:
        Company: Empresa con límites válidos
    
    Raises:
        HTTPException 402: Si se excede algún límite
    """
    company_result = await session.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = company_result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Aquí implementarías las validaciones específicas
    # según qué límite quieres verificar
    
    # EJEMPLO: Verificar límite de usuarios
    # users_count = await session.execute(
    #     select(func.count(User.id)).where(User.company_id == company.id)
    # )
    # if users_count.scalar() >= company.max_users:
    #     raise PLAN_LIMIT_EXCEEDED
    
    return company