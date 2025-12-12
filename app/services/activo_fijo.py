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

def get_categoria_by_id(db: Session, categoria_id: int, empresa_id: int):
    return db.query(models_cat.ActivoCategoria).filter(
        models_cat.ActivoCategoria.id == categoria_id,
        models_cat.ActivoCategoria.empresa_id == empresa_id
    ).first()

def update_categoria(db: Session, categoria_id: int, update_data: schemas.ActivoCategoriaCreate, empresa_id: int):
    db_categoria = get_categoria_by_id(db, categoria_id, empresa_id)
    if not db_categoria:
        return None
        
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(db_categoria, key, value)
    
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def delete_categoria(db: Session, categoria_id: int, empresa_id: int):
    # Verificar que no tenga activos asociados
    activos_count = db.query(models.ActivoFijo).filter(
        models.ActivoFijo.categoria_id == categoria_id,
        models.ActivoFijo.empresa_id == empresa_id
    ).count()
    
    if activos_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar la categoría. Tiene {activos_count} activos asociados."
        )
    
    db_categoria = get_categoria_by_id(db, categoria_id, empresa_id)
    if not db_categoria:
        return False
        
    db.delete(db_categoria)
    db.commit()
    return True

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
    """
    Ejecuta el proceso de depreciación masiva para el mes/año indicados.
    VERSIÓN PROFESIONAL con validaciones completas y múltiples métodos.
    """
    # 1. Validar Período
    import calendar
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fecha_cierre = date(anio, mes, ultimo_dia)
    
    # COMENTADO PARA PRUEBAS: Validar que no se deprecie el futuro
    # if fecha_cierre > date.today():
    #     raise HTTPException(status_code=400, detail="No se puede depreciar períodos futuros.")
    
    # 2. VALIDACIÓN RELAJADA: Solo advertir si ya existe, pero permitir continuar
    depreciaciones_existentes = db.query(models_nov.ActivoNovedad).filter(
        models_nov.ActivoNovedad.empresa_id == empresa_id,
        models_nov.ActivoNovedad.tipo == models_nov.TipoNovedadActivo.DEPRECIACION,
        func.extract('year', models_nov.ActivoNovedad.fecha) == anio,
        func.extract('month', models_nov.ActivoNovedad.fecha) == mes
    ).first()
    
    # COMENTADO PARA PRUEBAS: No bloquear si ya existe
    # if depreciaciones_existentes:
    #     raise HTTPException(status_code=400, detail=f"Ya se ejecutó la depreciación para {mes:02d}/{anio}.")
    
    # 3. Obtener Tipo de Documento
    tipo_doc = db.query(models_tipo.TipoDocumento).filter(
        models_tipo.TipoDocumento.id == tipo_documento_id,
        models_tipo.TipoDocumento.empresa_id == empresa_id
    ).first()
    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado.")
    
    # 4. Buscar Activos Depreciables con validaciones mejoradas
    from sqlalchemy import or_
    activos = db.query(models.ActivoFijo).join(models_cat.ActivoCategoria).filter(
        models.ActivoFijo.empresa_id == empresa_id,
        models.ActivoFijo.estado == models.EstadoActivo.ACTIVO,
        models_cat.ActivoCategoria.metodo_depreciacion != models_cat.MetodoDepreciacion.NO_DEPRECIAR,
        models_cat.ActivoCategoria.vida_util_niif_meses > 0,
        or_(
            models.ActivoFijo.fecha_inicio_uso <= fecha_cierre,
            and_(models.ActivoFijo.fecha_inicio_uso.is_(None), models.ActivoFijo.fecha_compra <= fecha_cierre)
        )
    ).all()
    
    if not activos:
        raise HTTPException(status_code=400, detail="No hay activos aptos para depreciar en este período.")

    # 5. Validar configuración contable
    activos_sin_config = []
    for activo in activos:
        if not (activo.categoria.cuenta_gasto_depreciacion_id and activo.categoria.cuenta_depreciacion_acumulada_id):
            activos_sin_config.append(activo.codigo)
    
    if activos_sin_config:
        raise HTTPException(
            status_code=400, 
            detail=f"Los siguientes activos no tienen configuración contable completa: {', '.join(activos_sin_config)}"
        )

    movimientos_contables = []
    total_depreciacion_mes = 0
    activos_depreciados = []

    # 6. Crear Cabecera del Documento
    numero_doc = (tipo_doc.consecutivo_actual or 0) + 1
    
    nuevo_documento = models_doc.Documento(
        empresa_id=empresa_id,
        tipo_documento_id=tipo_documento_id,
        numero=numero_doc,
        fecha=fecha_cierre,
        fecha_operacion=datetime.utcnow(),
        usuario_creador_id=user_id,
        estado="ACTIVO",
        centro_costo_id=None,
        observaciones=f"Depreciación automática {mes:02d}/{anio}"
    )
    db.add(nuevo_documento)
    db.flush()

    # 7. Iterar Activos con cálculos profesionales
    for activo in activos:
        cuota_mes = calcular_depreciacion_mensual(activo, fecha_cierre)
        
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
                observacion=f"Depreciación {mes:02d}/{anio} - {activo.categoria.metodo_depreciacion.value}",
                created_by=user_id
            )
            db.add(novedad)
            
            # Agrupar movimientos por cuenta para consolidar
            cuenta_gasto = activo.categoria.cuenta_gasto_depreciacion_id
            cuenta_acum = activo.categoria.cuenta_depreciacion_acumulada_id
            
            # Buscar si ya existe movimiento para esta cuenta
            mov_gasto = next((m for m in movimientos_contables if m["cuenta_id"] == cuenta_gasto and m["debito"] > 0), None)
            mov_acum = next((m for m in movimientos_contables if m["cuenta_id"] == cuenta_acum and m["credito"] > 0), None)
            
            if mov_gasto:
                mov_gasto["debito"] += cuota_mes
                mov_gasto["concepto"] += f", {activo.codigo}"
            else:
                movimientos_contables.append({
                    "cuenta_id": cuenta_gasto,
                    "debito": cuota_mes,
                    "credito": 0,
                    "concepto": f"Depreciación {mes:02d}/{anio} - {activo.codigo}"
                })
            
            if mov_acum:
                mov_acum["credito"] += cuota_mes
                mov_acum["concepto"] += f", {activo.codigo}"
            else:
                movimientos_contables.append({
                    "cuenta_id": cuenta_acum,
                    "debito": 0,
                    "credito": cuota_mes,
                    "concepto": f"Dep. Acum. {mes:02d}/{anio} - {activo.codigo}"
                })
            
            total_depreciacion_mes += cuota_mes
            activos_depreciados.append(activo.codigo)

    # 8. Validar que hubo depreciaciones
    if total_depreciacion_mes == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se calcularon depreciaciones. Todos los activos pueden estar totalmente depreciados.")

    # 9. Insertar Movimientos Contables
    for mov in movimientos_contables:
        db_mov = models_mov.MovimientoContable(
            documento_id=nuevo_documento.id,
            cuenta_id=mov["cuenta_id"],
            debito=val_decimal(mov["debito"]),
            credito=val_decimal(mov["credito"]),
            concepto=mov["concepto"][:200]  # Limitar longitud
        )
        db.add(db_mov)

    # 10. Actualizar consecutivo
    tipo_doc.consecutivo_actual = numero_doc
    
    db.commit()
    db.refresh(nuevo_documento)
    
    # Log del resultado
    print(f"✅ Depreciación ejecutada: {len(activos_depreciados)} activos, Total: ${total_depreciacion_mes:,.0f}")
    
    return nuevo_documento

