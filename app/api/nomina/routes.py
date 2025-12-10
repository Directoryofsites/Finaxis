from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models import nomina as models
from app.models import Tercero  # Importación explícita para evitar error
from app.services.nomina.liquidador import LiquidadorNominaService
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from app.core.security import get_current_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/nomina", tags=["Nomina"])

# --- SCHEMAS (Internal for now, later move to schemas/nomina.py) ---

class EmpleadoCreate(BaseModel):
    nombres: str
    apellidos: str
    numero_documento: str
    salario_base: float
    fecha_ingreso: date
    tiene_auxilio: bool = True
    tercero_id: Optional[int] = None

class EmpleadoResponse(EmpleadoCreate):
    id: int
    class Config:
        from_attributes = True

class LiquidarRequest(BaseModel):
    empleado_id: int
    dias_trabajados: int = 30
    horas_extras: float = 0
    comisiones: float = 0

# --- ROUTES ---

@router.post("/empleados", response_model=EmpleadoResponse)
def create_empleado(empleado: EmpleadoCreate, db: Session = Depends(get_db)):
    tercero = None

    # 1. Si viene tercero_id, buscarlo directamente
    if empleado.tercero_id:
        tercero = db.query(Tercero).filter(Tercero.id == empleado.tercero_id).first()
        if not tercero:
            raise HTTPException(status_code=404, detail="El Tercero seleccionado no existe.")

    # 2. Si no viene ID, buscar por documento (Lógica original fallback)
    if not tercero:
        tercero = db.query(Tercero).filter(Tercero.nit == empleado.numero_documento).first()
    
    # 3. Si aún no existe, crearlo automáticamente
    if not tercero:
        nuevo_tercero = Tercero(
            nit=empleado.numero_documento,
            nombre_razon_social=f"{empleado.nombres} {empleado.apellidos}",
            es_cliente=False,
            es_proveedor=True, # Empleado suele ser proveedor de servicios laborales
            direccion="Dirección pendiente", 
            telefono="Teléfono pendiente",
            email="email@pendiente.com"
        )
        db.add(nuevo_tercero)
        db.flush() # Para obtener ID
        tercero = nuevo_tercero
    
    # Validar si ya existe un empleado activo con ese tercero o documento para evitar duplicados en nómina
    # (Opcional pero recomendable)
    
    db_empleado = models.Empleado(
        nombres=empleado.nombres,
        apellidos=empleado.apellidos,
        numero_documento=empleado.numero_documento,
        salario_base=empleado.salario_base,
        fecha_ingreso=empleado.fecha_ingreso,
        auxilio_transporte=empleado.tiene_auxilio,
        tercero_id=tercero.id
    )
    db.add(db_empleado)
    db.commit()
    db.refresh(db_empleado)
    return db_empleado

@router.get("/empleados", response_model=List[EmpleadoResponse])
def get_empleados(db: Session = Depends(get_db)):
    return db.query(models.Empleado).all()

# --- CONFIGURACION PUC ---

class ConfigNominaSchema(BaseModel):
    tipo_documento_id: Optional[int] = None
    cuenta_sueldo_id: Optional[int] = None
    cuenta_auxilio_transporte_id: Optional[int] = None
    cuenta_horas_extras_id: Optional[int] = None
    cuenta_comisiones_id: Optional[int] = None
    cuenta_salarios_por_pagar_id: Optional[int] = None
    cuenta_aporte_salud_id: Optional[int] = None
    cuenta_aporte_pension_id: Optional[int] = None
    cuenta_fondo_solidaridad_id: Optional[int] = None
    
    class Config:
        from_attributes = True

