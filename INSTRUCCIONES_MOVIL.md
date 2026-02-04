# Acceso desde Móvil

Para acceder al sistema desde su celular, siga estos pasos:

## 1. Configuración de Red
Asegúrese de que su computadora y su celular estén conectados a la misma red Wi-Fi.

- **IP de su computadora**: 192.168.1.3 (Detectada)

## 2. Iniciar Backend (Docker)
Como su backend corre en Docker, ya está configurado para aceptar conexiones externas automáticamente:

1.  Asegúrese de que Docker Desktop esté corriendo.
2.  Inicie sus contenedores como lo hace normalmente:
    ```powershell
    docker-compose up
    ```
    *(O `docker compose up` dependiendo de su versión).*

El backend estará disponible en `http://192.168.1.3:8000` para su celular.

## 3. Iniciar Frontend (Local)
El frontend ya está configurado con detección automática de IP. Solo ejecute:

```powershell
npm run dev
```

Debería ver: `➜  Network: http://192.168.1.3:5173/`

## 4. Conectar desde el Celular
1. Conecte su celular al **mismo Wi-Fi** que la computadora.
2. Abra el navegador e ingrese: `http://192.168.1.3:5173`
3. **Solución a errores de Login (400/CORS)**:
   - He actualizado el backend para permitir conexiones de cualquier origen (`CORS`).
   - Si persiste el error, asegúrese de que el Firewall de Windows permita tráfico en el puerto **8000** y **5173**.
   - Pruebe abriendo `http://192.168.1.3:8000/health` en el navegador de su celular. Si NO carga, es el Firewall.


