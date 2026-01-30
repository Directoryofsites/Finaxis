# Plan de Implementación - Corrección Visualización Empresas para Rol Contador

- [x] 1. Investigar y diagnosticar el problema actual



  - Revisar la base de datos para verificar el estado actual de owner_id en empresas creadas por contadores
  - Ejecutar consultas de diagnóstico para identificar empresas huérfanas o mal asignadas
  - Verificar el estado de la tabla usuario_empresas para empresas creadas por contadores
  - _Requisitos: 1.1, 1.4_

- [ ] 2. Corregir la función get_empresas_para_usuario
  - Mejorar el logging de debug para facilitar el diagnóstico
  - Optimizar la lógica de consulta para ser más robusta y clara
  - Asegurar que la consulta de empresas owned funcione correctamente
  - Verificar que todas las fuentes de empresas se estén consultando apropiadamente
  - _Requisitos: 1.1, 1.2, 1.4, 2.1, 2.3_

- [ ]* 2.1 Escribir test de propiedad para visibilidad completa de empresas
  - **Propiedad 1: Visibilidad completa de empresas para contadores**
  - **Valida: Requisitos 1.1, 1.2, 1.4**

- [ ]* 2.2 Escribir test de propiedad para acceso total de soporte
  - **Propiedad 5: Acceso total para usuarios soporte**
  - **Valida: Requisitos 2.1**

- [ ] 3. Verificar y corregir la asignación de owner_id al crear empresas
  - Revisar la función create_empresa_con_usuarios para asegurar correcta asignación de owner_id
  - Verificar que el parámetro owner_id se esté pasando correctamente desde el endpoint
  - Asegurar que la relación en usuario_empresas se cree correctamente
  - _Requisitos: 1.2, 1.5_

- [ ]* 3.1 Escribir test de propiedad para persistencia inmediata
  - **Propiedad 2: Persistencia inmediata de empresas creadas**
  - **Valida: Requisitos 1.2**

- [ ]* 3.2 Escribir test de propiedad para visibilidad bidireccional
  - **Propiedad 4: Visibilidad bidireccional soporte-contador**
  - **Valida: Requisitos 1.5**

- [ ] 4. Implementar script de corrección de datos existentes
  - Crear script para identificar empresas con owner_id NULL que deberían tener un owner
  - Implementar lógica para corregir owner_id basado en el historial de creación
  - Crear entradas faltantes en la tabla usuario_empresas para empresas existentes
  - Ejecutar el script de corrección en modo dry-run primero
  - _Requisitos: 1.1, 1.4_

- [ ]* 4.1 Escribir test de propiedad para preservación de empresas asignadas
  - **Propiedad 3: Preservación de empresas asignadas por soporte**
  - **Valida: Requisitos 1.3**

- [ ] 5. Mejorar validación de permisos
  - Revisar y mejorar la lógica de validación de acceso a empresas
  - Implementar función helper para verificar permisos de usuario sobre empresa
  - Asegurar que la validación considere todas las fuentes de permisos (owner_id, asignación, rol)
  - _Requisitos: 2.2, 2.3, 2.4_

- [ ]* 5.1 Escribir test de propiedad para validación de permisos
  - **Propiedad 6: Validación correcta de permisos**
  - **Valida: Requisitos 2.2, 2.3**

- [ ]* 5.2 Escribir test de propiedad para denegación de acceso
  - **Propiedad 7: Denegación de acceso no autorizado**
  - **Valida: Requisitos 2.4**

- [ ] 6. Checkpoint - Verificar que todos los tests pasan
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas

- [ ] 7. Probar la corrección con datos reales
  - Ejecutar el script de corrección en el entorno de desarrollo
  - Verificar manualmente que los usuarios contadores pueden ver sus empresas
  - Probar con diferentes escenarios de usuarios y empresas
  - Documentar los resultados de las pruebas
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ]* 7.1 Escribir tests de integración para el endpoint completo
  - Crear tests que verifiquen el endpoint GET /empresas/ con diferentes tipos de usuarios
  - Probar escenarios edge case como usuarios sin empresas, empresas huérfanas, etc.
  - _Requisitos: 1.1, 2.1, 2.4_

- [ ] 8. Checkpoint final - Asegurar que todo funciona correctamente
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas