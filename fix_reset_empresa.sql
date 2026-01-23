-- ==========================================================
-- SCRIPT DE REINICIO DE EMPRESA (SAFE RESET v14 - DEPENDENCY FIX)
-- Objetivo: VACIAR datos operativos/maestros pero PRESERVAR Empresa y Acceso
-- Correcciones:
-- 1. Reordenamiento CRÍTICO: Documentos y Movimientos se borran ANTES que PH Unidades
--    para evitar violación de FK documentos_unidad_ph_id_fkey
-- ==========================================================
BEGIN;

-- 1. LIMPIEZA DE DATOS DE CONSUMO
DELETE FROM historial_consumo WHERE empresa_id = 132;
DELETE FROM recarga_adicional WHERE empresa_id = 132;
DELETE FROM bolsa_excedente WHERE empresa_id = 132;
DELETE FROM control_plan_mensual WHERE empresa_id = 132;

-- 2. LIMPIEZA DE DATOS ASOCIADOS A USUARIOS (Historial y Preferencias)
UPDATE documentos_eliminados SET log_eliminacion_id = NULL WHERE empresa_id = 132;

DELETE FROM usuarios_favoritos WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = 132);
DELETE FROM usuarios_busquedas_guardadas WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = 132);
-- DELETE FROM usuario_roles ... (PRESERVADO)

-- 3. CONCILIACIÓN BANCARIA
DELETE FROM reconciliation_movements WHERE reconciliation_id IN (SELECT id FROM reconciliations WHERE empresa_id = 132);
DELETE FROM reconciliation_audits WHERE empresa_id = 132;
DELETE FROM reconciliations WHERE empresa_id = 132;
DELETE FROM bank_movements WHERE empresa_id = 132 OR import_session_id IN (SELECT id FROM import_sessions WHERE empresa_id = 132);
DELETE FROM import_sessions WHERE empresa_id = 132;
DELETE FROM accounting_configs WHERE empresa_id = 132;
DELETE FROM import_configs WHERE empresa_id = 132;
DELETE FROM import_templates WHERE empresa_id = 132;

-- ... 
-- BLOQUE REUBICADO: LOS DOCUMENTOS DEBEN BORRARSE ANTES QUE LAS UNIDADES PH
-- PORQUE DOCUMENTOS TIENE FK HACIA PH_UNIDADES (unidad_ph_id)
-- ...

-- 4. MOVIMIENTOS Y DOCUMENTOS (Núcleo Contable) - MOVIDO AL INICIO DE LA CADENA DE BORRADO
DELETE FROM aplicacion_pagos WHERE documento_factura_id IN (SELECT id FROM documentos WHERE empresa_id = 132) OR documento_pago_id IN (SELECT id FROM documentos WHERE empresa_id = 132);
DELETE FROM movimientos_contables WHERE documento_id IN (SELECT id FROM documentos WHERE empresa_id = 132);
DELETE FROM movimientos_contables WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id = 132);
DELETE FROM movimientos_inventario WHERE documento_id IN (SELECT id FROM documentos WHERE empresa_id = 132);
DELETE FROM movimientos_inventario WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id = 132 OR grupo_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 132));

-- Historial Consumo Clean Up (redundante safe check)
DELETE FROM historial_consumo WHERE documento_id IN (SELECT id FROM documentos WHERE empresa_id = 132);

-- LOGS OPERACIONES (Que apuntan a documentos)
DELETE FROM log_operaciones WHERE documento_id_asociado IN (SELECT id FROM documentos WHERE empresa_id = 132);

-- AHORA SÍ: DOCUMENTOS
DELETE FROM documentos WHERE empresa_id = 132;


-- 5. CONFIS Y MAESTROS PH (Ahora es seguro borrar unidades)
DELETE FROM ph_vehiculos WHERE unidad_id IN (SELECT id FROM ph_unidades WHERE empresa_id = 132);
DELETE FROM ph_mascotas WHERE unidad_id IN (SELECT id FROM ph_unidades WHERE empresa_id = 132);
DELETE FROM ph_coeficientes_historial WHERE unidad_id IN (SELECT id FROM ph_unidades WHERE empresa_id = 132);
DELETE FROM ph_unidad_modulo_association WHERE unidad_id IN (SELECT id FROM ph_unidades WHERE empresa_id = 132);
DELETE FROM ph_unidad_modulo_association WHERE modulo_id IN (SELECT id FROM ph_modulos_contribucion WHERE empresa_id = 132);
DELETE FROM ph_modulos_contribucion WHERE empresa_id = 132;
DELETE FROM ph_unidades WHERE empresa_id = 132; -- Ya no debería fallar
DELETE FROM ph_torres WHERE empresa_id = 132;
DELETE FROM ph_concepto_modulo_association WHERE concepto_id IN (SELECT id FROM ph_conceptos WHERE empresa_id = 132);
DELETE FROM ph_configuracion WHERE empresa_id = 132;
DELETE FROM ph_conceptos WHERE empresa_id = 132;

