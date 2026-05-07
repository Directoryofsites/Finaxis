import datetime
from itsdangerous import URLSafeSerializer

# Mismas claves usadas en app/core/licencia.py
_CLAVE_MAESTRA = "FINAXIS_LOCAL_MASTER_KEY_2026_VERY_SECRET_DO_NOT_SHARE_THIS_123456789"
_SALT = "finaxis-local-activation-salt"

def generar_serial(version="FULL", cliente="Cliente Prueba", max_registros=-1, machine_id=None):
    """
    Genera un serial válido para activar el sistema Finaxis Local.
    """
    s = URLSafeSerializer(_CLAVE_MAESTRA, salt=_SALT)
    
    payload = {
        "version": version,
        "cliente": cliente,
        "emitida": datetime.datetime.now().date().isoformat(),
        "max_registros": max_registros,
        "machine_id": machine_id # <--- NUEVO: Amarre de Hardware
    }
    
    llave = s.dumps(payload)
    return llave

if __name__ == "__main__":
    print("========================================")
    print(" GENERADOR DE SERIALES - FINAXIS LOCAL ")
    print("========================================")
    
    nombre_cliente = input("Ingrese el nombre del cliente (Ej. Empresa XYZ): ") or "Empresa XYZ"
    mid = input("Ingrese el Machine ID del equipo del cliente (Opcional): ").strip() or None
    
    serial_generado = generar_serial(cliente=nombre_cliente, machine_id=mid)
    
    print("\n✅ Serial Generado Exitosamente:")
    print("--------------------------------------------------")
    print(serial_generado)
    print("--------------------------------------------------")
    if mid:
        print(f"⚠️  Esta llave SOLO funcionará en el equipo con ID: {mid}")
    else:
        print("ℹ️  Llave universal (no recomendada para producción)")
    print("--------------------------------------------------")
