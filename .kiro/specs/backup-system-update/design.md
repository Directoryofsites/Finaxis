# Diseño del Sistema de Actualización de Copias de Seguridad

## Overview

El sistema de migración de datos actual (versión 7.5) ya tiene una arquitectura sólida con firma digital, restauración atómica y manejo de dependencias. Esta actualización se enfoca en extender el soporte para los nuevos módulos agregados al sistema: Cotizaciones, Conciliación Bancaria, Producción, y mejoras en Propiedad Horizontal.

La actualización mantendrá la compatibilidad con backups existentes mientras agrega soporte completo para los nuevos módulos, incluyendo sus relaciones complejas y dependencias.

## Architecture

### Arquitectura Actual
El sistema actual utiliza:
- **Motor de Exportación**: Genera JSON firmado digitalmente con HMAC-SHA256
- **Motor de Análisis**: Valida integridad y analiza conflictos antes de restaurar
- **Motor de Restauración**: Aplica cambios de forma atómica con rollback automático
- **Mapeo de IDs**: Sistema robusto para mantener integridad referencial entre empresas

### Extensiones Propuestas
- **Registro de Módulos**: Sistema declarativo para registrar nuevos módulos
- **Procesadores Especializados**: Handlers específicos para módulos con lógica compleja
- **Validadores de Dependencias**: Verificación automática de prerequisitos por módulo
- **Reportes Detallados**: Análisis granular por módulo con métricas específicas

## Components and Interfaces

### 1. Registro de Módulos Nuevos
```python
NUEVOS_MODULOS = {
    'cotizaciones': {
        'modelos': [Cotizacion, CotizacionDetalle],
        'clave_natural': 'numero',
        'dependencias': ['terceros', 'productos', 'tipos_documento'],
        'procesador': 'procesar_cotizaciones'
    },
    'conciliacion_bancaria': {
        'modelos': [ImportConfig, ImportSession, BankMovement, Reconciliation, 
                   ReconciliationMovement, AccountingConfig, ReconciliationAudit],
        'clave_natural': 'id',
        'dependencias': ['plan_cuentas'],
        'procesador': 'procesar_conciliacion_bancaria'
    },
    'produccion': {
        'modelos': [Receta, RecetaDetalle, RecetaRecurso, OrdenProduccion, 
                   OrdenProduccionInsumo, OrdenProduccionRecurso, ConfiguracionProduccion],
        'clave_natural': 'codigo',
        'dependencias': ['productos', 'centros_costo'],
        'procesador': 'procesar_produccion'
    }
}
```

### 2. Extensión del Schema de Exportación
```python
class ExportPaquetesModulosEspecializados(BaseModel):
    propiedad_horizontal: bool = False
    activos_fijos: bool = False
    favoritos: bool = False
    cotizaciones: bool = False  # NUEVO
    conciliacion_bancaria: bool = False  # NUEVO
    produccion: bool = False  # NUEVO
```

### 3. Procesadores Especializados
Cada módulo nuevo tendrá un procesador dedicado que maneja:
- Exportación con relaciones complejas
- Validación de dependencias
- Restauración con orden correcto
- Manejo de claves foráneas

### 4. Sistema de Validación Mejorado
- Verificación de integridad por módulo
- Detección de dependencias faltantes
- Validación de versiones de schema
- Reportes de compatibilidad

## Data Models

### Estructura del Backup JSON Extendida
```json
{
  "data": {
    "metadata": {
      "fecha_generacion": "2024-12-21T10:00:00",
      "version_sistema": "7.6",
      "empresa_id_origen": 1,
      "modulos_incluidos": ["cotizaciones", "produccion", "conciliacion_bancaria"]
    },
    "cotizaciones": {
      "cotizaciones": [...],
      "detalles": [...]
    },
    "produccion": {
      "configuracion": {...},
      "recetas": [...],
      "ordenes": [...],
      "recursos": [...]
    },
    "conciliacion_bancaria": {
      "configuraciones": [...],
      "sesiones": [...],
      "movimientos": [...],
      "conciliaciones": [...]
    }
  },
  "signature": "..."
}
```

