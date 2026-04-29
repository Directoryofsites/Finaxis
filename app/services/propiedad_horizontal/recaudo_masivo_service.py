from typing import List
import io
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.propiedad_horizontal.unidad import PHUnidad, PHTorre
from app.models.propiedad_horizontal.configuracion import PHConfiguracion
from app.models.propiedad_horizontal.concepto import PHConcepto
from app.schemas.propiedad_horizontal import recaudo_masivo as schemas_rm
from app.services.propiedad_horizontal import pago_service, configuracion_service
from app.models import TipoDocumento, Documento, MovimientoContable
from app.schemas import documento as doc_schemas
from app.services import documento as documento_service, cartera as cartera_service
from app.utils.sorting import natural_sort_key

def parse_asobancaria_2001(file_content: bytes) -> List[schemas_rm.RecaudoFila]:
    """
    Parsea un archivo plano en formato Asobancaria 2001.
    Estructura básica:
    - Registro de detalle (Tipo 06)
    - Referencia 1: Posiciones 17-64 (Depende del convenio, a veces es menos)
    - Valor: Posiciones 65-82 (14 enteros, 2 decimales)
    - Fecha: Posiciones 117-124 (AAAAMMDD)
    """
    filas = []
    content = file_content.decode('utf-8', errors='ignore')
    lines = content.splitlines()
    
    for i, line in enumerate(lines):
        if not line.startswith('06'): # Registro de detalle
            continue
            
        try:
            # Referencia 1 (Suele ser de 48 chars, pero el ID real suele estar al inicio)
            # En muchos casos de PH es de 10-15 chars
            referencia_raw = line[16:64].strip()
            
            # Valor (18 chars, los últimos 2 son decimales)
            valor_raw = line[64:82].strip()
            monto = Decimal(valor_raw) / 100
            
            # Fecha (AAAAMMDD)
            fecha_raw = line[116:124].strip()
            fecha = datetime.strptime(fecha_raw, '%Y%m%d').date()
            
            filas.append(schemas_rm.RecaudoFila(
                referencia=referencia_raw,
                fecha=fecha,
                monto=monto,
                descripcion="Recaudo Asobancaria 2001",
                line_number=i + 1
            ))
        except Exception as e:
            # Ignorar líneas mal formadas
            continue
            
    return filas

def parse_recaudo_file(file_content: bytes, file_name: str) -> List[schemas_rm.RecaudoFila]:
    """
    Parsea un archivo detectando su formato (CSV, Excel o Asobancaria .TXT).
    """
    try:
        if file_name.lower().endswith('.txt'):
            # Intentar Asobancaria 2001
            return parse_asobancaria_2001(file_content)
            
        if file_name.lower().endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_name.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Formato no soportado. Use .csv, .xls, .xlsx o .txt (Asobancaria)")
        
        # Normalizar nombres de columnas
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Mapeo flexible
        col_ref = next((c for c in df.columns if any(x in c for x in ['ref', 'cod', 'iden', 'torre', 'apto'])), None)
        col_fecha = next((c for c in df.columns if any(x in c for x in ['fecha', 'date'])), None)
        col_monto = next((c for c in df.columns if any(x in c for x in ['monto', 'valor', 'pago', 'total'])), None)
        col_desc = next((c for c in df.columns if any(x in c for x in ['desc', 'det', 'obs'])), None)
        
        if not col_ref or not col_fecha or not col_monto:
            raise ValueError(f"No se identificaron las columnas requeridas (Referencia, Fecha, Monto). Columnas: {list(df.columns)}")
            
        filas = []
        for index, row in df.iterrows():
            try:
                referencia = str(row[col_ref]).strip()
                if pd.isna(row[col_ref]) or not referencia:
                    continue
                    
                raw_fecha = row[col_fecha]
                if pd.isna(raw_fecha):
                    fecha = date.today()
                elif isinstance(raw_fecha, (datetime, date)):
                    fecha = raw_fecha if isinstance(raw_fecha, date) else raw_fecha.date()
                else:
                    fecha = pd.to_datetime(raw_fecha, dayfirst=True).date()
                
                raw_monto = row[col_monto]
                if pd.isna(raw_monto): continue
                if isinstance(raw_monto, str):
                    raw_monto = raw_monto.replace('$', '').replace(',', '').strip()
                monto = Decimal(str(raw_monto))
                
                desc = str(row[col_desc]).strip() if col_desc and not pd.isna(row[col_desc]) else None
                
                filas.append(schemas_rm.RecaudoFila(
                    referencia=referencia,
                    fecha=fecha,
                    monto=monto,
                    descripcion=desc,
                    line_number=index + 1
                ))
            except:
                continue
                
        return filas
    except Exception as e:
        raise ValueError(f"Error parseando el archivo: {str(e)}")

