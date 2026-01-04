import sys
import os
sys.path.append(r"c:\ContaPY2")
from datetime import date
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.documento import Documento
from app.services.libros_oficiales import get_data_for_analisis_cuenta_por_documento, generate_analisis_cuenta_por_documento_pdf

def verify_analysis_doc():
    db: Session = SessionLocal()
    try:
        # 1. Emp y Fechas
        empresas = db.query(Empresa).all()
        empresa = None
        for emp in empresas:
             max_date = db.query(Documento.fecha).filter(Documento.empresa_id == emp.id).order_by(Documento.fecha.desc()).first()
             if max_date:
                 empresa = emp
                 break
        
        if not empresa or not max_date:
            print("No documents found in any company.")
            return

        fecha_fin = max_date[0]
        fecha_inicio = fecha_fin.replace(day=1)
        
        print(f"Testing Analysis Account Doc for: {empresa.razon_social}")
        print(f"Range: {fecha_inicio} to {fecha_fin}")
        
        # 2. Test JSON Data
        data = get_data_for_analisis_cuenta_por_documento(db, empresa.id, fecha_inicio, fecha_fin)
        print(f"JSON Data Keys: {data.keys()}")
        print(f"Cuentas Found: {len(data['cuentas'])}")
        
        if len(data['cuentas']) > 0:
            first_account = data['cuentas'][0]
            print(f"Sample Account: {first_account['cuenta_codigo']} - {first_account['cuenta_nombre']}")
            print(f"Mov Types: {len(first_account['movimientos_por_tipo'])}")
            if len(first_account['movimientos_por_tipo']) > 0:
                 m = first_account['movimientos_por_tipo'][0]
                 print(f"  - {m['tipo_nombre']}: D: {m['debito']}, C: {m['credito']}")

        # 3. Test PDF
        pdf_bytes = generate_analisis_cuenta_por_documento_pdf(db, empresa.id, fecha_inicio, fecha_fin)
        if pdf_bytes and len(pdf_bytes) > 2000:
            print(f"SUCCESS: PDF Generated ({len(pdf_bytes)} bytes)")
        else:
            print("FAILED: PDF size suspicious.")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_analysis_doc()
