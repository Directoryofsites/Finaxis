import sys
import os
sys.path.append(r"c:\ContaPY2")
from datetime import date
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.documento import Documento
from app.services.libros_oficiales import generate_libro_mayor_y_balances_pdf

def verify_mayor_pdf_generation():
    db: Session = SessionLocal()
    try:
        # Get a company with data
        empresas = db.query(Empresa).all()
        empresa = None
        fecha_fin = None
        fecha_inicio = None
        
        for emp in empresas:
            max_date_row = db.query(Documento.fecha).filter(Documento.empresa_id == emp.id).order_by(Documento.fecha.desc()).first()
            if max_date_row:
                empresa = emp
                fecha_fin = max_date_row[0]
                fecha_inicio = fecha_fin.replace(day=1) # First day of that month
                break
        
        if not empresa:
            print("No companies with documents found.")
            return

        print(f"Testing Mayor PDF Gen for Company: {empresa.razon_social}")
        print(f"Range: {fecha_inicio} to {fecha_fin}")
        
        from app.services.libros_oficiales import get_data_for_libro_mayor_y_balances
        
        # 2a. Call Data Service explicitly to debug count
        data = get_data_for_libro_mayor_y_balances(db, empresa.id, fecha_inicio, fecha_fin)
        cuentas = data.get("cuentas", [])
        print(f"DEBUG: Found {len(cuentas)} accounts for report.")
        if len(cuentas) > 0:
            print(f"DEBUG: Sample Account: {cuentas[0]['cuenta_nombre']} - Saldo Ini: {cuentas[0]['saldo_inicial']} - Nuevo Saldo: {cuentas[0]['nuevo_saldo']}")
        
        # 3. Call PDF Generation
        pdf_bytes = generate_libro_mayor_y_balances_pdf(
            db, empresa.id, fecha_inicio, fecha_fin
        )
        
        if pdf_bytes and len(pdf_bytes) > 1000:
            print(f"SUCCESS: Mayor PDF generated ({len(pdf_bytes)} bytes).")
        else:
            print("FAILED: Mayor PDF generated but seems empty or too small.")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_mayor_pdf_generation()
