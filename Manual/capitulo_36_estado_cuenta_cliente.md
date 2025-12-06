# Estado de Cuenta (Clientes)

El reporte de **Estado de Cuenta** es una herramienta vital para la gestión de cartera. Proporciona una visión clara de las deudas pendientes de un cliente a una fecha de corte específica, clasificándolas por su antigüedad y estado de vencimiento.

## 1. Generación del Reporte

Para consultar el estado de cuenta de un cliente:

1.  **Cliente**: Seleccione el cliente de la lista desplegable. Solo aparecerán los terceros marcados como "Cliente" en la gestión de terceros.
2.  **Fecha de Corte**: Seleccione la fecha hasta la cual desea calcular la deuda.
    *   *Por defecto, el sistema selecciona la fecha de hoy.*
    *   Si selecciona una fecha pasada, el sistema calculará la deuda "retroactivamente" (ideal para cierres de mes).

Haga clic en **"Generar Estado"** para visualizar la información.

## 2. Interpretación de Resultados

### Listado de Facturas
El sistema muestra una tabla con todas las facturas que tienen saldo pendiente a la fecha de corte:
-   **Documento**: Tipo y número de la factura.
-   **Emisión**: Fecha original de la factura.
-   **Valor Original**: Monto total inicial.
-   **Abonos**: Pagos recibidos hasta la fecha.
-   **Saldo**: Valor que el cliente aún debe.
-   **Estado**: Indicador visual de salud de la deuda:
    -   <span style="color:green">**Vence en X días**</span>: La factura está vigente.
    -   <span style="color:red">**X días mora**</span>: La factura ya venció y está en mora.

### Análisis de Vencimientos (Aging)
En la parte inferior, encontrará un panel de colores que clasifica la deuda total según su antigüedad:
-   **Por Vencer**: Deuda sana, aún no exigible.
-   **1-30 Días**: Mora temprana.
-   **31-60 Días**: Mora media.
-   **61-90 Días**: Mora crítica.
-   **+90 Días**: Cartera de difícil cobro.

## 3. Exportación y Envío

Este reporte está diseñado para ser enviado directamente a sus clientes como cobro persuasivo:

-   **PDF**: Genera un documento formal con el logo de su empresa, listo para enviar por correo electrónico.
-   **CSV**: Descarga los datos en formato Excel para análisis interno.
