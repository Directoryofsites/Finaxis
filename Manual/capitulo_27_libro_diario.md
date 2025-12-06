# Libro Diario

El **Libro Diario** es un reporte contable fundamental que presenta, en orden cronológico, todas las operaciones (asientos) registradas en el sistema durante un periodo determinado. Es esencial para el análisis detallado de la contabilidad y la auditoría de transacciones.

## 1. Generación del Reporte

Para visualizar la información, debe definir los criterios de búsqueda en el panel superior:

| Campo | Descripción |
| :--- | :--- |
| **Tipo de Documento** | Permite filtrar por una fuente específica (ej. solo Facturas de Venta). Si se deja en "Todos", muestra la contabilidad completa. |
| **Fecha Inicio / Fin** | Define el rango temporal del reporte. Ambos campos son obligatorios. |

Una vez definidos los filtros, haga clic en el botón **🔍 Generar Reporte**.

## 2. Interpretación de Resultados

El sistema desplegará una tabla detallada con la siguiente información por cada movimiento:

- **Fecha**: Día en que se contabilizó la operación.
- **Documento**: Código y consecutivo del comprobante (ej. `FV #1025`).
- **Beneficiario**: Tercero involucrado en la transacción.
- **Cuenta**: Código y nombre de la cuenta contable afectada.
- **Concepto**: Descripción detallada del movimiento.
- **Débito / Crédito**: Valores monetarios del asiento.

### Totales de Control
Al final de la tabla, encontrará una fila de **Totales Generales** que suma todas las columnas de Débito y Crédito. En una contabilidad sana, estos dos valores deben ser **iguales** (principio de partida doble).

## 3. Exportación e Impresión

En la esquina superior derecha de la tabla de resultados, encontrará opciones para extraer la información:

- **<span style="color:green">📄 Exportar CSV</span>**: Descarga un archivo compatible con Excel, ideal para análisis de datos, tablas dinámicas o auditorías externas.
- **<span style="color:red">🖨️ Imprimir PDF</span>**: Genera un documento oficial en formato PDF, listo para archivar o presentar a la gerencia.
