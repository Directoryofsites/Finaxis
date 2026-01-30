
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.permiso import Rol, Permiso
from app.core.seeder import seed_database

# Reusamos la lógica del seeder simplemente llamándolo, ya que es idempotente y actualiza permisos.
# O para ser más rápidos, solo actualizamos los permisos del rol contador.

def hotfix_permissions():
    db = SessionLocal()
    try:
        print("--- ACTUALIZANDO PERMISOS DE CONTADOR ---")
        contador_role = db.query(Rol).filter(Rol.nombre == "contador").first()
        if not contador_role:
            print("Rol contador no encontrado.")
            return

        # Lista de permisos nuevos según seeder.py (copia manual para asegurar)
        permisos_nombres = [
                # --- DASHBOARD & GENERAL ---
                "dashboard:contador",
                "empresa:crear_desde_plantilla",
                "empresa:gestionar_cartera",
                "reportes:ver_consolidado_cartera",
                "utilidades:comprar_recargas",
                "administracion:acceso",
                "contabilidad:acceso",
                "analisis_financiero:acceso",
                "ph:acceso",
                "nomina:acceso",
                "produccion:acceso",
                "conciliacion_bancaria:acceso",
                "facturacion:acceso",
                "compras:acceso",
                "activos:acceso",
                "centros_costo:acceso",
                "terceros:acceso",
                "impuestos:acceso",
                "inventario:acceso",
                "tesoreria:acceso", 
                "cartera:acceso",   

                # --- CONTABILIDAD ---
                "contabilidad:crear_documento",
                "contabilidad:captura_rapida",
                "contabilidad:explorador",
                "contabilidad:libro_diario",
                "contabilidad:analisis_cuenta",
                "contabilidad:balance_general",
                "contabilidad:pyg",
                "contabilidad:balance_prueba",
                "contabilidad:auxiliar",
                "contabilidad:libros_oficiales",
                "contabilidad:auditoria_avanzada",
                "contabilidad:editar_documento",
                "contabilidad:anular_documento",
                "contabilidad:configuracion_tipos_doc",
                "contabilidad:configuracion_plantillas",
                "contabilidad:configuracion_conceptos",
                "contabilidad:gestionar_puc",
                "contabilidad:traslados",    

                # --- ANALISIS FINANCIERO ---
                "analisis_financiero:dashboard",
                "analisis_financiero:ratios",
                "analisis_financiero:vertical",
                "analisis_financiero:horizontal",
                "analisis_financiero:fuentes_usos",
                "analisis_financiero:flujos_efectivo",

                # --- CENTROS DE COSTO ---
                "centros_costo:gestionar",
                "centros_costo:auxiliar",
                "centros_costo:balance",
                "centros_costo:pyg",
                "centros_costo:balance_prueba",

                # --- TERCEROS ---
                "terceros:gestionar",
                "terceros:auxiliar",
                "terceros:estado_cuenta_cliente",
                "terceros:cartera",
                "terceros:estado_cuenta_proveedor",
                "terceros:auxiliar_proveedores",
                
                # --- IMPUESTOS ---
                "impuestos:iva",
                "impuestos:renta",
                "impuestos:retefuente",
                "impuestos:reteica",
                "impuestos:timbre",
                "impuestos:consumo",
                "impuestos:calendario",

                # --- INVENTARIOS ---
                "inventario:configuracion",
                "inventario:kardex",
                "inventario:estadisticas",
                "inventario:auditoria",
                "inventario:traslados",
                "inventario:ajustes",
                "inventario:topes",
                "inventario:ver_reportes",
                "inventario:eliminar_producto",

                # --- FACTURACION ---
                "facturacion:nueva",
                "facturacion:remisiones",
                "facturacion:reporte_remisiones",
                "facturacion:cotizaciones",
                "facturacion:rentabilidad_producto",
                "facturacion:rentabilidad_doc",
                "facturacion:ventas_cliente",

                # --- ACTIVOS FIJOS ---
                "activos:listar",
                "activos:configurar",

                # --- PH ---
                "ph:unidades",
                "ph:propietarios",
                "ph:conceptos",
                "ph:facturacion",
                "ph:pagos",
                "ph:estado_cuenta",
                "ph:reportes",
                "ph:configuracion",

                # --- NOMINA ---
                "nomina:empleados",
                "nomina:liquidar",
                "nomina:desprendibles",
                "nomina:configuracion",

                # --- PRODUCCION ---
                "produccion:recetas",
                "produccion:ordenes",

                # --- CONCILIACION BANCARIA ---
                "conciliacion_bancaria:dashboard",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:reportes",
                "conciliacion_bancaria:configurar",
                "conciliacion_bancaria:ver",
                "conciliacion_bancaria:ajustar",
                "conciliacion_bancaria:auditoria",
                
                # --- ADMIN UTILIDADES ---
                "empresa:gestionar_empresas",
                "empresa:usuarios_roles",
                "utilidades:migracion",
                "utilidades:cierre_periodos",
                "utilidades:auditoria_consecutivos",
                "utilidades:conteo_registros",
                "utilidades:edicion_masiva",
                "utilidades:recodificacion",
                "papelera:usar",
                "utilidades:config_correo",
                
                "plantilla:crear",
                "reportes:ver_facturacion_detallado",
                "reportes:ver_officiales",
                "tesoreria:crear_comprobante",
                "cartera:ver_informes",
                "ventas:ver_reporte_gestion"
        ]

        nuevos_permisos = db.query(Permiso).filter(Permiso.nombre.in_(permisos_nombres)).all()
        
        # Actualizar relación
        contador_role.permisos = nuevos_permisos
        db.commit()
        print(f"Permisos actualizados. Total: {len(nuevos_permisos)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    hotfix_permissions()
