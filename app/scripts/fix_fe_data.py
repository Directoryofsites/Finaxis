
import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine
from sqlalchemy import text

def fix_data():
    db = SessionLocal()
    try:
        print("--- FIXING EMPRESA DATA ---")
        # Update Companies with default DIAN data
        db.execute(text("""
            UPDATE empresas 
            SET 
                dv = '0',
                municipio_dane = '11001',
                tipo_documento = '31',
                regimen_fiscal = '48',
                responsabilidad_fiscal = 'R-99-PN',
                tipo_persona = '1'
            WHERE dv IS NULL OR municipio_dane IS NULL
        """))
        
        print("--- FIXING TERCEROS DATA ---")
        # Update Clients with default DIAN data
        db.execute(text("""
            UPDATE terceros 
            SET 
                municipio_dane = '11001',
                tipo_documento = '13', -- Cedula default
                regimen_fiscal = '49', -- No responsable
                responsabilidad_fiscal = 'R-99-PN',
                tipo_persona = '2',    -- Natural
                codigo_postal = '110111'
            WHERE municipio_dane IS NULL
        """))
        
        # Ensure Config exists for ALL companies
        print("--- ENSURING CONFIGURACION_FE ---")
        
        # Get all company IDs
        companies = db.execute(text("SELECT id FROM empresas")).fetchall()
        
        for comp in companies:
            cid = comp[0]
            print(f"Checking Config for Company {cid}...")
            res = db.execute(text(f"SELECT id FROM configuracion_fe WHERE empresa_id = {cid}"))
            if not res.fetchone():
                 print(f"Creating Config for Company {cid}")
                 db.execute(text(f"""
                    INSERT INTO configuracion_fe (empresa_id, proveedor, ambiente, habilitado, prefijo, resolucion_numero)
                    VALUES ({cid}, 'MOCK', 'PRUEBAS', true, 'SETP', '18760000001')
                 """))

        db.commit()
        print("--- DATA FIXED SUCCESSFULLY ---")
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_data()
