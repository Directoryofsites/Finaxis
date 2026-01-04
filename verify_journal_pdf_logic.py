import sys
import os
sys.path.append(r"c:\ContaPY2")
from datetime import date
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.documento import Documento
from app.services.libros_oficiales import generate_libro_diario_pdf

def verify_pdf_generation():
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

        print(f"Testing PDF Gen for Company: {empresa.razon_social}")
        print(f"Range: {fecha_inicio} to {fecha_fin}")
        
        # 2. Call PDF Generation
        pdf_bytes = generate_libro_diario_pdf(
            db, empresa.id, fecha_inicio, fecha_fin
        )
        
        if pdf_bytes and len(pdf_bytes) > 1000:
            print(f"SUCCESS: PDF generated ({len(pdf_bytes)} bytes). Logic matches template.")
        else:
            print("FAILED: PDF generated but seems empty or too small.")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_pdf_generation()
