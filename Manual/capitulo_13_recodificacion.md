# Manual de Usuario - Capítulo 13: Recodificación Masiva

## 1. Introducción
La **Recodificación Masiva** es una herramienta de "cirugía mayor" para su contabilidad. Permite mover saldos y movimientos de un código a otro en bloque, ahorrando horas de corrección manual.

**Ubicación:** `Administración > Utilidades > Recodificación Masiva`

> [!CAUTION]
> **Acción Irreversible:** A diferencia de la anulación, esta acción reescribe la historia contable. Una vez ejecutada, no hay botón de "Deshacer" (Undo). Se recomienda hacer una Copia de Seguridad (ver *Capítulo 6*) antes de usarla.

---

## 2. ¿Qué puedo recodificar?
El sistema permite tres tipos de transformaciones, seleccionables mediante las pestañas superiores:

1.  **Cambiar Cuenta Contable:**
    *   *Caso de uso:* Registró todos los gastos de papelería en la cuenta `519530` pero el contador ordenó moverlos a la `519595`.
2.  **Cambiar Tercero (Beneficiario):**
    *   *Caso de uso:* Se crearon dos códigos para el mismo proveedor (uno con NIT y otro con Cédula) y desea unificar todos los movimientos en el NIT correcto.
3.  **Cambiar Centro de Costo:**
    *   *Caso de uso:* Un proyecto cambió de nombre o se fusionó con otro departamento.

---

## 3. Pasos para la Recodificación

### Paso 1: Definir el Alcance (Filtros)
Antes de cambiar nada, debe decirle al sistema **dónde** buscar.
*   **Tipo de Documento (Obligatorio):** Por seguridad, la recodificación se hace por tipo de documento. Debe seleccionar uno (ej: *Factura de Venta*).
*   **Rango de Fechas:** Puede limitar el cambio a un mes o año específico.
*   **Número:** Si solo desea corregir un documento específico, escriba su número aquí.

### Paso 2: Definir la Transformación
Aquí se configura la regla de cambio: **"Buscar X y reemplazarlo por Y"**.
*   **Origen (Izquierda):** El dato erróneo o antiguo que desea eliminar.
*   **Destino (Derecha):** El dato correcto o nuevo donde quedarán los saldos.

### Paso 3: Ejecución
Al presionar el botón rojo **"Ejecutar Recodificación Masiva"**, el sistema:
1.  Buscará todos los renglones que coincidan con los filtros y el dato de Origen.
2.  Cambiará el ID del Origen por el del Destino.
3.  Recalculará saldos si es necesario.

---

## 4. Preguntas Frecuentes y Solución de Problemas

*   **P: ¿Por qué me da error "El origen y destino no pueden ser el mismo"?**
    *   **R:** Está intentando mover saldos de la Cuenta A a la Cuenta A. Debe seleccionar una cuenta diferente en el destino.

*   **P: ¿Puedo recodificar documentos de años cerrados?**
    *   **R:** Técnicamente sí, pero **NO SE RECOMIENDA**. Alterar años cerrados cambiará los saldos iniciales del año siguiente, descuadrando los libros oficiales ya presentados.

*   **P: ¿Qué pasa con los documentos anulados?**
    *   **R:** La recodificación también afecta a los documentos anulados para mantener la consistencia histórica.

*   **P: ¿Puedo cambiar el Tercero de una Factura y un Recibo al mismo tiempo?**
    *   **R:** No. Debe ejecutar el proceso dos veces: una seleccionando "Tipo: Factura" y otra seleccionando "Tipo: Recibo". Esto es una medida de seguridad para evitar cambios masivos accidentales en toda la base de datos.

*   **P: ¿Cuánto tarda el proceso?**
    *   **R:** Depende del volumen de datos. Para unos pocos cientos de registros es instantáneo. Para miles, puede tardar unos segundos. No cierre la ventana hasta ver el mensaje de "Operación Exitosa".
