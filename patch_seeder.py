import re

file_path = r"C:\ContaPY2\app\core\seeder.py"

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

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

def inject_permissions(content, role_name):
    # Find the start of the list for the role
    match = re.search(f'"{role_name}":\s*\[', content)
    if not match:
        return content
    
    start_idx = match.end()
    # Construct the injection string
    injection = "\n" + "\n".join([f'                "{p}",' for p in permisos_faltantes]) + "\n"
    
    return content[:start_idx] + injection + content[start_idx:]

content = inject_permissions(content, "soporte")
content = inject_permissions(content, "Administrador")

# Write it back
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("seeder.py patched successfully!")
