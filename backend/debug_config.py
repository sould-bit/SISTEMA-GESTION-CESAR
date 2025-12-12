from app.config import settings
import os

print(f"--- DEBUG INFO ---")
print(f"DATABASE_URL len: {len(settings.DATABASE_URL)}")
print(f"DATABASE_URL content: {settings.DATABASE_URL!r}")
print(f"Attempting manual print of .env file bytes:")
try:
    with open('.env', 'rb') as f:
        content = f.read()
        print(f"Content length: {len(content)}")
        print(f"Content preview: {content[:100]}")
except Exception as e:
    print(f"Could not read .env: {e}")
