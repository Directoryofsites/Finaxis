# Actualización del Sistema de Copias de Seguridad

## Introducción

El sistema actual de migración de datos (copias de seguridad y restauración) necesita ser actualizado para incluir los nuevos módulos que se han agregado al sistema: Cotizaciones, Activos Fijos, Conciliación Bancaria, Producción, y mejoras en Propiedad Horizontal. El sistema actual ya maneja algunos de estos módulos parcialmente, pero necesita ser completado y mejorado.

## Glossario

- **Sistema_Migracion**: El módulo de migración de datos que maneja exportación, análisis y restauración de copias de seguridad
- **Backup_JSON**: Archivo de respaldo en formato JSON con firma digital que contiene los datos exportados
- **Modulos_Nuevos**: Los módulos agregados recientemente: Cotizaciones, Conciliación Bancaria, Producción, y mejoras en Propiedad Horizontal
- **Firma_Digital**: Sistema de validación de integridad usando HMAC-SHA256
- **Restauracion_Atomica**: Proceso que garantiza que todos los cambios se aplican o se revierten completamente

## Requisitos

### Requisito 1

**User Story:** Como administrador del sistema, quiero que el sistema de copias de seguridad incluya todos los nuevos módulos, para que pueda hacer respaldos completos de toda la información.

#### Acceptance Criteria

1. WHEN el usuario selecciona exportar datos THEN el Sistema_Migracion SHALL incluir opciones para Cotizaciones, Conciliación Bancaria, Producción y Propiedad Horizontal completa
2. WHEN se genera un Backup_JSON THEN el Sistema_Migracion SHALL incluir todas las tablas de los Modulos_Nuevos con sus relaciones
3. WHEN se exportan Cotizaciones THEN el Sistema_Migracion SHALL incluir tanto las cotizaciones maestras como sus detalles
4. WHEN se exportan datos de Producción THEN el Sistema_Migracion SHALL incluir recetas, órdenes de producción, recursos e insumos
5. WHEN se exportan datos de Conciliación Bancaria THEN el Sistema_Migracion SHALL incluir configuraciones, sesiones, movimientos y conciliaciones

### Requisito 2

**User Story:** Como administrador del sistema, quiero que la restauración de copias funcione correctamente con los nuevos módulos, para que pueda recuperar toda la información sin pérdida de datos.

#### Acceptance Criteria

1. WHEN se restaura un Backup_JSON con Cotizaciones THEN el Sistema_Migracion SHALL recrear todas las cotizaciones con sus detalles y relaciones correctas
2. WHEN se restaura un Backup_JSON con datos de Producción THEN el Sistema_Migracion SHALL recrear recetas, órdenes y sus dependencias manteniendo la integridad referencial
3. WHEN se restaura un Backup_JSON con Conciliación Bancaria THEN el Sistema_Migracion SHALL recrear todas las configuraciones y movimientos bancarios
4. WHEN se restaura un Backup_JSON con Propiedad Horizontal THEN el Sistema_Migracion SHALL recrear torres, unidades, conceptos y configuraciones completas
5. WHEN ocurre un error durante la restauración THEN el Sistema_Migracion SHALL revertir todos los cambios usando Restauracion_Atomica

### Requisito 3

**User Story:** Como administrador del sistema, quiero que el análisis de copias de seguridad muestre información detallada de los nuevos módulos, para que pueda revisar qué se va a restaurar antes de proceder.

#### Acceptance Criteria

1. WHEN se analiza un Backup_JSON THEN el Sistema_Migracion SHALL mostrar conteos de registros para Cotizaciones, Producción, Conciliación Bancaria y Propiedad Horizontal
2. WHEN se detectan conflictos en los Modulos_Nuevos THEN el Sistema_Migracion SHALL reportar específicamente qué registros ya existen
3. WHEN se valida la Firma_Digital THEN el Sistema_Migracion SHALL reportar el estado de integridad del archivo
4. WHEN se analizan dependencias THEN el Sistema_Migracion SHALL verificar que existan los maestros necesarios para los Modulos_Nuevos
5. WHEN se presenta el reporte de análisis THEN el Sistema_Migracion SHALL mostrar un resumen claro y organizado por módulo

### Requisito 4

**User Story:** Como desarrollador del sistema, quiero que el código de migración sea mantenible y extensible, para que sea fácil agregar nuevos módulos en el futuro.

#### Acceptance Criteria

1. WHEN se agrega un nuevo módulo THEN el Sistema_Migracion SHALL permitir su inclusión mediante configuración declarativa
2. WHEN se procesan los Modulos_Nuevos THEN el Sistema_Migracion SHALL usar funciones reutilizables para exportación y restauración
3. WHEN se manejan relaciones complejas THEN el Sistema_Migracion SHALL usar mapeos de ID consistentes para mantener integridad referencial
4. WHEN se actualiza el código THEN el Sistema_Migracion SHALL mantener compatibilidad con versiones anteriores de Backup_JSON
5. WHEN se ejecutan operaciones THEN el Sistema_Migracion SHALL registrar logs detallados para facilitar debugging

### Requisito 5

**User Story:** Como usuario del sistema, quiero que la interfaz de migración de datos sea clara y fácil de usar con los nuevos módulos, para que pueda realizar copias de seguridad sin confusión.

#### Acceptance Criteria

1. WHEN accedo a la página de migración THEN el Sistema_Migracion SHALL mostrar opciones organizadas por categorías para los Modulos_Nuevos
2. WHEN selecciono módulos para exportar THEN el Sistema_Migracion SHALL mostrar descripciones claras de qué incluye cada opción
3. WHEN proceso una restauración THEN el Sistema_Migracion SHALL mostrar progreso y resultados detallados
4. WHEN ocurre un error THEN el Sistema_Migracion SHALL mostrar mensajes de error claros y acciones sugeridas
5. WHEN completo una operación THEN el Sistema_Migracion SHALL mostrar un resumen de lo que se procesó exitosamente