# app/core/seeder.py (Versión con permiso para Super Informe Inventarios)

from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from ..models.empresa import Empresa
from ..models.usuario import Usuario
from ..models import permiso as models_permiso
from ..schemas import usuario as usuario_schema
from ..services import usuario as usuario_service
from ..services.seeder_puc import seed_puc_simplificado # Importar seeder PUC

def seed_database():
    """
    Función principal para sembrar la base de datos con datos iniciales.
    Sigue el Principio de la "Instalación Atómica".
    """
    db = SessionLocal()
    try:
        # Nota: Eliminamos el check de 'Rol' al inicio para permitir que updates progresivos (como nuevos permisos o PUC) corran.
        # En su lugar, cada bloque debe ser idempotente (verificar si existe antes de crear).
        
        print("Iniciando proceso de sembrado/actualización...")

        # ... (Mantener lógica de permisos y roles igual) ...

        
        # --- FASE 1: DEFINIR Y CREAR TODOS LOS DATOS INICIALES ---
        print("--> Definiendo roles y su mapa de permisos inicial...")

        # --- INICIO DE LA MODIFICACIÓN: Añadir permiso Super Informe ---
        permisos_por_rol = {
            "soporte": [
                "analisis_financiero:acceso",
                "analisis_financiero:dashboard",
                "analisis_financiero:ratios",
                "analisis_financiero:vertical",
                "analisis_financiero:horizontal",
                "analisis_financiero:fuentes_usos",
                "analisis_financiero:flujos_efectivo",
                "ph:acceso",
                "ph:unidades",
                "ph:propietarios",
                "ph:conceptos",
                "ph:facturacion",
                "ph:pagos",
                "ph:estado_cuenta",
                "ph:reportes",
                "ph:configuracion",
                "nomina:acceso",
                "nomina:empleados",
                "nomina:liquidar",
                "nomina:desprendibles",
                "nomina:configuracion",
                "produccion:acceso",
                "produccion:recetas",
                "produccion:ordenes",
                "conciliacion_bancaria:acceso",
                "conciliacion_bancaria:dashboard",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:reportes",
                "conciliacion_bancaria:configurar",
                "contabilidad:acceso",
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
                "centros_costo:acceso",
                "centros_costo:gestionar",
                "centros_costo:auxiliar",
                "centros_costo:balance",
                "centros_costo:pyg",
                "centros_costo:balance_prueba",
                "terceros:acceso",
                "terceros:gestionar",
                "terceros:auxiliar",
                "terceros:estado_cuenta_cliente",
                "terceros:cartera",
                "terceros:estado_cuenta_proveedor",
                "terceros:auxiliar_proveedores",
                "impuestos:acceso",
                "impuestos:iva",
                "impuestos:renta",
                "impuestos:retefuente",
                "impuestos:reteica",
                "impuestos:timbre",
                "impuestos:consumo",
                "impuestos:calendario",
                "inventario:acceso",
                "inventario:configuracion",
                "inventario:kardex",
                "inventario:estadisticas",
                "inventario:auditoria",
                "inventario:traslados",
                "inventario:ajustes",
                "inventario:topes",
                "facturacion:acceso",
                "facturacion:nueva",
                "facturacion:remisiones",
                "facturacion:reporte_remisiones",
                "facturacion:cotizaciones",
                "compras:acceso",
                "facturacion:rentabilidad_producto",
                "facturacion:rentabilidad_doc",
                "facturacion:ventas_cliente",
                "activos:acceso",
                "activos:listar",
                "activos:configurar",
                "administracion:acceso",
                "contabilidad:gestionar_puc",
                "contabilidad:configuracion_tipos_doc",
                "contabilidad:configuracion_plantillas",
                "contabilidad:configuracion_conceptos",
                "empresa:gestionar_empresas",
                "empresa:usuarios_roles",
                "utilidades:migracion",
                "utilidades:cierre_periodos",
                "utilidades:auditoria_consecutivos",
                "utilidades:conteo_registros",
                "utilidades:scripts",
                "utilidades:edicion_masiva",
                "utilidades:recodificacion",
                "papelera:usar",
                "utilidades:config_correo",

                "soporte:acceder_panel",
                "empresa:gestionar",
                "utilidades:usar_herramientas",
                "utilidades:scripts",
                "utilidades:conteo_registros",
                "utilidades:auditoria_consecutivos",
                "inventario:ver_super_informe",
                "empresa:usuarios_roles",
                
                # --- VISIBILIDAD DE MODULOS (Frontend Groups) ---
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
                "administracion:acceso",

                # --- OPERACIONES (Existing) ---
                "contabilidad:crear_documento",
                "contabilidad:editar_documento",
                "contabilidad:anular_documento",
                "contabilidad:explorador",
                "contabilidad:configuracion_tipos_doc",
                "contabilidad:gestionar_puc",
                
                "inventario:ver_reportes",
                "inventario:eliminar_producto",
                "plantilla:crear",
                
                "conciliacion_bancaria:ver",
                "conciliacion_bancaria:configurar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:ajustar",
                "conciliacion_bancaria:reportes",
                "conciliacion_bancaria:auditoria",
                
                "reportes:rentabilidad_producto",
                "ventas:ver_reporte_gestion",
                "reportes:ver_facturacion_detallado",
                "reportes:ver_officiales",
                
                "tesoreria:crear_comprobante",
                "cartera:ver_informes",
                "papelera:usar",
                "utilidades:migracion"
            ],
            "Administrador": [
                "analisis_financiero:acceso",
                "analisis_financiero:dashboard",
                "analisis_financiero:ratios",
                "analisis_financiero:vertical",
                "analisis_financiero:horizontal",
                "analisis_financiero:fuentes_usos",
                "analisis_financiero:flujos_efectivo",
                "ph:acceso",
                "ph:unidades",
                "ph:propietarios",
                "ph:conceptos",
                "ph:facturacion",
                "ph:pagos",
                "ph:estado_cuenta",
                "ph:reportes",
                "ph:configuracion",
                "nomina:acceso",
                "nomina:empleados",
                "nomina:liquidar",
                "nomina:desprendibles",
                "nomina:configuracion",
                "produccion:acceso",
                "produccion:recetas",
                "produccion:ordenes",
                "conciliacion_bancaria:acceso",
                "conciliacion_bancaria:dashboard",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:reportes",
                "conciliacion_bancaria:configurar",
                "contabilidad:acceso",
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
                "centros_costo:acceso",
                "centros_costo:gestionar",
                "centros_costo:auxiliar",
                "centros_costo:balance",
                "centros_costo:pyg",
                "centros_costo:balance_prueba",
                "terceros:acceso",
                "terceros:gestionar",
                "terceros:auxiliar",
                "terceros:estado_cuenta_cliente",
                "terceros:cartera",
                "terceros:estado_cuenta_proveedor",
                "terceros:auxiliar_proveedores",
                "impuestos:acceso",
                "impuestos:iva",
                "impuestos:renta",
                "impuestos:retefuente",
                "impuestos:reteica",
                "impuestos:timbre",
                "impuestos:consumo",
                "impuestos:calendario",
                "inventario:acceso",
                "inventario:configuracion",
                "inventario:kardex",
                "inventario:estadisticas",
                "inventario:auditoria",
                "inventario:traslados",
                "inventario:ajustes",
                "inventario:topes",
                "facturacion:acceso",
                "facturacion:nueva",
                "facturacion:remisiones",
                "facturacion:reporte_remisiones",
                "facturacion:cotizaciones",
                "compras:acceso",
                "facturacion:rentabilidad_producto",
                "facturacion:rentabilidad_doc",
                "facturacion:ventas_cliente",
                "activos:acceso",
                "activos:listar",
                "activos:configurar",
                "administracion:acceso",
                "contabilidad:gestionar_puc",
                "contabilidad:configuracion_tipos_doc",
                "contabilidad:configuracion_plantillas",
                "contabilidad:configuracion_conceptos",
                "empresa:gestionar_empresas",
                "empresa:usuarios_roles",
                "utilidades:migracion",
                "utilidades:cierre_periodos",
                "utilidades:auditoria_consecutivos",
                "utilidades:conteo_registros",
                "utilidades:scripts",
                "utilidades:edicion_masiva",
                "utilidades:recodificacion",
                "papelera:usar",
                "utilidades:config_correo",

                "empresa:gestionar", # Restaurado para acceso
                "utilidades:migracion", # Restaurado para Maestros
                "inventario:ver_super_informe", # Restaurado para Super Informe
                "inventario:ver_reportes",
                "reportes:rentabilidad_producto",
                "ventas:ver_reporte_gestion",
                "reportes:ver_facturacion_detallado",
                "papelera:usar",
                "plantilla:crear",
                "inventario:eliminar_producto",
                "conciliacion_bancaria:ver",
                "conciliacion_bancaria:configurar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:ajustar",
                "conciliacion_bancaria:reportes",
                "conciliacion_bancaria:auditoria",
                # --- PERMISOS CRÍTICOS RESTAURADOS DE EMERGENCIA ---
                "contabilidad:crear_documento",
                "contabilidad:editar_documento",
                "contabilidad:anular_documento",
                "contabilidad:explorador",
                "contabilidad:configuracion_tipos_doc",
                "contabilidad:gestionar_puc",
                "tesoreria:crear_comprobante",
                "cartera:ver_informes",
                "reportes:ver_officiales"
            ],
            "operador_bancario": [
                # Rol especializado para conciliación bancaria
                "conciliacion_bancaria:ver",
                "conciliacion_bancaria:configurar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:ajustar",
                "conciliacion_bancaria:reportes",
                "inventario:ver_reportes"
            ],
            "contador": [
                "dashboard:contador",
                "empresa:crear_desde_plantilla",
                "empresa:gestionar_cartera",
                "reportes:ver_consolidado_cartera",
                "utilidades:comprar_recargas",
                "administracion:acceso",
                
                # --- PERMISOS OPERATIVOS (HEREDADOS DE ADMIN) ---
                # El contador debe poder operar totalmente las empresas de sus clientes
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
                
                "contabilidad:crear_documento",
                "contabilidad:editar_documento",
                "contabilidad:anular_documento",
                "contabilidad:explorador",
                "contabilidad:configuracion_tipos_doc",
                "contabilidad:gestionar_puc",
                
                "inventario:ver_reportes",
                "inventario:eliminar_producto",
                "plantilla:crear",
                
                "conciliacion_bancaria:ver",
                "conciliacion_bancaria:configurar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:ajustar",
                "conciliacion_bancaria:reportes",
                "conciliacion_bancaria:auditoria",
                
                "reportes:rentabilidad_producto",
                "ventas:ver_reporte_gestion",
                "reportes:ver_facturacion_detallado",
                "reportes:ver_officiales",
                
                "tesoreria:crear_comprobante",
                "cartera:ver_informes",
                "papelera:usar"
            ],
            "clon_restringido": [
                 # Rol CLON RESTRINGIDO (Auditoría): Solo lectura, sin creación de documentos.
                 # Bloqueado: contabilidad:crear_documento, facturacion:crear (si existiera), etc.
                 "contabilidad:explorador",
                 "contabilidad:configuracion_tipos_doc",
                 "contabilidad:gestionar_puc",
                 "contabilidad:editar_documento",
                 
                 "inventario:ver_super_informe",
                 "inventario:ver_reportes",
                 "reportes:rentabilidad_producto",
                 "ventas:ver_reporte_gestion",
                 "reportes:ver_facturacion_detallado",
                 "reportes:ver_officiales",
                 
                 "cartera:ver_informes",
                 
                 "conciliacion_bancaria:ver",
                 "conciliacion_bancaria:reportes",
                 "conciliacion_bancaria:auditoria",
                 
                 # NOTA: Se excluyen explícitamente permisos de creación/edición/anulación
                 # y acceso a herramientas de soporte.
            ],
        }
        # --- FIN DE LA MODIFICACIÓN ---
        
        todos_los_permisos_nombres = set()
        for _, lista_permisos in permisos_por_rol.items():
            todos_los_permisos_nombres.update(lista_permisos)

        print(f"--> Asegurando la existencia de {len(todos_los_permisos_nombres)} permisos...")
        for nombre_permiso in todos_los_permisos_nombres:
            if not db.query(models_permiso.Permiso).filter(models_permiso.Permiso.nombre == nombre_permiso).first():
                db.add(models_permiso.Permiso(nombre=nombre_permiso, descripcion=f"Permiso para {nombre_permiso}"))
        
        db.flush()

        print("--> Asegurando la existencia de todos los roles...")
        roles_a_crear = ["soporte", "Administrador", "contador", "invitado", "operador_bancario", "clon_restringido"]
        for nombre_rol in roles_a_crear:
            if not db.query(models_permiso.Rol).filter(models_permiso.Rol.nombre == nombre_rol).first():
                db.add(models_permiso.Rol(nombre=nombre_rol, descripcion=f"Rol para {nombre_rol}"))
        
        db.flush()

        # --- FASE 2: ASIGNAR PERMISOS A ROLES ---
        print("--> Asignando permisos a los roles correspondientes...")
        for rol_nombre, lista_permisos in permisos_por_rol.items():
            rol_db = db.query(models_permiso.Rol).filter(models_permiso.Rol.nombre == rol_nombre).first()
            
            if not rol_db:
                print(f"--> ERROR: Rol '{rol_nombre}' no encontrado, saltando asignación.")
                continue

            # --- FIX GENERAL: PROTECCIÓN DE PERMISOS DE USUARIO ---
            # Si el rol ya tiene permisos asignados (proviene de DB con datos),
            # ASUMIMOS que el usuario pudo haberlos personalizado.
            # NO sobrescribimos para evitar "desbaratar" la configuración del administrador.
            if rol_db.permisos:
                 print(f"--> PROTEGIDO: Saltando actualización de permisos para rol '{rol_nombre}' (Ya configurado/Personalizado).")
                 continue
            # ------------------------------------------------------

            permisos_db = db.query(models_permiso.Permiso).filter(models_permiso.Permiso.nombre.in_(lista_permisos)).all()
            rol_db.permisos = permisos_db
        
        print("--> Permisos asignados exitosamente.")

        # --- FASE 3: CREAR USUARIO DE SOPORTE MAESTRO ---
        print("--> Creando usuario de soporte maestro...")
        
        usuario_soporte = {
            "email": "soporte@soporte.com", 
            "nombre_completo": "Usuario de Soporte Global", 
            "password": "Panica3319535576+-", 
            "rol_nombre": "soporte", 
            "empresa_id": None
        }
        
        rol_db_soporte = db.query(models_permiso.Rol).filter(models_permiso.Rol.nombre == usuario_soporte['rol_nombre']).first()
        if rol_db_soporte:
            if not usuario_service.get_user_by_email(db, email=usuario_soporte['email']):
                usuario_a_crear = usuario_schema.UserCreateInCompany(
                    email=usuario_soporte['email'], 
                    nombre_completo=usuario_soporte.get('nombre_completo'), 
                    password=usuario_soporte['password'], 
                    roles_ids=[rol_db_soporte.id]
                )
                usuario_service.create_user_in_company(db=db, user_data=usuario_a_crear, empresa_id=None)
                print("--> Usuario de Soporte creado con éxito.")
            else:
                print("--> Usuario de Soporte ya existe.")

        # --- NOTA: LA EMPRESA DEMO Y USUARIO ADMIN SE HAN ELIMINADO ---
        # Ahora el sistema se inicializará vía Asistente de Bienvenida (Setup Wizard)
        # cuando el usuario abra el programa por primera vez.

        # --- FASE 4: CIERRE DE LA TRANSACCIÓN ---
        db.commit()
        print("Proceso de sembrado atómico completado. Sistema listo para inicialización por el cliente.")
    except Exception as e:
        print(f"ERROR DURANTE EL SEMBRADO: {e}")
        db.rollback()
    finally:
        db.close()