from sqlmodel import Session, SQLModel
from app.database import engine
from app.models import User, Company, Branch, Subscription
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_db():
    print("🗑️  Borrando tablas antiguas...")
    SQLModel.metadata.drop_all(engine)
    
    print("🏗️  Creando nuevas tablas Multi-Tenant...")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # 1. Crear Compañía A (El Rincón)
        company_a = Company(
            name="Salchipapas El Rincón",
            slug="el-rincon",
            plan="premium"
        )
        session.add(company_a)
        session.commit()
        session.refresh(company_a) # Obtener ID asignado
        
        # Suscripción Comp A
        sub_a = Subscription(company_id=company_a.id, plan="premium")
        session.add(sub_a)
        
        # Sucursales Comp A
        branch_a1 = Branch(company_id=company_a.id, name="Sede Norte", code="NORTE", is_main=True)
        branch_a2 = Branch(company_id=company_a.id, name="Sede Centro", code="CENTRO")
        session.add(branch_a1)
        session.add(branch_a2)
        session.commit()
        session.refresh(branch_a1)
        
        # Usuario Admin Comp A
        admin_a = User(
            company_id=company_a.id,
            branch_id=branch_a1.id, # Asignado a sede norte
            username="admin", # Login: admin (en esta company)
            email="admin@elrincon.com",
            hashed_password=pwd_context.hash("admin123"),
            role="admin",
            full_name="Dueño El Rincón"
        )
        session.add(admin_a)
        
        # -----------------------------------------------------
        
        # 2. Crear Compañía B (La Competencia)
        company_b = Company(
            name="Hamburguesas del Valle",
            slug="del-valle",
            plan="basic"
        )
        session.add(company_b)
        session.commit()
        session.refresh(company_b)
        
        # Sucursal Comp B
        branch_b1 = Branch(company_id=company_b.id, name="Única Sede", code="MAIN", is_main=True)
        session.add(branch_b1)
        session.commit()
        session.refresh(branch_b1)
        
        # Usuario Admin Comp B
        admin_b = User(
            company_id=company_b.id,
            branch_id=branch_b1.id,
            username="admin", # ¡Mismo username "admin"! Esto prueba que la constraint funciona
            email="admin@delvalle.com",
            hashed_password=pwd_context.hash("admin123"),
            role="admin",
            full_name="Dueño Del Valle"
        )
        session.add(admin_b)
        
        session.commit()
        print("✅ Seed completado exitosamente!")
        print(f"   -> Creada Company: {company_a.name} (ID: {company_a.id})")
        print(f"   -> Creada Company: {company_b.name} (ID: {company_b.id})")
        print("   -> Usuarios 'admin' creados para ambas (prueba de aislamiento)")

if __name__ == "__main__":
    seed_db()