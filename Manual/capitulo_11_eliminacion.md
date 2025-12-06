# Manual de Usuario - Capítulo 11: Gestión Masiva de Documentos

## 1. Introducción

El módulo de **Gestión Masiva** es el centro de control para la depuración y corrección de datos a gran escala. Permite localizar grupos específicos de documentos y aplicarles acciones administrativas (Anular, Eliminar, Modificar) de forma eficiente y segura.

**Ubicación:** `Administración > Utilidades > Eliminación Masiva`

---

## 2. El Motor de Búsqueda Avanzada

Antes de actuar, es vital aislar los documentos correctos. El sistema ofrece una matriz de filtros que pueden combinarse entre sí:

### 2.1. Filtros de Identificación

*   **Tipo de Documento:** Permite seleccionar una categoría específica (ej: solo "Facturas de Venta" o "Comprobantes de Egreso").
*   **Tercero (Beneficiario):** Aísla todas las transacciones vinculadas a un cliente, proveedor o empleado específico.
*   **Número(s):** Búsqueda exacta. Puede ingresar múltiples números separados por comas (ej: `105, 108, 200`) para trabajar sobre una lista predefinida.

### 2.2. Filtros de Clasificación Contable

*   **Cuenta Contable:** "Rastreador de Imputaciones". Muestra todos los documentos que afectaron una cuenta específica (ej: buscar todo lo que movió la cuenta "Caja General").
*   **Centro de Costo:** Ideal para auditoría de presupuestos por departamento.
*   **Palabra Clave en Concepto:** Busca texto dentro de la descripción de los movimientos. Útil para encontrar rastros como "Ajuste", "Error", o nombres de proyectos específicos.

### 2.3. Filtros de Valor y Tiempo

*   **Rango de Fechas:** Delimita la búsqueda a un periodo fiscal específico.
*   **Filtro por Valor:** Herramienta de auditoría para detectar anomalías.
    *   *Ejemplo:* "Buscar todos los gastos MENORES a $1,000" (posible basura).
    *   *Ejemplo:* "Buscar todas las ventas MAYORES a $10,000,000" (transacciones significativas).

### 2.4. Opción "Incluir Anulados"

Por defecto, el sistema oculta los documentos que ya están anulados. Marque esta casilla si necesita reactivarlos o auditarlos.

---

## 3. Acciones de Gestión

Una vez obtenidos los resultados, seleccione los documentos usando las casillas de verificación (o el selector "Todos" en el encabezado de la tabla).

### 3.1. Anulación Masiva (Botón Naranja)

*   **Función:** Revierte los efectos contables de los documentos seleccionados sin borrarlos.
*   **Estado Resultante:** Los documentos pasan a estado **ANULADO**. Sus valores débito/crédito se vuelven cero internamente, pero el registro histórico permanece.
*   **Caso de Uso:** Errores contables donde se debe preservar la secuencia numérica (consecutivo) para cumplir con la legislación fiscal.

### 3.2. Eliminación Definitiva (Botón Rojo)

*   **Función:** Retira los documentos de la contabilidad activa y libera sus números consecutivos.
*   **Destino:** Los documentos **NO** desaparecen inmediatamente; son enviados a la **Papelera de Reciclaje** del sistema, desde donde podrían ser recuperados en caso de emergencia.
*   **Requisito de Seguridad:** El sistema exigirá que escriba la palabra clave `"ELIMINAR"` para confirmar esta acción crítica.
*   **Justificación:** Es **obligatorio** escribir una razón en el campo de texto (ej: "Error de digitación duplicado"). Esta nota quedará adjunta al registro en la papelera.

### 3.3. Modificar (Botón Azul)

*   **Restricción:** Solo funciona cuando se selecciona **un único documento**.
*   **Función:** Le redirige inmediatamente a la pantalla de Edición del documento seleccionado.

#### 3.3.1. Guía de Edición de Documentos

La interfaz de **Edición** es un entorno controlado diseñado para modificar transacciones contables ya guardadas. A diferencia de la creación inicial, este módulo impone restricciones estrictas para garantizar la integridad de la base de datos histórica.

#### 3.3.2. Estructura de la Pantalla

Al ingresar al modo de edición, la pantalla se divide en tres secciones críticas:

**A. Encabezado de Identificación (Zona Bloqueada)**
En la parte superior derecha, verá campos con fondo grisáceo que **NO** son editables por seguridad:
*   **Tipo de Documento y Número:** (Ej: *Comprobante #111*). Son inmutables para no romper la secuencia cronológica.

**B. Datos de Encabezado (Zona Editable)**
A la izquierda y centro, encontrará los campos modificables:
*   **Fecha:** Permite mover el documento en el tiempo (dentro de periodos abiertos).
*   **Beneficiario:** Para reasignar la transacción a otro Tercero.
*   **Centro de Costo:** Para reclasificar el gasto o ingreso.

**C. Tabla de Movimientos Contables**
El núcleo de la edición. Aquí se visualiza el asiento contable completo.
*   **Modificar Valores:** Haga clic en cualquier celda de Débito o Crédito para ajustar montos.
*   **Eliminar Filas (X Roja):** Borra movimientos erróneos.
*   **Agregar Fila (Botón Blanco):** Añade nuevas cuentas (ej: una retención olvidada).

#### 3.3.3. Validaciones y Guardado

> [!IMPORTANT]
> **La Regla de Oro: "Sumas Iguales"**
> El botón verde **"Guardar Cambios"** solo funcionará si la diferencia entre Débitos y Créditos es exactamente **$0,00**. Si los montos no coinciden, el sistema impedirá guardar para proteger la contabilidad.

### 3.4. Guardar como Plantilla (Botón Morado)

*   **Restricción:** Solo funciona con un único documento seleccionado.
*   **Función:** Clona la estructura del documento (cuentas, terceros, conceptos) y la guarda como una nueva **Plantilla** (ver *Capítulo 3*).
*   **Caso de Uso:** Si descubre que una factura compleja se repite mes a mes, puede convertirla en plantilla desde aquí para automatizarla en el futuro.

### 3.5. Reactivar (Botón Individual)

*   Si busca documentos anulados, aparecerá un botón de "Reactivar" (flecha circular) en cada fila. Esto restaura los valores contables originales del documento.

---

## 4. Consejos de Seguridad

1.  **Verifique el Contador:** Antes de presionar cualquier botón masivo, mire el número en "Resultados Encontrados" para asegurarse de que coincide con lo que espera.
2.  **Auditoría de Valores:** Use el filtro de "Valor Mayor Que" para revisar las transacciones más grandes del mes antes de cerrar el periodo.
3.  **Limpieza de Consecutivos:** Si tiene saltos en la numeración (Huecos), use esta herramienta para encontrar los documentos "basura" que están ocupando números y elimínelos para liberar la secuencia.