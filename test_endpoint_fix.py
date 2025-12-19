#!/usr/bin/env python3
"""
Script para probar el endpoint de movimientos no conciliados
"""

import requests
import json

def test_unmatched_movements_endpoint():
    """Probar el endpoint de movimientos no conciliados"""
    
    # URL del endpoint
    url = "http://localhost:8002/api/conciliacion-bancaria/manual-reconciliation/unmatched-movements"
    
    # Parámetros de prueba
    params = {
        "bank_account_id": 1,
        "limit": 10,
        "offset": 0
    }
    
    # Headers
    headers = {
        "accept": "application/json"
    }
    
    try:
        print("🔍 Probando endpoint de movimientos no conciliados...")
        print(f"URL: {url}")
        print(f"Parámetros: {params}")
        
        response = requests.get(url, params=params, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint funcionando correctamente")
            print(f"Movimientos bancarios: {len(data.get('bank_movements', []))}")
            print(f"Movimientos contables: {len(data.get('accounting_movements', []))}")
            return True
        else:
            print(f"❌ Error en endpoint: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al backend. ¿Está corriendo en puerto 8002?")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    test_unmatched_movements_endpoint()