-- 6. CONFIGURACIONES DE MÓDULOS (Producción, Nómina, etc)
DELETE FROM produccion_configuracion WHERE empresa_id = 132;
DELETE FROM nomina_configuracion WHERE empresa_id = 132;

-- 7. LIMPIEZA RESIDUAL (Logs y Documentos Eliminados)
DELETE FROM movimientos_eliminados WHERE documento_eliminado_id IN (SELECT id FROM documentos_eliminados WHERE empresa_id = 132);
DELETE FROM documentos_eliminados WHERE empresa_id = 132;
-- Y logs generales de usuarios
DELETE FROM log_operaciones WHERE usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = 132);

-- 8. NÓMINA (Resto de tablas)
DELETE FROM nomina_detalles WHERE nomina_id IN (SELECT id FROM nomina_documentos WHERE empresa_id = 132);
DELETE FROM nomina_detalles WHERE empleado_id IN (SELECT id FROM nomina_empleados WHERE empresa_id = 132 OR tipo_nomina_id IN (SELECT id FROM nomina_tipos WHERE empresa_id = 132));
DELETE FROM nomina_empleados WHERE empresa_id = 132 OR tipo_nomina_id IN (SELECT id FROM nomina_tipos WHERE empresa_id = 132);
DELETE FROM nomina_documentos WHERE empresa_id = 132;
DELETE FROM nomina_tipos WHERE empresa_id = 132;

-- 9. MÓDULOS SATÉLITE RESTANTES
DELETE FROM orden_produccion_insumos WHERE orden_id IN (SELECT id FROM ordenes_produccion WHERE empresa_id = 132);
DELETE FROM orden_produccion_recursos WHERE orden_id IN (SELECT id FROM ordenes_produccion WHERE empresa_id = 132);
DELETE FROM ordenes_produccion WHERE empresa_id = 132;
DELETE FROM receta_detalles WHERE receta_id IN (SELECT id FROM recetas WHERE empresa_id = 132);
DELETE FROM receta_recursos WHERE receta_id IN (SELECT id FROM recetas WHERE empresa_id = 132);
DELETE FROM recetas WHERE empresa_id = 132;
DELETE FROM activos_novedades WHERE activo_id IN (SELECT id FROM activos_fijos WHERE empresa_id = 132);
DELETE FROM activos_fijos WHERE empresa_id = 132 OR categoria_id IN (SELECT id FROM activos_categorias WHERE empresa_id = 132);
DELETE FROM activos_categorias WHERE empresa_id = 132;
DELETE FROM cotizaciones_detalles WHERE cotizacion_id IN (SELECT id FROM cotizaciones WHERE empresa_id = 132);
DELETE FROM cotizaciones WHERE empresa_id = 132;
DELETE FROM remisiones_detalles WHERE remision_id IN (SELECT id FROM remisiones WHERE empresa_id = 132);
DELETE FROM remisiones WHERE empresa_id = 132;

-- 10. STOCK Y PRODUCTOS
DELETE FROM stock_bodegas WHERE bodega_id IN (SELECT id FROM bodegas WHERE empresa_id = 132);
DELETE FROM stock_bodegas WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id = 132 OR grupo_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 132));
DELETE FROM caracteristica_valores_producto WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id = 132 OR grupo_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 132));
DELETE FROM productos WHERE empresa_id = 132 OR grupo_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 132);

-- 11. MAESTROS
DELETE FROM plantillas_detalles WHERE plantilla_maestra_id IN (SELECT id FROM plantillas_maestras WHERE empresa_id = 132);
DELETE FROM plantillas_maestras WHERE empresa_id = 132;
DELETE FROM formatos_documento_impresion WHERE empresa_id = 132;

-- 12. TERCEROS E INVENTARIOS BASE
UPDATE terceros SET lista_precio_id = NULL WHERE empresa_id = 132;
DELETE FROM terceros WHERE empresa_id = 132;
DELETE FROM reglas_precio_grupo WHERE grupo_inventario_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 132);
DELETE FROM caracteristica_definiciones WHERE grupo_inventario_id IN (SELECT id FROM grupos_inventario WHERE empresa_id = 132);
DELETE FROM listas_precio WHERE empresa_id = 132;
DELETE FROM bodegas WHERE empresa_id = 132;
DELETE FROM grupos_inventario WHERE empresa_id = 132;
DELETE FROM tasas_impuesto WHERE empresa_id = 132;

-- 13. CONTABILIDAD MAESTRA
DELETE FROM tipos_documento WHERE empresa_id = 132;
DELETE FROM conceptos_favoritos WHERE empresa_id = 132;
DELETE FROM centros_costo WHERE empresa_id = 132;
DELETE FROM plan_cuentas WHERE empresa_id = 132;
DELETE FROM periodos_cerrados WHERE empresa_id = 132;

COMMIT;

-- Verificación final
SELECT count(*) as documentos_restantes FROM documentos WHERE empresa_id = 132;
SELECT count(*) as unidades_restantes FROM ph_unidades WHERE empresa_id = 132;
