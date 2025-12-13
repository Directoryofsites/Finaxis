#!/usr/bin/env python3
"""
Script para probar los endpoints de documentos contables
y comparar las respuestas
"""

import requests
import json

def test_endpoints():
    base_url = "http://localhost:8002/api"
    
    # Simular headers de autenticación (necesitarás ajustar esto)
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🔍 PROBANDO ENDPOINTS DE DOCUMENTOS")
    print("=" * 50)
    
    # Test 1: Endpoint general de documentos
    print("\n1. 📄 ENDPOINT GENERAL: /documentos/")
    try:
        response = requests.get(
            f"{base_url}/documentos/",
            params={
                "observaciones": "depreciación",
                "limit": 100
            },
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Tipo de respuesta: {type(data)}")
            print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'No es dict'}")
            
            if isinstance(data, dict) and 'documentos' in data:
                docs = data['documentos']
                print(f"   Total documentos: {len(docs)}")
                
                if docs:
                    doc = docs[0]
                    print(f"   Primer documento keys: {list(doc.keys())}")
                    print(f"   Tipo documento código: {doc.get('tipo_documento_codigo')}")
                    print(f"   Tipo documento nombre: {doc.get('tipo_documento_nombre')}")
            else:
                print(f"   Respuesta completa: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Endpoint específico de activos
    print("\n2. 🏢 ENDPOINT ACTIVOS: /activos/documentos-contables")
    try:
        response = requests.get(
            f"{base_url}/activos/documentos-contables",
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Tipo de respuesta: {type(data)}")
            print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'No es dict'}")
            
            if isinstance(data, dict) and 'documentos' in data:
                docs = data['documentos']
                print(f"   Total documentos: {len(docs)}")
                
                if docs:
                    doc = docs[0]
                    print(f"   Primer documento keys: {list(doc.keys())}")
                    print(f"   Tipo documento código: {doc.get('tipo_documento_codigo')}")
                    print(f"   Tipo documento nombre: {doc.get('tipo_documento_nombre')}")
            else:
                print(f"   Respuesta completa: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Probar PDF específico
    print("\n3. 📋 ENDPOINT PDF: /documentos/165/pdf")
    try:
        response = requests.head(
            f"{base_url}/documentos/165/pdf",
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_endpoints()