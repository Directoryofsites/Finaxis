from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional # <--- Added Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.models.usuario_busqueda import UsuarioBusqueda

router = APIRouter(prefix="/busquedas", tags=["Usuarios - Búsquedas Guardadas"])

# --- SCHEMAS ---
class BusquedaCreate(BaseModel):
    titulo: str
    comando: str
    parametros: Optional[str] = None # <--- Fixed

class BusquedaResponse(BaseModel):
    id: int
    titulo: str
    comando: str
    parametros: Optional[str] = None # <--- Fixed
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# --- ENDPOINTS ---

from fastapi.security import OAuth2PasswordBearer
from app.core import security

# Fix para evitar bloqueos si el token falla (auto_error=False)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

async def get_user_silent(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[Usuario]:
    if not token:
        return None
    try:
        # Reutilizamos la lógica de security pero manejando el error
        return await security.get_current_user(token, db)
    except HTTPException:
        return None

@router.get("/", response_model=List[BusquedaResponse])
async def obtener_busquedas_guardadas(
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_user_silent)
):
    """
    Obtiene todas las búsquedas guardadas. Retorna lista vacía si no hay usuario válido.
    """
    if not current_user:
        return []
        
    return db.query(UsuarioBusqueda).filter(UsuarioBusqueda.usuario_id == current_user.id).order_by(UsuarioBusqueda.fecha_creacion.desc()).all()

@router.post("/", response_model=BusquedaResponse)
def guardar_busqueda(
    busqueda: BusquedaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Guarda una nueva búsqueda en la biblioteca del usuario.
    """
    # Verificar límite opcional (por ahora ilimitado, pero bueno tenerlo en mente)
    # count = db.query(UsuarioBusqueda).filter(UsuarioBusqueda.usuario_id == current_user.id).count()
    
    nueva_busqueda = UsuarioBusqueda(
        usuario_id=current_user.id,
        titulo=busqueda.titulo,
        comando=busqueda.comando,
        parametros=busqueda.parametros
    )
    db.add(nueva_busqueda)
    db.commit()
    db.refresh(nueva_busqueda)
    return nueva_busqueda

@router.delete("/{busqueda_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_busqueda(
    busqueda_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina una búsqueda guardada.
    """
    busqueda = db.query(UsuarioBusqueda).filter(
        UsuarioBusqueda.id == busqueda_id,
        UsuarioBusqueda.usuario_id == current_user.id
    ).first()
    
    if not busqueda:
        raise HTTPException(status_code=404, detail="Búsqueda no encontrada")
        
    db.delete(busqueda)
    db.commit()
    return None

@router.put("/{busqueda_id}", response_model=BusquedaResponse)
def actualizar_busqueda(
    busqueda_id: int,
    datos: BusquedaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza el título o comando de una búsqueda guardada.
    """
    busqueda = db.query(UsuarioBusqueda).filter(
        UsuarioBusqueda.id == busqueda_id,
        UsuarioBusqueda.usuario_id == current_user.id
    ).first()
    
    if not busqueda:
        raise HTTPException(status_code=404, detail="Búsqueda no encontrada")

    busqueda.titulo = datos.titulo
    busqueda.comando = datos.comando
    if datos.parametros is not None:
        busqueda.parametros = datos.parametros
    
    db.commit()
    db.refresh(busqueda)
    return busqueda
