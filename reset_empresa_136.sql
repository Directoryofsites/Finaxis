-- ==========================================================
-- SCRIPT DE REINICIO DE EMPRESA (SAFE RESET v13 - FIX)
-- Objetivo: VACIAR datos operativos/maestros pero PRESERVAR Empresa y Acceso
-- Correcciones:
-- 1. Orden de borrado de HistorialConsumo (NUEVO)
-- 2. Orden de borrado de Logs y Documentos Eliminados
-- 3. Manejo de dependencias circulares en Terceros
-- ==========================================================

BEGIN; -- 🚀 Inicia la transacción

-- 1. LIMPIEZA DE DATOS DE CONSUMO (Nueva funcionalidad que bloqueaba borrado de documentos)
-- Primero borramos el historial que tiene FK a documentos y empresa
DELETE FROM historial_consumo WHERE empresa_id = 136;
-- Luego borramos las fuentes de consumo
DELETE FROM recarga_adicional WHERE empresa_id = 136;
DELETE FROM bolsa_excedente WHERE empresa_id = 136;
DELETE FROM control_plan_mensual WHERE empresa_id = 136;

-- 2. LIMPIEZA DE DATOS ASOCIADOS A USUARIOS (Historial y Preferencias)
-- Primero rompemos referencias en documentos_eliminados que apuntan a logs
UPDATE documentos_eliminados SET log_eliminacion_id = NULL WHERE empresa_id = 136;

DELETE FROM usuarios_favoritos WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = 136);
DELETE FROM usuarios_busquedas_guardadas WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = 136);
-- DELETE FROM usuario_roles ... (PRESERVADO)

-- 3. CONCILIACIÓN BANCARIA
DELETE FROM reconciliation_movements WHERE reconciliation_id IN (SELECT id FROM reconciliations WHERE empresa_id = 136);
DELETE FROM reconciliation_audits WHERE empresa_id = 136;
DELETE FROM reconciliations WHERE empresa_id = 136;
DELETE FROM bank_movements WHERE empresa_id = 136 OR import_session_id IN (SELECT id FROM import_sessions WHERE empresa_id = 136);
DELETE FROM import_sessions WHERE empresa_id = 136;
DELETE FROM accounting_configs WHERE empresa_id = 136;
DELETE FROM import_configs WHERE empresa_id = 136;
DELETE FROM import_templates WHERE empresa_id = 136;

-- 4. CONFIS Y MAESTROS PH
DELETE FROM ph_vehiculos WHERE unidad_id IN (SELECT id FROM ph_unidades WHERE empresa_id = 136);
DELETE FROM ph_mascotas WHERE unidad_id IN (SELECT id FROM ph_unidades WHERE empresa_id = 136);
DELETE FROM ph_coeficientes_historial WHERE unidad_id IN (SELECT id FROM ph_unidades WHERE empresa_id = 136);
DELETE FROM ph_unidad_modulo_association WHERE unidad_id IN (SELECT id FROM ph_unidades WHERE empresa_id = 136);
DELETE FROM ph_unidad_modulo_association WHERE modulo_id IN (SELECT id FROM ph_modulos_contribucion WHERE empresa_id = 136);
DELETE FROM ph_modulos_contribucion WHERE empresa_id = 136;
DELETE FROM ph_unidades WHERE empresa_id = 136;
DELETE FROM ph_torres WHERE empresa_id = 136;
DELETE FROM ph_concepto_modulo_association WHERE concepto_id IN (SELECT id FROM ph_conceptos WHERE empresa_id = 136);
DELETE FROM ph_configuracion WHERE empresa_id = 136;
DELETE FROM ph_conceptos WHERE empresa_id = 136;

-- 5. CONFIGURACIONES DE MÓDULOS
DELETE FROM produccion_configuracion WHERE empresa_id = 136;
DELETE FROM nomina_configuracion WHERE empresa_id = 136;

-- 6. LIMPIEZA INICIAL (Logs y Documentos Eliminados)
DELETE FROM movimientos_eliminados WHERE documento_eliminado_id IN (SELECT id FROM documentos_eliminados WHERE empresa_id = 136);
DELETE FROM documentos_eliminados WHERE empresa_id = 136;
-- Ahora sí podemos borrar los logs asociados a documentos de esta empresa
DELETE FROM log_operaciones WHERE documento_id_asociado IN (SELECT id FROM documentos WHERE empresa_id = 136);
-- Y logs generales de usuarios de esta empresa (que no estén ligados a documentos de otras empresas, si fuera multitenant compartido)
DELETE FROM log_operaciones WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = 136);

-- 7. NÓMINA
DELETE FROM nomina_detalles WHERE nomina_id IN (SELECT id FROM nomina_documentos WHERE empresa_id = 136);
DELETE FROM nomina_detalles WHERE empleado_id IN (SELECT id FROM nomina_empleados WHERE empresa_id = 136 OR tipo_nomina_id IN (SELECT id FROM nomina_tipos WHERE empresa_id = 136));
DELETE FROM nomina_empleados WHERE empresa_id = 136 OR tipo_nomina_id IN (SELECT id FROM nomina_tipos WHERE empresa_id = 136);
DELETE FROM nomina_documentos WHERE empresa_id = 136;
DELETE FROM nomina_tipos WHERE empresa_id = 136;

