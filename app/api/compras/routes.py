from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import usuario as models_usuario
from app.schemas import compras as schemas_compras
from app.schemas import documento as schemas_doc
from app.services import compras as service_compras

router = APIRouter()

@router.post("/", response_model=schemas_doc.Documento, status_code=status.HTTP_201_CREATED)
def crear_nueva_factura_compra(
    compra: schemas_compras.CompraCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Endpoint para crear una nueva factura de compra.
    Utiliza el servicio orquestador para manejar la contabilidad y el inventario.
    """
    return service_compras.crear_factura_compra(
        db=db, 
        compra=compra, 
        user_id=current_user.id,
        empresa_id=current_user.empresa_id
    )

