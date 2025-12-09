from sqlalchemy.orm import Session, joinedload, selectinload
from fastapi import HTTPException
from app.models.propiedad_horizontal import PHUnidad, PHConfiguracion
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.tipo_documento import TipoDocumento
from app.services import cartera as cartera_service
from app.services import documento as documento_service
from app.schemas import documento as doc_schemas
from app.core.constants import FuncionEspecial
from datetime import date

def get_estado_cuenta_unidad(db: Session, unidad_id: int, empresa_id: int):
    # 1. Obtener Unidad y Propietario
    unidad = db.query(PHUnidad).filter(PHUnidad.id == unidad_id, PHUnidad.empresa_id == empresa_id).first()
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    
    if not unidad.propietario_principal_id:
        return {"unidad": unidad.codigo, "propietario": "Sin Propietario", "saldo_total": 0, "facturas_pendientes": []}

    # 2. Consultar Cartera del Propietario
    # OJO: Esto trae TODA la deuda del tercero. Si tuviera multiples unidades, se mezcla.
    # Idealmente filtraríamos por un campo en el documento, pero por ahora asumimos 1 propietario -> N unidades (o deuda global).
    
    # IMPORTANTE: Forzamos el recálculo de cruces para asegurar que la vista esté actualizada
    # con cualquier cambio de lógica o documento nuevo que no haya disparado el trigger.
    cartera_service.recalcular_aplicaciones_tercero(db, unidad.propietario_principal_id, empresa_id)
    
    facturas_pendientes = cartera_service.get_facturas_pendientes_por_tercero(db, unidad.propietario_principal_id, empresa_id)
    
    saldo_total = sum(f['saldo_pendiente'] for f in facturas_pendientes)

    return {
        "unidad": unidad.codigo,
        "propietario_id": unidad.propietario_principal_id,
        "propietario_nombre": unidad.propietario_principal.razon_social if unidad.propietario_principal else "Desconocido",
        "saldo_total": saldo_total,
        "facturas_pendientes": facturas_pendientes
    }

def get_historial_cuenta_unidad(db: Session, unidad_id: int, empresa_id: int):
    # 1. Obtener Datos Básicos
    unidad = db.query(PHUnidad).filter(PHUnidad.id == unidad_id, PHUnidad.empresa_id == empresa_id).first()
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    
    tercero_id = unidad.propietario_principal_id
    if not tercero_id:
         return {"unidad": unidad, "transacciones": [], "saldo_actual": 0}

    # 2. Consultar Movimientos
    # Buscamos Documentos donde el beneficiario sea el propietario
    # Y que sean de tipos de documento de CXC (Factura o Recibo)
    
    docs = db.query(Documento).options(
        joinedload(Documento.tipo_documento),
        selectinload(Documento.movimientos).joinedload(MovimientoContable.cuenta)
    ).filter(
        Documento.empresa_id == empresa_id,
        Documento.beneficiario_id == tercero_id,
        Documento.estado.in_(['ACTIVO', 'PROCESADO'])
    ).order_by(Documento.fecha.asc(), Documento.id.asc()).all()

    # 3. Construir Historial
    transacciones = []
    saldo = 0
    
    # Identificar cuentas de cartera validas (incluyendo la configurada en PH)
    cuentas_cxc_ids = cartera_service.get_cuentas_especiales_ids(db, empresa_id, 'cxc')

    for doc in docs:
        # Calcular impacto en cartera de este documento
        # Usamos los movimientos del documento.
        
        impacto_cxc = 0
        for mov in doc.movimientos:
            # Si la cuenta está en el grupo de Cartera (13, 16 config, etc)
            if mov.cuenta_id in cuentas_cxc_ids:
                impacto_cxc += (mov.debito - mov.credito)
        
        if impacto_cxc != 0:
            saldo += impacto_cxc
            transacciones.append({
                "fecha": doc.fecha,
                "documento": f"{doc.tipo_documento.codigo} - {doc.numero}",
                "tipo": doc.tipo_documento.nombre,
                "detalle": doc.observaciones,
                "cargo": impacto_cxc if impacto_cxc > 0 else 0,
                "abono": abs(impacto_cxc) if impacto_cxc < 0 else 0,
                "saldo": saldo
            })

    return {
        "unidad": unidad,
        "propietario": unidad.propietario_principal,
        "transacciones": transacciones,
        "saldo_actual": saldo
    }

