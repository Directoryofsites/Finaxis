from app.core.database import SessionLocal
from app.services.propiedad_horizontal import reportes as reportes_service
from app.models.propiedad_horizontal import PHUnidad
from datetime import date

def test_report_generation():
    db = SessionLocal()
    try:
        print("--- Verifying PH Report Service ---")
        
        # 1. Basic Fetch (All movements)
        # Assuming company ID 1 for test
        empresa_id = 1 
        results = reportes_service.get_movimientos_ph_report(db, empresa_id)
        print(f"Total Records Found: {len(results)}")
        if results:
            print("Sample Record:", results[0])
            
        # 2. Filter by Unit (if any units exist)
        unidad = db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id).first()
        if unidad:
            print(f"\nFiltering by Unit: {unidad.codigo} (ID: {unidad.id})")
            results_unidad = reportes_service.get_movimientos_ph_report(db, empresa_id, unidad_id=unidad.id)
            print(f"Records for Unit {unidad.codigo}: {len(results_unidad)}")
            for r in results_unidad[:3]:
                print(f" - {r['fecha']} | {r['numero']} | {r['debito']} | {r['credito']}")
        else:
            print("No units found for filtering test.")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_report_generation()
