import json
import hmac
import hashlib
import sys
import os
from datetime import datetime

# Add project root to path to import config
sys.path.append(os.getcwd())
from app.core.config import settings

INPUT_FILE = r"c:\ContaPY2\Manual\maestros\activos.txt"
OUTPUT_FILE = r"c:\ContaPY2\Manual\maestros\PUC_Clase_1_Activos_Imported.json"

def parse_line(line):
    """Extracts code and name from a line like '110505 CAJA GENERAL'"""
    parts = line.strip().split(' ', 1)
    if len(parts) < 2:
        return None
    return parts[0], parts[1]

def get_level(codigo):
    l = len(codigo)
    if l == 1: return 1
    if l == 2: return 2
    if l == 4: return 3
    if l == 6: return 4
    if l == 8: return 5
    return 6 # Fallback

def generate_puc_from_txt():
    print(f"Leyendo archivo: {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print("Error: El archivo no existe.")
        return

    cuentas_raw = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            parsed = parse_line(line)
            if parsed:
                cuentas_raw.append(parsed)
            else:
                print(f"Linea ignorada (formato incorrecto): {line.strip()}")

    print(f"Se encontraron {len(cuentas_raw)} cuentas.")
    print("Construyendo jerarquía...")

    plan_cuentas = []
    code_to_id = {}
    current_id = 1
    
    # Primera pasada: Asignar IDs
    temp_list = []
    for codigo, nombre in cuentas_raw:
        code_to_id[codigo] = current_id
        temp_list.append({
            "codigo": codigo,
            "nombre": nombre,
            "nivel": get_level(codigo),
            "id": current_id
        })
        current_id += 1
        
    # Segunda pasada: Construir Objetos
    for item in temp_list:
        codigo = item["codigo"]
        nivel = item["nivel"]
        
        # Determinar Padre
        padre_id = None
        if nivel > 1:
            len_padre = 0
            if nivel == 2: len_padre = 1
            elif nivel == 3: len_padre = 2
            elif nivel == 4: len_padre = 4
            elif nivel == 5: len_padre = 6
            elif nivel == 6: len_padre = 8
            
            codigo_padre = codigo[:len_padre]
            padre_id = code_to_id.get(codigo_padre)
            
            if not padre_id:
                # Opcional: Imprimir advertencia si falta el padre
                pass

        # Determinar si permite movimiento (Nivel 4 o superior)
        permite_movimiento = (nivel >= 4)
        
        # Determinar Clase
        clase = int(codigo[0])
        es_ingresos = (clase == 4)

        cuenta_obj = {
            "id": item["id"],
            "empresa_id": 0,
            "codigo": codigo,
            "nombre": item["nombre"],
            "nivel": nivel,
            "clase": clase,
            "permite_movimiento": permite_movimiento,
            "cuenta_padre_id": padre_id,
            "es_cuenta_de_ingresos": es_ingresos,
        }
        plan_cuentas.append(cuenta_obj)

    # Estructura Final
    backup_data = {
        "metadata": {
            "fecha_generacion": datetime.utcnow().isoformat(),
            "version_sistema": "7.0",
            "empresa_id_origen": 0,
            "descripcion": "PUC IMPORTADO DESDE TXT"
        },
        "empresa": {}, 
        "configuracion": {}, 
        "maestros": {
            "plan_cuentas": plan_cuentas
        }, 
        "inventario": {}, 
        "transacciones": []
    }
    
    # Firmar
    print("Firmando archivo...")
    json_str = json.dumps(backup_data, sort_keys=True, separators=(',', ':'))
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        json_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    signed_backup = {
        "data": backup_data,
        "signature": signature
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(signed_backup, f, indent=2, ensure_ascii=False)
        
    print(f"Archivo JSON generado: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_puc_from_txt()
