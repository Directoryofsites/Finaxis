import sys
import os
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.consumo_registros import ControlPlanMensual, HistorialConsumo, EstadoPlan, TipoFuenteConsumo
from app.models.empresa import Empresa
from app.services.consumo_service import _get_or_create_plan_mensual, registrar_consumo, revertir_consumo, verificar_disponibilidad
from app.services.dashboard import get_consumo_actual

def verify_rolling_quota():
    db = SessionLocal()
    try:
        print("=== INICIANDO VERIFICACIÓN ROLLING QUOTA ===")
        
        # 1. Setup Test Company
        empresa = db.query(Empresa).filter_by(nit="TEST_ROLLING_Q").first()
        if not empresa:
            empresa = Empresa(
                razon_social="Test Rolling Quota Corp",
                nit="TEST_ROLLING_Q",
                email="test@rolling.com",
                limite_registros_mensual=100,
                limite_registros=100
            )
            db.add(empresa)
            db.commit()
            db.refresh(empresa)
        
        # FORCE UPDATE LIMITS (In case it existed with old values)
        empresa.limite_registros = 100
        empresa.limite_registros_mensual = 100
        db.commit()

        print(f"Empresa Test ID: {empresa.id}")
        
        # 2. Setup Past Month Plan (Manual Injection to simulate passed time)
        # Month: Last Month
        today = date.today()
        last_month_date = (today.replace(day=1) - timedelta(days=1))
        anio_past = last_month_date.year
        mes_past = last_month_date.month
        
        # Ensure plan exists or create/update it
        plan_past = db.query(ControlPlanMensual).filter_by(
            empresa_id=empresa.id, anio=anio_past, mes=mes_past
        ).first()
        
        if not plan_past:
            plan_past = ControlPlanMensual(
                empresa_id=empresa.id, anio=anio_past, mes=mes_past,
                limite_asignado=100, cantidad_disponible=50, # Surplus of 50
                estado=EstadoPlan.CERRADO.value, # It is closed administratively
                fecha_creacion=datetime.now()
            )
            db.add(plan_past)
        else:
            plan_past.cantidad_disponible = 50 # Reset to 50 for test
            plan_past.estado = EstadoPlan.CERRADO.value
            
        db.commit()
        print(f"Plan Pasado ({mes_past}/{anio_past}) configurado con Saldo 50.")
        
        # 3. Setup Current Month Plan (Fresh)
        plan_current = _get_or_create_plan_mensual(db, empresa.id, datetime.now())
        plan_current.cantidad_disponible = 100 # Reset full
        db.commit()
        print(f"Plan Actual ({today.month}/{today.year}) configurado con Saldo 100.")
        
        # 4. Check Dashboard Limit (Should be 100 + 50 = 150)
        # Note: Depending on where 'now' falls, get_consumo_actual logic works.
        dashboard_stats = get_consumo_actual(db, empresa.id)
        limit_shown = dashboard_stats['limite_registros']
        print(f"Dashboard Limit Shown: {limit_shown}")
        
        if limit_shown == 150:
            print("[OK] Dashboard Limit Calculation CORRECT (Current + Rolling)")
        else:
            print(f"[FAIL] Dashboard Limit Calculation FAILED. Expected 150, got {limit_shown}")
            
        # 5. Consume 120 Units
        print("--- Intentando Consumir 120 Unidades (100 Current + 20 Past) ---")
        
        # Create Dummy Document for FK
        from app.models.documento import Documento
        dummy_doc = Documento(
            empresa_id=empresa.id,
            tipo_documento_id=1, # Mock ID, hope it exists or use simple insert
            numero=12345,
            fecha=datetime.now(),
            anulado=False
        )
        # We need a valid tipo_documento_id if FK exists there too. 
        # Checking if TipoDocumento exists or we need to mock it too.
        # Assuming TipoDocumento 1 exists or we don't valid FK strictly there?
        # Actually safest is to fetch first TipoDocumento
        from app.models.tipo_documento import TipoDocumento
        tipo_doc = db.query(TipoDocumento).first()
        if not tipo_doc:
             tipo_doc = TipoDocumento(codigo="TEST", nombre="Test Doc", empresa_id=empresa.id)
             db.add(tipo_doc)
             db.commit()
             db.refresh(tipo_doc)
        
        dummy_doc.tipo_documento_id = tipo_doc.id
        db.add(dummy_doc)
        db.commit()
        db.refresh(dummy_doc)
        
        doc_id = dummy_doc.id
        print(f"Documento Mock creado: ID {doc_id}")
        
        # Check availability first
        can_consume = verificar_disponibilidad(db, empresa.id, 120)
        print(f"Verificar Disponibilidad(120): {can_consume}")
        
        if can_consume:
            registrar_consumo(db, empresa.id, 120, doc_id, datetime.now())
            db.commit()
            print("Consumo registrado.")
            
            # 6. Verify Balances
            db.refresh(plan_current)
            db.refresh(plan_past)
            
            print(f"Saldo Plan Actual: {plan_current.cantidad_disponible} (Expected 0)")
            print(f"Saldo Plan Pasado: {plan_past.cantidad_disponible} (Expected 30)")
            
            if plan_current.cantidad_disponible == 0 and plan_past.cantidad_disponible == 30:
                print("[OK] Rolling Quota Consumption CORRECT (Waterfall logic)")
            else:
                print("[FAIL] Rolling Quota Consumption FAILED")
                
            # 7. Check History Links
            historia = db.query(HistorialConsumo).filter_by(documento_id=doc_id, tipo_operacion="CONSUMO").all()
            print(f"Historial Entries: {len(historia)}")
            for h in historia:
                print(f" - Fuente: {h.fuente_tipo}, ID: {h.fuente_id}, Cantidad: {h.cantidad}")
                
            # 8. Revert Consumption
            print("--- Revertir Consumo ---")
            revertir_consumo(db, doc_id)
            db.commit()
            
            db.refresh(plan_current)
            db.refresh(plan_past)
            
            print(f"Saldo Plan Actual tras Reversión: {plan_current.cantidad_disponible} (Expected 100)")
            print(f"Saldo Plan Pasado tras Reversión: {plan_past.cantidad_disponible} (Expected 50)") 
            
            if plan_current.cantidad_disponible == 100 and plan_past.cantidad_disponible == 50:
                 print("[OK] Reversion CORRECT (Restored to exact sources)")
            else:
                 print("[FAIL] Reversion FAILED")
                 
        else:
            print("[FAIL] verificar_disponibilidad failed unexpectedly.")

    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_rolling_quota()
