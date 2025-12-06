# Reporte de Movimiento por Tercero y Cuenta

El reporte de **Movimiento por Tercero y Cuenta** (también conocido como *Auxiliar por Tercero*) es una herramienta fundamental para la auditoría contable. Le permite visualizar detalladamente todas las transacciones asociadas a un tercero específico en un rango de fechas, desglosadas cuenta por cuenta.

## 1. Generación del Reporte

Para generar el reporte, debe configurar los siguientes parámetros obligatorios:

1.  **Tercero**: Seleccione la persona natural o jurídica que desea auditar. Puede buscar por nombre o razón social en la lista desplegable.
2.  **Rango de Fechas**: Defina las fechas "Desde" y "Hasta" para acotar la búsqueda.
3.  **Filtrar Cuentas (Opcional)**:
    *   Por defecto, el sistema muestra **"Todas las Cuentas"** donde el tercero ha tenido movimiento.
    *   Si desea auditar solo una cuenta específica (ej. *130505 Clientes Nacionales*), selecciónela en la lista.
    *   *Tip:* Puede seleccionar múltiples cuentas manteniendo presionada la tecla `Ctrl` (Windows) o `Cmd` (Mac).

Haga clic en el botón **"Consultar Movimientos"** para cargar la información.

## 2. Interpretación de Resultados

El reporte se estructura de manera jerárquica para facilitar la lectura:

### Estructura del Informe
-   **Saldo Inicial Tercero**: Es el saldo neto acumulado de ese tercero en *todas* las cuentas antes de la fecha de inicio seleccionada.
-   **Agrupación por Cuenta**: Los movimientos se agrupan por código contable.
    -   Cada grupo inicia indicando el **Saldo Inicial de la Cuenta** específica.
    -   Se listan los movimientos cronológicamente (Fecha, Documento, Concepto, Débito, Crédito).
    -   La columna **Saldo Parcial** muestra el acumulado línea a línea.

### Totales
Al final del reporte encontrará una fila de totales con:
-   Total Débitos del periodo.
-   Total Créditos del periodo.
-   **Saldo Final**: El estado de cuenta definitivo del tercero a la fecha de corte.

## 3. Herramientas Avanzadas

### Botón "Recalcular" (Reconstrucción de Saldos)
> [!WARNING]
> **¿Cuándo usar este botón?**
> Utilice esta opción **SOLO** si detecta inconsistencias en los saldos (ej. el saldo final no coincide con la suma de movimientos).
>
> Al hacer clic en "Recalcular", el sistema revisará **todo el historial** de movimientos del tercero desde el principio de los tiempos y reconstruirá los saldos acumulados. Esta operación puede tardar unos segundos.

### Exportación
-   **CSV**: Descarga un archivo plano ideal para auditorías en Excel.
-   **PDF**: Genera un documento formal listo para imprimir o enviar al cliente/proveedor como estado de cuenta.
