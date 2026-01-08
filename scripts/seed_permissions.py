import sys
import os
import re

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.permiso import Permiso
from sqlalchemy.orm import Session

# HARDCODED LIST EXTRACTED FROM THE PREVIOUS EDIT TO menuData.js
NEW_PERMISSIONS = [
    # Analisis Financiero
    "analisis_financiero:acceso",
    "analisis_financiero:dashboard",
    "analisis_financiero:ratios",
    "analisis_financiero:vertical",
    "analisis_financiero:horizontal",
    "analisis_financiero:fuentes_usos",
    "analisis_financiero:flujos_efectivo",
    
    # PH
    "ph:acceso",
    "ph:unidades",
    "ph:propietarios",
    "ph:conceptos",
    "ph:facturacion",
    "ph:pagos",
    "ph:estado_cuenta",
    "ph:reportes",
    "ph:configuracion",

    # Nomina
    "nomina:acceso",
    "nomina:empleados",
    "nomina:liquidar",
    "nomina:desprendibles",
    "nomina:configuracion",
    
    # Produccion
    "produccion:acceso",
    "produccion:recetas",
    "produccion:ordenes",

    # Conciliacion
    "conciliacion_bancaria:acceso",
    "conciliacion_bancaria:dashboard",
    "conciliacion_bancaria:conciliar",
    "conciliacion_bancaria:importar",
    "conciliacion_bancaria:reportes",
    "conciliacion_bancaria:configurar",

    # Contabilidad
    "contabilidad:acceso",
    "contabilidad:gestionar_puc", 
    "contabilidad:acceso",
    "contabilidad:gestionar_puc", 
    
    # Control & Herramientas (Admin)
    "utilidades:migracion", # Backups
    "utilidades:cierre_periodos",
    "utilidades:auditoria_consecutivos",
    "utilidades:conteo_registros",
    "utilidades:scripts",
    "utilidades:edicion_masiva",
    "utilidades:recodificacion",
    "papelera:usar",
    "utilidades:config_correo",
    
    # Granular Config
    "contabilidad:configuracion_tipos_doc", 
    "contabilidad:configuracion_plantillas",
    "contabilidad:configuracion_conceptos",

    # Granular Empresa
    "empresa:gestionar_empresas", 
    "empresa:usuarios_roles",

    "contabilidad:crear_documento",
    "contabilidad:captura_rapida",
    "contabilidad:explorador",
    "contabilidad:libro_diario", # Used twice
    "contabilidad:analisis_cuenta",
    "contabilidad:balance_general",
    "contabilidad:pyg",
    "contabilidad:balance_prueba",
    "contabilidad:auxiliar",
    "contabilidad:libros_oficiales",
    "contabilidad:auditoria_avanzada",

    # CCostos
    "centros_costo:acceso",
    "centros_costo:gestionar",
    "centros_costo:auxiliar",
    "centros_costo:balance",
    "centros_costo:pyg",
    "centros_costo:balance_prueba",

    # Terceros
    "terceros:acceso",
    "terceros:gestionar",
    "terceros:auxiliar",
    "terceros:estado_cuenta_cliente",
    "terceros:cartera",
    "terceros:estado_cuenta_proveedor",
    "terceros:auxiliar_proveedores",

    # Impuestos
    "impuestos:acceso",
    "impuestos:iva",
    "impuestos:renta",
    "impuestos:retefuente",
    "impuestos:reteica",
    "impuestos:timbre",
    "impuestos:consumo",
    "impuestos:calendario",

    # Inventarios
    "inventario:acceso",
    "inventario:configuracion",
    "inventario:kardex",
    "inventario:estadisticas",
    "inventario:auditoria",
    "inventario:traslados",
    "inventario:ajustes",
    "inventario:topes",

    # Facturacion
    "facturacion:acceso",
    "facturacion:nueva",
    "facturacion:remisiones",
    "facturacion:reporte_remisiones",
    "facturacion:cotizaciones",
    "compras:acceso",
    "facturacion:rentabilidad_producto",
    "facturacion:rentabilidad_doc",
    "facturacion:ventas_cliente",

    # Activos
    "activos:acceso",
    "activos:listar",
    "activos:configurar"
]

def seed_permissions():
    db = SessionLocal()
    try:
        print("Starting Permission Seeding...")
        for perm_name in NEW_PERMISSIONS:
            exists = db.query(Permiso).filter(Permiso.nombre == perm_name).first()
            if not exists:
                print(f"Creating permission: {perm_name}")
                # Create readable description by capitalizing and replacing _ with space
                parts = perm_name.split(':')
                module = parts[0].replace('_', ' ').capitalize()
                action = parts[1].replace('_', ' ').capitalize()
                desc = f"Permite acceso a {module} - {action}"
                
                new_perm = Permiso(nombre=perm_name, descripcion=desc)
                db.add(new_perm)
            else:
                print(f"Permission exists: {perm_name}")
        
        db.commit()
        print("Seeding Complete.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_permissions()