### Mapeos de Dependencias
```python
DEPENDENCIAS_MODULOS = {
    'cotizaciones': {
        'terceros': 'cliente_id',
        'productos': 'producto_id',
        'tipos_documento': 'tipo_documento_id'
    },
    'produccion': {
        'productos': ['producto_terminado_id', 'insumo_id'],
        'centros_costo': 'centro_costo_id'
    },
    'conciliacion_bancaria': {
        'plan_cuentas': 'cuenta_bancaria_id'
    }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

Después de revisar todas las propiedades identificadas en el prework, se identificaron las siguientes redundancias y consolidaciones:

- Las propiedades 1.3, 1.4, 1.5 (exportación completa por módulo) pueden consolidarse en una propiedad general de completitud de exportación
- Las propiedades 2.1, 2.2, 2.3, 2.4 (round-trip por módulo) pueden consolidarse en una propiedad general de round-trip
- Las propiedades 5.2, 5.3, 5.5 (feedback de UI) pueden consolidarse en una propiedad general de feedback apropiado

### Propiedades de Correctitud

**Property 1: Completitud de exportación de módulos nuevos**
*Para cualquier* combinación de módulos nuevos seleccionados (Cotizaciones, Producción, Conciliación Bancaria), la exportación debe incluir todas las tablas principales y sus relaciones del módulo
**Validates: Requirements 1.2, 1.3, 1.4, 1.5**

**Property 2: Round-trip de módulos nuevos**
*Para cualquier* conjunto de datos de módulos nuevos, exportar y luego restaurar debe producir datos equivalentes con todas las relaciones intactas
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

**Property 3: Atomicidad de restauración**
*Para cualquier* operación de restauración que falle, el sistema debe revertir completamente todos los cambios sin dejar datos parciales
**Validates: Requirements 2.5**

**Property 4: Completitud de análisis**
*Para cualquier* backup que contenga módulos nuevos, el análisis debe reportar conteos correctos para todos los módulos incluidos
**Validates: Requirements 3.1**

**Property 5: Detección de conflictos**
*Para cualquier* backup con datos que generen conflictos, el análisis debe identificar específicamente qué registros ya existen
**Validates: Requirements 3.2**

**Property 6: Validación de firma digital**
*Para cualquier* archivo de backup, la validación debe reportar correctamente si la firma es válida o inválida
**Validates: Requirements 3.3**

**Property 7: Validación de dependencias**
*Para cualquier* módulo nuevo en un backup, el análisis debe verificar que existan todos los maestros requeridos
**Validates: Requirements 3.4**

**Property 8: Estructura de reporte de análisis**
*Para cualquier* análisis completado, el reporte debe contener secciones organizadas para cada módulo incluido
**Validates: Requirements 3.5**

**Property 9: Extensibilidad declarativa**
*Para cualquier* módulo agregado al registro de configuración, debe estar automáticamente disponible en las opciones de exportación
**Validates: Requirements 4.1**

**Property 10: Integridad referencial**
*Para cualquier* conjunto de datos con relaciones complejas, los mapeos de ID deben mantener la integridad referencial después de restaurar
**Validates: Requirements 4.3**

**Property 11: Compatibilidad hacia atrás**
*Para cualquier* backup de versión anterior, el sistema debe procesarlo correctamente sin errores
**Validates: Requirements 4.4**

**Property 12: Feedback apropiado de UI**
*Para cualquier* operación de migración, la interfaz debe mostrar información apropiada sobre progreso, resultados y errores
**Validates: Requirements 5.2, 5.3, 5.4, 5.5**

## Error Handling

### Estrategias de Manejo de Errores

1. **Validación Temprana**: Verificar integridad de archivos y dependencias antes de iniciar restauración
2. **Rollback Automático**: Usar transacciones de base de datos para revertir cambios en caso de error
3. **Logging Detallado**: Registrar cada paso para facilitar debugging
4. **Mensajes Claros**: Proporcionar información específica sobre errores y acciones sugeridas

### Tipos de Errores Manejados

- **Errores de Integridad**: Firma digital inválida, archivo corrupto
- **Errores de Dependencias**: Maestros faltantes, relaciones rotas
- **Errores de Conflictos**: Registros duplicados, violaciones de unicidad
- **Errores de Sistema**: Problemas de base de datos, memoria insuficiente

## Testing Strategy

### Enfoque Dual de Testing

El sistema utilizará tanto pruebas unitarias como pruebas basadas en propiedades:

**Pruebas Unitarias:**
- Verificarán ejemplos específicos de exportación/restauración
- Probarán casos edge como archivos vacíos o datos malformados
- Validarán integración entre componentes del sistema

**Pruebas Basadas en Propiedades:**
- Utilizarán **Hypothesis** como biblioteca de property-based testing para Python
- Cada prueba ejecutará un mínimo de **100 iteraciones** para asegurar cobertura robusta
- Cada prueba estará etiquetada con el formato: **Feature: backup-system-update, Property {number}: {property_text}**
- Las pruebas generarán datos aleatorios para empresas, módulos y configuraciones
- Verificarán que las propiedades se mantengan independientemente de los datos de entrada

**Generadores de Datos:**
- Generadores inteligentes que crean datos válidos para cada módulo
- Generadores de conflictos para probar detección de duplicados
- Generadores de dependencias para probar validación de relaciones
- Generadores de archivos corruptos para probar manejo de errores

**Configuración de Testing:**
- Las pruebas de propiedades se ejecutarán con configuración de 100+ iteraciones
- Se utilizarán bases de datos de prueba aisladas para cada test
- Se implementarán fixtures para datos de prueba consistentes
- Se incluirán pruebas de rendimiento para operaciones con grandes volúmenes de datos