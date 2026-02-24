# app/services/ai_quota_service.py
from datetime import date
from sqlalchemy.orm import Session
from app.models.empresa import Empresa

class AIQuotaException(Exception):
    """Excepción lanzada cuando una empresa excede su cuota de IA asignada."""
    pass

class AIQuotaService:
    @staticmethod
    def verificar_y_descontar_cuota_ia(empresa_id: int, db: Session) -> bool:
        """
        Verifica si la empresa tiene saldo disponible para usar Inteligencia Artificial.
        Si la fecha de reinicio es de un mes anterior, resetea el consumo a 0.
        Si hay saldo disponible, incrementa el consumo en 1 y devuelve True.
        Si no hay saldo o el límite es 0, lanza AIQuotaException.
        """
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        
        if not empresa:
            raise AIQuotaException("Empresa no encontrada.")

        # Obtener fecha actual
        hoy = date.today()

        # Si no hay fecha de reinicio o es de un mes/año anterior, reiniciar cuotas
        if not empresa.fecha_reinicio_cuota_ia or \
           empresa.fecha_reinicio_cuota_ia.month != hoy.month or \
           empresa.fecha_reinicio_cuota_ia.year != hoy.year:
            empresa.consumo_mensajes_ia_actual = 0
            empresa.fecha_reinicio_cuota_ia = hoy
            # Hacemos flush para asegurar que el reinicio queda en memoria transaccional
            db.flush()

        # Validaciones de Límite
        limite = empresa.limite_mensajes_ia_mensual
        consumo = empresa.consumo_mensajes_ia_actual

        if limite is None or limite <= 0:
            raise AIQuotaException("Tu plan no incluye consultas de Inteligencia Artificial.")

        if consumo is None:
            consumo = 0

        if consumo >= limite:
            raise AIQuotaException(f"Has alcanzado tu límite mensual de consultas IA ({consumo}/{limite}). Solicita una ampliación de plan a tu administrador.")

        # Si llegamos aquí, hay saldo disponible. Descontamos 1.
        empresa.consumo_mensajes_ia_actual += 1
        db.commit()
        db.refresh(empresa)

        return True

    @staticmethod
    def verificar_solo_cuota_ia(empresa_id: int, db: Session) -> dict:
        """
        Solo consulta el estado actual sin consumir la cuota. Útil para mostrar en frontend.
        Resetea automáticamente si corresponde.
        """
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            return {"autorizado": False, "limite": 0, "consumo": 0}

        hoy = date.today()

        if not empresa.fecha_reinicio_cuota_ia or \
           empresa.fecha_reinicio_cuota_ia.month != hoy.month or \
           empresa.fecha_reinicio_cuota_ia.year != hoy.year:
            empresa.consumo_mensajes_ia_actual = 0
            empresa.fecha_reinicio_cuota_ia = hoy
            db.commit()
            db.refresh(empresa)
            
        limite = empresa.limite_mensajes_ia_mensual or 0
        consumo = empresa.consumo_mensajes_ia_actual or 0
            
        return {
            "autorizado": limite > 0 and consumo < limite,
            "limite": limite,
            "consumo": consumo
        }
