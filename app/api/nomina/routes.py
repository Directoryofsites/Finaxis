from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models import nomina as models
from app.models import Tercero, Documento  # Importaciones explícitas

# ... existing imports ...

from app.services import documento as documento_service
from app.services.nomina.liquidador import LiquidadorNominaService
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from app.core.security import get_current_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/nomina", tags=["Nomina"])

from app.schemas.nomina import (
    TipoNominaCreate, TipoNominaUpdate, TipoNominaResponse,
    EmpleadoCreate, EmpleadoResponse, LiquidarRequest, GuardarNominaRequest
)

# --- ROUTES TIPOS NOMINA (NUEVO) ---

@router.get("/tipos", response_model=List[TipoNominaResponse])
def get_tipos_nomina(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(models.TipoNomina).filter(models.TipoNomina.empresa_id == current_user.empresa_id).all()

@router.post("/tipos", response_model=TipoNominaResponse)
def create_tipo_nomina(tipo: TipoNominaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    nuevo_tipo = models.TipoNomina(
        empresa_id=current_user.empresa_id,
        nombre=tipo.nombre,
        descripcion=tipo.descripcion,
        periodo_pago=tipo.periodo_pago
    )
    db.add(nuevo_tipo)
    db.commit()
    db.refresh(nuevo_tipo)
    return nuevo_tipo

@router.put("/tipos/{id}", response_model=TipoNominaResponse)
def update_tipo_nomina(id: int, tipo: TipoNominaUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_tipo = db.query(models.TipoNomina).filter(
        models.TipoNomina.id == id,
        models.TipoNomina.empresa_id == current_user.empresa_id
    ).first()
    
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de nómina no encontrado")
        
    if tipo.nombre is not None:
        db_tipo.nombre = tipo.nombre
    if tipo.descripcion is not None:
        db_tipo.descripcion = tipo.descripcion
    if tipo.periodo_pago is not None:
        db_tipo.periodo_pago = tipo.periodo_pago
        
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

@router.delete("/tipos/{id}")
def delete_tipo_nomina(id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_tipo = db.query(models.TipoNomina).filter(
        models.TipoNomina.id == id,
        models.TipoNomina.empresa_id == current_user.empresa_id
    ).first()
    
    if not db_tipo:
        raise HTTPException(status_code=404, detail="Tipo de nómina no encontrado")
    
    # Validar que no tenga empleados asociados
    empleados_count = db.query(models.Empleado).filter(models.Empleado.tipo_nomina_id == id).count()
    if empleados_count > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar porque hay empleados asociados a este tipo.")
        
    db.delete(db_tipo)
    db.commit()
    return {"message": "Tipo de nómina eliminado correctamente"}


# --- ROUTES EMPLEADOS ---

@router.post("/empleados", response_model=EmpleadoResponse)
def create_empleado(empleado: EmpleadoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
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
            es_empleado=True,  # MARCADO AUTOMÁTICO
            direccion="Dirección pendiente", 
            telefono="Teléfono pendiente",
            email="email@pendiente.com"
        )
        db.add(nuevo_tercero)
        db.flush() # Para obtener ID
        tercero = nuevo_tercero
    else:
        # Asegurar que esté marcado como empleado si ya existía
        if not tercero.es_empleado:
            tercero.es_empleado = True
            db.add(tercero) # Mark for update
    
    # Validar si ya existe un empleado activo con ese tercero o documento para evitar duplicados en nómina
    # AHORA VALIDAMOS por documento y empresa
    existing_emp = db.query(models.Empleado).filter(
        models.Empleado.numero_documento == empleado.numero_documento,
        models.Empleado.empresa_id == current_user.empresa_id
    ).first()
    
    if existing_emp:
        raise HTTPException(status_code=400, detail="Ya existe un empleado con este documento en la empresa.")
    
    db_empleado = models.Empleado(
        empresa_id=current_user.empresa_id,
        nombres=empleado.nombres,
        apellidos=empleado.apellidos,
        numero_documento=empleado.numero_documento,
        salario_base=empleado.salario_base,
        fecha_ingreso=empleado.fecha_ingreso,
        auxilio_transporte=empleado.tiene_auxilio,
        tercero_id=tercero.id,
        tipo_nomina_id=empleado.tipo_nomina_id
    )
    db.add(db_empleado)
    db.commit()
    db.refresh(db_empleado)
    return db_empleado

@router.get("/empleados", response_model=List[EmpleadoResponse])
def get_empleados(tipo_nomina_id: Optional[int] = None, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    query = db.query(models.Empleado).filter(models.Empleado.empresa_id == current_user.empresa_id)
    if tipo_nomina_id:
        query = query.filter(models.Empleado.tipo_nomina_id == tipo_nomina_id)
    return query.all()

@router.put("/empleados/{id}", response_model=EmpleadoResponse)
def update_empleado(id: int, empleado: EmpleadoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_empleado = db.query(models.Empleado).filter(
        models.Empleado.id == id,
        models.Empleado.empresa_id == current_user.empresa_id
    ).first()
    
    if not db_empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
    db_empleado.nombres = empleado.nombres
    db_empleado.apellidos = empleado.apellidos
    db_empleado.numero_documento = empleado.numero_documento
    db_empleado.salario_base = empleado.salario_base
    db_empleado.fecha_ingreso = empleado.fecha_ingreso
    db_empleado.auxilio_transporte = empleado.tiene_auxilio
    db_empleado.tipo_nomina_id = empleado.tipo_nomina_id
    
    db.commit()
    db.refresh(db_empleado)
    return db_empleado

# --- CONFIGURACION PUC ---

from app.schemas.nomina import ConfigNominaSchema

@router.get("/configuracion", response_model=ConfigNominaSchema)
def get_configuracion(tipo_nomina_id: Optional[int] = None, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    query = db.query(models.ConfiguracionNomina).filter(models.ConfiguracionNomina.empresa_id == current_user.empresa_id)
    
    if tipo_nomina_id:
        query = query.filter(models.ConfiguracionNomina.tipo_nomina_id == tipo_nomina_id)
    else:
        # Default global config (where tipo_nomina_id is None)
        query = query.filter(models.ConfiguracionNomina.tipo_nomina_id == None)
        
    config = query.first()
    
    if not config:
        return ConfigNominaSchema(tipo_nomina_id=tipo_nomina_id)
    return config

@router.post("/configuracion", response_model=ConfigNominaSchema)
def save_configuracion(config: ConfigNominaSchema, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Buscar config existente para ese tipo (o global si es None)
    query = db.query(models.ConfiguracionNomina).filter(models.ConfiguracionNomina.empresa_id == current_user.empresa_id)
    
    if config.tipo_nomina_id:
        query = query.filter(models.ConfiguracionNomina.tipo_nomina_id == config.tipo_nomina_id)
    else:
        query = query.filter(models.ConfiguracionNomina.tipo_nomina_id == None)
        
    db_config = query.first()
    
    if not db_config:
        db_config = models.ConfiguracionNomina(
            empresa_id=current_user.empresa_id,
            tipo_nomina_id=config.tipo_nomina_id
        )
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
    
    # NUEVOS CAMPOS
    db_config.cuenta_otros_devengados_id = config.cuenta_otros_devengados_id
    db_config.cuenta_otras_deducciones_id = config.cuenta_otras_deducciones_id
    
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
        comisiones=Decimal(req.comisiones),
        otros_devengados=Decimal(req.otros_devengados),
        otras_deducciones=Decimal(req.otras_deducciones)
    )

    
    return {
        "empleado": f"{empleado.nombres} {empleado.apellidos}",
        "detalle": resultado
    }


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
            comisiones=Decimal(req.comisiones),
            otros_devengados=Decimal(req.otros_devengados),
            otras_deducciones=Decimal(req.otras_deducciones)
        )
        return {"status": "success", "mensaje": "Liquidación guardada correctamente", "detalle_id": detalle.id}
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
        raise HTTPException(status_code=500, detail="Error interno al guardar la nómina.")

@router.get("/historial")
def get_historial_nomina(
    anio: Optional[int] = None,
    mes: Optional[int] = None,
    tipo_nomina_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna lista plana de desprendibles generados (DetalleNomina).
    """
    # Filtrar por empresa del usuario
    query = db.query(models.DetalleNomina).join(models.Nomina).join(models.Empleado).filter(models.Nomina.empresa_id == current_user.empresa_id)

    if anio:
        query = query.filter(models.Nomina.anio == anio)
    if mes:
        query = query.filter(models.Nomina.mes == mes)
    if tipo_nomina_id:
        query = query.filter(models.Empleado.tipo_nomina_id == tipo_nomina_id)

    detalles = query.all()
    
    # --- ENRIQUECIMIENTO CON DATOS CONTABLES ---
    # Estrategia: Buscar documentos que coincidan en observaciones
    # Para optimizar, filtramos solo documentos recientes o del periodo activo (opcional)
    # Por ahora, traemos documentos que contengan "Ref:" en observaciones de la empresa
    # (En producción esto debería limitarse por fecha también para no cargar todo)
    
    docs_map = {}
    if detalles:
        # Obtener rango mas amplio de fechas si es necesario, o traer ultimos 500 docs si es muy pesado.
        # Aquí haremos una búsqueda exacta por IDs para ser precisos.
        # Pero SQL 'OR' con muchos LIKE es lento.
        # Mejor: Traer los documentos tipo 'NM' (Nomina) del periodo.
        
        # Simplificación para UI: Devolver placeholders si es muy complejo
        # Pero el usuario pidió verlo.
        
        # Intento de optimización: Traer todos los documentos que digan "Ref:" de la empresa
        # Si la tabla es gigante esto es lento. Mejor filtrar por fecha min/max de los detalles.
        if len(detalles) > 0:
            min_date = min([d.nomina.fecha_inicio_periodo for d in detalles])
            # max_date = max([d.nomina.fecha_fin_periodo for d in detalles])
            
            # Buscar candidatos
            # Usando contains es mas rapido que regex en DB a veces
            candidate_docs = db.query(Documento).filter(
                Documento.empresa_id == current_user.empresa_id,
                Documento.fecha >= min_date,
                Documento.observaciones.contains("Ref: ") # Filtro clave
            ).all()
            
            import re
            for cdoc in candidate_docs:
                # Extraer ID
                match = re.search(r"Ref:\s*(\d+)", cdoc.observaciones or "")
                if match:
                    det_id = int(match.group(1))
                    docs_map[det_id] = {
                        "tipo": cdoc.tipo_documento.codigo if cdoc.tipo_documento else "DOC",
                        "numero": cdoc.numero,
                        "id": cdoc.id
                    }

    res = []
    for d in detalles:
        emp = d.empleado
        nom = d.nomina
        doc_info = docs_map.get(d.id, {"tipo": "-", "numero": "-", "id": None})
        
        res.append({
            "id": d.id,
            "empleado": f"{emp.nombres} {emp.apellidos}",
            "documento": emp.numero_documento,
            "periodo": f"{nom.anio}-{nom.mes:02d}",
            "neto": d.neto_pagar,
            "estado": "GENERADO",
            "doc_contable_tipo": doc_info["tipo"],
            "doc_contable_numero": doc_info["numero"],
            "doc_contable_id": doc_info["id"]
        })
    return res

from fastapi.responses import StreamingResponse
from app.services.nomina.reportes import ReportesNominaService
import io

@router.delete("/desprendibles/{id}")
def eliminar_desprendible(id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    detalle = db.query(models.DetalleNomina).get(id)
    if not detalle:
        raise HTTPException(status_code=404, detail="Desprendible no encontrado")
        
    # --- REVERSION CONTABLE AUTOMATICA Y SEGURA (CON ID) ---
    doc_id = detalle.documento_contable_id
    
    # Fallback (Compatibilidad hacia atrás): Buscar por Ref string si no tiene ID
    if not doc_id:
        ref_str = f"Ref: {detalle.id}"
        documento_contable = db.query(Documento).filter(
            Documento.observaciones.contains(ref_str),
            Documento.estado != 'ANULADO'
        ).first()
        if documento_contable:
            doc_id = documento_contable.id

    if doc_id:
        # STRICT DELETION: Si falla la contabilidad, debe fallar todo para evitar inconsistencias.
        # Nada de "try/except pass" aquí.
        documento_service.eliminar_documento(
            db=db,
            documento_id=doc_id,
            empresa_id=current_user.empresa_id,
            user_id=current_user.id,
            razon=f"Eliminación autom. desde Nómina (Ref: {id})"
        )
            
    # -------------------------------------
    
    # Eliminar Detalle
    db.delete(detalle)
    db.commit()
    return {"message": "Desprendible eliminado y asiento contable enviado a papelera."}

@router.get("/desprendibles/{id}/pdf")
def descargar_desprendible_pdf(id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
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

@router.get("/resumen-pdf")
def descargar_resumen_pdf(
    anio: int, 
    mes: int, 
    tipo_nomina_id: Optional[int] = None, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        pdf_bytes, filename = ReportesNominaService.generar_pdf_resumen_nomina(
            db=db, 
            empresa_id=current_user.empresa_id, 
            anio=anio, 
            mes=mes,
            tipo_nomina_id=tipo_nomina_id
        )
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type='application/pdf', headers=headers)
    except ValueError as ve:
         raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR PDF RESUMEN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")


@router.get("/empleados/pdf")
def descargar_reporte_empleados(
    tipo_nomina_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        pdf_bytes, filename = ReportesNominaService.generar_pdf_lista_empleados(
            db=db, 
            empresa_id=current_user.empresa_id, 
            tipo_nomina_id=tipo_nomina_id
        )
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type='application/pdf', headers=headers)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR PDF EMPLEADOS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")
