from fastapi import APIRouter, UploadFile, File, HTTPException, status
import shutil
import os
import uuid
from pathlib import Path
from typing import List

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Directorio base para subidas (relativo a backend/)
UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Subir una imagen y obtener su URL.
    """
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

        # Retornar URL relativa (asumiendo montaje en /static)
        # Ajustamos para devolver la URL completa si es necesario, 
        # pero por ahora devolvemos path absoluto http relativo
        return {
            "url": f"/static/uploads/{unique_filename}",
            "filename": unique_filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo: {str(e)}"
        )
