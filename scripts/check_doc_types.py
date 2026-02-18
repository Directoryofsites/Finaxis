from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento
from app.models.empresa import Empresa

def check_types():
    db = SessionLocal()
    try:
        # Buscar empresa Verduras la 21
        empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Verduras la 21%")).first()
        if not empresa:
            print("Empresa 'Verduras la 21' not found. Listing for ID 134 as fallback.")
            empresa_id = 134
        else:
            empresa_id = empresa.id
            print(f"Found Empresa: {empresa.razon_social} (ID: {empresa.id})")

        types = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == empresa_id).all()
        print(f"\nDocument Types for Empresa ID {empresa_id}:")
        print(f"{'ID':<5} | {'Code':<10} | {'Name':<30} | {'Special Func'}")
        print("-" * 70)
        for t in types:
            print(f"{t.id:<5} | {t.codigo:<10} | {t.nombre:<30} | {t.funcion_especial or ''}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_types()
