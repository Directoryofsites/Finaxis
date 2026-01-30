from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import indicador_economico as service
from app.schemas import indicador_economico as schema
from app.core.security import get_current_user

router = APIRouter(prefix="/indicadores", tags=["configuracion", "indicadores"])

@router.get("/{vigencia}", response_model=schema.IndicadorResponse)
def get_indicadores(vigencia: int, db: Session = Depends(get_db)):
    """Obtiene indicadores de una vigencia (año). Si no existen, los inicializa."""
    return service.get_by_vigencia(db, vigencia)

@router.put("/{vigencia}", response_model=schema.IndicadorResponse)
def update_indicadores(
    vigencia: int, 
    data: schema.IndicadorUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualiza indicadores (TRM, UVT, etc). Requiere autenticación."""
    # Podríamos agregar check de rol admin aqui si es critico
    return service.update_indicadores(db, vigencia, data)
