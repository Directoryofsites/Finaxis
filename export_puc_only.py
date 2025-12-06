import sys
import os
import json
import codecs

# Force UTF-8 for stdout/stderr to avoid charmap errors with emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.services.migracion import generar_backup_json

def export_puc_only(empresa_id=1):
    db = SessionLocal()
    try:
        print(f"Generando exportación SOLO PUC para Empresa ID: {empresa_id}...")
        
        # Filtros estrictos para solo PUC
        filtros = {
            'paquetes': {
                'maestros': {
                    'plan_cuentas': True,
                    'terceros': False,
                    'centros_costo': False,
                    'tipos_documento': False,
                    'bodegas': False,
                    'grupos_inventario': False,
                    'tasas_impuesto': False,
                    'productos': False
                },
                'configuraciones': {
                    'plantillas_documentos': False,
                    'libreria_conceptos': False
                },
                'transacciones': False
            }
        }
        
        # Llamamos al servicio de migración con los filtros
        # Nota: generar_backup_json devuelve un dict con 'data' y 'signature' (o solo data si no firma, pero vimos que firma)
        # Revisando migracion.py: generar_backup_json devuelve el dict completo firmado.
        
        backup_data = generar_backup_json(db, empresa_id, filtros)
        
        # Guardar archivo
        output_file = r"c:\ContaPY2\Manual\maestros\PUC_ONLY_BACKUP.json"
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
        print(f"¡Éxito! Archivo generado en: {output_file}")
        
        # Verificación rápida
        if "maestros" in backup_data["data"] and "plan_cuentas" in backup_data["data"]["maestros"]:
            count = len(backup_data["data"]["maestros"]["plan_cuentas"])
            print(f"Total cuentas exportadas: {count}")
        else:
            print("Advertencia: No se encontraron cuentas en el export.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    export_puc_only()
