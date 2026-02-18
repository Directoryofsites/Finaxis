import sys
import os

# Añadir el directorio raíz al path para poder importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.producto import Producto
from app.models.lista_precio import ListaPrecio
from app.models.regla_precio_grupo import ReglaPrecioGrupo
from app.models.tercero import Tercero
from sqlalchemy import or_

def diagnose_price(product_name_part: str, target_empresa_id: int = None):
    db = SessionLocal()
    try:
        print(f"\n=== DIAGNÓSTICO DE PRECIO: '{product_name_part}' ===")
        
        query = db.query(Producto).filter(Producto.nombre.ilike(f"%{product_name_part}%"))
        if target_empresa_id:
            query = query.filter(Producto.empresa_id == target_empresa_id)
            
        products = query.all()
        
        if not products:
            print(f"[-] No se encontró ningún producto que coincida con '{product_name_part}'.")
            return

        for p in products:
            print(f"\n[+] PRODUCTO: {p.nombre} (ID: {p.id}, Código: {p.codigo}, Empresa: {p.empresa_id})")
            print(f"    - Grupo ID: {p.grupo_id}")
            print(f"    - Precio Base Manual: {p.precio_base_manual}")
            print(f"    - Costo Promedio: {p.costo_promedio}")
            
            if p.grupo_id:
                reglas = db.query(ReglaPrecioGrupo).filter(ReglaPrecioGrupo.grupo_inventario_id == p.grupo_id).all()
                if reglas:
                    print(f"    - Reglas de Grupo encontradas: {len(reglas)}")
                    for r in reglas:
                        lp = db.query(ListaPrecio).filter(ListaPrecio.id == r.lista_precio_id).first()
                        lp_name = lp.nombre if lp else "DESCONOCIDA"
                        empresa_match = "COINCIDE" if lp and lp.empresa_id == p.empresa_id else "ERROR: OTRA EMPRESA"
                        print(f"      * Lista ID {r.lista_precio_id} ({lp_name}) [{empresa_match}]: +{r.porcentaje_incremento*100}%")
                else:
                    print(f"    - [-] No hay reglas de precio para el grupo {p.grupo_id}.")
            else:
                print(f"    - [-] El producto no tiene un grupo asignado.")
    finally:
        db.close()

def diagnose_tercero(nit: str, empresa_id: int):
    db = SessionLocal()
    try:
        print(f"\n=== DIAGNÓSTICO DE TERCERO: '{nit}' (Empresa {empresa_id}) ===")
        t = db.query(Tercero).filter(Tercero.nit == nit, Tercero.empresa_id == empresa_id).first()
        if not t:
            print(f"[-] No se encontró el tercero con NIT {nit} en la empresa {empresa_id}.")
            return
        
        print(f"[+] TERCERO: {t.razon_social} (ID: {t.id})")
        print(f"    - Lista de Precios asignada (ID): {t.lista_precio_id}")
        
        if t.lista_precio_id:
            lp = db.query(ListaPrecio).filter(ListaPrecio.id == t.lista_precio_id).first()
            if lp:
                print(f"    - Lista encontrada: {lp.nombre} (ID: {lp.id}, Empresa: {lp.empresa_id})")
                if lp.empresa_id != empresa_id:
                    print(f"    - [!] ERROR: La lista pertenece a la empresa {lp.empresa_id}, no a la {empresa_id}.")
            else:
                print(f"    - [-] ERROR: La lista con ID {t.lista_precio_id} NO EXISTE en la base de datos.")
        else:
            print(f"    - [-] El tercero no tiene lista de precios asignada.")
    finally:
        db.close()

if __name__ == "__main__":
    # Buscar Arracacha en empresa 134
    diagnose_price("Arracacha", 134)
    
    # Listar clientes con lista en la 134 para ver si alguno está roto
    internal_db = SessionLocal()
    try:
        clientes = internal_db.query(Tercero).filter(Tercero.empresa_id == 134, Tercero.lista_precio_id.isnot(None)).limit(10).all()
        print("\n=== MUESTRA DE CLIENTES CON LISTA EN EMPRESA 134 ===")
        for c in clientes:
            diagnose_tercero(c.nit, 134)
    finally:
        internal_db.close()