def generar_preview(db: Session, empresa_id: int, filas: List[schemas_rm.RecaudoFila]) -> schemas_rm.RecaudoPreviewResult:
    detalles = []
    total_recaudado = Decimal('0.0')
    filas_validas = 0
    filas_error = 0
    
    # 1. OPTIMIZACIÓN: Carga masiva de unidades para mapeo rápido
    unidades_db = db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id, PHUnidad.activo == True).all()
    map_por_ref = {u.referencia_recaudo.strip().lower(): u for u in unidades_db if u.referencia_recaudo}
    map_por_codigo = {u.codigo.strip().lower(): u for u in unidades_db if u.codigo}

    # 2. OPTIMIZACIÓN "CAPA ESTÁTICA": Obtener saldos de TODAS las unidades de la empresa de una vez
    from app.models.movimiento_contable import MovimientoContable
    from app.models.documento import Documento
    from sqlalchemy import func

    # Identificar cuentas de cartera para el cálculo masivo
    config = configuracion_service.get_configuracion(db, empresa_id)
    cuentas_cxc_ids = cartera_service.get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    cuentas_validas = set(cuentas_cxc_ids)
    if config and config.cuenta_anticipos_id:
        cuentas_validas.add(config.cuenta_anticipos_id)

    saldos_raw = db.query(
        Documento.unidad_ph_id,
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label('saldo')
    ).join(MovimientoContable, Documento.id == MovimientoContable.documento_id)\
     .filter(
         Documento.empresa_id == empresa_id,
         Documento.estado.in_(['ACTIVO', 'PROCESADO']),
         MovimientoContable.cuenta_id.in_(list(cuentas_validas))
     ).group_by(Documento.unidad_ph_id).all()

    map_saldos = {s.unidad_ph_id: Decimal(str(s.saldo or 0)) for s in saldos_raw}
    
    for fila in filas:
        match_info = schemas_rm.RecaudoMatch(
            line_number=fila.line_number,
            referencia=fila.referencia,
            fecha_pago=fila.fecha,
            monto_recibido=fila.monto,
            is_valid=False
        )
        
        ref_busqueda = fila.referencia.lower()
        unidad = map_por_ref.get(ref_busqueda) or map_por_codigo.get(ref_busqueda)
            
        if not unidad:
            match_info.error_msg = f"No se encontró unidad con referencia '{fila.referencia}'"
            filas_error += 1
            detalles.append(match_info)
            continue
            
        match_info.unidad_id = unidad.id
        match_info.unidad_codigo = f"{unidad.torre.nombre if unidad.torre else ''} - {unidad.codigo}"
        match_info.unidad_propietario = unidad.propietario_nombre
        
        try:
            # OPTIMIZACIÓN: Usar el saldo del mapa pre-cargado en lugar de llamar al servicio N veces
            deuda = map_saldos.get(unidad.id, Decimal('0.0'))
            match_info.deuda_total = deuda
            
            if fila.monto > deuda:
                match_info.monto_a_aplicar = deuda
                match_info.excedente_anticipo = fila.monto - deuda
            else:
                match_info.monto_a_aplicar = fila.monto
                match_info.excedente_anticipo = Decimal('0.0')
                
            match_info.is_valid = True
            filas_validas += 1
            total_recaudado += fila.monto
            
        except Exception as e:
            match_info.error_msg = f"Error financiero: {str(e)}"
            filas_error += 1
            
        detalles.append(match_info)
        
    detalles.sort(key=lambda x: natural_sort_key(x.unidad_codigo or ""))
        
    return schemas_rm.RecaudoPreviewResult(
        total_filas=len(filas),
        filas_validas=filas_validas,
        filas_error=filas_error,
        total_recaudado=total_recaudado,
        detalles=detalles
    )

