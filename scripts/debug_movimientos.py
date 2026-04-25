"""
Script de diagnóstico: muestra los textos EXACTOS en MovimientoContable
para las facturas PH de una unidad, junto con las cuentas y montos.
Ejecutar: .venv\Scripts\python.exe -m scripts.debug_movimientos
"""
from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()
try:
    # Buscar las últimas facturas PH (tipo FPH)
    facturas = db.execute(text("""
        SELECT d.id, d.numero, d.fecha, d.unidad_ph_id
        FROM documentos d
        JOIN tipos_documento td ON td.id = d.tipo_documento_id
        WHERE td.codigo IN ('FPH','FFPH')
        AND d.anulado = false
        ORDER BY d.fecha DESC, d.id DESC
        LIMIT 10
    """)).fetchall()

    print(f"\n{'='*80}")
    print(f"ÚLTIMAS FACTURAS PH")
    print(f"{'='*80}")
    for fac in facturas:
        print(f"\nFACTURA ID={fac.id} | Num={fac.numero} | Fecha={fac.fecha} | Unidad={fac.unidad_ph_id}")
        
        movs = db.execute(text("""
            SELECT mc.id, mc.cuenta_id, pc.codigo as cuenta_cod, pc.nombre as cuenta_nom,
                   mc.debito, mc.credito, mc.concepto
            FROM movimientos_contables mc
            LEFT JOIN plan_cuentas pc ON pc.id = mc.cuenta_id
            WHERE mc.documento_id = :doc_id
            ORDER BY mc.id
        """), {"doc_id": fac.id}).fetchall()
        
        for m in movs:
            tipo = "DB" if (m.debito or 0) > 0 else "CR"
            monto = m.debito if (m.debito or 0) > 0 else m.credito
            print(f"  [{tipo}] ${monto:>10.0f} | Cta: {m.cuenta_cod} | TEXTO: '{m.concepto}'")

    # También buscar recibos PH recientes
    print(f"\n{'='*80}")
    print(f"ÚLTIMOS RECIBOS PH (pagos)")
    print(f"{'='*80}")
    recibos = db.execute(text("""
        SELECT d.id, d.numero, d.fecha, d.unidad_ph_id
        FROM documentos d
        JOIN tipos_documento td ON td.id = d.tipo_documento_id
        WHERE td.codigo IN ('RPH','RRPH','RC','RRC')
        AND d.anulado = false
        ORDER BY d.fecha DESC, d.id DESC
        LIMIT 5
    """)).fetchall()

    for rec in recibos:
        print(f"\nRECIBO ID={rec.id} | Num={rec.numero} | Fecha={rec.fecha}")
        movs = db.execute(text("""
            SELECT mc.cuenta_id, pc.codigo as cuenta_cod,
                   mc.debito, mc.credito, mc.concepto
            FROM movimientos_contables mc
            LEFT JOIN plan_cuentas pc ON pc.id = mc.cuenta_id
            WHERE mc.documento_id = :doc_id
            ORDER BY mc.id
        """), {"doc_id": rec.id}).fetchall()
        for m in movs:
            tipo = "DB" if (m.debito or 0) > 0 else "CR"
            monto = m.debito if (m.debito or 0) > 0 else m.credito
            print(f"  [{tipo}] ${monto:>10.0f} | Cta: {m.cuenta_cod} | TEXTO: '{m.concepto}'")

finally:
    db.close()
