# Capítulo 45: Reporte de Movimiento Analítico (Kardex)

El **Reporte de Movimiento Analítico**, también conocido como **Kardex Analítico**, es una herramienta fundamental para el control detallado del inventario. Permite visualizar el flujo completo de cada producto (saldo inicial, entradas, salidas y saldo final) durante un periodo específico, facilitando la auditoría de existencias y la detección de inconsistencias.

## 1. Acceso al Módulo

Para acceder a este reporte, diríjase al menú principal:
*   **Ruta:** `Inventario y Logística` > `Estado General y Movimientos`
*   **Ruta Alternativa:** `Contabilidad` > `Reportes` > `Movimiento Analítico`

## 2. Filtros y Configuración

El módulo cuenta con un panel de filtros robusto que le permite refinar la búsqueda de información.

### 2.1. Filtros Básicos
*   **Rango de Fechas (Desde - Hasta):** Define el periodo a analizar. El sistema calcula el "Saldo Inicial" basándose en todos los movimientos anteriores a la fecha "Desde".
*   **Bodega:** Permite filtrar los movimientos de una bodega específica o ver el consolidado de todas las bodegas ("Todas las Bodegas").

### 2.2. Filtros Avanzados
Al hacer clic en el botón **"Más Filtros"**, se despliegan opciones adicionales:
*   **Grupo de Inventario:** Permite analizar solo los productos pertenecientes a una familia o categoría específica (ej. "Lácteos", "Electrónica").
*   **Producto Específico:** Permite buscar y seleccionar un único producto para ver su historial detallado.
*   **Modo de Visualización:**
    *   **Cantidad:** Muestra las cifras en unidades físicas.
    *   **Valor ($):** Muestra las cifras en términos monetarios (costo).

## 3. Interpretación de Resultados

Una vez generada la consulta, se presenta una tabla detallada con la siguiente estructura para cada producto:

| Columna | Descripción |
| :--- | :--- |
| **Producto** | Código y nombre del ítem. |
| **Saldo Inicial** | Cantidad y valor del producto al inicio del periodo seleccionado (antes de la fecha "Desde"). |
| **Entradas (+)** | Suma de todas las compras, traslados de entrada, devoluciones en venta y ajustes positivos durante el periodo. |
| **Salidas (-)** | Suma de todas las ventas, traslados de salida, devoluciones en compra y ajustes negativos durante el periodo. |
| **Saldo Final** | El resultado aritmético: *Inicial + Entradas - Salidas*. Representa la existencia teórica al final del periodo (fecha "Hasta"). |

### 3.1. Totales del Periodo
Al final de la tabla, una fila de **TOTALES** resume las cantidades y valores globales de todos los productos listados, permitiendo una visión macro del movimiento de inventario.

## 4. Trazabilidad (Drill-Down)

El reporte es interactivo. Si un producto tiene movimientos en el periodo (Entradas o Salidas > 0):
*   Los valores de **Cantidad de Entradas** y **Cantidad de Salidas** aparecen como enlaces (color verde o rojo respectivamente).
*   Al hacer clic en estos números, se abrirá una nueva pestaña con el **Kardex Detallado** de ese producto específico, mostrando documento por documento (facturas, recibos, ajustes) qué originó ese movimiento.

## 5. Exportación

*   **Botón PDF:** Genera un documento PDF formal con la información visible en pantalla, ideal para imprimir, archivar o presentar en auditorías.
*   **Botón Limpiar:** Reinicia todos los filtros a sus valores predeterminados.

---
> **Nota:** Este reporte es esencial para el cierre de mes y la conciliación de inventarios físicos vs. sistema.