def procesar_lote_pagos(db: Session, empresa_id: int, request: schemas_rm.RecaudoProcessRequest, usuario_id: int) -> schemas_rm.RecaudoProcessResponse:
    exitosos = 0
    fallidos = 0
    errores = []
    
    # OPTIMIZACIÓN: Cargar configuración y tipos de documento FUERA del bucle
    config = configuracion_service.get_configuracion(db, empresa_id)
    tipo_doc_recibo = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_recibo_id).first()
    
    if not config.cuenta_cartera_id and (not tipo_doc_recibo or not tipo_doc_recibo.cuenta_debito_cxc_id):
        raise ValueError("No se ha configurado la cuenta de cartera (1305).")

    cuenta_cxc_global = config.cuenta_cartera_id or tipo_doc_recibo.cuenta_debito_cxc_id
    cuenta_anticipos_global = config.cuenta_anticipos_id

    filas_a_procesar = [f for f in request.filas if f.is_valid and f.unidad_id]
    
    # Mapear unidades necesarias para evitar consultas individuales
    unidades_ids = {f.unidad_id for f in filas_a_procesar}
    unidades_map = {u.id: u for u in db.query(PHUnidad).filter(PHUnidad.id.in_(unidades_ids)).all()}

    # --- OPTIMIZACIÓN LOTE ---
    cuentas_cxc_batch = cartera_service.get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    cuentas_cxp_batch = cartera_service.get_cuentas_especiales_ids(db, empresa_id, 'cxp')
    conceptos_ph_batch = db.query(PHConcepto).filter(
        PHConcepto.empresa_id == empresa_id,
        PHConcepto.activo == True
    ).order_by(db.func.coalesce(PHConcepto.orden, 999).asc(), PHConcepto.id.asc()).all()
    # -------------------------
    terceros_a_recalcular = set()

    for fila in filas_a_procesar:
        try:
            unidad = unidades_map.get(fila.unidad_id)
            if not unidad: continue
            
            monto_cartera = fila.monto_a_aplicar
            monto_anticipo = fila.excedente_anticipo
            
            movimientos = []
            # 1. Entrada a Banco
            movimientos.append(doc_schemas.MovimientoContableCreate(
                cuenta_id=request.cuenta_bancaria_id,
                concepto=f"Recaudo Masivo {unidad.codigo} - {fila.referencia}",
                debito=fila.monto_recibido,
                credito=0
            ))
            
            # 2. Crédito a Cartera
            if monto_cartera > 0:
                movimientos.append(doc_schemas.MovimientoContableCreate(
                    cuenta_id=cuenta_cxc_global,
                    concepto=f"Abono Cartera {unidad.codigo}",
                    debito=0,
                    credito=monto_cartera
                ))
            
            # 3. Crédito a Anticipos (El excedente)
            if monto_anticipo > 0:
                if not cuenta_anticipos_global:
                    # Si no hay cuenta de anticipos, todo va a cartera
                    if movimientos[-1].cuenta_id == cuenta_cxc_global:
                        movimientos[-1].credito += monto_anticipo
                    else:
                        movimientos.append(doc_schemas.MovimientoContableCreate(
                            cuenta_id=cuenta_cxc_global,
                            concepto=f"Excedente Cartera {unidad.codigo}",
                            debito=0,
                            credito=monto_anticipo
                        ))
                else:
                    movimientos.append(doc_schemas.MovimientoContableCreate(
                        cuenta_id=cuenta_anticipos_global,
                        concepto=f"Excedente Recaudo -> Anticipo {unidad.codigo}",
                        debito=0,
                        credito=monto_anticipo
                    ))
            
            # Crear el documento
            doc_create = doc_schemas.DocumentoCreate(
                empresa_id=empresa_id,
                tipo_documento_id=config.tipo_documento_recibo_id,
                numero=0,
                fecha=fila.fecha_pago,
                fecha_vencimiento=fila.fecha_pago,
                beneficiario_id=unidad.propietario_principal_id,
                observaciones=f"Recaudo Masivo Automatizado - Unidad {unidad.codigo}",
                movimientos=movimientos,
                unidad_ph_id=unidad.id
            )
            
            # skip_recalculo=True es CLAVE aquí para que no se dispare el motor contable en cada inserción
            new_doc = documento_service.create_documento(db, doc_create, user_id=usuario_id, skip_recalculo=True)
            
            # Guardamos el tercero para procesarlo al final
            if unidad.propietario_principal_id:
                terceros_a_recalcular.add(unidad.propietario_principal_id)
            
            exitosos += 1
        except Exception as e:
            fallidos += 1
            errores.append(f"Fila {fila.line_number}: {str(e)}")
            
    # --- PROCESAMIENTO FINAL (FUERA DEL BUCLE) ---
    # Ahora sí, recalculamos una sola vez por cada tercero involucrado
    for t_id in terceros_a_recalcular:
        try:
            cartera_service.recalcular_aplicaciones_tercero(
                db, 
                t_id, 
                empresa_id,
                injected_cuentas_cxc=cuentas_cxc_batch,
                injected_cuentas_cxp=cuentas_cxp_batch,
                injected_conceptos_ph=conceptos_ph_batch
            )
        except:
            pass # No bloqueamos el commit por un error de aplicación

    db.commit()
    mensaje = f"Lote procesado: {exitosos} exitosos, {fallidos} fallidos."
        
    return schemas_rm.RecaudoProcessResponse(
        exitosos=exitosos,
        fallidos=fallidos,
        errores=errores,
        mensaje=mensaje
    )

