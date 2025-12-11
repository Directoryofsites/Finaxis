import json
import hmac
import hashlib
import sys
import os
from datetime import datetime

# Secret Key (Hardcoded as per previous scripts)
SECRET_KEY = "4af644a993b9f44e700e7257b7ee90c826cd0c886b36e23a7855e86402aabd53"

INPUT_FILE = r"c:\ContaPY2\Manual\maestros\tipos de doc.txt"
OUTPUT_FILE = r"c:\ContaPY2\Manual\maestros\Maestro_Tipos_Documento.json"

def get_properties(codigo, nombre):
    """
    Infiere las propiedades del tipo de documento basado en su código o nombre.
    """
    props = {
        "afecta_inventario": False,
        "es_venta": False,
        "es_compra": False,
        "numeracion_manual": False,
        "consecutivo_actual": 0,
        "funcion_especial": None
    }
    
    codigo = codigo.upper()
    nombre = nombre.upper()
    
    # Ventas
    if codigo in ["FV", "FVC", "FVE"]:
        props["es_venta"] = True
        props["afecta_inventario"] = True # Generalmente mueven inventario
    
    # Compras
    elif codigo in ["FC", "FCE"]:
        props["es_compra"] = True
        props["afecta_inventario"] = True
        props["numeracion_manual"] = True # Facturas de proveedores suelen ser manuales (su número)
        
    # Inventario
    elif codigo in ["ENT", "SAL", "AJI", "TRI", "REM", "DEV", "DEVG"]:
        props["afecta_inventario"] = True
        
    # Notas (Afectan inventario si son devoluciones, pero por defecto no siempre)
    elif codigo in ["NC", "ND", "NCC", "NDC"]:
        # Asumimos que notas crédito/débito comerciales pueden afectar inventario
        # pero dejémoslo en False para que el usuario decida, o True si es devolución explícita.
        pass

    # Tesorería (Recibos, Egresos)
    elif codigo in ["RC", "RCM", "CE", "CEC", "CHE", "TR", "CONB"]:
        pass # Por defecto todo False
        
    # Contabilidad
    elif codigo in ["CD", "AJ", "REV", "CIER", "APER"]:
        pass
        
    # Nómina
    elif codigo in ["NOM", "NOVE", "LIQ", "PAGN"]:
        pass

    return props

def generate_json():
    print(f"Leyendo archivo: {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print("Error: El archivo no existe.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = json.load(f)
        
    source_docs = content.get("tipos_documento", [])
    print(f"Se encontraron {len(source_docs)} tipos de documento.")
    
    tipos_documento_final = []
    current_id = 1
    
    for item in source_docs:
        codigo = item["codigo"]
        nombre = item["nombre"]
        
        props = get_properties(codigo, nombre)
        
        doc_obj = {
            "id": current_id,
            "empresa_id": 0, # Plantilla
            "codigo": codigo,
            "nombre": nombre,
            "consecutivo_actual": props["consecutivo_actual"],
            "numeracion_manual": props["numeracion_manual"],
            "afecta_inventario": props["afecta_inventario"],
            "es_venta": props["es_venta"],
            "es_compra": props["es_compra"],
            "funcion_especial": props["funcion_especial"],
            # Campos opcionales de cuentas en null para que el usuario configure
            "cuenta_caja_id": None,
            "cuenta_debito_cxc_id": None,
            "cuenta_credito_cxc_id": None,
            "cuenta_debito_cxp_id": None,
            "cuenta_credito_cxp_id": None
        }
        
        tipos_documento_final.append(doc_obj)
        current_id += 1

    # Estructura Final del Backup
    backup_data = {
        "metadata": {
            "fecha_generacion": datetime.utcnow().isoformat(),
            "version_sistema": "7.0",
            "empresa_id_origen": 0,
            "descripcion": "PLANTILLA MAESTRA - TIPOS DE DOCUMENTO"
        },
        "empresa": {}, 
        "configuracion": {}, 
        "maestros": {
            "tipos_documento": tipos_documento_final
        }, 
        "inventario": {}, 
        "transacciones": []
    }
    
    # Firmar
    json_str = json.dumps(backup_data, sort_keys=True, separators=(',', ':'))
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        json_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    signed_backup = {
        "data": backup_data,
        "signature": signature
    }
    
    # Guardar
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(signed_backup, f, indent=2, ensure_ascii=False)
        
    print(f"Archivo generado: {OUTPUT_FILE}")
    print(f"Total tipos de documento: {len(tipos_documento_final)}")

if __name__ == "__main__":
    generate_json()
