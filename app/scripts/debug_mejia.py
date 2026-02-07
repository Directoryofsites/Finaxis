from app.core.database import SessionLocal
from sqlalchemy import text
from datetime import datetime

def debug_mejia():
    db = SessionLocal()
    empresa_id = 179
    now = datetime.now()
    
    print(f"--- DEBUGGING RESOURCES FOR EMPRESA {empresa_id} ---")
    print(f"Current Server Time: {now}")
    
    try:
        # 1. PLAN MENSUAL
        print("\n[1. CONTROL PLAN MENSUAL]")
        sql = text("SELECT * FROM control_plan_mensual WHERE empresa_id = :eid AND anio = :y AND mes = :m")
        rows = db.execute(sql, {"eid": empresa_id, "y": now.year, "m": now.month}).fetchall()
        for r in rows:
            print(f"  Existing Plan: Anio={r.anio}, Mes={r.mes}, Limite={r.limite_asignado}, DISPONIBLE={r.cantidad_disponible}, Estado={r.estado}")
            
        # 2. BOLSAS
        print("\n[2. BOLSAS EXCEDENTES]")
        sql_b = text("SELECT * FROM bolsa_excedente WHERE empresa_id = :eid")
        rows_b = db.execute(sql_b, {"eid": empresa_id}).fetchall()
        for r in rows_b:
            is_vigente = (r.estado == 'VIGENTE')
            is_future = (r.fecha_vencimiento >= now)
            print(f"  Bolsa ID={r.id}: Disp={r.cantidad_disponible}, Vence={r.fecha_vencimiento}, Estado={r.estado} | Valid? {is_vigente and is_future}")

        # 3. RECARGAS
        print("\n[3. RECARGAS]")
        sql_r = text("SELECT * FROM recarga_adicional WHERE empresa_id = :eid")
        rows_r = db.execute(sql_r, {"eid": empresa_id}).fetchall()
        for r in rows_r:
             print(f"  Recarga ID={r.id}: Disp={r.cantidad_disponible}, Estado={r.estado}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_mejia()
