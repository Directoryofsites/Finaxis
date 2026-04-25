import os
import sys

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.propiedad_horizontal.pago_service_new import get_cartera_ph_pendientes_detallada
from app.models.propiedad_horizontal.unidad import PHUnidad

def check_cartera():
    db = SessionLocal()
    try:
        # Get unit b2/101 which is the one mentioned in the report.
        # It's enterprise 222 based on the DB check.
        unidad = db.query(PHUnidad).filter(PHUnidad.codigo == 'b 2 / 101').first()
        if not unidad:
            # try without spaces
            unidad = db.query(PHUnidad).filter(PHUnidad.codigo.like('%b2/101%')).first()
            if not unidad:
                print("No se encontró la unidad b2/101. Listando unidades para Empresa 222:")
                for u in db.query(PHUnidad).filter(PHUnidad.empresa_id == 222).limit(5):
                    print(u.codigo)
                return

        empresa_id = unidad.empresa_id
        
        print(f"--- Probando saldo detallado para {unidad.codigo} (Empresa {empresa_id}) ---")
        resultados = get_cartera_ph_pendientes_detallada(db, empresa_id, unidad.id)
        
        total = 0
        for r in resultados:
            print(f"Concepto: {r['nombre']} | Saldo: {r['saldo']}")
            total += r['saldo']
        print(f"--- TOTAL SALDO MOSTRADO: {total} ---")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_cartera()
