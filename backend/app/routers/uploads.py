from fastapi import APIRouter, UploadFile, File, HTTPException, status, Response
from fastapi.responses import FileResponse
import shutil
import os
import uuid
from pathlib import Path
from typing import List
import logging

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Directorio base para subidas (relativo a backend/)
# Usamos ruta absoluta para evitar ambigüedades
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/{filename}")
async def get_uploaded_file(filename: str):
    """
    Servir archivos subidos manualmente.
    Leyendo en memoria para evitar problemas de locking/streaming en Docker Windows.
    """
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Lectura síncrona simple para máxima compatibilidad
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        
        # Determinar content type básico
        content_type = "application/octet-stream"
        suffix = file_path.suffix.lower()
        if suffix in [".png"]: content_type = "image/png"
        elif suffix in [".jpg", ".jpeg"]: content_type = "image/jpeg"
        elif suffix in [".webp"]: content_type = "image/webp"
            
        return Response(content=data, media_type=content_type)
    except Exception as e:
        print(f"❌ Read Error: {e}")
        raise HTTPException(500, detail=str(e))

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Subir una imagen y obtener su URL.
    """
    print(f"📤 [UPLOAD] Received upload request")
    print(f"📤 [UPLOAD] Filename: {file.filename}")
    
    try:
        # Validar extensión
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de archivo no permitido. Use imágenes (jpg, png, webp)"
            )

        # Generar nombre único
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        # Guardar archivo
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Verificar que se guardó
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"✅ [UPLOAD] File saved: {file_path} ({file_size} bytes)")
        
        # Retornar URL apuntando al nuevo endpoint GET
        # Nota: El frontend espera /static/uploads/... si usa StaticFiles
        # pero ahora devolveremos /uploads/{filename} que el backend resolverá.
        response = {
            "url": f"/uploads/{unique_filename}",
            "filename": unique_filename
        }
        return response

    except Exception as e:
        print(f"❌ [UPLOAD] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo: {str(e)}"
        )