def registrar_pago_unidad(db: Session, unidad_id: int, empresa_id: int, usuario_id: int, monto: float, fecha_pago: date, forma_pago_id: int = None):
    # 1. Validaciones
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0.")
    
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    if not config or not config.tipo_documento_recibo_id:
        raise HTTPException(status_code=400, detail="No se ha configurado el Tipo de Documento para Recibos de Caja en PH.")

    tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_recibo_id).first()
    if not tipo_doc:
         raise HTTPException(status_code=404, detail="Tipo de Documento de Recibo no encontrado.")

    estado_cuenta = get_estado_cuenta_unidad(db, unidad_id, empresa_id)
    if not estado_cuenta['propietario_id']:
        raise HTTPException(status_code=400, detail="La unidad no tiene propietario asignado para registrar el pago.")

    # 2. Crear Movimientos Contables
    movimientos = []
    
    # A. Débito (Entrada de Dinero - Caja/Banco)
    # PRIORIDAD: Usar Cuenta Caja de PH Config
    cuenta_caja_final = config.cuenta_caja_id
    
    if not cuenta_caja_final:
        # Fallback: Usar cuenta debito del tipo doc (si se usa para eso, aunque logicamente es variable)
        # O mejor, requerir configuración centralizada para evitar ambigüedades.
        # Por compatibilidad, intentamos la del tipo doc.
        cuenta_caja_final = tipo_doc.cuenta_debito_cxc_id # A veces lo ponen aqui? No, seria debito_cxc. 
        # En RC, Debito es Caja.
        if not cuenta_caja_final:
             # Si no hay config central ni en doc -> fallback a una caja por defecto (ej. 110505) si pudiéramos adivinarla, pero mejor error.
             # Pero para ser amigables, si el usuario usó la cuenta DEBITO (Cartera) del tipo doc como Caja? (Error común).
             pass
    
    if not cuenta_caja_final:
         raise HTTPException(status_code=400, detail="No se encontró cuenta de Caja/Bancos. Configure 'Cuenta Caja' en Parámetros PH.")

    # B. Crédito a Cartera (Disminuye deuda)
    # PRIORIDAD: Usar Cuenta Cartera de PH Config
    cuenta_cartera_final = config.cuenta_cartera_id
    
    if not cuenta_cartera_final:
        # Fallback Tipo Doc
        cuenta_cartera_final = tipo_doc.cuenta_credito_cxc_id
    
    if not cuenta_cartera_final:
        raise HTTPException(status_code=400, detail="No se encontró cuenta de Cartera. Configure 'Cuenta Cartera' en Parámetros PH.")
    
    # Agregar Movimiento Crédito (Abono a Cartera)
    movimientos.append(doc_schemas.MovimientoContableCreate(
        cuenta_id=cuenta_cartera_final,
        concepto=f"Abono/Pago Unidad {estado_cuenta['unidad']}",
        debito=0,
        credito=monto
    ))

    # C. Agregar Movimiento Débito (Entra a Caja)
    # OJO: Anteriormente estaba implícito o faltaba en el snippet, aqui lo agrego explicito.
    movimientos.append(doc_schemas.MovimientoContableCreate(
        cuenta_id=cuenta_caja_final,
        concepto=f"Ingreso Pago Unidad {estado_cuenta['unidad']}",
        debito=monto,
        credito=0
    ))

    # C. Débito a Caja (Entra dinero)
    # Necesitamos una cuenta de caja. 
    # VOY A ASUMIR que por ahora usamos la cuenta DEBITO del mismo tipo de documento si está configurada, sino ERROR.

    # 3. Crear Documento
    doc_create = doc_schemas.DocumentoCreate(
        empresa_id=empresa_id,
        tipo_documento_id=tipo_doc.id,
        numero=0,
        fecha=fecha_pago,
        beneficiario_id=estado_cuenta['propietario_id'],
        observaciones=f"Pago PH Unidad {estado_cuenta['unidad']}",
        movimientos=movimientos
    )

    new_doc = documento_service.create_documento(db, doc_create, user_id=usuario_id)

    # 4. Integridad: El servicio create_documento YA llama a 'cartera_service.recalcular_aplicaciones_tercero'
    # si el tipo_doc tiene funcion especial RC_CLIENTE.
    # Así que las facturas se cruzarán automáticamente FIFO dentro del create_documento.

    return new_doc