-- 8. MÓDULOS SATÉLITE
DELETE FROM orden_produccion_insumos WHERE orden_id IN (SELECT id FROM ordenes_produccion WHERE empresa_id = 136);
DELETE FROM orden_produccion_recursos WHERE orden_id IN (SELECT id FROM ordenes_produccion WHERE empresa_id = 136);
DELETE FROM ordenes_produccion WHERE empresa_id = 136;
DELETE FROM receta_detalles WHERE receta_id IN (SELECT id FROM recetas WHERE empresa_id = 136);
DELETE FROM receta_recursos WHERE receta_id IN (SELECT id FROM recetas WHERE empresa_id = 136);
DELETE FROM recetas WHERE empresa_id = 136;
DELETE FROM activos_novedades WHERE activo_id IN (SELECT id FROM activos_fijos WHERE empresa_id = 136);
DELETE FROM activos_fijos WHERE empresa_id = 136 OR categoria_id IN (SELECT id FROM activos_categorias WHERE empresa_id = 136);
DELETE FROM activos_categorias WHERE empresa_id = 136;
DELETE FROM cotizaciones_detalles WHERE cotizacion_id IN (SELECT id FROM cotizaciones WHERE empresa_id = 136);
DELETE FROM cotizaciones WHERE empresa_id = 136;
DELETE FROM remisiones_detalles WHERE remision_id IN (SELECT id FROM remisiones WHERE empresa_id = 136);
DELETE FROM remisiones WHERE empresa_id = 136;

-- 9. MOVIMIENTOS Y DOCUMENTOS (Núcleo Contable)
DELETE FROM aplicacion_pagos WHERE documento_factura_id IN (SELECT id FROM documentos WHERE empresa_id = 136) OR documento_pago_id IN (SELECT id FROM documentos WHERE empresa_id = 136);
DELETE FROM movimientos_contables WHERE documento_id IN (SELECT id FROM documentos WHERE empresa_id = 136);
DELETE FROM movimientos_contables WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id = 136);
DELETE FROM movimientos_inventario WHERE documento_id IN (SELECT id FROM documentos WHERE empresa_id = 136);
DELETE FROM movimientos_inventario WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id = 136 OR grupo_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 136));

-- IMPORTANTE: Borrar HistorialConsumo de nuevo por si acaso quedó algo huerfano referenciando documentos
DELETE FROM historial_consumo WHERE documento_id IN (SELECT id FROM documentos WHERE empresa_id = 136);

DELETE FROM documentos WHERE empresa_id = 136;

-- 10. STOCK Y PRODUCTOS
DELETE FROM stock_bodegas WHERE bodega_id IN (SELECT id FROM bodegas WHERE empresa_id = 136);
DELETE FROM stock_bodegas WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id = 136 OR grupo_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 136));
DELETE FROM caracteristica_valores_producto WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id = 136 OR grupo_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 136));
DELETE FROM productos WHERE empresa_id = 136 OR grupo_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 136);

-- 11. MAESTROS
DELETE FROM plantillas_detalles WHERE plantilla_maestra_id IN (SELECT id FROM plantillas_maestras WHERE empresa_id = 136);
DELETE FROM plantillas_maestras WHERE empresa_id = 136;
DELETE FROM formatos_documento_impresion WHERE empresa_id = 136;

-- 12. TERCEROS E INVENTARIOS BASE
-- Romper referencias circulares antes de borrar
UPDATE terceros SET lista_precio_id = NULL WHERE empresa_id = 136;
DELETE FROM terceros WHERE empresa_id = 136;

DELETE FROM reglas_precio_grupo WHERE grupo_inventario_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 136);
DELETE FROM caracteristica_definiciones WHERE grupo_inventario_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 136);
DELETE FROM listas_precio WHERE empresa_id = 136;
DELETE FROM bodegas WHERE empresa_id = 136;
DELETE FROM grupos_inventario WHERE empresa_id = 136;
DELETE FROM tasas_impuesto WHERE empresa_id = 136;

-- 13. CONTABILIDAD MAESTRA
-- Las cuentas pueden estar en TiposDocumento, así que primero TiposDoc
DELETE FROM tipos_documento WHERE empresa_id = 136;
DELETE FROM conceptos_favoritos WHERE empresa_id = 136;
DELETE FROM centros_costo WHERE empresa_id = 136;
DELETE FROM plan_cuentas WHERE empresa_id = 136;
DELETE FROM periodos_cerrados WHERE empresa_id = 136;

COMMIT;

-- Verificación final
SELECT count(*) as documentos_restantes FROM documentos WHERE empresa_id = 136;
