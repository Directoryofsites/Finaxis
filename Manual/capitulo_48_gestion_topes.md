# Capítulo 48: Gestión de Topes (Mínimos y Máximos)

El módulo de **Gestión de Topes** es su asistente inteligente para la reposición de inventario. Su función principal es analizar el saldo actual de cada producto frente a los límites (topes) establecidos en su ficha maestra, generando alertas automáticas de compra o sobre-stock.

## 1. Modos de Análisis

El sistema ofrece dos estrategias de análisis que puede alternar con los botones grandes en la parte superior:

### 1.1. 🚨 Mínimo: HACER PEDIDO
Este modo identifica los productos cuyo saldo actual está **por debajo** del stock mínimo permitido.
*   **Objetivo:** Evitar roturas de stock (quedarse sin mercancía).
*   **Decisión Sugerida:** "PEDIR". Indica que es urgente realizar una orden de compra al proveedor.
*   **Cálculo:** *Diferencia = Stock Mínimo - Saldo Actual*. Esta es la cantidad sugerida a pedir para volver a la zona segura.

### 1.2. ⚠️ Máximo: NO COMPRAR
Este modo identifica los productos cuyo saldo actual está **por encima** del stock máximo deseado.
*   **Objetivo:** Evitar sobre-costos de almacenamiento y capital inmovilizado.
*   **Decisión Sugerida:** "NO COMPRAR". Advierte que no se debe adquirir más mercancía e incluso sugiere realizar promociones para evacuar el exceso.
*   **Cálculo:** *Diferencia = Saldo Actual - Stock Máximo*. Esta es la cantidad de exceso que tiene en bodega.

## 2. Indicadores Clave (KPIs)

En la parte superior verá tres tarjetas con cifras en tiempo real:
*   **Alertas Mínimas:** Número de productos críticos que necesitan reposición inmediata.
*   **Alertas Máximas:** Número de productos con exceso de inventario.
*   **Total en Lista:** Cantidad total de ítems que requieren su atención según el filtro seleccionado.

## 3. Tabla de Resultados

La tabla detalla la situación de cada producto en alerta:
*   **Saldo Actual:** Existencia física a la fecha de corte.
*   **Mínimo / Máximo:** Los límites configurados en el sistema para ese producto.
*   **Diferencia:** La cantidad exacta que le falta (en alertas de mínimo) o le sobra (en alertas de máximo).
*   **Decisión:** Una etiqueta visual clara ("PEDIR" o "NO COMPRAR") para facilitar la toma de decisiones rápida.

## 4. Exportación

*   **Botón PDF:** Genera un reporte formal con la lista de productos en alerta. Este documento es ideal para entregárselo directamente al departamento de compras como una "Sugerencia de Pedido".

---
> **Nota Importante:** Para que este reporte funcione correctamente, asegúrese de haber configurado los campos "Stock Mínimo" y "Stock Máximo" en la ficha de creación de cada producto (Ver Capítulo: Catálogo de Productos).
