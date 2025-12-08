from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import date, datetime
from fastapi import HTTPException
from ..models import activo_fijo as models, activo_categoria as models_cat, activo_novedad as models_nov
from ..models import documento as models_doc, movimiento_contable as models_mov, tipo_documento as models_tipo
from ..services import periodo as service_periodo
from ..schemas import activo_fijo as schemas

# --- CATEGORIAS ---

def create_categoria(db: Session, categoria: schemas.ActivoCategoriaCreate, empresa_id: int):
    # Validar nombre único? Opcional/Recomendado
    db_cat = models_cat.ActivoCategoria(**categoria.model_dump(), empresa_id=empresa_id)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

def get_categorias(db: Session, empresa_id: int, skip: int = 0, limit: int = 100):
    return db.query(models_cat.ActivoCategoria).filter(
        models_cat.ActivoCategoria.empresa_id == empresa_id
    ).offset(skip).limit(limit).all()

# --- ACTIVOS FIJOS ---

def create_activo(db: Session, activo: schemas.ActivoFijoCreate, user_id: int, empresa_id: int):
    # 1. Validar unicidad de código
    existing = db.query(models.ActivoFijo).filter(
        models.ActivoFijo.codigo == activo.codigo, 
        models.ActivoFijo.empresa_id == empresa_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un activo con ese código/placa.")

    # 2. Crear el Activo
    # BUG FIX: Default fecha_inicio_uso to fecha_compra if None
    activo_data = activo.model_dump()
    if not activo_data.get('fecha_inicio_uso'):
        activo_data['fecha_inicio_uso'] = activo_data['fecha_compra']

    db_activo = models.ActivoFijo(**activo_data, empresa_id=empresa_id)
    db.add(db_activo)
    db.flush() # Para obtener el ID
    
    # 3. Registrar Novedad de ALTA (Historia)
    novedad_alta = models_nov.ActivoNovedad(
        empresa_id=empresa_id,
        activo_id=db_activo.id,
        fecha=activo.fecha_compra,
        tipo=models_nov.TipoNovedadActivo.ALTA,
        valor=activo.costo_adquisicion,
        observacion="Registro inicial del activo",
        created_by=user_id,
        detalles={"origen": "CREACION_MANUAL"}
    )
    db.add(novedad_alta)
    
    db.commit()
    db.refresh(db_activo)
    return db_activo

def get_activos(
    db: Session, 
    empresa_id: int, 
    skip: int = 0, 
    limit: int = 100,
    categoria_id: Optional[int] = None,
    responsable_id: Optional[int] = None,
    estado: Optional[str] = None,
    filtro_texto: Optional[str] = None
):
    query = db.query(models.ActivoFijo).filter(models.ActivoFijo.empresa_id == empresa_id)
    
    if categoria_id:
        query = query.filter(models.ActivoFijo.categoria_id == categoria_id)
    if responsable_id:
        query = query.filter(models.ActivoFijo.responsable_id == responsable_id)
    if estado:
        query = query.filter(models.ActivoFijo.estado == estado)
    
    if filtro_texto:
        search = f"%{filtro_texto}%"
        query = query.filter(
            (models.ActivoFijo.nombre.ilike(search)) | 
            (models.ActivoFijo.codigo.ilike(search)) |
            (models.ActivoFijo.serial.ilike(search))
        )
        
    return query.offset(skip).limit(limit).all()

def get_activo_by_id(db: Session, activo_id: int, empresa_id: int):
    return db.query(models.ActivoFijo).filter(
        models.ActivoFijo.id == activo_id,
        models.ActivoFijo.empresa_id == empresa_id
    ).first()

def update_activo(db: Session, activo_id: int, update_data: schemas.ActivoFijoUpdate, empresa_id: int):
    db_activo = get_activo_by_id(db, activo_id, empresa_id)
    if not db_activo:
        return None
        
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(db_activo, key, value)
    
    db.commit()
    db.refresh(db_activo)
    return db_activo

def val_decimal(val):
    from decimal import Decimal
    return Decimal(str(val))

# --- MOTOR DE DEPRECIACIÓN ---

def ejecutar_depreciacion(db: Session, empresa_id: int, anio: int, mes: int, user_id: int, tipo_documento_id: int):
    # 1. Validar Período
    import calendar
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fecha_cierre = date(anio, mes, ultimo_dia)
    
    # service_periodo.validar_periodo_abierto(db, empresa_id, fecha_cierre) # Descomentar cuando esté listo
    
    # 2. Obtener Tipo de Documento
    tipo_doc = db.query(models_tipo.TipoDocumento).filter(
        models_tipo.TipoDocumento.id == tipo_documento_id,
        models_tipo.TipoDocumento.empresa_id == empresa_id
    ).first()
    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado.")
    
    # 3. Buscar Activos Depreciables
    # Modificación Robustez: Si fecha_inicio_uso es NULL, usar fecha_compra
    from sqlalchemy import or_
    activos = db.query(models.ActivoFijo).filter(
        models.ActivoFijo.empresa_id == empresa_id,
        models.ActivoFijo.estado == models.EstadoActivo.ACTIVO,
        or_(
            models.ActivoFijo.fecha_inicio_uso <= fecha_cierre,
            and_(models.ActivoFijo.fecha_inicio_uso.is_(None), models.ActivoFijo.fecha_compra <= fecha_cierre)
        )
    ).all()
    
    if not activos:
        raise HTTPException(status_code=400, detail="No hay activos aptos para depreciar en este período (o no han iniciado uso).")

    movimientos_contables = []
    total_depreciacion_mes = 0

    # 4. Crear Cabecera del Documento
    numero_doc = (tipo_doc.consecutivo_actual or 0) + 1
    
    # Importante: Fecha operación hora actual, fecha documento cierre de mes
    nuevo_documento = models_doc.Documento(
        empresa_id=empresa_id,
        tipo_documento_id=tipo_documento_id,
        numero=numero_doc,
        fecha=fecha_cierre,
        fecha_operacion=datetime.utcnow(),
        usuario_creador_id=user_id,
        estado="ACTIVO",
        centro_costo_id=None 
    )
    db.add(nuevo_documento)
    db.flush()

    # 5. Iterar Activos
    for activo in activos:
        # Lógica NIIF Simplificada: Línea Recta
        base_niif = float(activo.costo_adquisicion) - float(activo.valor_residual)
        vida_util = activo.categoria.vida_util_niif_meses
        
        if vida_util > 0 and base_niif > 0:
            cuota_mes = base_niif / vida_util
            
            # Control de Saldo para no depreciar de más
            dep_acum_actual = float(activo.depreciacion_acumulada_niif)
            saldo_pendiente = base_niif - dep_acum_actual
            
            # Si ya está depreciado, saltar
            if saldo_pendiente <= 0:
                continue

            # Ajuste fina
            if cuota_mes > saldo_pendiente:
                cuota_mes = saldo_pendiente
            
            if cuota_mes > 0:
                # Actualizar Activo
                activo.depreciacion_acumulada_niif += val_decimal(cuota_mes)
                
                # Crear Novedad
                novedad = models_nov.ActivoNovedad(
                    empresa_id=empresa_id,
                    activo_id=activo.id,
                    fecha=fecha_cierre,
                    tipo=models_nov.TipoNovedadActivo.DEPRECIACION,
                    valor=cuota_mes,
                    documento_contable_id=nuevo_documento.id,
                    observacion=f"Cierre {mes}/{anio}",
                    created_by=user_id
                )
                db.add(novedad)
                
                # Preparar Movimientos Contables
                # GASTO (DEBITO)
                if activo.categoria.cuenta_gasto_depreciacion_id:
                    movimientos_contables.append({
                        "cuenta_id": activo.categoria.cuenta_gasto_depreciacion_id,
                        "debito": cuota_mes,
                        "credito": 0,
                        "concepto": f"Deprec. {activo.codigo} {activo.nombre}"
                    })
                
                # ACUMULADA (CREDITO)
                if activo.categoria.cuenta_depreciacion_acumulada_id:
                     movimientos_contables.append({
                        "cuenta_id": activo.categoria.cuenta_depreciacion_acumulada_id,
                        "debito": 0,
                        "credito": cuota_mes,
                        "concepto": f"Deprec. {activo.codigo} {activo.nombre}"
                    })
                
                total_depreciacion_mes += cuota_mes

    if total_depreciacion_mes == 0:
         # Si llegó hasta aquí pero no hubo valores, puede que todos estén depreciados.
         # Opcional: Lanzar error o solo loguear.
         pass # Permitimos crear el documento vacío o con 0? Mejor lanzar error si está vacío.
    
    if not movimientos_contables:
          # Rollback manual o raise
          # raise HTTPException(status_code=400, detail="Todos los activos están totalmente depreciados.")
          pass 

    # 6. Insertar Movimientos
    for mov in movimientos_contables:
        db_mov = models_mov.MovimientoContable(
            documento_id=nuevo_documento.id,
            cuenta_id=mov["cuenta_id"],
            debito=mov["debito"],
            credito=mov["credito"],
            concepto=mov["concepto"]
        )
        db.add(db_mov)

    # Actualizar consecutivo
    tipo_doc.consecutivo_actual = numero_doc
    
    db.commit()
    db.refresh(nuevo_documento)
    return nuevo_documento
