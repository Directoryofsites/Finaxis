
import sys
import os

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.configuracion_reporte import ConfiguracionReporte
from app.models.plan_cuenta import PlanCuenta
from sqlalchemy import text

def inspect_company(db, empresa_id):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        print(f"Empresa {empresa_id} not found.")
        return

    print(f"\n--- Inspecting Company: {empresa.razon_social} (ID: {empresa.id}) ---")
    print(f"Is Template: {empresa.is_template}")
    
    # Check Config Reporte
    configs = db.query(ConfiguracionReporte).filter(ConfiguracionReporte.empresa_id == empresa_id).all()
    print(f"Found {len(configs)} Tax Config Lines (Renglones):")
    for c in configs:
        print(f" - [{c.tipo_reporte}] Renglon {c.renglon}: {c.concepto} | Accounts: {c.cuentas_ids}")

    # Check a sample account to verify Code
    if configs and configs[0].cuentas_ids:
        try:
            sample_id = int(configs[0].cuentas_ids[0])
            acc = db.query(PlanCuenta).filter(PlanCuenta.id == sample_id).first()
            if acc:
                print(f"   sample account {sample_id} -> Code: '{acc.codigo}'")
            else:
                print(f"   sample account {sample_id} -> NOT FOUND")
        except:
            pass

def main():
    db = SessionLocal()
    try:
        # Ask user for IDs or search for recent ones
        last_companies = db.query(Empresa).order_by(Empresa.id.desc()).limit(5).all()
        print("Last 5 Companies created:")
        for e in last_companies:
            print(f"ID: {e.id} | Name: {e.razon_social} | Template: {e.is_template}")
            
        # Hardcoding the investigation based on user description
        print("\n>>> INSPECTING TEMPLATE (189) <<<")
        inspect_company(db, 189)
        
        print("\n>>> INSPECTING TARGET COMPANY (190) <<<")
        inspect_company(db, 190)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
