
import sys
import os
from datetime import datetime, timedelta

# Hack para importar app desde la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.consumo_registros import ControlPlanMensual, BolsaExcedente, RecargaAdicional, HistorialConsumo, EstadoPlan, EstadoBolsa, EstadoRecarga
from app.models.empresa import Empresa
from app.models.documento import Documento
from app.services.consumo_service import registrar_consumo, revertir_consumo, SaldoInsuficienteException, comprar_recarga

def setup_test_data(db, empresa_id):
    """Limpia y prepara datos para el test"""
    print(f"--- Limpiando datos para empresa {empresa_id} ---")
    db.query(ControlPlanMensual).filter_by(empresa_id=empresa_id).delete()
    db.query(BolsaExcedente).filter_by(empresa_id=empresa_id).delete()
    db.query(RecargaAdicional).filter_by(empresa_id=empresa_id).delete()
    
    # Limpiar documentos de test previos si quedaron (por numero o algo identificable)
    # Por seguridad no borramos documentos masivamente.
    
    db.commit()

    # Crear Plan Mensual con 100 registros
    now = datetime.now()
    plan = ControlPlanMensual(
        empresa_id=empresa_id,
        anio=now.year,
        mes=now.month,
        limite_asignado=100,
        cantidad_disponible=100,
        estado=EstadoPlan.ABIERTO
    )
    db.add(plan)
    
    # Crear Bolsa Excedente con 50 registros
    bolsa = BolsaExcedente(
        empresa_id=empresa_id,
        anio_origen=now.year,
        mes_origen=now.month - 1, # Mes anterior
        cantidad_inicial=50,
        cantidad_disponible=50,
        fecha_creacion=now,
        fecha_vencimiento=now + timedelta(days=300),
        estado=EstadoBolsa.VIGENTE
    )
    db.add(bolsa)
    
    # Crear Documento Dummy para FK
    doc = Documento(
        empresa_id=empresa_id,
        tipo_documento_id=1491, # ID valido obtenido
        numero=999999,
        fecha=now.date(),
        estado='ACTIVO'
    )
    db.add(doc)
    db.commit() # Commit para obtener ID
    db.refresh(doc)
    
    print(f"--- Datos iniciales creados: Plan=100, Bolsa=50. Dummy Document ID={doc.id} ---")
    return doc.id

def test_consumo_simple(db, empresa_id, doc_id):
    print("\n[TEST] Consumo Simple (Solo Plan)")
    # Consumir 20
    try:
        registrar_consumo(db, empresa_id, 20, documento_id=doc_id, fecha_doc=datetime.now())
        db.commit()
        
        now = datetime.now()
        plan = db.query(ControlPlanMensual).filter_by(empresa_id=empresa_id, anio=now.year, mes=now.month).first()
        print(f"Resultado: Plan Disponible = {plan.cantidad_disponible} (Esperado: 80)")
        assert plan.cantidad_disponible == 80
        print("[PASSED]")
    except Exception as e:
        print(f"[FAILED]: {e}")
        # raise e

def test_consumo_cascada(db, empresa_id, doc_id):
    print("\n[TEST] Consumo Cascada (Plan -> Bolsa)")
    # El plan tiene 80 (del test anterior). Consumimos 90.
    # Debería tomar 80 del plan y 10 de la bolsa.
    try:
        registrar_consumo(db, empresa_id, 90, documento_id=doc_id, fecha_doc=datetime.now())
        db.commit()
        
        now = datetime.now()
        plan = db.query(ControlPlanMensual).filter_by(empresa_id=empresa_id, anio=now.year, mes=now.month).first()
        bolsa = db.query(BolsaExcedente).filter_by(empresa_id=empresa_id).first()
        
        print(f"Resultado: Plan Disponible = {plan.cantidad_disponible} (Esperado: 0)")
        print(f"Resultado: Bolsa Disponible = {bolsa.cantidad_disponible} (Esperado: 40)")
        
        assert plan.cantidad_disponible == 0
        assert bolsa.cantidad_disponible == 40
        print("[PASSED]")
    except Exception as e:
        print(f"[FAILED]: {e}")
        import traceback
        traceback.print_exc()

def test_reversion(db, empresa_id, doc_id):
    print("\n[TEST] Reversion de Consumo")
    # Revertimos el consumo de TODO el documento doc_id.
    # Se consumieron 20 (simple) + 90 (cascada) = 110 en total para este documento (usamos el mismo ID para simplificar).
    # Debería devolver:
    # 20 al Plan
    # 80 al Plan
    # 10 a la Bolsa
    # Total devuelto al Plan: 100. Total devuelto a Bolsa: 10.
    # Estado final esperado: Plan 100, Bolsa 50.
    
    try:
        revertir_consumo(db, doc_id)
        db.commit()
        
        now = datetime.now()
        plan = db.query(ControlPlanMensual).filter_by(empresa_id=empresa_id, anio=now.year, mes=now.month).first()
        bolsa = db.query(BolsaExcedente).filter_by(empresa_id=empresa_id).first()
        
        print(f"Resultado post-reversion: Plan Disponible = {plan.cantidad_disponible} (Esperado: 100)")
        print(f"Resultado post-reversion: Bolsa Disponible = {bolsa.cantidad_disponible} (Esperado: 50)")
        
        assert plan.cantidad_disponible == 100
        assert bolsa.cantidad_disponible == 50
        print("[PASSED]")
    except Exception as e:
        print(f"[FAILED]: {e}")
        import traceback
        traceback.print_exc()

def test_compra_recarga(db, empresa_id):
    print("\n[TEST] Compra de Recarga Adicional")
    # Comprar paquete 'basic' (100 regs, $15000)
    import traceback
    try:
        recarga = comprar_recarga(db, empresa_id, "basic")
        
        # Verificar que se creó
        assert recarga.id is not None
        assert recarga.cantidad_disponible == 100
        assert recarga.valor_total == 15000
        assert recarga.facturado is False
        assert recarga.estado == EstadoRecarga.VIGENTE
        
        print(f"Recarga creada ID={recarga.id}, Valor=${recarga.valor_total}, Facturado={recarga.facturado}")
        print("[PASSED]")
    except Exception as e:
        print(f"[FAILED]: {e}")
        traceback.print_exc()

def cleanup(db, doc_id):
    # Borrar historial primero
    db.query(HistorialConsumo).filter(HistorialConsumo.documento_id == doc_id).delete()
    # Borrar documento dummy
    db.query(Documento).filter(Documento.id == doc_id).delete()
    db.commit()

def run_tests():
    db = SessionLocal()
    empresa_id = 128
    
    try:
        doc_id = setup_test_data(db, empresa_id)
        test_consumo_simple(db, empresa_id, doc_id)
        test_consumo_cascada(db, empresa_id, doc_id)
        test_reversion(db, empresa_id, doc_id)
        test_compra_recarga(db, empresa_id)
        cleanup(db, doc_id)
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
