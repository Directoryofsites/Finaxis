import sys
import os
import time
from datetime import date, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services import reportes_inventario
from app.schemas import reportes_inventario as schemas_reportes

def profile_generation():
    db = SessionLocal()
    try:
        print("--- STARTING PROFILE ---")
        
        # Mock Filters - Adjust dates to match a "Super Informe" volume
        # Assuming user is running for a large range or current month
        filtros = schemas_reportes.SuperInformeFiltros(
            fecha_inicio=date(2000, 1, 1), 
            fecha_fin=date(2100, 12, 31),
            bodega_ids=[],
            grupo_ids=[],
            producto_ids=[],
            vista_reporte=schemas_reportes.VistaSuperInformeEnum.MOVIMIENTOS
        )
        
        empresa_id = 218 # Found via find_heavy_company.py
        
        print(f"Generando PDF para Empresa {empresa_id} con filtros: {filtros}")
        
        pdf_content, filename = reportes_inventario.generar_pdf_super_informe_reportlab(
            db=db,
            empresa_id=empresa_id,
            filtros=filtros
        )
        
        print(f"--- END PROFILE ---")
        print(f"Filename: {filename}")
        print(f"Size: {len(pdf_content)} bytes")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    profile_generation()
