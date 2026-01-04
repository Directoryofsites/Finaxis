import sys
import os
sys.path.append(r"c:\ContaPY2")
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento
from app.services.libros_oficiales import get_data_for_libro_diario

def verify_detailed_journal():
    db: Session = SessionLocal()
    try:
        # 1. Get a company with data
        empresas = db.query(Empresa).all()
        empresa = None
        fecha_fin = None
        fecha_inicio = None
        
        for emp in empresas:
            max_date_row = db.query(Documento.fecha).filter(Documento.empresa_id == emp.id).order_by(Documento.fecha.desc()).first()
            if max_date_row:
                empresa = emp
                fecha_fin = max_date_row[0]
                fecha_inicio = fecha_fin.replace(day=1)
                break
        
        if not empresa:
            print("No companies with documents found.")
            return

        print(f"Testing with Company: {empresa.razon_social} (ID: {empresa.id})")
        print(f"Testing Date Range: {fecha_inicio} to {fecha_fin}")

        # 3. Test Multi-Select Document Types
        # Get some types
        tipos = db.query(TipoDocumento).all()
        if len(tipos) < 2:
            print("Not enough document types to test multi-select.")
        else:
            selected_ids = [t.id for t in tipos[:2]]
            print(f"Testing filter with Document Type IDs: {selected_ids}")
            
            data = get_data_for_libro_diario(
                db, empresa.id, fecha_inicio, fecha_fin, 
                tipos_documento_ids=selected_ids
            )
            
            print(f"Found {len(data)} rows.")
            
            # Verify
            invalid = [row for row in data if row['tipo_documento'] not in [t.nombre for t in tipos[:2]]]
            if invalid:
                print(f"FAILED: Found documents with wrong types: {[i['tipo_documento'] for i in invalid]}")
            else:
                print("PASSED: All rows match selected document types.")

        # 4. Test Account Filter
        account_filter = "1" # Should match assets usually
        print(f"Testing Account Filter: '{account_filter}'")
        
        data_acc = get_data_for_libro_diario(
            db, empresa.id, fecha_inicio, fecha_fin,
            cuenta_filtro=account_filter
        )
        print(f"Found {len(data_acc)} rows with account filter.")
        
        # Verify
        invalid_acc = [row for row in data_acc if account_filter not in row['cuenta_codigo'] and account_filter.lower() not in row['cuenta_nombre'].lower()]
        if invalid_acc:
             print(f"FAILED: Found rows not matching account filter: {[i['cuenta_codigo'] for i in invalid_acc]}")
        else:
             print("PASSED: All rows match account filter.")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_detailed_journal()
