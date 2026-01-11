import sys
import os
sys.path.append(os.getcwd())
import calendar
from datetime import datetime
from app.core.database import SessionLocal
from app.models.consumo_registros import BolsaExcedente, EstadoBolsa

def fix_bolsas_v2():
    db = SessionLocal()
    try:
        # Filtrar solo las vigentes o agotadas
        bolsas = db.query(BolsaExcedente).filter(BolsaExcedente.estado.in_([EstadoBolsa.VIGENTE, EstadoBolsa.AGOTADO])).all()
        print(f"Procesando {len(bolsas)} bolsas activas...")
        
        count = 0
        for b in bolsas:
            # Calcular fecha correcta: Fin de mes del año siguiente al origen
            last_day = calendar.monthrange(b.anio_origen + 1, b.mes_origen)[1]
            correct_date = datetime(b.anio_origen + 1, b.mes_origen, last_day, 23, 59, 59)
            
            print(f"Bolsa {b.id} (Origen {b.mes_origen}/{b.anio_origen}):")
            print(f"   - Actual: {b.fecha_vencimiento}")
            print(f"   - Correcta: {correct_date}")
            
            # Actualizar siempre para asegurar
            b.fecha_vencimiento = correct_date
            count += 1
            
        if count > 0:
            db.commit()
            print(f"¡Éxito! Se actualizaron {count} registros.")
        else:
            print("No se requirieron cambios.")
            
    except Exception as e:
        print(f"Error crítico: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_bolsas_v2()
