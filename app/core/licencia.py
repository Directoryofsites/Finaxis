"""
===========================================================
  MÓDULO DE LICENCIAMIENTO FINAXIS
  Valida llaves de activación generadas por el desarrollador.
  
  ℹ️  Este módulo SÍ va en el instalador.
  ℹ️  Solo contiene el VALIDADOR, no el generador.
===========================================================
"""
import os
import sys
import uuid
import hashlib
import subprocess
from itsdangerous import URLSafeSerializer, BadSignature, BadData
from sqlalchemy.orm import Session
from app.models.empresa import Empresa

def get_machine_id():
    """
    Genera un ID único para el hardware de este computador.
    Usa el número de serie de la placa base (UUID) en Windows.
    """
    try:
        # Intentamos obtener el UUID de la placa base vía WMIC (Estándar en Windows)
        # Redirigimos stderr a DEVNULL para evitar mensajes molestos si wmic no está en el PATH
        cmd = 'wmic csproduct get uuid'
        uuid_out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().split('\n')[1].strip()
        if not uuid_out or "UUID" in uuid_out or uuid_out == "":
            # Fallback a la dirección MAC si falla WMIC
            uuid_out = str(uuid.getnode())
    except Exception:
        # Último recurso: MAC address
        uuid_out = str(uuid.getnode())
        
    return hashlib.sha256(uuid_out.encode()).hexdigest()[:12].upper()

# ⚠️ Esta clave debe ser idéntica a la del generador privado.
_CLAVE_MAESTRA = "FINAXIS_LOCAL_MASTER_KEY_2026_VERY_SECRET_DO_NOT_SHARE_THIS_123456789"
_SALT = "finaxis-local-activation-salt"

# Límite de registros por defecto en modo DEMO
DEMO_LIMITE_REGISTROS_DEFAULT = 200


class LicenciaInvalidaError(Exception):
    """Se lanza cuando una llave de licencia no es válida o fue manipulada."""
    pass


def validar_llave(llave: str) -> dict:
    """
    Valida criptográficamente una llave de activación y verifica el Machine ID.
    """
    s = URLSafeSerializer(_CLAVE_MAESTRA, salt=_SALT)
    try:
        payload = s.loads(llave)
        
        # VERIFICACIÓN DE SEGURIDAD: Machine ID
        lic_machine_id = payload.get("machine_id")
        current_id = get_machine_id()
        
        if lic_machine_id and lic_machine_id != current_id:
            raise LicenciaInvalidaError("Esta licencia pertenece a otro computador. Debe activar una licencia válida para este equipo.")
            
        return payload
    except (BadSignature, BadData):
        raise LicenciaInvalidaError("La llave de licencia no es válida o fue modificada.")
    except LicenciaInvalidaError as e:
        raise e
    except Exception:
        raise LicenciaInvalidaError("Error al procesar la llave de licencia.")


def activar_licencia(db: Session, empresa_id: int, llave: str) -> dict:
    """
    Activa una licencia para una empresa específica.
    
    1. Valida criptográficamente la llave.
    2. Actualiza el limite_registros_mensual de la empresa.
    3. Guarda la llave en la BD para futuras verificaciones.
    
    Returns:
        dict con el resultado de la activación.
    
    Raises:
        LicenciaInvalidaError: Si la llave no es válida.
        ValueError: Si la empresa no existe.
    """
    # 1. Validar la llave
    payload = validar_llave(llave)  # lanza LicenciaInvalidaError si falla
    
    # 2. Buscar la empresa
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise ValueError(f"Empresa con id={empresa_id} no encontrada.")
    
    # 3. Aplicar los límites de la licencia
    max_registros = payload.get("max_registros", -1)
    
    if max_registros == -1:
        # Licencia FULL: ponemos un número muy alto (prácticamente ilimitado)
        empresa.limite_registros_mensual = 999_999
        empresa.limite_registros = 999_999
    else:
        empresa.limite_registros_mensual = max_registros
        empresa.limite_registros = max_registros
    
    # 4. Guardar la llave en la BD para mostrar el estado en el panel
    empresa.licencia_key = llave
    empresa.licencia_version = payload.get("version", "FULL")
    empresa.licencia_cliente = payload.get("cliente", "")
    empresa.licencia_activada_en = payload.get("emitida", "")
    
    db.commit()
    db.refresh(empresa)
    
    return {
        "mensaje": f"✅ Licencia activada para '{payload.get('cliente')}'.",
        "version": payload.get("version"),
        "limite_registros": "Ilimitado" if max_registros == -1 else max_registros,
        "emitida": payload.get("emitida"),
    }


def obtener_estado_licencia(db: Session, empresa_id: int) -> dict:
    """
    Retorna el estado actual de la licencia de una empresa.
    Útil para mostrar en el panel de configuración.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        return {"modo": "DEMO", "limite": DEMO_LIMITE_REGISTROS_DEFAULT}
    
    tiene_licencia = hasattr(empresa, 'licencia_key') and empresa.licencia_key
    
    if tiene_licencia:
        # Verificar que la llave sigue siendo válida (no fue manipulada en la BD)
        try:
            payload = validar_llave(empresa.licencia_key)
            limite_actual = empresa.limite_registros_mensual if empresa.limite_registros_mensual is not None else DEMO_LIMITE_REGISTROS_DEFAULT
            return {
                "modo": "FULL",
                "cliente": empresa.licencia_cliente,
                "version": empresa.licencia_version,
                "limite": "Ilimitado" if limite_actual >= 999_999 else limite_actual,
                "activada_en": empresa.licencia_activada_en,
                "llave_valida": True,
                "machine_id_actual": get_machine_id()
            }
        except LicenciaInvalidaError as e:
            # Si el error es por cambio de máquina, NO la removemos pero informamos el bloqueo
            if "otro computador" in str(e):
                return {
                    "modo": "BLOQUEADO",
                    "error": str(e),
                    "machine_id_actual": get_machine_id()
                }
            
            # La llave fue manipulada en la BD — revertir a DEMO
            empresa.licencia_key = None
            empresa.limite_registros_mensual = DEMO_LIMITE_REGISTROS_DEFAULT
            db.commit()
            return {
                "modo": "DEMO",
                "limite": DEMO_LIMITE_REGISTROS_DEFAULT,
                "advertencia": "La llave de licencia fue detectada como inválida y fue removida.",
                "machine_id_actual": get_machine_id()
            }
    else:
        return {
            "modo": "DEMO",
            "limite": empresa.limite_registros_mensual or DEMO_LIMITE_REGISTROS_DEFAULT,
            "machine_id_actual": get_machine_id()
        }
