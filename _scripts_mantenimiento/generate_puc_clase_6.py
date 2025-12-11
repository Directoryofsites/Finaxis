import json
import hmac
import hashlib
import sys
import os
import re
from datetime import datetime

# sys.path.append(os.getcwd())
# from app.core.config import settings

SECRET_KEY = "4af644a993b9f44e700e7257b7ee90c826cd0c886b36e23a7855e86402aabd53"

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
INPUT_FILE = r"c:\ContaPY2\Manual\maestros\costos de ventas.txt"
OUTPUT_FILE = r"c:\ContaPY2\Manual\maestros\PUC_Clase_6_Costos_Ventas.json"

def get_level(codigo):
    l = len(codigo)
    if l == 1: return 1
    if l == 2: return 2
    if l == 4: return 3
    if l == 6: return 4
    if l == 8: return 5
    return 6 # Fallback

def clean_name(name):
    # Reemplazar saltos de línea y múltiples espacios con un solo espacio
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Reemplazos de caracteres especiales para evitar problemas de importación
    replacements = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'Ñ': 'N', 'ñ': 'n',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Ü': 'U', 'ü': 'u',
        '': '', '•': '',
    }
    for char, rep in replacements.items():
        name = name.replace(char, rep)
        
    # Eliminar cualquier otro caracter no imprimible o extraño
    name = ''.join(c for c in name if c.isprintable())
    
    return name.strip()

def parse_costos_txt():
    print(f"Leyendo archivo: {INPUT_FILE}...")
    
    if not os.path.exists(INPUT_FILE):
        print("Error: El archivo no existe.")
        return []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex para encontrar códigos de cuenta válidos (1, 2, 4, 6, 8 dígitos)
    code_pattern = re.compile(r'(?<!\d)(\d{1}|\d{2}|\d{4}|\d{6}|\d{8})(?!\d)')
    
    matches = list(code_pattern.finditer(content))
    
    cuentas_raw = []
    
    for i in range(len(matches)):
        match = matches[i]
        codigo = match.group(1)
        
        # FILTRO ESTRICTO: Solo cuentas que empiezan por '6' (Costos de Ventas)
        if not codigo.startswith('6'):
            continue
            
        start_idx = match.end()
        
        # El nombre va hasta el inicio del siguiente match o hasta el final del archivo
        if i < len(matches) - 1:
            end_idx = matches[i+1].start()
        else:
            end_idx = len(content)
            
        raw_name = content[start_idx:end_idx]
        nombre = clean_name(raw_name)
        
        # Filtrar basura o rangos
        if len(nombre) < 2 and nombre.lower() == 'a':
            continue
            
        nombre = nombre.lstrip('.').strip()
        
        if not nombre:
            continue

        cuentas_raw.append((codigo, nombre))

    print(f"Se encontraron {len(cuentas_raw)} cuentas potenciales (Filtradas solo Clase 6).")
    return cuentas_raw

def generate_puc_clase_6():
    print("Construyendo PUC Maestro - CLASE 6 (COSTOS DE VENTAS)...")
    
    cuentas_raw = parse_costos_txt()
    if not cuentas_raw:
        print("No se encontraron cuentas para procesar.")
        return

    plan_cuentas = []
    code_to_id = {}
    current_id = 1
    
    # Primera pasada: Asignar IDs y crear objetos base
    temp_list = []
    for codigo, nombre in cuentas_raw:
        # Validación extra: el código debe ser numérico
        if not codigo.isdigit(): continue
        
        code_to_id[codigo] = current_id
        temp_list.append({
            "codigo": codigo,
            "nombre": nombre,
            "nivel": get_level(codigo),
            "id": current_id
        })
        current_id += 1
        
    # Segunda pasada: Construir Jerarquía
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
            elif nivel == 5: len_padre = 6 # Si hubiera nivel 5 (8 digitos)
            elif nivel == 6: len_padre = 8
            
            codigo_padre = codigo[:len_padre]
            padre_id = code_to_id.get(codigo_padre)
            
        # Determinar si permite movimiento (Nivel 4 o superior)
        permite_movimiento = (nivel >= 4)
        
        # Determinar Clase (Primer dígito)
        clase = int(codigo[0])

        # Determinar si es cuenta de ingresos (Clase 4)
        es_ingresos = (clase == 4)

        cuenta_obj = {
            "id": item["id"],
            "empresa_id": 0, # Genérico para plantilla
            "codigo": codigo,
            "nombre": item["nombre"],
            "nivel": nivel,
            "clase": clase,
            "permite_movimiento": permite_movimiento,
            "cuenta_padre_id": padre_id,
            "es_cuenta_de_ingresos": es_ingresos,
        }
        plan_cuentas.append(cuenta_obj)

    # 2. Estructura Final (Formato B)
    backup_data = {
        "metadata": {
            "fecha_generacion": datetime.utcnow().isoformat(),
            "version_sistema": "7.0",
            "empresa_id_origen": 0,
            "descripcion": "PLANTILLA MAESTRA PUC - CLASE 6 COSTOS DE VENTAS"
        },
        "empresa": {}, 
        "configuracion": {}, 
        "maestros": {
            "plan_cuentas": plan_cuentas
        }, 
        "inventario": {}, 
        "transacciones": []
    }
    
    # 3. Firmar
    print("Firmando archivo...")
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
    
    # 4. Guardar
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(signed_backup, f, indent=2, ensure_ascii=False)
        
    print(f"Archivo generado exitosamente en: {OUTPUT_FILE}")
    print(f"Total cuentas exportadas: {len(plan_cuentas)}")

if __name__ == "__main__":
    generate_puc_clase_6()
