#!/usr/bin/env python3
"""
Script para probar la funcionalidad de importación de archivos bancarios
"""

import requests
import json
import os
from datetime import datetime

# Configuración
BASE_URL = "http://127.0.0.1:8002"
API_BASE = f"{BASE_URL}/api/conciliacion-bancaria"

def test_import_functionality():
    """Prueba completa de la funcionalidad de importación"""
    
    print("🧪 Iniciando pruebas de importación de archivos bancarios...")
    
    # 1. Crear configuración de importación de ejemplo
    print("\n1. Creando configuración de importación...")
    
    config_data = {
        "name": "Banco Ejemplo - CSV",
        "bank_id": 1,
        "file_format": "CSV",
        "delimiter": ",",
        "date_format": "%Y-%m-%d",
        "field_mapping": {
            "date": 0,
            "description": 1,
            "amount": 2,
            "reference": 3
        },
        "header_rows": 1
    }
    
    try:
        # Nota: Este endpoint requiere autenticación
        # En un entorno real, necesitarías hacer login primero
        response = requests.post(f"{API_BASE}/import-configs", json=config_data)
        
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Configuración creada con ID: {config['id']}")
            config_id = config['id']
        else:
            print(f"⚠️ No se pudo crear configuración (requiere autenticación): {response.status_code}")
            # Usar ID de configuración existente para pruebas
            config_id = 1
            
    except Exception as e:
        print(f"⚠️ Error creando configuración: {e}")
        config_id = 1
    
    # 2. Crear archivo de ejemplo para importar
    print("\n2. Creando archivo de ejemplo...")
    
    sample_data = """Fecha,Descripción,Monto,Referencia
2024-01-15,Transferencia recibida,1500000.00,TRF001
2024-01-16,Pago servicios públicos,-250000.00,PSP002
2024-01-17,Consignación cliente,800000.00,CON003
2024-01-18,Comisión bancaria,-15000.00,COM004
2024-01-19,Intereses ganados,45000.00,INT005"""
    
    sample_file = "sample_bank_statement.csv"
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(sample_data)
    
    print(f"✅ Archivo de ejemplo creado: {sample_file}")
    
    # 3. Probar validación de archivo
    print("\n3. Probando validación de archivo...")
    
    try:
        with open(sample_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_BASE}/import-configs/{config_id}/validate", files=files)
            
        if response.status_code == 200:
            validation = response.json()
            print(f"✅ Validación exitosa:")
            print(f"   - Archivo válido: {validation.get('is_valid', False)}")
            print(f"   - Total filas: {validation.get('total_rows', 0)}")
            if validation.get('sample_data'):
                print(f"   - Datos de muestra: {len(validation['sample_data'])} registros")
        else:
            print(f"⚠️ Error en validación: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Error probando validación: {e}")
    
    # 4. Información sobre importación completa
    print("\n4. Información sobre importación completa...")
    print("📋 Para importar completamente:")
    print("   1. Usa el endpoint POST /api/conciliacion-bancaria/import")
    print("   2. Envía: file, config_id, bank_account_id")
    print("   3. El sistema validará y almacenará los movimientos")
    print("   4. Podrás ver los movimientos en la interfaz de conciliación")
    
    # 5. Limpiar archivo temporal
    if os.path.exists(sample_file):
        os.remove(sample_file)
        print(f"\n✅ Archivo temporal eliminado: {sample_file}")
    
    print("\n🎉 Pruebas de importación completadas!")
    print("\n📌 Próximos pasos:")
    print("   1. Configura las configuraciones de importación en la UI")
    print("   2. Sube archivos reales del banco")
    print("   3. Ejecuta la conciliación automática")
    print("   4. Revisa y ajusta manualmente si es necesario")

if __name__ == "__main__":
    test_import_functionality()