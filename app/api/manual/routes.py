from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
import os

router = APIRouter()

MANUAL_DIR = r"C:\ContaPY2\Manual"

@router.get("/{filename}")
def get_manual_file(filename: str):
    """
    Lee y devuelve el contenido de un archivo Markdown del manual.
    """
    # Seguridad básica para evitar Path Traversal
    if ".." in filename or "/" in filename or "\\" in filename:
         raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    file_path = os.path.join(MANUAL_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo del manual no encontrado")

    # Leemos el archivo y devolvemos el contenido como texto
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el manual: {str(e)}")
