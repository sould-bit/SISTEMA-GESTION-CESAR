from sqlalchemy import create_engine, text

def check_image():
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/el_rincon_db')
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name, image_url FROM products WHERE name ILIKE '%hamburguesa bacon%'")).fetchall()
        print("DB Result:", result)

if __name__ == "__main__":
    check_image()
