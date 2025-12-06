# Capítulo 46: Kardex Detallado por Producto

El **Kardex Detallado** es la vista de máxima granularidad para el análisis de inventario. A diferencia del reporte general, esta pantalla se enfoca en un único producto y muestra cronológicamente cada documento que afectó su saldo.

> **Nota de Navegación:** Esta pantalla generalmente se accede haciendo clic en las cifras de "Entradas" o "Salidas" desde el **Reporte de Movimiento Analítico** (Capítulo 45), permitiendo una auditoría profunda del origen de los datos.

## 1. Información del Encabezado

En la parte superior encontrará:
*   **Identificación del Producto:** Nombre completo y código del ítem analizado.
*   **Periodo del Reporte:** Las fechas "Desde" y "Hasta" que se están consultando (heredadas de la pantalla anterior).
*   **Filtro de Bodega:** Un menú desplegable que le permite alternar entre ver el movimiento consolidado de **"Todas las Bodegas"** o filtrar los movimientos de una bodega específica.

## 2. Estructura del Kardex

La tabla principal presenta la historia del producto, movimiento a movimiento:

### 2.1. Saldo Anterior
La primera fila (resaltada en amarillo) muestra el **Saldo Anterior**. Esto representa la cantidad y el valor total que tenía el producto justo antes de la fecha de inicio del reporte. Es el punto de partida para los cálculos siguientes.

### 2.2. Columnas de Movimiento
Para cada transacción registrada en el periodo, se detallan:
*   **Fecha:** Día en que se registró la operación.
*   **Documento:** Tipo y número del documento (ej. "Factura de Venta #123", "Compra #456", "Ajuste #789").
*   **Movimiento:** Descripción de la operación (ej. "Venta", "Compra", "Traslado Entrada").
*   **Bodega:** Nombre de la bodega donde ocurrió el movimiento.

### 2.3. Secciones de Cantidades y Costos
La tabla se divide en tres grandes secciones para facilitar la lectura:
*   **Entradas (Verde):** Muestra la cantidad que ingresó y su costo unitario de adquisición.
*   **Salidas (Rojo):** Muestra la cantidad que salió, su costo unitario y el costo total de la salida.
*   **Saldo (Azul):** Muestra el estado del inventario *después* de cada movimiento.
    *   **Cant:** Existencia física actual.
    *   **Costo Prom:** Costo promedio ponderado actualizado.
    *   **Valor Total:** Valor total del inventario (Cant * Costo Prom).

## 3. Exportación de Datos

Para facilitar el análisis externo o el archivo físico, dispone de dos opciones:
*   **Botón CSV (Excel):** Descarga un archivo plano compatible con Excel, ideal para realizar cálculos propios o tablas dinámicas.
*   **Botón PDF:** Genera un documento PDF con formato oficial, perfecto para imprimir o enviar por correo electrónico como soporte de auditoría.

---
**Tip de Auditoría:** Si detecta un saldo negativo o un costo promedio inusual, revise los movimientos cronológicos en esta pantalla para identificar el documento exacto que causó la distorsión (por ejemplo, una salida sin stock previo o una compra con costo cero).
