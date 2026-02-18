import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento
from app.models.usuario import Usuario

def audit_tipos_doc():
    db = SessionLocal()
    try:
        user_email = "mar1@mar.com"
        user = db.query(Usuario).filter(Usuario.email == user_email).first()
        if not user:
            print("User not found")
            return
            
        empresa_id = user.empresa_id
        print(f"Auditing TipoDocumento for Empresa: {empresa_id}")
        
        docs = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == empresa_id).all()
        
        print(f"{'ID':<6} | {'COD':<10} | {'NOMBRE':<30} | {'CXC':<8} | {'CAJA':<8} | {'INC_INV':<7} | {'FUNC_ESP':<15} | {'STATUS'}")
        print("-" * 120)
        
        for doc in docs:
            account_cxc = doc.cuenta_debito_cxc_id
            account_caja = doc.cuenta_caja_id
            
            status = "OK"
            if not account_cxc or not account_caja:
                status = "MISSING"
            
            color = ""
            if doc.afecta_inventario and doc.funcion_especial == 'cartera_cliente':
                color = "*" # MARKER FOR FRONTEND VISIBILITY
                
            print(f"{doc.id:<6} | {doc.codigo:<10} | {doc.nombre[:30]:<30} | {str(account_cxc):<8} | {str(account_caja):<8} | {str(doc.afecta_inventario):<7} | {str(doc.funcion_especial):<15} | {status} {color}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    audit_tipos_doc()