def generar_archivo_asobancaria_test(db: Session, empresa_id: int) -> str:
    """
    Genera un archivo plano Asobancaria 2001 representativo de la cartera actual.
    OPTIMIZACIÓN: Usa una sola consulta para obtener todos los saldos en lugar de N consultas.
    """
    from app.models.movimiento_contable import MovimientoContable
    from app.models.documento import Documento
    from sqlalchemy import func

    # 1. Obtener Unidades
    unidades = db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id, PHUnidad.activo == True).all()
    if not unidades:
        return ""

    # 2. OPTIMIZACIÓN "CAPA ESTÁTICA": Obtener configuración una sola vez
    config = configuracion_service.get_configuracion(db, empresa_id)
    cuentas_cxc_ids = cartera_service.get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    cuentas_validas = set(cuentas_cxc_ids)
    if config and config.cuenta_anticipos_id:
        cuentas_validas.add(config.cuenta_anticipos_id)

    # 3. BATCH QUERY: Obtener saldos de todas las unidades en una sola pasada
    # Sumamos (debito - credito) de los movimientos en cuentas de cartera agrupados por unidad
    saldos_raw = db.query(
        Documento.unidad_ph_id,
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label('saldo')
    ).join(MovimientoContable, Documento.id == MovimientoContable.documento_id)\
     .filter(
         Documento.empresa_id == empresa_id,
         Documento.estado.in_(['ACTIVO', 'PROCESADO']),
         MovimientoContable.cuenta_id.in_(list(cuentas_validas))
     ).group_by(Documento.unidad_ph_id).all()

    map_saldos = {s.unidad_ph_id: s.saldo for s in saldos_raw}

    hoy = datetime.now()
    fecha_str = hoy.strftime('%Y%m%d')
    lines = []
    
    # Registro de Control (Tipo 01) - Header
    nit = "900000000"
    header = f"01{nit.zfill(10)}{' ' * 150}"
    lines.append(header[:162])
    
    total_monto = Decimal('0.0')
    count = 0
    
    for u in unidades:
        # Consultamos el "caché local" (map_saldos) en lugar de llamar a pago_service (DB)
        deuda = map_saldos.get(u.id, Decimal('0.0'))
        
        if deuda <= 0:
            continue
            
        count += 1
        total_monto += deuda
        
        referencia = (u.referencia_recaudo or u.codigo or "").ljust(48)
        valor_str = str(int(deuda * 100)).zfill(18)
        
        # Construir línea de detalle (162 caracteres)
        line_content = f"06{'0' * 14}{referencia}{valor_str}{'0' * 34}{fecha_str}{' ' * 38}"
        lines.append(line_content[:162])
        
    # Registro de Control (Tipo 09) - Footer
    footer = f"09{str(count).zfill(9)}{str(int(total_monto * 100)).zfill(18)}{' ' * 135}"
    lines.append(footer[:162])
    
    return "\n".join(lines)
