# Plan de Implementación - Actualización del Sistema de Copias de Seguridad

## Tareas de Implementación

- [x] 1. Actualizar esquemas de exportación para nuevos módulos


  - Extender `ExportPaquetesModulosEspecializados` en `app/schemas/migracion.py` para incluir cotizaciones, producción y conciliación bancaria
  - Agregar validación para las nuevas opciones de módulos
  - Actualizar documentación de esquemas
  - _Requirements: 1.1, 5.1_

- [ ]* 1.1 Escribir prueba de propiedad para opciones de exportación
  - **Property 1: Completitud de exportación de módulos nuevos**
  - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**



- [ ] 2. Implementar exportación de módulo de Cotizaciones
  - Agregar lógica de exportación para `Cotizacion` y `CotizacionDetalle` en `generar_backup_json`
  - Implementar manejo de relaciones con terceros, productos y tipos de documento
  - Incluir validación de dependencias para cotizaciones
  - _Requirements: 1.3, 2.1_

- [x]* 2.1 Escribir prueba de propiedad para round-trip de cotizaciones


  - **Property 2: Round-trip de módulos nuevos (Cotizaciones)**
  - **Validates: Requirements 2.1**

- [ ] 3. Implementar exportación de módulo de Producción
  - Agregar exportación para `Receta`, `RecetaDetalle`, `RecetaRecurso`, `OrdenProduccion`, `OrdenProduccionInsumo`, `OrdenProduccionRecurso`, `ConfiguracionProduccion`
  - Manejar relaciones complejas entre recetas, órdenes, productos e insumos
  - Implementar orden correcto de exportación para mantener dependencias
  - _Requirements: 1.4, 2.2_



- [ ]* 3.1 Escribir prueba de propiedad para round-trip de producción
  - **Property 2: Round-trip de módulos nuevos (Producción)**
  - **Validates: Requirements 2.2**

- [ ] 4. Implementar exportación de módulo de Conciliación Bancaria
  - Agregar exportación para `ImportConfig`, `ImportSession`, `BankMovement`, `Reconciliation`, `ReconciliationMovement`, `AccountingConfig`, `ReconciliationAudit`
  - Manejar relaciones con plan de cuentas y configuraciones bancarias


  - Implementar serialización de datos JSON complejos
  - _Requirements: 1.5, 2.3_

- [ ]* 4.1 Escribir prueba de propiedad para round-trip de conciliación bancaria
  - **Property 2: Round-trip de módulos nuevos (Conciliación Bancaria)**
  - **Validates: Requirements 2.3**

- [x] 5. Mejorar exportación de Propiedad Horizontal


  - Completar exportación de `PHConfiguracion`, incluyendo todos los campos faltantes
  - Agregar exportación de `PHVehiculo` y `PHMascota` si están en uso
  - Mejorar manejo de relaciones entre torres, unidades y terceros
  - _Requirements: 2.4_

- [ ]* 5.1 Escribir prueba de propiedad para round-trip de propiedad horizontal
  - **Property 2: Round-trip de módulos nuevos (Propiedad Horizontal)**
  - **Validates: Requirements 2.4**

- [ ] 6. Actualizar motor de análisis para nuevos módulos
  - Extender `analizar_backup` para incluir análisis de cotizaciones, producción y conciliación bancaria
  - Agregar conteos específicos y detección de conflictos para cada módulo nuevo
  - Implementar validación de dependencias específicas por módulo
  - _Requirements: 3.1, 3.2, 3.4_

- [x]* 6.1 Escribir prueba de propiedad para completitud de análisis


  - **Property 4: Completitud de análisis**
  - **Validates: Requirements 3.1**

- [x]* 6.2 Escribir prueba de propiedad para detección de conflictos


  - **Property 5: Detección de conflictos**
  - **Validates: Requirements 3.2**

- [x]* 6.3 Escribir prueba de propiedad para validación de dependencias


  - **Property 7: Validación de dependencias**
  - **Validates: Requirements 3.4**

- [x] 7. Implementar restauración de módulo de Cotizaciones


  - Crear función `_restaurar_cotizaciones` con manejo de dependencias
  - Implementar mapeo de IDs para terceros, productos y tipos de documento
  - Agregar validación de integridad referencial para cotizaciones y detalles
  - _Requirements: 2.1_

