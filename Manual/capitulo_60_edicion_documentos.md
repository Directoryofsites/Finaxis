# Edición de Documentos

El módulo de **Edición de Documentos** es una herramienta controlada que permite realizar correcciones a transacciones ya guardadas en el sistema. A diferencia de otros sistemas contables rígidos, ContaPY permite la flexibilidad de corregir errores humanos sin necesidad de anular y volver a hacer todo el trabajo, siempre y cuando se cumplan ciertas reglas de seguridad y auditoría.

## Reglas de Seguridad

Para garantizar la integridad de la información financiera, el sistema impone las siguientes restricciones estrictas para la edición:

1.  **Estado del Documento:** Solo se pueden editar documentos en estado **ACTIVO**. Los documentos anulados no son modificables.
2.  **Periodo Contable:** El sistema valida la fecha del documento. Si el mes correspondiente ya ha sido **CERRADO** (ver capítulo de Control y Cierre), la edición será bloqueada inmediatamente para proteger los estados financieros ya reportados.
3.  **Integridad de Claves:** No es posible modificar el **Tipo de Documento** ni el **Número Consecutivo** una vez creado el registro. Estos campos son la llave única de la transacción. Si cometió un error aquí, la única vía es la anulación.

## Campos Editables

Al ingresar al modo de edición, usted podrá modificar:

*   **Encabezado:**
    *   **Tercero (Beneficiario):** Puede reasignar la factura a otro cliente o proveedor.
    *   **Centro de Costo:** Puede corregir la imputación a la unidad de negocio.
    *   **Fechas:** Fecha de documento y vencimiento (respetando el periodo contable).
    *   **Detalles:** Vendedor, notas, observaciones.

*   **Cuerpo (Movimientos):**
    *   **Agregar Ítems:** Puede insertar nuevas líneas de productos o cuentas contables.
    *   **Eliminar Ítems:** Puede borrar líneas incorrectas.
    *   **Modificar Valores:** Cantidades, precios unitarios, descuentos e impuestos.
    *   **Cuentas Contables:** Puede cambiar la cuenta contable de una línea específica (ej: cambiar de un Gasto de Viaje a un Gasto de Representación).

## Impacto Contable

Cualquier cambio realizado en este módulo tiene un efecto **inmediato y en tiempo real** sobre la contabilidad.
*   Si cambia un valor, el Balance de Prueba se actualizará al instante.
*   Si cambia un tercero, el Estado de Cuenta de ambos (el anterior y el nuevo) reflejará el cambio inmediatamente.
*   Si agrega productos, el Kardex de inventario se recalculará.

## Auditoría de Cambios

Por seguridad, el sistema guarda un rastro silencioso de todas las ediciones. En el **Log de Operaciones** (visible para auditores), quedará registrado:
*   Quién realizó la modificación.
*   La fecha y hora exacta.
*   El documento afectado.

> **Recomendación:** Utilice la edición para correcciones menores (fechas, valores, conceptos). Para errores estructurales graves, es preferible anular y crear un nuevo documento para mantener una traza más clara.
