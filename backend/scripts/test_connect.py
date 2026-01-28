import urllib.request
import urllib.error
import time

URL = "http://127.0.0.1:8000/docs" # Docs always exists in FastAPI

print(f"🔎 Probando conexión a {URL}...")

try:
    req = urllib.request.Request(URL, method='GET')
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"✅ ÉXITO: Servidor responde con código {response.getcode()}")
        content = response.read(100).decode('utf-8')
        print(f"   Snippet: {content}...")
except urllib.error.HTTPError as e:
    # 404 is also success (server is reachable)
    print(f"✅ ÉXITO PARCIAL: Servidor alcanzable pero retornó {e.code}")
except urllib.error.URLError as e:
    print(f"❌ ERROR DE RED: {e.reason}")
    print("   -> El servidor no es alcanzable desde Windows.")
except Exception as e:
    print(f"❌ ERROR INESPERADO: {e}")
