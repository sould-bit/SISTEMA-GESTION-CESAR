from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://admin:admin123456789@localhost:5432/bdfastops"
engine = create_engine(DATABASE_URL)

sql = """
SELECT 
    u.email,
    r.code as role_code,
    p.code as permission_code
FROM users u
LEFT JOIN roles r ON u.role_id = r.id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON rp.permission_id = p.id
WHERE u.email = 'kate@gmail.com';
"""

try:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        
        if not rows:
            print("User not found.")
        else:
            print(f"User: {rows[0].email} | Role Code: {rows[0].role_code}")
            print("Permissions:")
            for row in rows:
                if row.permission_code:
                    print(f"- {row.permission_code}")
                else:
                    print("- No permissions assigned (or role has no permissions)")
except Exception as e:
    print(f"Error: {e}")
