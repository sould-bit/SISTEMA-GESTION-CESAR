from sqlmodel import select, Session
from app.database import engine
from passlib.context import CryptContext
from app.models.user  import User


#configuracion para hasehar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    with Session(engine) as session:
        #verificamos si ya existe 
        statement = select(User).where(User.username == "admin")
        user = session.exec(statement).first()

        if user:
            print("el usuario admin ya existe")
            return    

        admin_user = User(
            username="admin",
            email="admin@sisalchi.com",
            full_name="Administrador Sistema",
            role="admin",
            hashed_password=pwd_context.hash("admin123"),  # ¡Contraseña hasheada!
            company_id=1,
            branch_id=1
        )


        session.add(admin_user)
        session.commit()
        print("Admin creado exitosamente")

if __name__ == "__main__":
    create_admin()
