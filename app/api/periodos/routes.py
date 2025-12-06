from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.services import periodo as periodo_service
from app.schemas import periodo as periodo_schemas
from app.core.database import get_db
from app.core.security import get_current_user, get_current_soporte_user
from app.models import Usuario as models_usuario

router = APIRouter()

@router.post("/", response_model=periodo_schemas.PeriodoResponse, status_code=status.HTTP_201_CREATED)
def cerrar_periodo(
    periodo_data: periodo_schemas.PeriodoCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Cierra un nuevo período contable para la empresa del usuario.
    """
    try:
        # --- CORRECCIÓN CLAVE ---
        # Desempaquetamos el año y el mes del objeto 'periodo_data'
        # y los pasamos como argumentos separados, que es lo que el servicio ahora espera.
        return periodo_service.cerrar_periodo(
            db=db,
            empresa_id=current_user.empresa_id,
            ano=periodo_data.ano,
            mes=periodo_data.mes,
            user_id=current_user.id
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{ano}/{mes}", status_code=status.HTTP_200_OK)
def reabrir_periodo(
    ano: int,
    mes: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Reabre un período contable para la empresa del usuario.
    """
    try:
        return periodo_service.reabrir_periodo(
            db=db,
            empresa_id=current_user.empresa_id,
            ano=ano,
            mes=mes
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=List[periodo_schemas.PeriodoResponse])
def get_periodos_cerrados(
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de todos los períodos cerrados para la empresa del usuario actual.
    """
    try:
        # Usamos el nombre correcto de la función que ya existe en tu servicio
        return periodo_service.get_periodos_cerrados_por_empresa(db=db, empresa_id=current_user.empresa_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{empresa_id}", response_model=List[periodo_schemas.PeriodoResponse])
def get_periodos_cerrados_para_soporte(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_soporte_user)
):
    """
    Obtiene la lista de todos los períodos cerrados para una empresa específica (SOPORTE).
    """
    try:
        # Usamos el nombre correcto de la función que ya existe en tu servicio
        return periodo_service.get_periodos_cerrados_por_empresa(db=db, empresa_id=empresa_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))