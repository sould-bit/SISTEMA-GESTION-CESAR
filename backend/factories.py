# backend/factories.py
import factory
from factory import Faker, SubFactory, LazyAttribute
from datetime import datetime, timedelta
from passlib.context import CryptContext
# Importamos desde la ubicación correcta dentro del proyecto
from app.database import engine
from app.models import Company, Branch, Subscription, User
from sqlmodel import Session


# Para hashear contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class BaseFactory(factory.Factory):
    """
    Clase base. NO usa SQLAlchemy directamente.
    Esto nos da más control sobre cuándo guardar en la DB.
    """
    class Meta:
        abstract = True  # No se puede instanciar directamente



# 1. COMPANY FACTORY (El Tenant - debe crearse PRIMERO)
# =============================================================================

class CompanyFactory(BaseFactory):
    """Genera compañías/negocios de prueba."""
    
    class Meta:
        model = Company
    
    # Faker genera datos aleatorios realistas
    name = Faker('company', locale='es_CO')  # Nombres de empresas colombianas
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-').replace('.', '')[:50])
    legal_name = Faker('company', locale='es_CO')
    tax_id = Faker('numerify', text='###.###.###-#')  # Formato NIT colombiano
    
    owner_name = Faker('name', locale='es_CO')
    owner_email = Faker('email')
    owner_phone = Faker('phone_number', locale='es_CO')
    
    plan = factory.Iterator(['free', 'basic', 'premium'])
    is_active = True
    
    created_at = factory.LazyFunction(datetime.utcnow)


# 2. BRANCH FACTORY (Depende de Company)
# =============================================================================
class BranchFactory(BaseFactory):
    """Genera sucursales de prueba."""
    
    class Meta:
        model = Branch
    
    # SubFactory: Crea automáticamente una Company si no se proporciona
    company = SubFactory(CompanyFactory)
    company_id = LazyAttribute(lambda obj: obj.company.id if obj.company else None)
    
    name = Faker('street_name', locale='es_CO')
    code = factory.Sequence(lambda n: f'SUC{n:03d}')  # SUC001, SUC002, etc.
    address = Faker('address', locale='es_CO')
    phone = Faker('phone_number', locale='es_CO')
    
    is_active = True
    is_main = False
    
    created_at = factory.LazyFunction(datetime.utcnow)
    
# 3. SUBSCRIPTION FACTORY (Depende de Company)
# =============================================================================
class SubscriptionFactory(BaseFactory):
    """Genera suscripciones de prueba."""
    
    class Meta:
        model = Subscription
    
    company = SubFactory(CompanyFactory)
    company_id = LazyAttribute(lambda obj: obj.company.id if obj.company else None)
    
    plan = factory.Iterator(['free', 'basic', 'premium'])
    status = 'active'
    
    started_at = factory.LazyFunction(datetime.utcnow)
    current_period_start = factory.LazyFunction(datetime.utcnow)
    current_period_end = factory.LazyFunction(lambda: datetime.utcnow() + timedelta(days=30))
    
    amount = factory.LazyAttribute(lambda obj: {'free': 0, 'basic': 50000, 'premium': 100000}.get(obj.plan, 0))
    currency = 'COP'
    
    created_at = factory.LazyFunction(datetime.utcnow)

# 4. USER FACTORY (Depende de Company y opcionalmente de Branch)
# =============================================================================
class UserFactory(BaseFactory):
    """Genera usuarios de prueba."""
    
    class Meta:
        model = User
    
    company = SubFactory(CompanyFactory)
    company_id = LazyAttribute(lambda obj: obj.company.id if obj.company else None)
    
    branch = None  # Opcional
    branch_id = LazyAttribute(lambda obj: obj.branch.id if obj.branch else None)
    
    username = Faker('user_name')
    email = Faker('email')
    hashed_password = factory.LazyFunction(lambda: pwd_context.hash('test123'))
    full_name = Faker('name', locale='es_CO')
    
    role = factory.Iterator(['admin', 'cajero', 'cocinero', 'mesero'])
    is_active = True
    
    created_at = factory.LazyFunction(datetime.utcnow)

# HELPER: Función para crear y guardar en la base de datos
# =============================================================================
def create_and_save(factory_class, session: Session, **kwargs):
    """
    Crea un objeto usando la factory y lo guarda en la base de datos.
    
    Uso:
        with Session(engine) as session:
            company = create_and_save(CompanyFactory, session, name="Mi Empresa")
    """
    obj = factory_class.build(**kwargs)  # .build() NO guarda en DB
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj
