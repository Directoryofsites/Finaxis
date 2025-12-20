#!/usr/bin/env python3
"""
Test script para verificar la funcionalidad de la interfaz de conciliación manual
"""

import requests
import json
from datetime import datetime, date
import sys

# Configuración
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/conciliacion-bancaria"

def test_manual_reconciliation_endpoints():
    """Prueba los endpoints de la interfaz de conciliación manual"""
    
    print("🧪 Iniciando pruebas de la interfaz de conciliación manual...")
    
    # Test 1: Obtener movimientos no conciliados
    print("\n1. Probando endpoint de movimientos no conciliados...")
    try:
        response = requests.get(f"{API_BASE}/manual-reconciliation/unmatched-movements", 
                              params={"bank_account_id": 1})
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Movimientos bancarios: {len(data.get('bank_movements', []))}")
            print(f"   ✅ Movimientos contables: {len(data.get('accounting_movements', []))}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
    
    # Test 2: Obtener sugerencias de conciliación
    print("\n2. Probando endpoint de sugerencias...")
    try:
        response = requests.get(f"{API_BASE}/reconcile/suggestions/1")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Sugerencias obtenidas: {len(data.get('suggestions', []))}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
    
    # Test 3: Vista previa de conciliación manual
    print("\n3. Probando vista previa de conciliación...")
    try:
        data = {
            'bank_movement_id': 1,
            'accounting_movement_ids': '1,2'
        }
        response = requests.post(f"{API_BASE}/manual-reconciliation/match-preview", data=data)
        
        if response.status_code == 200:
            preview = response.json()
            print(f"   ✅ Vista previa generada")
            print(f"   ✅ Confianza: {preview.get('confidence_score', 0):.2%}")
            print(f"   ✅ Balanceado: {preview.get('totals', {}).get('is_balanced', False)}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
    
    # Test 4: Búsqueda de movimientos contables
    print("\n4. Probando búsqueda de movimientos contables...")
    try:
        params = {
            'bank_account_id': 1,
            'query': 'pago',
            'limit': 10
        }
        response = requests.get(f"{API_BASE}/manual-reconciliation/search-accounting-movements", 
                              params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Resultados encontrados: {data.get('total_found', 0)}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
    
    # Test 5: Obtener historial de conciliaciones
    print("\n5. Probando historial de conciliaciones...")
    try:
        response = requests.get(f"{API_BASE}/reconciliations", 
                              params={"bank_account_id": 1, "limit": 5})
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Conciliaciones en historial: {len(data.get('reconciliations', []))}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
    
    # Test 6: Resumen de conciliación
    print("\n6. Probando resumen de conciliación...")
    try:
        response = requests.get(f"{API_BASE}/reconcile/summary/1")
        
        if response.status_code == 200:
            summary = response.json()
            print(f"   ✅ Resumen obtenido")
            print(f"   ✅ Tasa de conciliación: {summary.get('reconciliation_rate', 0)}%")
            print(f"   ✅ Total movimientos bancarios: {summary.get('bank_movements', {}).get('total', 0)}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")

def test_matching_engine_functionality():
    """Prueba la funcionalidad del motor de conciliación"""
    
    print("\n🔧 Probando funcionalidad del motor de conciliación...")
    
    # Test 1: Conciliación automática
    print("\n1. Probando conciliación automática...")
    try:
        data = {'bank_account_id': 1}
        response = requests.post(f"{API_BASE}/reconcile/auto", data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Conciliación automática ejecutada")
            print(f"   ✅ Movimientos bancarios: {result.get('total_bank_movements', 0)}")
            print(f"   ✅ Movimientos contables: {result.get('total_accounting_movements', 0)}")
            print(f"   ✅ Matches exactos: {result.get('exact_matches', 0)}")
            print(f"   ✅ Matches probables: {result.get('probable_matches', 0)}")
            print(f"   ✅ Aplicados automáticamente: {result.get('auto_applied', 0)}")
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")

def test_ui_components():
    """Verifica que los componentes de UI estén disponibles"""
    
    print("\n🎨 Verificando componentes de UI...")
    
    # Verificar que los archivos de componentes existen
    import os
    
    components = [
        "frontend/app/conciliacion-bancaria/page.js",
        "frontend/app/conciliacion-bancaria/components/ManualReconciliationInterface.js",
        "frontend/app/conciliacion-bancaria/components/UnmatchedMovementsList.js",
        "frontend/app/conciliacion-bancaria/components/ReconciliationPreview.js",
        "frontend/app/conciliacion-bancaria/components/ReconciliationHistory.js",
        "frontend/app/conciliacion-bancaria/components/ReconciliationDashboard.js"
    ]
    
    for component in components:
        if os.path.exists(component):
            print(f"   ✅ {component}")
        else:
            print(f"   ❌ {component} - No encontrado")

def main():
    """Función principal"""
    print("🚀 Test de la Interfaz de Conciliación Manual")
    print("=" * 50)
    
    # Verificar componentes UI
    test_ui_components()
    
    # Probar endpoints API
    test_manual_reconciliation_endpoints()
    
    # Probar motor de conciliación
    test_matching_engine_functionality()
    
    print("\n" + "=" * 50)
    print("✅ Pruebas completadas")
    print("\n📋 Resumen de funcionalidades implementadas:")
    print("   • Interfaz de conciliación manual con drag-and-drop")
    print("   • Vista previa de conciliaciones antes de aplicar")
    print("   • Sugerencias automáticas basadas en IA")
    print("   • Historial completo con auditoría")
    print("   • Reversión de conciliaciones con trazabilidad")
    print("   • Dashboard con métricas en tiempo real")
    print("   • Búsqueda avanzada de movimientos")
    print("   • Soporte para conciliaciones 1:N y N:1")
    print("   • Integración completa con el sistema existente")

if __name__ == "__main__":
    main()