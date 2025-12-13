#!/usr/bin/env python3
"""
Script para probar el endpoint de documentos contables de activos fijos
"""

import requests
import json

def test_documentos_contables():
    """
    Prueba el endpoint /api/activos/documentos-contables
    """
    url = "http://localhost:8002/api/activos/documentos-contables"
    
    # Headers básicos
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("🔍 Probando endpoint:", url)
        response = requests.get(url, headers=headers)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Respuesta exitosa:")
            print(f"   Total documentos: {data.get('total', 0)}")
            print(f"   Documentos: {len(data.get('documentos', []))}")
            
            # Mostrar primer documento si existe
            if data.get('documentos'):
                primer_doc = data['documentos'][0]
                print(f"   Primer documento: {primer_doc.get('tipo_documento_codigo', 'N/A')}-{primer_doc.get('numero', 'N/A')}")
        
        elif response.status_code == 422:
            print("❌ Error 422 - Unprocessable Entity:")
            try:
                error_data = response.json()
                print(f"   Detalle: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Texto: {response.text}")
        
        else:
            print(f"❌ Error {response.status_code}:")
            print(f"   Texto: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión. ¿Está corriendo el backend en puerto 8002?")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_documentos_contables()