@router.get("/configuracion", response_model=ConfigNominaSchema)
def get_configuracion(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    config = db.query(models.ConfiguracionNomina).filter(models.ConfiguracionNomina.empresa_id == current_user.empresa_id).first()
    if not config:
        # Devolver vacÃo o defaults
        return ConfigNominaSchema()
    return config

@router.post("/configuracion", response_model=ConfigNominaSchema)
def save_configuracion(config: ConfigNominaSchema, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_config = db.query(models.ConfiguracionNomina).filter(models.ConfiguracionNomina.empresa_id == current_user.empresa_id).first()
    
    if not db_config:
        db_config = models.ConfiguracionNomina(empresa_id=current_user.empresa_id)
        db.add(db_config)
    
    # Actualizar campos
    db_config.tipo_documento_id = config.tipo_documento_id
    db_config.cuenta_sueldo_id = config.cuenta_sueldo_id
    db_config.cuenta_auxilio_transporte_id = config.cuenta_auxilio_transporte_id
    db_config.cuenta_horas_extras_id = config.cuenta_horas_extras_id
    db_config.cuenta_comisiones_id = config.cuenta_comisiones_id
    db_config.cuenta_salarios_por_pagar_id = config.cuenta_salarios_por_pagar_id
    db_config.cuenta_aporte_salud_id = config.cuenta_aporte_salud_id
    db_config.cuenta_aporte_pension_id = config.cuenta_aporte_pension_id
    db_config.cuenta_fondo_solidaridad_id = config.cuenta_fondo_solidaridad_id
    
    db.commit()
    db.refresh(db_config)
    return db_config


@router.post("/liquidar-preview")
def liquidar_preview(req: LiquidarRequest, db: Session = Depends(get_db)):
    """
    Simula la liquidaciÃ³n de un empleado sin guardar cambios.
    """
    empleado = db.query(models.Empleado).filter(models.Empleado.id == req.empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    resultado = LiquidadorNominaService.calcular_devengados_deducciones(
        salario_base=Decimal(empleado.salario_base),
        dias_trabajados=req.dias_trabajados,
        tiene_auxilio=empleado.auxilio_transporte,
        horas_extras=Decimal(req.horas_extras),
        comisiones=Decimal(req.comisiones)
    )
    
    return {
        "empleado": f"{empleado.nombres} {empleado.apellidos}",
        "detalle": resultado
    }

class GuardarNominaRequest(BaseModel):
    empleado_id: int
    anio: int
    mes: int
    dias_trabajados: int = 30
    horas_extras: float = 0
    comisiones: float = 0

@router.post("/liquidar/guardar")
def guardar_liquidacion_route(
    req: GuardarNominaRequest, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        detalle = LiquidadorNominaService.guardar_nomina(
            db=db,
            empresa_id=current_user.empresa_id,
            anio=req.anio,
            mes=req.mes,
            empleado_id=req.empleado_id,
            dias=req.dias_trabajados,
            extras=Decimal(req.horas_extras),
            comisiones=Decimal(req.comisiones)
        )
        return {"status": "success", "mensaje": "Liquidación guardada correctamente", "detalle_id": detalle.id}
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
        raise HTTPException(status_code=500, detail="Error interno al guardar la nómina.")

@router.get("/historial")
def get_historial_nomina(db: Session = Depends(get_db)):
    """
    Retorna lista plana de desprendibles generados (DetalleNomina).
    """
    detalles = db.query(models.DetalleNomina).all()
    # Enriquecer o usar response_model
    # Para simplicidad retornamos lista de dicts
    res = []
    for d in detalles:
        emp = d.empleado
        nom = d.nomina
        res.append({
            "id": d.id,
            "empleado": f"{emp.nombres} {emp.apellidos}",
            "documento": emp.numero_documento,
            "periodo": f"{nom.anio}-{nom.mes:02d}",
            "neto": d.neto_pagar,
            "estado": "GENERADO"
        })
    return res

from fastapi.responses import StreamingResponse
from app.services.nomina.reportes import ReportesNominaService
import io

@router.get("/desprendibles/{id}/pdf")
def descargar_desprendible_pdf(id: int, db: Session = Depends(get_db)):
    try:
        pdf_bytes, filename = ReportesNominaService.generar_pdf_desprendible(db, id)
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type='application/pdf', headers=headers)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error generando PDF: {str(e)}")
