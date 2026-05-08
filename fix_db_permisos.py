import sqlite3
import json

db_path = r"C:\Users\lenovo\AppData\Roaming\Finaxis\finaxis_local.db"

permisos_faltantes = [
    "analisis_financiero:acceso", "analisis_financiero:dashboard", "analisis_financiero:ratios", "analisis_financiero:vertical",
    "analisis_financiero:horizontal", "analisis_financiero:fuentes_usos", "analisis_financiero:flujos_efectivo",
    "ph:acceso", "ph:unidades", "ph:propietarios", "ph:conceptos", "ph:facturacion", "ph:pagos", "ph:estado_cuenta",
    "ph:reportes", "ph:configuracion", "nomina:acceso", "nomina:empleados", "nomina:liquidar", "nomina:desprendibles",
    "nomina:configuracion", "produccion:acceso", "produccion:recetas", "produccion:ordenes", "conciliacion_bancaria:acceso",
    "conciliacion_bancaria:dashboard", "conciliacion_bancaria:conciliar", "conciliacion_bancaria:importar", "conciliacion_bancaria:reportes",
    "conciliacion_bancaria:configurar", "contabilidad:acceso", "contabilidad:crear_documento", "contabilidad:captura_rapida",
    "contabilidad:explorador", "contabilidad:libro_diario", "contabilidad:analisis_cuenta", "contabilidad:balance_general",
    "contabilidad:pyg", "contabilidad:balance_prueba", "contabilidad:auxiliar", "contabilidad:libros_oficiales", "contabilidad:auditoria_avanzada",
    "centros_costo:acceso", "centros_costo:gestionar", "centros_costo:auxiliar", "centros_costo:balance", "centros_costo:pyg",
    "centros_costo:balance_prueba", "terceros:acceso", "terceros:gestionar", "terceros:auxiliar", "terceros:estado_cuenta_cliente",
    "terceros:cartera", "terceros:estado_cuenta_proveedor", "terceros:auxiliar_proveedores", "impuestos:acceso", "impuestos:iva",
    "impuestos:renta", "impuestos:retefuente", "impuestos:reteica", "impuestos:timbre", "impuestos:consumo", "impuestos:calendario",
    "inventario:acceso", "inventario:configuracion", "inventario:kardex", "inventario:estadisticas", "inventario:auditoria",
    "inventario:traslados", "inventario:ajustes", "inventario:topes", "facturacion:acceso", "facturacion:nueva", "facturacion:remisiones",
    "facturacion:reporte_remisiones", "facturacion:cotizaciones", "compras:acceso", "facturacion:rentabilidad_producto",
    "facturacion:rentabilidad_doc", "facturacion:ventas_cliente", "activos:acceso", "activos:listar", "activos:configurar",
    "administracion:acceso", "contabilidad:gestionar_puc", "contabilidad:configuracion_tipos_doc", "contabilidad:configuracion_plantillas",
    "contabilidad:configuracion_conceptos", "empresa:gestionar_empresas", "empresa:usuarios_roles", "utilidades:migracion",
    "utilidades:cierre_periodos", "utilidades:auditoria_consecutivos", "utilidades:conteo_registros", "utilidades:scripts",
    "utilidades:edicion_masiva", "utilidades:recodificacion", "papelera:usar", "utilidades:config_correo"
]

def fix_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Insert missing permissions
    for perm in permisos_faltantes:
        cursor.execute("SELECT id FROM permisos WHERE nombre = ?", (perm,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO permisos (nombre, descripcion) VALUES (?, ?)", (perm, f"Permiso para {perm}"))
            print(f"Creado permiso: {perm}")
    
    # 2. Get the 'soporte' and 'Administrador' roles
    roles = ["soporte", "Administrador"]
    for role_name in roles:
        cursor.execute("SELECT id FROM roles WHERE nombre = ?", (role_name,))
        row = cursor.fetchone()
        if row:
            role_id = row[0]
            # 3. Associate all permissions with the role
            for perm in permisos_faltantes:
                cursor.execute("SELECT id FROM permisos WHERE nombre = ?", (perm,))
                perm_id = cursor.fetchone()[0]
                
                cursor.execute("SELECT 1 FROM rol_permisos WHERE rol_id = ? AND permiso_id = ?", (role_id, perm_id))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO rol_permisos (rol_id, permiso_id) VALUES (?, ?)", (role_id, perm_id))
            print(f"Asignados todos los permisos al rol: {role_name}")

    conn.commit()
    conn.close()
    print("Database fix completed!")

if __name__ == '__main__':
    fix_db()
