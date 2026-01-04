
from app.core.database import SessionLocal
from app.models import FormatoImpresion, TipoDocumento, Documento, Empresa

def debug_templates():
    db = SessionLocal()
    try:
        # 1. List all companies
        empresas = db.query(Empresa).all()
        print(f"--- EMPRESAS ({len(empresas)}) ---")
        for e in empresas:
            print(f"ID: {e.id} | Nom: {e.razon_social}")

        # 2. List ALL templates
        formatos = db.query(FormatoImpresion).all()
        print(f"--- GLOBAL: FORMATOS ENCONTRADOS ({len(formatos)}) ---")
        for f in formatos:
            tipo_nom = f.tipo_documento.nombre if f.tipo_documento else "N/A"
            print(f"Empresa: {f.empresa_id} | ID: {f.id} | Nom: {f.nombre} | TipoDoc ID: {f.tipo_documento_id} ({tipo_nom})")

        # 3. List ALL document types
        tipos = db.query(TipoDocumento).all()
        print(f"\n--- GLOBAL: TIPOS DE DOCUMENTO ({len(tipos)}) ---")
        for t in tipos:
             print(f"Empresa: {t.empresa_id} | ID: {t.id} | Cod: {t.codigo} | Nom: {t.nombre}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_templates()