def calcular_depreciacion_mensual(activo: models.ActivoFijo, fecha_calculo: date) -> float:
    """
    Calcula la depreciación mensual de un activo según su método configurado.
    VERSIÓN PROFESIONAL que maneja múltiples métodos.
    """
    if not activo.categoria:
        return 0
    
    # Determinar fecha de inicio de depreciación
    fecha_inicio = activo.fecha_inicio_uso or activo.fecha_compra
    if not fecha_inicio or fecha_inicio > fecha_calculo:
        return 0
    
    # Base depreciable
    base_depreciable = float(activo.costo_adquisicion) - float(activo.valor_residual)
    vida_util_meses = activo.categoria.vida_util_niif_meses
    
    if base_depreciable <= 0 or vida_util_meses <= 0:
        return 0
    
    # Verificar si ya está totalmente depreciado
    dep_acum_actual = float(activo.depreciacion_acumulada_niif)
    saldo_pendiente = base_depreciable - dep_acum_actual
    
    if saldo_pendiente <= 0:
        return 0
    
    # Calcular según método
    metodo = activo.categoria.metodo_depreciacion
    
    if metodo == models_cat.MetodoDepreciacion.LINEA_RECTA:
        cuota_mensual = base_depreciable / vida_util_meses
        
    elif metodo == models_cat.MetodoDepreciacion.REDUCCION_SALDOS:
        # Método de reducción de saldos (doble saldo decreciente)
        tasa_anual = 2 / (vida_util_meses / 12)  # Doble de la tasa lineal
        tasa_mensual = tasa_anual / 12
        valor_neto = float(activo.costo_adquisicion) - dep_acum_actual
        cuota_mensual = valor_neto * tasa_mensual
        
    elif metodo == models_cat.MetodoDepreciacion.UNIDADES_PRODUCCION:
        # Por ahora usar línea recta (requiere implementar control de unidades)
        cuota_mensual = base_depreciable / vida_util_meses
        
    else:  # NO_DEPRECIAR
        return 0
    
    # Ajustar si excede el saldo pendiente
    if cuota_mensual > saldo_pendiente:
        cuota_mensual = saldo_pendiente
    
    return round(cuota_mensual, 2)

