from sqlalchemy import create_engine, text

def check_enum():
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/el_rincon_db')
    with engine.connect() as conn:
        result = conn.execute(text("SELECT unnest(enum_range(NULL::ingredient_type_enum))")).fetchall()
        print("Enum Values:", result)

if __name__ == "__main__":
    check_enum()
