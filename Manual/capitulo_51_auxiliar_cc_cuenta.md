# Manual de Usuario - Capítulo 51: Auxiliar por Centro de Costo

## 1. Introducción
El reporte **Auxiliar por Centro de Costo y Cuenta** es una herramienta de auditoría detallada que le permite analizar todos los movimientos contables imputados a un centro de costo específico.

A diferencia de un Balance de Prueba que solo muestra saldos totales, este reporte desglosa **cada transacción individual** (facturas, egresos, notas), permitiéndole responder preguntas como: *"¿En qué se gastó exactamente el presupuesto del Departamento de Ventas este mes?"*.

---

## 2. Criterios de Búsqueda (Filtros)

Para generar el reporte, debe configurar los siguientes parámetros en la parte superior de la pantalla:

*   **Centro de Costo (Obligatorio):** Seleccione el área o proyecto que desea auditar. Solo aparecerán los centros de costo auxiliares (los que reciben movimientos).
*   **Cuenta (Opcional):**
    *   Si lo deja en `-- TODAS --`, el sistema mostrará todos los movimientos de todas las cuentas afectadas en ese centro de costo.
    *   Si selecciona una cuenta específica (ej: `510506 - Sueldos`), el reporte se filtrará para mostrar solo esa cuenta dentro del centro de costo seleccionado.
*   **Rango de Fechas:** Defina el periodo de análisis (Desde / Hasta).

Una vez configurados, haga clic en el botón **Generar Reporte**.

---

## 3. Interpretación de Resultados

El reporte presenta la información agrupada por **Cuenta Contable**. Esto significa que verá bloques separados para cada cuenta (ej: un bloque para "Arrendamientos", otro para "Servicios Públicos", etc.).

### 3.1. Estructura de Saldos
El reporte maneja tres niveles de saldos para facilitar la auditoría:

1.  **Saldo Inicial Centro de Costo:** Es el valor neto acumulado de *todas* las cuentas de ese centro de costo antes de la fecha de inicio consultada.
2.  **Saldo Inicial por Cuenta:** Al inicio de cada bloque de cuenta, verá con cuánto saldo venía esa cuenta específica antes del periodo.
3.  **Saldo Final:** Al final del reporte, se muestra el saldo total acumulado del centro de costo a la fecha de corte.

### 3.2. Columnas del Reporte
*   **Fecha:** Fecha de contabilización del movimiento.
*   **Documento:** Tipo y número del comprobante (ej: `FV-1025`, `CE-501`).
*   **Cuenta:** Código y nombre de la cuenta contable afectada.
*   **Beneficiario:** Tercero asociado al movimiento (Proveedor, Empleado, Cliente).
*   **Concepto:** Descripción detallada de la transacción.
*   **Débito / Crédito:** Valor del movimiento.
*   **Saldo:** Saldo parcial acumulado línea por línea.

---

## 4. Exportación y Herramientas

En la parte superior derecha de los resultados encontrará botones para descargar la información:

*   **CSV (Excel):** Descarga un archivo plano separado por comas, ideal para abrir en Excel y realizar tablas dinámicas o análisis propios.
*   **PDF:** Genera un documento imprimible con formato oficial, útil para presentar informes a gerencia o anexar a carpetas físicas.
