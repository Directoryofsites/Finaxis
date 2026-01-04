
from app.core.database import SessionLocal
from app.models import FormatoImpresion, TipoDocumento, Empresa

def fix_links():
    db = SessionLocal()
    try:
        # Get all formats with missing link
        formatos = db.query(FormatoImpresion).filter(FormatoImpresion.tipo_documento_id == None).all()
        print(f"Found {len(formatos)} unlinked formats.")

        for f in formatos:
            # Heuristic: Extract name from "Formato NAME (ID)" logic or just substring
            # Example: "Formato COMPROBANTE DE CONTABILIDAD (45)" -> "COMPROBANTE DE CONTABILIDAD"
            # Example: "Formato RECIBO DE CAJA (56)" -> "RECIBO DE CAJA"
            
            clean_name = f.nombre.replace("Formato ", "").split("(")[0].strip()
            print(f"\nProcessing: '{f.nombre}' -> Search for: '{clean_name}'")

            # Try exact match first
            tipo = db.query(TipoDocumento).filter(
                TipoDocumento.empresa_id == f.empresa_id,
                TipoDocumento.nombre.ilike(clean_name)
            ).first()

            if not tipo:
                # Try partial match (contains)
                tipo = db.query(TipoDocumento).filter(
                    TipoDocumento.empresa_id == f.empresa_id,
                    TipoDocumento.nombre.ilike(f"%{clean_name}%")
                ).first()
            
            if not tipo:
                # Try specific mappings based on known data
                if "RECIBO DE CAJA MENOR" in f.nombre.upper():
                     tipo = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == f.empresa_id, TipoDocumento.codigo == 'RCM').first()
                elif "COMPROBANTE DE CONTABILIDAD" in f.nombre.upper():
                     tipo = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == f.empresa_id, TipoDocumento.codigo == 'CC').first()
                elif "FACTURA DE VENTA" in f.nombre.upper():
                     tipo = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == f.empresa_id, TipoDocumento.codigo == 'FV').first()
                elif "FACTURA DE COMPRA" in f.nombre.upper():
                     tipo = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == f.empresa_id, TipoDocumento.codigo == 'FC').first()
                elif "AJUSTE DE INVENTARIO" in f.nombre.upper():
                     tipo = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == f.empresa_id, TipoDocumento.codigo == 'AI').first()
                elif "RECIBO DE CAJA" in f.nombre.upper() and "MENOR" not in f.nombre.upper():
                     tipo = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == f.empresa_id, TipoDocumento.codigo == 'RC').first()

            if tipo:
                print(f"   MATCH FOUND! Linking to Type ID {tipo.id} ({tipo.nombre})")
                f.tipo_documento_id = tipo.id
            else:
                print("   NO MATCH FOUND.")

        db.commit()
        print("\nFix applied successfully.")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_links()
