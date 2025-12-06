# Manual de Usuario - Capítulo 53: Estado de Resultados Detallado (CC)

## 1. Introducción
El **Estado de Resultados Detallado por Centro de Costo** es un informe gerencial que permite medir la rentabilidad (Ganancias o Pérdidas) de una unidad de negocio específica.

A diferencia del Balance General que es una "foto" estática, este reporte es una "película" que muestra qué pasó en un periodo de tiempo: cuánto vendió esa sucursal, cuánto costó producirlo y cuánto se gastó en administración, para llegar a la utilidad final.

---

## 2. Criterios de Búsqueda (Filtros)

Para generar el análisis, configure los siguientes parámetros:

*   **Centro de Costo:**
    *   Seleccione un centro específico (ej: "Proyecto Edificio Norte") para ver solo su rentabilidad.
    *   Seleccione `Todos (Consolidado)` para ver el Estado de Resultados global de la empresa.
*   **Rango de Fechas:** Defina el periodo a evaluar (ej: Del 1 de Enero al 31 de Enero).

Haga clic en **Generar** para visualizar los datos.

---

## 3. Interpretación de Resultados

El reporte estructura la información de forma escalonada para llegar a la Utilidad Neta:

### 3.1. Ingresos Operacionales (+)
Son las ventas o servicios facturados por ese centro de costo.
*   *Detalle:* Se muestra cuenta por cuenta (ej: "4135 - Comercio al por mayor").

### 3.2. Costos de Venta (-)
Es lo que costó directamente producir el bien o servicio vendido.
*   *Cálculo:* `Ingresos - Costos = Utilidad Bruta`.

### 3.3. Gastos Operacionales (-)
Son los gastos necesarios para que el centro de costo funcione (Arriendos, Nómina Administrativa, Servicios).
*   *Detalle:* Se listan todas las cuentas de gasto (Clase 5) imputadas a este centro.

### 3.4. Utilidad Neta del Ejercicio (=)
Es el resultado final.
*   Si el valor es positivo (Verde), el centro de costo generó ganancias.
*   Si el valor es negativo (Rojo), el centro de costo dio pérdidas en ese periodo.

---

## 4. Exportación

En la parte superior derecha encontrará las opciones de descarga:

*   **CSV (Excel):** Descarga la tabla completa en formato plano, ideal para copiar y pegar en hojas de cálculo para análisis financieros avanzados.
*   **PDF:** Genera el informe oficial con membrete y firma, listo para presentar en juntas directivas.
