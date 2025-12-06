# app/api/reportes_financieros_inventario/routes.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import io
import weasyprint
from jinja2 import Environment, DictLoader

from app.core.database import get_db
from app.core.security import has_permission, create_signed_token, validate_signed_token
from app.models import usuario as models_usuario, producto as models_producto, empresa as models_empresa
from app.services import reportes_financieros as service_reportes
from app.schemas.reporte_rentabilidad import RentabilidadProductoFiltros, RentabilidadProductoResponse
from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS

router = APIRouter()

@router.post(
    "/rentabilidad-producto",
    response_model=RentabilidadProductoResponse
)
def generar_reporte_rentabilidad(
    filtros: RentabilidadProductoFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("reportes:rentabilidad_producto"))
):
    return service_reportes.get_reporte_rentabilidad_producto(
        db=db, 
        filtros=filtros, 
        empresa_id=current_user.empresa_id
    )

@router.post(
    "/rentabilidad-producto/solicitar-pdf"
)
def solicitar_url_pdf_rentabilidad(
    filtros: RentabilidadProductoFiltros,
    current_user: models_usuario.Usuario = Depends(has_permission("reportes:rentabilidad_producto"))
):
    token_payload = filtros.model_dump_json()
    token = create_signed_token(token_payload, salt='pdf-rentabilidad')
    return {"token": token}


@router.get("/rentabilidad-producto/imprimir/{token}")
def imprimir_pdf_rentabilidad(token: str, db: Session = Depends(get_db)):
    payload_str = validate_signed_token(token, salt='pdf-rentabilidad', max_age=60)
    if not payload_str:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    
    filtros = RentabilidadProductoFiltros.model_validate_json(payload_str)
    
    producto = db.query(models_producto.Producto).filter(models_producto.Producto.id == filtros.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    
    empresa = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == producto.empresa_id).first()
    
    report_data = service_reportes.get_reporte_rentabilidad_producto(db=db, filtros=filtros, empresa_id=producto.empresa_id)

    context = {
        # --- CORRECCIÓN CLAVE: Usar 'razon_social' en lugar de 'nombre' ---
        "empresa_nombre": empresa.razon_social if empresa else "N/A",
        "producto_info": producto,
        "filtros": filtros,
        "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": report_data
    }

    env = Environment(loader=DictLoader(TEMPLATES_EMPAQUETADOS))
    template = env.get_template("reports/rentabilidad_producto.html")
    html_content = template.render(context)
    
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf")