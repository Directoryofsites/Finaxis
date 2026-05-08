"""
===========================================================
  GENERADOR DE LICENCIAS FINAXIS
  ⚠️  PRIVADO - SOLO PARA USO DE HÉCTOR (EL DESARROLLADOR)
  ⚠️  ESTE ARCHIVO NUNCA DEBE IR EN EL INSTALADOR
===========================================================
  
  Uso:
    python generar_licencia.py

  Genera una llave de activación para un cliente.
  La llave se le envía al cliente por correo o WhatsApp.
  El cliente la ingresa en Finaxis > Configuración > Licencia.
"""

from itsdangerous import URLSafeSerializer
import datetime

# =============================================================
# 🔐 CLAVE MAESTRA (NUNCA LA CAMBIES UNA VEZ EN PRODUCCIÓN)
#    Si la cambias, TODAS las llaves generadas anteriormente
#    dejarán de funcionar para los clientes ya activados.
# =============================================================
CLAVE_MAESTRA_FINAXIS = "finaxis-2026-licencia-hectorm-clave-secreta-unica-v1"
SALT = "finaxis-activacion-salt-v1"

def generar_licencia(
    nombre_cliente: str,
    limite_registros: int = -1,  # -1 = Ilimitado
    version: str = "FULL"
) -> str:
    """
    Genera una llave de licencia firmada criptográficamente.
    
    Args:
        nombre_cliente: Nombre de la empresa del cliente (ej: "Comercial Torres S.A.S")
        limite_registros: -1 para FULL (sin límite). 
                          Un número para una licencia con cupo específico.
        version: "FULL" para versión completa, "DEMO" para demo extendido.
    
    Returns:
        La llave de activación (string largo y seguro).
    """
    s = URLSafeSerializer(CLAVE_MAESTRA_FINAXIS, salt=SALT)
    
    payload = {
        "cliente": nombre_cliente,
        "max_registros": limite_registros,  # -1 = sin límite
        "version": version,
        "emitida": datetime.date.today().isoformat(),  # ej: "2026-05-04"
    }
    
    llave = s.dumps(payload)
    return llave


def verificar_licencia(llave: str) -> dict | None:
    """
    Verifica una llave de licencia. (Para pruebas internas)
    Retorna el payload si es válida, None si es inválida.
    """
    s = URLSafeSerializer(CLAVE_MAESTRA_FINAXIS, salt=SALT)
    try:
        payload = s.loads(llave)
        return payload
    except Exception:
        return None


# =============================================================
#  INTERFAZ INTERACTIVA — Ejecuta este archivo para generar
# =============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  🔑 GENERADOR DE LICENCIAS FINAXIS")
    print("=" * 60)
    print()
    
    nombre = input("Nombre del cliente (ej: Empresa XYZ S.A.S): ").strip()
    if not nombre:
        print("❌ Error: El nombre del cliente no puede estar vacío.")
        exit(1)
    
    print()
    print("Tipo de licencia:")
    print("  [1] FULL - Sin límite de registros (RECOMENDADO)")
    print("  [2] Personalizada - Con límite específico")
    
    opcion = input("Selecciona (1 o 2): ").strip()
    
    if opcion == "2":
        limite_str = input("¿Cuántos registros mensuales máximo?: ").strip()
        try:
            limite = int(limite_str)
        except ValueError:
            print("❌ Error: Debes ingresar un número.")
            exit(1)
    else:
        limite = -1  # Ilimitado
    
    llave = generar_licencia(
        nombre_cliente=nombre,
        limite_registros=limite,
        version="FULL"
    )
    
    print()
    print("=" * 60)
    print("  ✅ LLAVE GENERADA CON ÉXITO")
    print("=" * 60)
    print()
    print(f"  Cliente : {nombre}")
    print(f"  Límite  : {'Ilimitado' if limite == -1 else f'{limite} registros/mes'}")
    print(f"  Fecha   : {datetime.date.today().strftime('%d/%m/%Y')}")
    print()
    print("  🔑 LLAVE DE ACTIVACIÓN:")
    print()
    print(f"  {llave}")
    print()
    print("=" * 60)
    print("  📧 Envía esta llave al cliente por correo o WhatsApp.")
    print("  El cliente la ingresa en: Configuración > Licencia > Activar")
    print("=" * 60)
    
    # Verificación interna de prueba
    verificacion = verificar_licencia(llave)
    if verificacion:
        print()
        print("  ✔ Verificación interna: Llave válida y firma correcta.")
    else:
        print()
        print("  ✘ Error interno: La llave no pudo verificarse. Revisar.")
