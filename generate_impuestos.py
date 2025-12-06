import json
import hashlib
import hmac
import os

# --- Configuration ---
SECRET_KEY = "4af644a993b9f44e700e7257b7ee90c826cd0c886b36e23a7855e86402aabd53"  # Must match the one used in the app
OUTPUT_FILE = r"c:\ContaPY2\Manual\maestros\Maestro_Impuestos.json"
PUC_FILE = r"c:\ContaPY2\Manual\maestros\Maestro_Plan_Cuentas.json"

# --- Tax Definitions (Mapped to User's PUC) ---
# Based on the user's PUC analysis:
# IVA Generado (Ventas): 240805 (19%), 240810 (5%), 240815 (0%), 240820 (No Gravado)
# IVA Descontable (Compras): 13551701 (19%), 13551702 (5%), 13551703 (0%), 13551704 (No Gravado)
# Retenciones: 236540 (Compras 2.5%), 236525 (Servicios 4%), 236515 (Honorarios 10%)
# ReteIVA: 236705 (15%)
# ReteICA: 236805 (ICA retenido a proveedores)

TAX_DEFINITIONS = [
    {
        "nombre": "IVA 19%",
        "tasa": 0.19,
        "tipo": "IVA",
        "cuenta_venta_codigo": "240805",
        "cuenta_compra_codigo": "13551701",
        "descripcion": "Impuesto al valor agregado tarifa general"
    },
    {
        "nombre": "IVA 5%",
        "tasa": 0.05,
        "tipo": "IVA",
        "cuenta_venta_codigo": "240810",
        "cuenta_compra_codigo": "13551702",
        "descripcion": "Impuesto al valor agregado tarifa reducida"
    },
    {
        "nombre": "IVA Exento (0%)",
        "tasa": 0,
        "tipo": "IVA",
        "cuenta_venta_codigo": "240815",
        "cuenta_compra_codigo": "13551703",
        "descripcion": "Bienes exentos de IVA con derecho a devolucion"
    },
    {
        "nombre": "No Gravado (Excluido)",
        "tasa": 0,
        "tipo": "IVA",
        "cuenta_venta_codigo": "240820",
        "cuenta_compra_codigo": "13551704",
        "descripcion": "Bienes o servicios que no causan IVA"
    },
    {
        "nombre": "ReteFuente Compras 2.5%",
        "tasa": 0.025,
        "tipo": "Retencion",
        "cuenta_compra_codigo": "236540", # Retencion en la fuente por compras
        "descripcion": "Retencion en la fuente por compras generales (Declarantes)"
    },
    {
        "nombre": "ReteFuente Servicios 4%",
        "tasa": 0.04,
        "tipo": "Retencion",
        "cuenta_compra_codigo": "236525", # Retencion por servicios
        "descripcion": "Retencion en la fuente por servicios generales"
    },
    {
        "nombre": "ReteFuente Honorarios 10%",
        "tasa": 0.1,
        "tipo": "Retencion",
        "cuenta_compra_codigo": "236515", # Retencion por honorarios
        "descripcion": "Retencion en la fuente por honorarios (Personas juridicas)"
    },
    {
        "nombre": "ReteIVA 15%",
        "tasa": 0.15,
        "tipo": "ReteIVA",
        "cuenta_compra_codigo": "236705", # Retencion de IVA del 15%
        "descripcion": "Retencion de IVA del 15% sobre el valor del impuesto"
    },
    {
        "nombre": "ReteICA (Generico)",
        "tasa": 0, # La tasa varia por municipio, se deja en 0 o configurable
        "tipo": "ReteICA",
        "cuenta_compra_codigo": "236805", # ICA retenido a proveedores
        "descripcion": "Retencion de Industria y Comercio (Tasa variable)"
    }
]

def load_puc_accounts(puc_path):
    """Loads the PUC JSON and returns a mapping of codigo -> id."""
    if not os.path.exists(puc_path):
        print(f"Error: PUC file not found at {puc_path}")
        return {}
    
    try:
        with open(puc_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Access the list of accounts inside the 'data' -> 'maestros' -> 'plan_cuentas' structure
            accounts = data.get('data', {}).get('maestros', {}).get('plan_cuentas', [])
            
            # Create a dictionary mapping account code to account ID
            account_map = {acc['codigo']: acc['id'] for acc in accounts if 'codigo' in acc and 'id' in acc}
            return account_map
    except Exception as e:
        print(f"Error reading PUC file: {e}")
        return {}

def generate_impuestos_json():
    print("Cargando cuentas del PUC...")
    account_map = load_puc_accounts(PUC_FILE)
    
    if not account_map:
        print("No se pudieron cargar las cuentas del PUC. Abortando.")
        return

    impuestos_list = []
    
    # Construct the payload data
    payload_data = {
        "inventario": {
            "impuestos": [
                {
                    "nombre": t["nombre"],
                    "tasa": t["tasa"],
                    "descripcion": t["descripcion"],
                    "cuenta_codigo": t.get("cuenta_venta_codigo"),
                    "cuenta_iva_descontable_codigo": t.get("cuenta_compra_codigo")
                }
                for t in TAX_DEFINITIONS
            ]
        }
    }

    # Serialize payload to JSON string for signing
    json_str = json.dumps(payload_data, separators=(',', ':'), sort_keys=True)
    
    # Generate HMAC signature
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        json_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Construct the final output structure with 'data' wrapper
    final_output = {
        "data": payload_data,
        "signature": signature
    }

    # Write to file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        print(f"Archivo generado exitosamente: {OUTPUT_FILE}")
        print(f"Total de tasas generadas: {len(impuestos_list)}")
    except Exception as e:
        print(f"Error escribiendo el archivo JSON: {e}")

if __name__ == "__main__":
    generate_impuestos_json()