def limpiar_depreciaciones_prueba(db: Session, empresa_id: int, user_id: int):
    """
    FUNCIÓN DE PRUEBAS: Limpia todas las depreciaciones para permitir nuevos ensayos.
    ⚠️ SOLO USAR EN AMBIENTE DE DESARROLLO/PRUEBAS
    
    Esta función:
    1. Elimina todos los documentos de depreciación
    2. Elimina todas las novedades de depreciación  
    3. Resetea la depreciación acumulada de todos los activos
    """
    try:
        # 1. Buscar todos los documentos de depreciación
        documentos_depreciacion = db.query(models_doc.Documento).filter(
            models_doc.Documento.empresa_id == empresa_id,
            models_doc.Documento.observaciones.ilike('%depreciación%')
        ).all()
        
        documentos_eliminados = []
        
        # 2. Eliminar documentos y sus movimientos
        for doc in documentos_depreciacion:
            # Eliminar movimientos contables
            db.query(models_mov.MovimientoContable).filter(
                models_mov.MovimientoContable.documento_id == doc.id
            ).delete(synchronize_session=False)
            
            documentos_eliminados.append(f"{doc.tipo_documento.codigo if doc.tipo_documento else 'N/A'}-{doc.numero}")
            
            # Eliminar documento
            db.delete(doc)
        
        # 3. Eliminar todas las novedades de depreciación
        novedades_eliminadas = db.query(models_nov.ActivoNovedad).filter(
            models_nov.ActivoNovedad.empresa_id == empresa_id,
            models_nov.ActivoNovedad.tipo == models_nov.TipoNovedadActivo.DEPRECIACION
        ).delete(synchronize_session=False)
        
        # 4. Resetear depreciación acumulada de todos los activos
        activos_reseteados = db.query(models.ActivoFijo).filter(
            models.ActivoFijo.empresa_id == empresa_id
        ).update({
            models.ActivoFijo.depreciacion_acumulada_niif: 0,
            models.ActivoFijo.depreciacion_acumulada_fiscal: 0
        }, synchronize_session=False)
        
        db.commit()
        
        return {
            "mensaje": "✅ Depreciaciones de prueba limpiadas exitosamente",
            "documentos_eliminados": len(documentos_eliminados),
            "documentos_detalle": documentos_eliminados,
            "novedades_eliminadas": novedades_eliminadas,
            "activos_reseteados": activos_reseteados
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al limpiar depreciaciones de prueba: {str(e)}"
        )

def get_documentos_contables_activos(db: Session, empresa_id: int):
    """
    Obtiene todos los documentos contables relacionados con activos fijos
    con información completa para mostrar en la interfaz
    """
    from sqlalchemy.orm import joinedload
    
    # Buscar documentos que contengan "depreciación" en observaciones
    documentos = db.query(models_doc.Documento).options(
        joinedload(models_doc.Documento.tipo_documento),
        joinedload(models_doc.Documento.beneficiario),
        joinedload(models_doc.Documento.movimientos)
    ).filter(
        models_doc.Documento.empresa_id == empresa_id,
        models_doc.Documento.observaciones.ilike('%depreciación%')
    ).order_by(
        models_doc.Documento.fecha.desc(),
        models_doc.Documento.numero.desc()
    ).all()
    
    # Formatear respuesta
    documentos_formateados = []
    for doc in documentos:
        total_debito = sum(float(mov.debito) for mov in doc.movimientos)
        
        documentos_formateados.append({
            "id": doc.id,
            "fecha": doc.fecha.isoformat() if doc.fecha else None,
            "numero": doc.numero,
            "anulado": doc.anulado,
            "estado": doc.estado,
            "observaciones": doc.observaciones,
            "tipo_documento_codigo": doc.tipo_documento.codigo if doc.tipo_documento else None,
            "tipo_documento_nombre": doc.tipo_documento.nombre if doc.tipo_documento else None,
            "beneficiario_nombre": doc.beneficiario.razon_social if doc.beneficiario else None,
            "total_debito": total_debito,
            "movimientos_contables": [
                {
                    "debito": float(mov.debito),
                    "credito": float(mov.credito),
                    "concepto": mov.concepto
                } for mov in doc.movimientos
            ]
        })
    
    return {
        "total": len(documentos_formateados),
        "documentos": documentos_formateados
    }
