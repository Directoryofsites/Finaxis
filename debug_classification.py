from app.core.database import SessionLocal
from app.services.propiedad_horizontal import pago_service
from app.models.propiedad_horizontal import PHUnidad
from app.models.documento import Documento, MovimientoContable
from sqlalchemy.orm import joinedload, selectinload
from datetime import date

def debug_classification():
    db = SessionLocal()
    try:
        # 1. Buscar unidad b 5 / 501
        unidad = db.query(PHUnidad).filter(PHUnidad.codigo.ilike("%5 / 501%")).first()
        if not unidad:
            print("No se encontro unidad especifica, buscando la primera...")
            unidad = db.query(PHUnidad).first()

        print(f"Debugueando Unidad: {unidad.codigo} ID: {unidad.id}")

        # 2. Configurar cuentas
        # Necesitamos simular la logica de cuentas_interes/multa
        # Copiamos logica de _simular_cronologia_pagos
        # Copiamos logica de _simular_cronologia_pagos
        from app.models.propiedad_horizontal import PHConfiguracion, PHConcepto
        
        # 1. Config Global
        config_ph = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == unidad.empresa_id).first()
        
        cuentas_interes = set()
        cuentas_multa = set()
        
        if config_ph and config_ph.cuenta_ingreso_intereses_id:
            cuentas_interes.add(config_ph.cuenta_ingreso_intereses_id)

        # 2. Conceptos
        conceptos = db.query(PHConcepto).filter(PHConcepto.empresa_id == unidad.empresa_id).all()
        for c in conceptos:
            if c.es_interes and c.cuenta_interes_id:
                cuentas_interes.add(c.cuenta_interes_id)
                if c.cuenta_ingreso_id: cuentas_interes.add(c.cuenta_ingreso_id)
            if "MULTA" in c.nombre.upper() or "SANCION" in c.nombre.upper():
                 if c.cuenta_ingreso_id: cuentas_multa.add(c.cuenta_ingreso_id)

        print(f"Cuentas Interes: {cuentas_interes}")
        print(f"Cuentas Multa: {cuentas_multa}")

        # 3. Obtener Docs
        docs = db.query(Documento).options(
            selectinload(Documento.movimientos).joinedload(MovimientoContable.cuenta),
            joinedload(Documento.tipo_documento),
            joinedload(Documento.unidad_ph)
        ).filter(
            Documento.empresa_id == unidad.empresa_id,
            Documento.unidad_ph_id == unidad.id,
            Documento.estado.in_(['ACTIVO', 'PROCESADO'])
        ).order_by(Documento.fecha.asc(), Documento.id.asc()).all()

        # 4. Iterar y Clasificar (Simulacion dummy)
        print("\n--- ANALISIS DE DOCUMENTOS ---")
        for doc in docs:
            print(f"\nDOC: {doc.tipo_documento.nombre} #{doc.numero} ({doc.fecha})")
            
            # Chequear cxc
            es_factura = False
            for mov in doc.movimientos:
                # Simplificado: si tiene credito en cuenta de ingreso
                tipo = 'CAPITAL'
                if mov.cuenta_id in cuentas_interes: tipo = 'INTERES'
                elif mov.cuenta_id in cuentas_multa: tipo = 'MULTA'
                elif "INTERES" in (mov.concepto or "").upper() or "MORA" in (mov.concepto or "").upper(): tipo = 'INTERES'
                elif "MULTA" in (mov.concepto or "").upper() or "SANCION" in (mov.concepto or "").upper(): tipo = 'MULTA'
                
                if mov.credito > 0:
                    priority = 0
                    if tipo == 'INTERES': priority = 1
                    elif tipo == 'MULTA': priority = 2
                    else: priority = 3
                    
                    print(f"  -> Credito: {mov.credito} | Concepto: '{mov.concepto}' | TIPO: {tipo} | PRIORITY: {priority}")
                    if priority == 3 and "INTERES" in (mov.concepto or "").upper():
                         print("     [warning] POSSIBLE MISCLASSIFICATION! Contains 'INTERES' but labeled CAPITAL?")

    finally:
        db.close()

if __name__ == "__main__":
    debug_classification()
