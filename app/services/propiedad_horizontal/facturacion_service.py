from sqlalchemy.orm import Session
from datetime import date
from typing import List, Dict, Any

from app.models.propiedad_horizontal import PHUnidad, PHConfiguracion, PHConcepto
from app.models.documento import Documento, MovimientoContable
from app.models.tipo_documento import TipoDocumento
from app.models.plan_cuenta import PlanCuenta
from app.services import documento as documento_service
from app.schemas import documento as doc_schemas
from fastapi import HTTPException

def generar_facturacion_masiva(db: Session, empresa_id: int, fecha_factura: date, usuario_id: int, conceptos_ids: List[int] = None):
    # 1. Obtener Configuración
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    # Nota: Ya no es estrictamente obligatorio el global si los conceptos tienen el suyo
    
    # 2. Obtener Conceptos Activos
    query = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id, PHConcepto.activo == True)
    
    # Filtrar por IDs seleccionados si se proporcionan
    if conceptos_ids:
        query = query.filter(PHConcepto.id.in_(conceptos_ids))
        
    conceptos = query.all()
    if not conceptos:
        raise HTTPException(status_code=400, detail="No hay conceptos de cobro activos (o seleccionados) para facturar.")

    # 3. Pre-cargar Cuentas Contables de los Conceptos (Optimización)
    cuentas_map = {} # Codigo -> ID
    for concepto in conceptos:
        if concepto.codigo_contable:
            cuenta = db.query(PlanCuenta).filter(
                PlanCuenta.empresa_id == empresa_id, 
                PlanCuenta.codigo == concepto.codigo_contable
            ).first()
            if cuenta:
                cuentas_map[concepto.codigo_contable] = cuenta.id

    # 4. Obtener Unidades Activas con Propietario
    unidades = db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id, PHUnidad.activo == True).all()
    
    resultados = {
        "generadas": 0,
        "errores": 0,
        "detalles": []
    }

    # 5. Agrupar Conceptos por Tipo de Documento
    # Esto permite que si un concepto usa Doc A y otro Doc B, se generen 2 facturas.
    # Si no tiene tipo_doc especifico, usar el Global.
    conceptos_por_doc = {} # tipo_doc_id -> [conceptos] (Usar Global si id es None)
    
    global_doc_id = config.tipo_documento_factura_id if config else None

    for c in conceptos:
        tid = c.tipo_documento_id if c.tipo_documento_id else global_doc_id
        if not tid:
             # Concepto sin tipo y sin global -> Skip o Error
             continue
        if tid not in conceptos_por_doc:
            conceptos_por_doc[tid] = []
        conceptos_por_doc[tid].append(c)

    # 6. Iterar Unidades y Generar Facturas (Una por cada Tipo Doc necesario)
    for unidad in unidades:
        try:
            if not unidad.propietario_principal_id:
                resultados["errores"] += 1
                resultados["detalles"].append(f"Unidad {unidad.codigo}: Sin propietario asignado.")
                continue

            # Iterar sobre los grupos de Documentos identificados
            for doc_type_id, lista_conceptos in conceptos_por_doc.items():
                
                # Obtener Tipo Doc
                tipo_doc_obj = db.query(TipoDocumento).filter(TipoDocumento.id == doc_type_id).first()
                if not tipo_doc_obj:
                    resultados["errores"] += 1 
                    continue

                movimientos = []
                total_factura = 0
                
                # Procesar conceptos de este grupo
                for concepto in lista_conceptos:
                    valor_linea = 0
                    if concepto.tipo_calculo == 'FIJO':
                        valor_linea = float(concepto.valor_defecto)
                    elif concepto.tipo_calculo == 'COEFICIENTE':
                        valor_linea = float(concepto.valor_defecto) * float(unidad.coeficiente)
                    
                    if valor_linea > 0:
                        # 1. Credito (Ingreso)
                        cuenta_ingreso_id = cuentas_map.get(concepto.codigo_contable)
                        if not cuenta_ingreso_id:
                            # Fallback o skip
                            continue

                        movimientos.append(doc_schemas.MovimientoContableCreate(
                            cuenta_id=cuenta_ingreso_id,
                            concepto=f"{concepto.nombre} - {fecha_factura.strftime('%B %Y')}",
                            debito=0,
                            credito=valor_linea,
                            centro_costo_id=None # Configurable si se requiere
                        ))
                        
                        # 2. Debito (Cartera) - ESPECIFICO DEL CONCEPTO
                        # Aqui está la magia: Cada concepto aporta su propia cuenta de cartera
                        cuenta_cartera_id = concepto.cuenta_cartera_id
                        if not cuenta_cartera_id:
                             # Fallback a Config Global -> Fallback a Tipo Doc
                             cuenta_cartera_id = config.cuenta_cartera_id if config else None
                             if not cuenta_cartera_id:
                                 cuenta_cartera_id = tipo_doc_obj.cuenta_debito_cxc_id
                        
                        if not cuenta_cartera_id:
                            raise Exception(f"Concepto {concepto.nombre} no tiene Cuenta Cartera definida.")

                        movimientos.append(doc_schemas.MovimientoContableCreate(
                            cuenta_id=cuenta_cartera_id,
                            concepto=f"CxC {concepto.nombre} - {unidad.codigo}",
                            debito=valor_linea,
                            credito=0
                        ))
                        
                        total_factura += valor_linea

                if total_factura > 0:
                    # Crear Documento
                    # Usamos una observacion generica o personalizada
                    obs = f"Factura {tipo_doc_obj.nombre} - PH Unidad {unidad.codigo}"
                    if config and config.mensaje_factura:
                         obs += f" | {config.mensaje_factura}"

                    doc_create = doc_schemas.DocumentoCreate(
                        empresa_id=empresa_id,
                        tipo_documento_id=doc_type_id,
                        numero=0, 
                        fecha=fecha_factura,
                        fecha_vencimiento=fecha_factura, 
                        beneficiario_id=unidad.propietario_principal_id,
                        observaciones=obs,
                        movimientos=movimientos
                    )
                    
                    new_doc = documento_service.create_documento(db, doc_create, user_id=usuario_id)
                    resultados["generadas"] += 1
                    resultados["detalles"].append(f"Unidad {unidad.codigo}: Doc {new_doc.numero} ({tipo_doc_obj.codigo}) por ${total_factura:,.0f}")

        except Exception as e:
            resultados["errores"] += 1
            resultados["detalles"].append(f"Unidad {unidad.codigo}: Error - {str(e)}")
            continue

    return resultados
