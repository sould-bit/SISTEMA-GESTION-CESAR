from sqlalchemy import create_engine, text

def list_categories():
    engine = create_engine('postgresql://admin:admin123456789@localhost:5432/bdfastops')
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name FROM categories")).fetchall()
        print("Categories:", result)

if __name__ == "__main__":
    list_categories()
