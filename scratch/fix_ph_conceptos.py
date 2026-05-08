import sys
import os

# Añadir el directorio raíz al path para poder importar la app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.propiedad_horizontal.concepto import PHConcepto
from app.models.plan_cuenta import PlanCuenta

def fix_concepts():
    db = SessionLocal()
    try:
        print("--- Iniciando Corrección de Conceptos PH ---")
        
        # Buscar conceptos con cuenta CXC que no empiece por 13
        concepts = db.query(PHConcepto).all()
        fixed_count = 0
        
        for c in concepts:
            if c.cuenta_cxc_id:
                cta = db.query(PlanCuenta).filter(PlanCuenta.id == c.cuenta_cxc_id).first()
                if cta and not cta.codigo.startswith('13'):
                    print(f"CORRIGIENDO: Concepto '{c.nombre}' (ID {c.id})")
                    print(f"  - Cuenta actual errónea: {cta.codigo} - {cta.nombre}")
                    print(f"  - Acción: Reseteando a NULL para usar configuración global.")
                    
                    c.cuenta_cxc_id = None
                    fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            print(f"\nSe corrigieron {fixed_count} conceptos exitosamente.")
        else:
            print("\nNo se encontraron conceptos con configuraciones erróneas.")
            
    except Exception as e:
        db.rollback()
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_concepts()
