# -*- coding: utf-8 -*-
"""
Script to manually apply the partial unique index migration.
"""
import psycopg2

# Hardcoded connection (from .env)
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "bdfastops"
DB_USER = "admin"
DB_PASS = "admin123456789"

SQL_STATEMENTS = [
    "ALTER TABLE products DROP CONSTRAINT IF EXISTS uq_products_company_name;",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_products_company_name_active 
       ON products(company_id, name) WHERE is_active = true;""",
]

def apply_migration():
    print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    for sql in SQL_STATEMENTS:
        print(f"Executing...")
        cur.execute(sql)
        print("  OK")
    
    # Verify indexes
    cur.execute("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename = 'products' AND indexname LIKE '%uq_products%'
    """)
    indexes = cur.fetchall()
    print(f"\nCurrent unique indexes on products: {[i[0] for i in indexes]}")
    
    cur.close()
    conn.close()
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    apply_migration()
