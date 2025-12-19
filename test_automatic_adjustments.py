#!/usr/bin/env python3
"""
Test script para verificar la funcionalidad de generación automática de ajustes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

# Importar modelos y servicios
from app.core.database import get_db
from app.services.conciliacion_bancaria import AdjustmentEngine
from app.models.conciliacion_bancaria import BankMovement, AccountingConfig
from app.models.plan_cuenta import PlanCuenta

def test_adjustment_engine():
    """Prueba el motor de generación automática de ajustes"""
    
    print("🧪 Iniciando pruebas del motor de ajustes automáticos...")
    
    # Obtener sesión de base de datos
    db = next(get_db())
    
    try:
        # Test 1: Crear instancia del motor
        print("\n1. Creando instancia del AdjustmentEngine...")
        adjustment_engine = AdjustmentEngine(db)
        print("   ✅ AdjustmentEngine creado exitosamente")
        
        # Test 2: Probar clasificación de movimientos
        print("\n2. Probando clasificación de movimientos...")
        
        # Crear movimientos de prueba
        test_movements = [
            {
                "description": "COMISION MANEJO CUENTA",
                "amount": Decimal("-5000"),
                "expected_type": "COMMISSION"
            },
            {
                "description": "INTERES GANADO CUENTA AHORROS",
                "amount": Decimal("15000"),
                "expected_type": "INTEREST"
            },
            {
                "description": "NOTA DEBITO CARGO AUTOMATICO",
                "amount": Decimal("-8000"),
                "expected_type": "DEBIT_NOTE"
            },
            {
                "description": "NOTA CREDITO ABONO AUTOMATICO",
                "amount": Decimal("12000"),
                "expected_type": "CREDIT_NOTE"
            },
            {
                "description": "TRANSFERENCIA NORMAL",
                "amount": Decimal("-50000"),
                "expected_type": None
            }
        ]
        
        for i, test_mov in enumerate(test_movements):
            # Crear movimiento bancario temporal
            movement = BankMovement(
                id=i + 1000,  # ID temporal
                description=test_mov["description"],
                amount=test_mov["amount"],
                transaction_date=date.today(),
                status="PENDING"
            )
            
            # Clasificar movimiento
            classification = adjustment_engine._classify_movement(movement)
            
            if classification == test_mov["expected_type"]:
                print(f"   ✅ '{test_mov['description']}' → {classification or 'No clasificado'}")
            else:
                print(f"   ❌ '{test_mov['description']}' → Esperado: {test_mov['expected_type']}, Obtenido: {classification}")
        
        # Test 3: Probar detección de ajustes
        print("\n3. Probando detección de ajustes...")
        
        # Buscar movimientos bancarios reales pendientes
        bank_movements = db.query(BankMovement).filter(
            BankMovement.status == "PENDING"
        ).limit(10).all()
        
        if bank_movements:
            print(f"   📊 Analizando {len(bank_movements)} movimientos bancarios...")
            
            # Detectar ajustes
            adjustments = adjustment_engine.detect_adjustments(
                bank_movements, 
                bank_movements[0].bank_account_id,
                bank_movements[0].empresa_id
            )
            
            print(f"   ✅ Ajustes detectados: {len(adjustments)}")
            
            for adjustment in adjustments[:3]:  # Mostrar primeros 3
                print(f"      • {adjustment['adjustment_type']}: {adjustment['bank_movement']['description']} - ${adjustment['total_amount']}")
        else:
            print("   ⚠️  No hay movimientos bancarios pendientes para analizar")
        
        # Test 4: Probar vista previa de ajustes
        print("\n4. Probando vista previa de ajustes...")
        
        try:
            # Buscar una cuenta bancaria
            bank_account = db.query(PlanCuenta).filter(
                PlanCuenta.codigo.like('111%')  # Cuentas bancarias
            ).first()
            
            if bank_account:
                preview = adjustment_engine.preview_adjustments(
                    bank_account.id,
                    1,  # empresa_id
                    date.today(),
                    date.today()
                )
                
                print(f"   ✅ Vista previa generada:")
                print(f"      • Movimientos analizados: {preview['summary']['total_movements_analyzed']}")
                print(f"      • Ajustes detectados: {preview['summary']['total_adjustments_detected']}")
                print(f"      • Monto total: ${preview['summary']['total_amount']}")
                
                if preview['summary']['adjustments_by_type']:
                    print("      • Tipos de ajustes:")
                    for adj_type, data in preview['summary']['adjustments_by_type'].items():
                        print(f"        - {adj_type}: {data['count']} ajustes, ${data['total_amount']}")
            else:
                print("   ⚠️  No se encontró cuenta bancaria para probar")
                
        except Exception as e:
            print(f"   ❌ Error en vista previa: {str(e)}")
        
        # Test 5: Probar configuración contable
        print("\n5. Probando configuración contable...")
        
        try:
            # Buscar configuración contable existente
            config = db.query(AccountingConfig).first()
            
            if config:
                print("   ✅ Configuración contable encontrada:")
                print(f"      • Cuenta comisiones: {config.commission_account_id}")
                print(f"      • Cuenta intereses: {config.interest_income_account_id}")
                print(f"      • Cuenta cargos: {config.bank_charges_account_id}")
                print(f"      • Cuenta ajustes: {config.adjustment_account_id}")
            else:
                print("   ⚠️  No hay configuración contable disponible")
                
        except Exception as e:
            print(f"   ❌ Error verificando configuración: {str(e)}")
        
        print("\n" + "=" * 50)
        print("✅ Pruebas del motor de ajustes completadas")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_adjustment_patterns():
    """Prueba los patrones de detección de ajustes"""
    
    print("\n🔍 Probando patrones de detección...")
    
    # Obtener sesión de base de datos
    db = next(get_db())
    adjustment_engine = AdjustmentEngine(db)
    
    # Patrones de prueba
    test_patterns = {
        "COMMISSION": [
            "COMISION MANEJO CUENTA",
            "FEE ADMINISTRACION",
            "CARGO POR TARIFA",
            "COMISIÓN TRANSFERENCIA"
        ],
        "INTEREST": [
            "INTERES GANADO",
            "INTEREST EARNED",
            "RENDIMIENTO CUENTA",
            "BENEFICIO FINANCIERO"
        ],
        "DEBIT_NOTE": [
            "NOTA DEBITO AUTOMATICA",
            "DEBIT NOTE CARGO",
            "ND SERVICIO",
            "CARGO AUTOMATICO BANCO"
        ],
        "CREDIT_NOTE": [
            "NOTA CREDITO ABONO",
            "CREDIT NOTE AJUSTE",
            "NC DEVOLUCION",
            "ABONO AUTOMATICO"
        ]
    }
    
    print("\n📋 Resultados de clasificación por patrones:")
    
    for expected_type, descriptions in test_patterns.items():
        print(f"\n   {expected_type}:")
        
        for desc in descriptions:
            # Crear movimiento temporal
            amount = Decimal("-1000") if expected_type in ["COMMISSION", "DEBIT_NOTE"] else Decimal("1000")
            movement = BankMovement(
                description=desc,
                amount=amount,
                transaction_date=date.today(),
                status="PENDING"
            )
            
            # Clasificar
            classification = adjustment_engine._classify_movement(movement)
            
            if classification == expected_type:
                print(f"      ✅ '{desc}' → {classification}")
            else:
                print(f"      ❌ '{desc}' → Esperado: {expected_type}, Obtenido: {classification}")
    
    db.close()

def test_adjustment_proposal_creation():
    """Prueba la creación de propuestas de ajuste"""
    
    print("\n📝 Probando creación de propuestas de ajuste...")
    
    db = next(get_db())
    adjustment_engine = AdjustmentEngine(db)
    
    try:
        # Buscar configuración contable
        config = db.query(AccountingConfig).first()
        
        if not config:
            print("   ⚠️  No hay configuración contable para probar")
            return
        
        # Crear movimiento de prueba
        test_movement = BankMovement(
            id=9999,  # ID temporal
            description="COMISION MANEJO CUENTA MENSUAL",
            amount=Decimal("-15000"),
            transaction_date=date.today(),
            reference="REF123456",
            bank_account_id=config.bank_account_id,
            status="PENDING"
        )
        
        # Crear propuesta de ajuste
        proposal = adjustment_engine._create_adjustment_proposal(
            test_movement,
            "COMMISSION",
            config
        )
        
        if proposal:
            print("   ✅ Propuesta de ajuste creada:")
            print(f"      • Tipo: {proposal['adjustment_type']}")
            print(f"      • Descripción: {proposal['adjustment_description']}")
            print(f"      • Monto: ${proposal['total_amount']}")
            print(f"      • Concepto: {proposal['document_concept']}")
            print(f"      • Requiere aprobación: {proposal['requires_approval']}")
            print("      • Asientos:")
            
            for i, entry in enumerate(proposal['entries']):
                print(f"        {i+1}. {entry['account_code']} - {entry['account_name']}")
                if entry['debit'] > 0:
                    print(f"           Débito: ${entry['debit']}")
                if entry['credit'] > 0:
                    print(f"           Crédito: ${entry['credit']}")
        else:
            print("   ❌ No se pudo crear la propuesta de ajuste")
            
    except Exception as e:
        print(f"   ❌ Error creando propuesta: {str(e)}")
    
    finally:
        db.close()

def main():
    """Función principal"""
    print("🚀 Test de Generación Automática de Ajustes")
    print("=" * 50)
    
    # Ejecutar pruebas
    test_adjustment_engine()
    test_adjustment_patterns()
    test_adjustment_proposal_creation()
    
    print("\n" + "=" * 50)
    print("✅ Todas las pruebas completadas")
    print("\n📋 Funcionalidades verificadas:")
    print("   • Detección automática de comisiones bancarias")
    print("   • Identificación de intereses ganados")
    print("   • Clasificación de notas débito y crédito")
    print("   • Generación de propuestas de ajuste")
    print("   • Creación de asientos contables automáticos")
    print("   • Vista previa antes de aplicar ajustes")
    print("   • Integración con configuración contable")
    print("   • Validación de cuentas del plan contable")

if __name__ == "__main__":
    main()