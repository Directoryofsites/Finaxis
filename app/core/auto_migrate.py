
from sqlalchemy import text
from app.core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_auto_migrations():
    """
    Ejecuta migraciones automáticas simples al iniciar la aplicación.
    Verifica y añade columnas faltantes en tablas clave (empresas y configuracion_fe).
    """
    logger.info("Iniciando auto-migraciones de esquema...")
    
    try:
        migrations = []
        # Usamos una conexión limpia para inspeccionar
        with engine.connect() as connection:
            
            # 1. Obtener todas las columnas existentes en las tablas objetivo
            # Esto evita errores de 'transaction aborted' al intentar SELECTs de columnas inexistentes
            def get_existing_columns(table_name):
                # Usamos LOWER(table_name) para mayor seguridad en PostgreSQL
                sql = text("SELECT column_name FROM information_schema.columns WHERE LOWER(table_name) = LOWER(:t)")
                try:
                    res = connection.execute(sql, {"t": table_name}).fetchall()
                    return {row[0].lower() for row in res}
                except Exception as e:
                    logger.warning(f"Error inspeccionando tabla {table_name}: {e}")
                    return set()

            cols_config_fe = get_existing_columns('configuracion_fe')
            cols_empresas = get_existing_columns('empresas')
            cols_productos = get_existing_columns('productos')
            cols_stock_bodegas = get_existing_columns('stock_bodegas')
            cols_grupos = get_existing_columns('grupos_inventario')
            cols_tasas = get_existing_columns('tasas_impuesto')
            cols_documentos = get_existing_columns('documentos')
            cols_terceros = get_existing_columns('terceros')
            cols_usuarios = get_existing_columns('usuarios')
            
            # --- PRIORIDAD #1: PROPIEDAD HORIZONTAL (Resuelve Problema de Abono Dirigido) ---
            # ph_conceptos
            cols_ph_conceptos = get_existing_columns('ph_conceptos')
            if cols_ph_conceptos: # Solo si la tabla ya existe (evita error en primer deploy)
                if 'orden' not in cols_ph_conceptos:
                    migrations.append(('ph_conceptos', 'orden', 'INTEGER DEFAULT 99'))
                if 'cuenta_caja_id' not in cols_ph_conceptos:
                    migrations.append(('ph_conceptos', 'cuenta_caja_id', 'INTEGER'))
            
            # ph_configuracion
            cols_ph_config = get_existing_columns('ph_configuracion')
            if cols_ph_config:
                if 'cuenta_anticipos_id' not in cols_ph_config:
                    migrations.append(('ph_configuracion', 'cuenta_anticipos_id', 'INTEGER'))
                if 'tipo_documento_cruce_id' not in cols_ph_config:
                    migrations.append(('ph_configuracion', 'tipo_documento_cruce_id', 'INTEGER'))
                if 'cuenta_descuento_id' not in cols_ph_config:
                    migrations.append(('ph_configuracion', 'cuenta_descuento_id', 'INTEGER'))
                if 'tipo_documento_mora_id' not in cols_ph_config:
                    migrations.append(('ph_configuracion', 'tipo_documento_mora_id', 'INTEGER'))
                if 'tipo_negocio' not in cols_ph_config:
                    migrations.append(('ph_configuracion', 'tipo_negocio', "VARCHAR(50) DEFAULT 'PH_RESIDENCIAL'"))
                if 'interes_mora_habilitado' not in cols_ph_config:
                    migrations.append(('ph_configuracion', 'interes_mora_habilitado', "BOOLEAN DEFAULT TRUE"))
                if 'descuento_pronto_pago_habilitado' not in cols_ph_config:
                    migrations.append(('ph_configuracion', 'descuento_pronto_pago_habilitado', "BOOLEAN DEFAULT TRUE"))

            # ph_unidades
            cols_ph_unidades = get_existing_columns('ph_unidades')
            if cols_ph_unidades:
                if 'referencia_recaudo' not in cols_ph_unidades:
                    migrations.append(('ph_unidades', 'referencia_recaudo', 'VARCHAR(50)'))
                if 'aplica_pronto_pago' not in cols_ph_unidades:
                    migrations.append(('ph_unidades', 'aplica_pronto_pago', 'BOOLEAN DEFAULT TRUE'))

            # --- OTRAS MIGRACIONES ---
            # configuracion_fe (FACTURACIÓN ELECTRÓNICA, DS, NOTAS)
            config_fe_cols = [
                ("factura_rango_id", "INTEGER"),
                ("ds_prefijo", "VARCHAR(10)"),
                ("ds_resolucion_numero", "VARCHAR(50)"),
            ]
            # configuracion_fe
            for col, col_type in config_fe_cols:
                if col not in cols_config_fe:
                    migrations.append(('configuracion_fe', col, col_type))
                
            # empresas
            empresa_lite_cols = [
                ("is_lite_mode", "BOOLEAN DEFAULT FALSE"),
                ("saldo_facturas_venta", "INTEGER DEFAULT 0"),
                ("saldo_documentos_soporte", "INTEGER DEFAULT 0"),
                ("saldo_notas_credito", "INTEGER DEFAULT 0"),
                ("fecha_vencimiento_plan", "DATE"),
                ("limite_mensajes_ia_mensual", "INTEGER DEFAULT 0"),
                ("consumo_mensajes_ia_actual", "INTEGER DEFAULT 0"),
                ("fecha_reinicio_cuota_ia", "DATE")
            ]
            for col, col_type in empresa_lite_cols:
                if col not in cols_empresas:
                    migrations.append(('empresas', col, col_type))

            # usuarios
            if 'whatsapp_number' not in cols_usuarios:
                migrations.append(('usuarios', 'whatsapp_number', 'VARCHAR(50)'))
            if 'totp_secret' not in cols_usuarios:
                migrations.append(('usuarios', 'totp_secret', 'VARCHAR(64)'))
            if 'totp_enabled' not in cols_usuarios:
                migrations.append(('usuarios', 'totp_enabled', 'BOOLEAN DEFAULT FALSE'))

            # productos
            producto_cols = [
                ("controlar_inventario", "BOOLEAN DEFAULT TRUE"),
                ("precio_base_manual", "FLOAT"),
                ("impuesto_iva_id", "INTEGER")
            ]
            for col, col_type in producto_cols:
                if col not in cols_productos:
                    migrations.append(('productos', col, col_type))

            # stock_bodegas
            if 'stock_comprometido' not in cols_stock_bodegas:
                migrations.append(('stock_bodegas', 'stock_comprometido', 'FLOAT DEFAULT 0.0'))

            # grupos_inventario
            grupo_cols = [
                ("cuenta_costo_produccion_id", "INTEGER"),
                ("impuesto_predeterminado_id", "INTEGER")
            ]
            for col, col_type in grupo_cols:
                if col not in cols_grupos:
                    migrations.append(('grupos_inventario', col, col_type))

            # tasas_impuesto
            tasa_cols = [
                ("cuenta_id", "INTEGER"),
                ("cuenta_iva_descontable_id", "INTEGER")
            ]
            for col, col_type in tasa_cols:
                if col not in cols_tasas:
                    migrations.append(('tasas_impuesto', col, col_type))

            # documentos
            documento_cols = [
                ("dian_estado", "VARCHAR(20)"),
                ("dian_cufe", "VARCHAR(255)"),
                ("dian_xml_url", "VARCHAR(500)"),
                ("dian_error", "TEXT"),
                ("provider_id", "VARCHAR(255)"),
                ("reconciliation_reference", "VARCHAR(255)"),
                ("documento_referencia_id", "INTEGER"),
                ("descuento_global_valor", "NUMERIC(15, 2) DEFAULT 0"),
                ("cargos_globales_valor", "NUMERIC(15, 2) DEFAULT 0"),
                ("unidad_ph_id", "INTEGER"),
                ("vendedor_id", "INTEGER"),
            ]
            for col, col_type in documento_cols:
                if col not in cols_documentos:
                    migrations.append(('documentos', col, col_type))

            # terceros
            tercero_cols = [
                ("tipo_documento", "VARCHAR(5) DEFAULT '13'"),
                ("tipo_persona", "VARCHAR(1) DEFAULT '2'"),
                ("municipio_dane", "VARCHAR(10)"),
                ("codigo_postal", "VARCHAR(10)"),
                ("regimen_fiscal", "VARCHAR(5)"),
                ("responsabilidad_fiscal", "VARCHAR(20)"),
                ("lista_precio_id", "INTEGER"),
                ("cuenta_gasto_defecto_id", "INTEGER"),
                ("es_vendedor", "BOOLEAN DEFAULT FALSE"),
            ]
            for col, col_type in tercero_cols:
                if col not in cols_terceros:
                    migrations.append(('terceros', col, col_type))

            # indicadores_economicos
            cols_indicadores = get_existing_columns('indicadores_economicos')
            if cols_indicadores:
                indicadores_cols = [("tasa_usura", "FLOAT"), ("fecha_sincronizacion", "DATE")]
                for col, col_type in indicadores_cols:
                    if col not in cols_indicadores:
                        migrations.append(('indicadores_economicos', col, col_type))

            # empresa_config_buzon
            cols_empresa_config_buzon = get_existing_columns('empresa_config_buzon')
            if cols_empresa_config_buzon:
                empresa_config_buzon_cols = [
                    ("venta_tipo_documento_id", "INTEGER"),
                    ("venta_cuenta_ingreso_id", "INTEGER"),
                    ("venta_cuenta_caja_id", "INTEGER"),
                    ("soporte_tipo_documento_id", "INTEGER"),
                    ("soporte_cuenta_gasto_id", "INTEGER"),
                    ("soporte_cuenta_caja_id", "INTEGER"),
                    ("is_active", "BOOLEAN DEFAULT TRUE")
                ]
                for col, col_type in empresa_config_buzon_cols:
                    if col not in cols_empresa_config_buzon:
                        migrations.append(('empresa_config_buzon', col, col_type))



            # copia_seguridad
            cols_copia_seguridad = get_existing_columns('copia_seguridad')
            if cols_copia_seguridad:
                if 'es_valido' not in cols_copia_seguridad:
                    migrations.append(('copia_seguridad', 'es_valido', 'INTEGER DEFAULT 0'))
                if 'error_verificacion' not in cols_copia_seguridad:
                    migrations.append(('copia_seguridad', 'error_verificacion', 'TEXT'))

            # 3. Ejecutar migraciones independientemente para evitar Rollbacks completos
            if migrations:
                with engine.connect() as conn:
                    for table, col, col_type in migrations:
                        logger.info(f"Migrando: Añadiendo {col} a {table}...")
                        try:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                            conn.commit()
                            logger.info(f"Columna {col} verificada/añadida en {table}.")
                        except Exception as e:
                            logger.error(f"Error añadiendo {col} a {table}: {e}")
                            conn.rollback() # Limpiar la transacción para la siguiente
            else:
                logger.info("No se requieren migraciones de esquema pendientes.")

            # 4. Crear tabla ph_modulo_torre_association si no existe
            logger.info("Verificando tabla ph_modulo_torre_association...")
            with engine.begin() as trans_conn:
                trans_conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ph_modulo_torre_association (
                        modulo_id INTEGER NOT NULL REFERENCES ph_modulos_contribucion(id) ON DELETE CASCADE,
                        torre_id INTEGER NOT NULL REFERENCES ph_torres(id) ON DELETE CASCADE,
                        PRIMARY KEY (modulo_id, torre_id)
                    )
                """))
                logger.info("Tabla ph_modulo_torre_association verificada/creada.")

            # 4. Auto-configuración de Rangos Sandbox (Self-healing)
            # Si estamos en PRUEBAS y los rangos son NULL, poner los defaults conocidos
            logger.info("Verificando consistencia de rangos en ambiente PRUEBAS...")
            with engine.begin() as trans_conn:
                # Factura (8), NC (9), ND (10), DS (148)
                trans_conn.execute(text("""
                    UPDATE configuracion_fe 
                    SET factura_rango_id = 8 
                    WHERE ambiente = 'PRUEBAS' AND factura_rango_id IS NULL
                """))
                trans_conn.execute(text("""
                    UPDATE configuracion_fe 
                    SET nc_rango_id = 9 
                    WHERE ambiente = 'PRUEBAS' AND nc_rango_id IS NULL
                """))
                trans_conn.execute(text("""
                    UPDATE configuracion_fe 
                    SET nd_rango_id = 10 
                    WHERE ambiente = 'PRUEBAS' AND nd_rango_id IS NULL
                """))
                trans_conn.execute(text("""
                    UPDATE configuracion_fe 
                    SET ds_rango_id = 148 
                    WHERE ambiente = 'PRUEBAS' AND ds_rango_id IS NULL
                """))
                
    except Exception as e:
        logger.error(f"Error crítico en auto-migraciones: {e}")
            
    logger.info("Auto-migraciones finalizadas.")

    # 5. DATA FIX: Asegurar que los tipos de documento de compra tengan es_compra=True
    # Esto corrige datos históricos donde el campo fue añadido después de crear los tipos.
    # Es idempotente (safe to run multiple times).
    logger.info("Verificando flags es_compra / es_venta en tipos_documento...")
    try:
        with engine.begin() as trans_conn:
            # Tipos de Compra: Por función seleccionada en UI o por código clásico
            trans_conn.execute(text("""
                UPDATE tipos_documento
                SET es_compra = TRUE
                WHERE (UPPER(codigo) IN ('FC', 'OC', 'RC', 'REC', 'NCC', 'DVC', 'DEVP')
                       OR LOWER(funcion_especial) IN ('cxp_proveedor', 'documento_soporte', 'pago_proveedor'))
                  AND es_compra = FALSE
            """))
            # Tipos de Venta: Por función seleccionada en UI o por código clásico
            trans_conn.execute(text("""
                UPDATE tipos_documento
                SET es_venta = TRUE
                WHERE (UPPER(codigo) IN ('FV', 'FE', 'NCV', 'NDV', 'REM', 'COT')
                       OR LOWER(funcion_especial) IN ('cartera_cliente', 'rc_cliente', 'factura_venta'))
                  AND es_venta = FALSE
            """))
            logger.info("Data fix de es_compra / es_venta aplicado correctamente.")
    except Exception as e:
        logger.error(f"Error en data fix de tipos_documento: {e}")

    # 6. DATA FIX: Asegurar que todas las empresas tengan cuota de IA inicializada (Auto-healing para producción)
    logger.info("Asegurando cuotas de IA para todas las empresas...")
    try:
        with engine.begin() as trans_conn:
            trans_conn.execute(text("""
                UPDATE empresas
                SET limite_mensajes_ia_mensual = 100
                WHERE limite_mensajes_ia_mensual IS NULL OR limite_mensajes_ia_mensual <= 0
            """))
            logger.info("Cuotas de IA inicializadas correctamente para todas las empresas.")
    except Exception as e:
        logger.error(f"Error inicializando cuotas de IA: {e}")

    # 7. Tabla de persistencia para el Tutor IA
    logger.info("Verificando tabla ai_tutor_messages...")
    try:
        with engine.begin() as trans_conn:
            trans_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_tutor_messages (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL, -- 'user' o 'assistant'
                    content TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("Tabla ai_tutor_messages verificada/creada.")
    except Exception as e:
        logger.error(f"Error creando tabla ai_tutor_messages: {e}")