- [ ] 8. Implementar restauración de módulo de Producción
  - Crear función `_restaurar_produccion` con orden correcto de restauración
  - Manejar dependencias complejas entre recetas, órdenes, productos e insumos


  - Implementar validación de configuración de producción
  - _Requirements: 2.2_

- [ ] 9. Implementar restauración de módulo de Conciliación Bancaria
  - Crear función `_restaurar_conciliacion_bancaria`
  - Manejar configuraciones, sesiones y movimientos bancarios
  - Implementar validación de cuentas bancarias y configuraciones contables
  - _Requirements: 2.3_



- [ ] 10. Mejorar sistema de rollback atómico
  - Reforzar manejo de transacciones para incluir todos los nuevos módulos
  - Agregar logging detallado de operaciones de rollback
  - Implementar verificación post-rollback para asegurar estado limpio
  - _Requirements: 2.5_

- [x]* 10.1 Escribir prueba de propiedad para atomicidad de restauración


  - **Property 3: Atomicidad de restauración**
  - **Validates: Requirements 2.5**

- [ ] 11. Actualizar interfaz de usuario del frontend
  - Modificar `ExportacionForm` para incluir opciones de nuevos módulos
  - Agregar descripciones claras para cada opción de módulo
  - Implementar agrupación visual de opciones relacionadas
  - _Requirements: 5.1, 5.2_



- [ ]* 11.1 Escribir prueba de ejemplo para opciones de UI
  - Verificar que la página contenga opciones para todos los módulos nuevos
  - **Validates: Requirements 5.1**

- [ ] 12. Mejorar feedback y reportes de usuario
  - Actualizar mensajes de progreso para incluir información de nuevos módulos
  - Mejorar formato de reportes de análisis con secciones por módulo


  - Implementar mensajes de error específicos para cada tipo de módulo
  - _Requirements: 5.3, 5.4, 5.5_

- [ ]* 12.1 Escribir prueba de propiedad para feedback apropiado de UI
  - **Property 12: Feedback apropiado de UI**
  - **Validates: Requirements 5.2, 5.3, 5.4, 5.5**

- [x] 13. Implementar sistema de registro de módulos declarativo


  - Crear estructura `NUEVOS_MODULOS` con configuración por módulo



  - Implementar funciones genéricas que usen esta configuración
  - Agregar validación automática de dependencias basada en configuración
  - _Requirements: 4.1_

- [ ]* 13.1 Escribir prueba de propiedad para extensibilidad declarativa
  - **Property 9: Extensibilidad declarativa**
  - **Validates: Requirements 4.1**

- [ ] 14. Reforzar integridad referencial y mapeo de IDs
  - Mejorar funciones `_get_id_translation_map` para manejar casos complejos
  - Implementar validación cruzada de relaciones entre módulos
  - Agregar verificación post-restauración de integridad referencial
  - _Requirements: 4.3_

- [ ]* 14.1 Escribir prueba de propiedad para integridad referencial
  - **Property 10: Integridad referencial**
  - **Validates: Requirements 4.3**

- [ ] 15. Asegurar compatibilidad hacia atrás
  - Implementar detección de versión de backup y manejo apropiado
  - Agregar migración automática de formatos antiguos si es necesario
  - Crear pruebas con backups de versiones anteriores
  - _Requirements: 4.4_

- [ ]* 15.1 Escribir prueba de propiedad para compatibilidad hacia atrás
  - **Property 11: Compatibilidad hacia atrás**
  - **Validates: Requirements 4.4**

- [ ] 16. Checkpoint - Verificar funcionamiento completo
  - Asegurar que todas las pruebas pasen, preguntar al usuario si surgen dudas

- [ ] 17. Actualizar documentación y validación final
  - Actualizar comentarios en código para reflejar nuevos módulos
  - Verificar que todos los esquemas estén correctamente documentados
  - Realizar pruebas de integración completas con datos reales
  - _Requirements: Todos_

- [ ]* 17.1 Escribir pruebas de integración para validación final
  - Crear pruebas end-to-end que cubran exportación, análisis y restauración completa
  - Verificar funcionamiento con volúmenes grandes de datos